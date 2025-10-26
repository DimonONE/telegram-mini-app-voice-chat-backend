# Telegram Mini App - Voice & Video Chat

Полнофункциональное Telegram Mini App с голосовым и видеочатом, которое стабильно работает даже при слабом интернете.

## 🚀 Возможности

- ✅ Запуск внутри Telegram через WebApp API
- ✅ Авторизация через Telegram (отображение имени и аватара)
- ✅ Голосовой и видеочат через WebRTC
- ✅ Комнаты по ID (например, "room123")
- ✅ Список участников с аватарами Telegram
- ✅ Индикатор говорящих (анимация и подсветка)
- ✅ Управление микрофоном и камерой
- ✅ Статус "В эфире" для участников
- ✅ Автоматическое обновление при входе/выходе
- ✅ Стабильная работа при слабом интернете (STUN/TURN)
- ✅ UI в стиле Telegram (светлая/тёмная тема)

## 📋 Требования

- Python 3.11+
- Node.js 20+

## 🛠 Установка

1. **Установите зависимости Python:**
```bash
pip install -r requirements.txt
```

2. **Установите зависимости Node.js:**
```bash
npm install
```

## ▶️ Запуск

### Запуск Backend (Signaling Server)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Backend будет доступен на `http://localhost:8000`

### Запуск Frontend

```bash
npm run dev
```

Frontend будет доступен на `http://localhost:5000`

## 📱 Настройка Telegram Bot для Mini App

### 1. Создайте бота

Откройте [@BotFather](https://t.me/BotFather) в Telegram и создайте нового бота:

```
/newbot
```

### 2. Настройте Mini App

После создания бота, установите WebApp URL:

```
/newapp
```

Выберите своего бота и введите:
- **Title**: Voice Chat
- **Description**: Голосовой и видеочат в Telegram
- **Photo**: Загрузите иконку (512x512 px)
- **Web App URL**: `https://your-domain.com` (или Replit URL после публикации)

### 3. Пример настройки через Bot API

Вы также можете настроить через Bot API:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setChatMenuButton" \
  -H "Content-Type: application/json" \
  -d '{
    "menu_button": {
      "type": "web_app",
      "text": "Open Voice Chat",
      "web_app": {
        "url": "https://your-domain.com"
      }
    }
  }'
```

## 🔧 Конфигурация TURN сервера

⚠️ **ВАЖНО**: Для стабильной работы в production рекомендуется настроить TURN сервер!

Без TURN сервера приложение будет использовать только STUN, и соединения могут не работать на ограниченных сетях.

### Настройка через переменные окружения

1. Скопируйте `.env.example` в `.env`:
```bash
cp .env.example .env
```

2. Получите бесплатные учётные данные TURN сервера:

- **[Metered OpenRelay](https://www.metered.ca/tools/openrelay/)** - бесплатный TURN сервер
- **[Twilio STUN/TURN](https://www.twilio.com/stun-turn)** - 10 ГБ бесплатно
- **[Xirsys](https://xirsys.com/)** - бесплатный план для разработки

3. Обновите `.env` с вашими учётными данными:

```bash
TURN_URL=turn:global.relay.metered.ca:80
TURN_USERNAME=ваш-username
TURN_PASSWORD=ваш-password
```

4. Перезапустите backend:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Автоматическая конфигурация

Приложение автоматически:
- Загружает ICE конфигурацию с backend при подключении
- Использует TURN сервер, если указаны учётные данные
- Переключается на STUN-only для разработки без TURN

### Проверка конфигурации

Откройте `http://localhost:8000/api/ice-config` чтобы увидеть текущую конфигурацию ICE серверов.

## 📁 Структура проекта

```
.
├── main.py                      # FastAPI signaling server
├── requirements.txt             # Python зависимости
├── package.json                 # Node.js зависимости
├── vite.config.js              # Vite конфигурация
├── tailwind.config.js          # TailwindCSS конфигурация
├── index.html                  # HTML entry point
└── src/
    ├── main.jsx                # React entry point
    ├── App.jsx                 # Главный компонент
    ├── index.css               # Глобальные стили
    ├── components/
    │   ├── RoomJoin.jsx        # Компонент входа в комнату
    │   ├── VoiceChat.jsx       # Главный компонент чата
    │   ├── ParticipantList.jsx # Список участников
    │   ├── VideoGrid.jsx       # Сетка видео
    │   └── ControlPanel.jsx    # Панель управления
    └── hooks/
        └── useWebRTC.js        # WebRTC логика
```

## 🌐 Развертывание

Приложение готово к развертыванию на Replit:

1. Frontend и Backend автоматически запустятся
2. Используйте предоставленный Replit URL в настройках Telegram Bot
3. HTTPS включен автоматически для Telegram Mini Apps

## 💡 Использование

1. Откройте приложение в Telegram
2. Введите ID комнаты (например, "room123")
3. Разрешите доступ к микрофону
4. Поделитесь ID комнаты с друзьями
5. Общайтесь голосом или включите камеру для видео!

## 🔒 Безопасность

- Все WebRTC соединения зашифрованы (DTLS-SRTP)
- Signaling через WebSocket
- Никакие медиа не проходят через сервер (peer-to-peer)
- Поддержка HTTPS для Telegram Mini Apps

## 📝 Лицензия

MIT

## 🤝 Поддержка

При возникновении проблем проверьте:
1. Разрешения на доступ к микрофону/камере
2. HTTPS используется (обязательно для WebRTC)
3. Backend сервер запущен и доступен
4. WebSocket соединение установлено

---

Создано для стабильной работы в Telegram с поддержкой слабого интернета 🚀
