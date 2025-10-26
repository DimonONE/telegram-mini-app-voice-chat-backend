"""
Telegram Bot API Integration
Handles user data fetching and notifications
"""

import httpx
import os
from typing import Optional, Dict, Any
import asyncio


class TelegramBot:
    """Telegram Bot API client"""
    
    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        
    def is_configured(self) -> bool:
        """Check if bot token is configured"""
        return bool(self.bot_token)
    
    async def get_user_profile_photos(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user profile photos
        https://core.telegram.org/bots/api#getuserprofilephotos
        """
        if not self.is_configured():
            return None
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/getUserProfilePhotos",
                    params={"user_id": user_id, "limit": 1}
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("ok") and data.get("result", {}).get("total_count", 0) > 0:
                    return data["result"]
                return None
            except Exception as e:
                print(f"Error fetching user profile photos: {e}")
                return None
    
    async def get_file_url(self, file_id: str) -> Optional[str]:
        """
        Get file download URL
        https://core.telegram.org/bots/api#getfile
        """
        if not self.is_configured():
            return None
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/getFile",
                    params={"file_id": file_id}
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("ok"):
                    file_path = data["result"]["file_path"]
                    return f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                return None
            except Exception as e:
                print(f"Error getting file URL: {e}")
                return None
    
    async def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML") -> bool:
        """
        Send message to user
        https://core.telegram.org/bots/api#sendmessage
        """
        if not self.is_configured():
            print("Bot token not configured, cannot send message")
            return False
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data.get("ok", False)
            except Exception as e:
                print(f"Error sending message: {e}")
                return False
    
    async def notify_user_joined(self, user_id: int, user_name: str, room_id: str) -> bool:
        """
        Notify user that they joined a voice chat room
        """
        text = f"🎙 <b>Вы присоединились к голосовому чату</b>\n\n" \
               f"Комната: <code>{room_id}</code>\n" \
               f"Пользователь: {user_name}"
        
        return await self.send_message(user_id, text)
    
    async def notify_participant_list(self, user_id: int, room_id: str, participants: list) -> bool:
        """
        Send participant list to user
        """
        if not participants:
            text = f"📋 <b>Участники комнаты {room_id}</b>\n\nВ комнате пока никого нет."
        else:
            participants_text = "\n".join([
                f"• {p.get('first_name', '')} {p.get('last_name', '')} (@{p.get('username', 'N/A')})"
                for p in participants
            ])
            text = f"📋 <b>Участники комнаты {room_id}</b>\n\n{participants_text}\n\n" \
                   f"Всего участников: {len(participants)}"
        
        return await self.send_message(user_id, text)
    
    async def notify_user_speaking(self, user_id: int, speaker_name: str) -> bool:
        """
        Notify user about someone speaking
        """
        text = f"🎤 <b>{speaker_name}</b> говорит сейчас"
        return await self.send_message(user_id, text)


# Global bot instance
bot = TelegramBot()
