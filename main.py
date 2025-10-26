"""
FastAPI WebSocket Signaling Server for Telegram Mini App Voice/Video Chat
Handles WebRTC signaling (offer, answer, ICE candidates) and room management
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Set, Optional
import json
import asyncio
import os
from telegram_bot import bot

app = FastAPI(title="Telegram Mini App Signaling Server")

# CORS configuration for Telegram Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active connections: {room_id: {user_id: websocket}}
rooms: Dict[str, Dict[str, WebSocket]] = {}

# Store user information: {user_id: {name, photo_url, room_id}}
users: Dict[str, dict] = {}


class ConnectionManager:
    """Manages WebSocket connections for rooms"""
    
    async def connect(self, websocket: WebSocket, room_id: str, user_id: str, user_info: dict):
        """Add user to room"""
        await websocket.accept()
        
        if room_id not in rooms:
            rooms[room_id] = {}
        
        rooms[room_id][user_id] = websocket
        users[user_id] = {
            **user_info,
            "room_id": room_id
        }
        
        # Notify all users in room about new participant
        await self.broadcast_to_room(room_id, {
            "type": "user_joined",
            "user_id": user_id,
            "user_info": user_info,
            "participants": self.get_room_participants(room_id)
        }, exclude_user=None)
    
    def disconnect(self, room_id: str, user_id: str):
        """Remove user from room"""
        if room_id in rooms and user_id in rooms[room_id]:
            del rooms[room_id][user_id]
            
            if not rooms[room_id]:
                del rooms[room_id]
        
        if user_id in users:
            del users[user_id]
    
    async def broadcast_to_room(self, room_id: str, message: dict, exclude_user: Optional[str] = None):
        """Send message to all users in room"""
        if room_id not in rooms:
            return
        
        disconnected_users = []
        
        for user_id, websocket in rooms[room_id].items():
            if user_id == exclude_user:
                continue
            
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(room_id, user_id)
    
    async def send_to_user(self, room_id: str, user_id: str, message: dict):
        """Send message to specific user"""
        if room_id in rooms and user_id in rooms[room_id]:
            try:
                await rooms[room_id][user_id].send_json(message)
            except Exception:
                self.disconnect(room_id, user_id)
    
    def get_room_participants(self, room_id: str) -> list:
        """Get list of participants in room"""
        if room_id not in rooms:
            return []
        
        participants = []
        for user_id in rooms[room_id].keys():
            if user_id in users:
                participants.append({
                    "user_id": user_id,
                    **users[user_id]
                })
        
        return participants


manager = ConnectionManager()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Telegram Mini App Signaling Server",
        "active_rooms": len(rooms),
        "active_users": len(users)
    }


@app.get("/api/ice-config")
async def get_ice_config():
    """
    Get ICE server configuration including STUN/TURN servers
    TURN credentials can be configured via environment variables:
    - TURN_URL: TURN server URL (default: turn:global.relay.metered.ca:80)
    - TURN_USERNAME: TURN server username
    - TURN_PASSWORD: TURN server password
    """
    ice_servers = [
        {
            "urls": "stun:stun.l.google.com:19302"
        },
        {
            "urls": "stun:stun1.l.google.com:19302"
        }
    ]
    
    # Add TURN servers if credentials are configured
    turn_url = os.getenv("TURN_URL", "turn:global.relay.metered.ca:80")
    turn_username = os.getenv("TURN_USERNAME")
    turn_password = os.getenv("TURN_PASSWORD")
    
    if turn_username and turn_password:
        # Add TURN servers with valid credentials
        ice_servers.extend([
            {
                "urls": turn_url,
                "username": turn_username,
                "credential": turn_password
            },
            {
                "urls": turn_url.replace(":80", ":80?transport=tcp"),
                "username": turn_username,
                "credential": turn_password
            },
            {
                "urls": turn_url.replace(":80", ":443"),
                "username": turn_username,
                "credential": turn_password
            }
        ])
    else:
        # Use public STUN servers only (fallback for development)
        # Note: Without TURN servers, connections may fail on restrictive networks
        ice_servers.append({
            "urls": "stun:stun2.l.google.com:19302"
        })
    
    return {
        "iceServers": ice_servers,
        "iceCandidatePoolSize": 10
    }


@app.get("/api/user/{user_id}")
async def get_user_info(user_id: int):
    """
    Get enhanced user information from Telegram Bot API
    Requires TELEGRAM_BOT_TOKEN environment variable
    """
    if not bot.is_configured():
        return {
            "success": False,
            "message": "Telegram Bot API не настроен. Установите TELEGRAM_BOT_TOKEN в переменных окружения."
        }
    
    photos = await bot.get_user_profile_photos(user_id)
    
    if photos and photos.get("total_count", 0) > 0:
        # Get first photo
        photo = photos["photos"][0][-1]  # Largest size
        file_id = photo["file_id"]
        photo_url = await bot.get_file_url(file_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "photo_url": photo_url,
            "has_photo": True
        }
    
    return {
        "success": True,
        "user_id": user_id,
        "has_photo": False
    }


@app.post("/api/room/{room_id}/participants/notify")
async def notify_room_participants(room_id: str, user_id: int):
    """
    Send list of participants to user via Telegram bot
    """
    if not bot.is_configured():
        return {
            "success": False,
            "message": "Telegram Bot API не настроен"
        }
    
    participants = manager.get_room_participants(room_id)
    success = await bot.notify_participant_list(user_id, room_id, participants)
    
    return {
        "success": success,
        "message": "Уведомление отправлено" if success else "Ошибка отправки уведомления"
    }


@app.get("/api/room/{room_id}/participants")
async def get_room_participants(room_id: str):
    """
    Get list of participants in a room
    """
    participants = manager.get_room_participants(room_id)
    return {
        "room_id": room_id,
        "participants": participants,
        "count": len(participants)
    }


@app.post("/api/notify/joined")
async def notify_user_joined(user_id: int, user_name: str, room_id: str):
    """
    Notify user that they joined a room via Telegram
    """
    if not bot.is_configured():
        return {"success": False, "message": "Bot не настроен"}
    
    success = await bot.notify_user_joined(user_id, user_name, room_id)
    return {"success": success}


@app.websocket("/ws/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: str):
    """
    WebSocket endpoint for signaling
    Handles WebRTC offer, answer, and ICE candidate exchange
    """
    user_info = None
    
    try:
        # Wait for initial user info
        await websocket.accept()
        init_message = await websocket.receive_json()
        
        if init_message.get("type") == "join":
            user_info = init_message.get("user_info", {})
            
            # Add user to room
            if room_id not in rooms:
                rooms[room_id] = {}
            
            rooms[room_id][user_id] = websocket
            users[user_id] = {
                **user_info,
                "room_id": room_id
            }
            
            # Send current participants to new user
            await websocket.send_json({
                "type": "room_state",
                "participants": manager.get_room_participants(room_id)
            })
            
            # Notify others about new participant
            await manager.broadcast_to_room(room_id, {
                "type": "user_joined",
                "user_id": user_id,
                "user_info": user_info
            }, exclude_user=user_id)
            
            # Send Telegram notification if bot is configured
            if bot.is_configured():
                try:
                    telegram_user_id = int(user_id) if user_id.isdigit() else None
                    if telegram_user_id:
                        user_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
                        asyncio.create_task(bot.notify_user_joined(telegram_user_id, user_name, room_id))
                except (ValueError, AttributeError):
                    pass  # user_id is not a Telegram ID
        
        # Handle signaling messages
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "offer":
                # Forward offer to target user
                target_user = data.get("target_user_id")
                await manager.send_to_user(room_id, target_user, {
                    "type": "offer",
                    "from_user_id": user_id,
                    "offer": data.get("offer")
                })
            
            elif message_type == "answer":
                # Forward answer to target user
                target_user = data.get("target_user_id")
                await manager.send_to_user(room_id, target_user, {
                    "type": "answer",
                    "from_user_id": user_id,
                    "answer": data.get("answer")
                })
            
            elif message_type == "ice_candidate":
                # Forward ICE candidate to target user
                target_user = data.get("target_user_id")
                await manager.send_to_user(room_id, target_user, {
                    "type": "ice_candidate",
                    "from_user_id": user_id,
                    "candidate": data.get("candidate")
                })
            
            elif message_type == "speaking":
                # Broadcast speaking status
                await manager.broadcast_to_room(room_id, {
                    "type": "speaking",
                    "user_id": user_id,
                    "is_speaking": data.get("is_speaking", False)
                }, exclude_user=user_id)
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Clean up on disconnect
        manager.disconnect(room_id, user_id)
        
        # Notify others about user leaving
        await manager.broadcast_to_room(room_id, {
            "type": "user_left",
            "user_id": user_id
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
