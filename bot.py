import logging
import asyncio
from telegram import Bot
from telegram.ext import Application
import requests

# Replace with your actual Telegram API token
TELEGRAM_API_TOKEN = '7514207604:AAE_p_eFFQ3yOoNn-GSvTSjte2l8UEHl7b8'
# Replace with your actual backend URL
BACKEND_URL = 'https://backend1-production-29e4.up.railway.app'

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def notify_participant(user_id: int, message: str) -> None:
    try:
        bot = Bot(token=TELEGRAM_API_TOKEN)
        await bot.send_message(chat_id=user_id, text=message)
    except Exception as e:
        logger.error(f"Error sending message to user {user_id}: {e}")

async def notify_winner(user_id: int, message: str) -> None:
    try:
        bot = Bot(token=TELEGRAM_API_TOKEN)
        await bot.send_message(chat_id=user_id, text=message)
    except Exception as e:
        logger.error(f"Error sending message to user {user_id}: {e}")

async def post_giveaway_announcement(channel_id: str, message: str) -> None:
    try:
        bot = Bot(token=TELEGRAM_API_TOKEN)
        # If channel_id is not numeric, assume it's a username and prepend '@'
        chat_identifier = channel_id if channel_id.isnumeric() else f'@{channel_id}'
        await bot.send_message(chat_id=chat_identifier, text=message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error posting message to channel {channel_id}: {e}")

async def fetch_and_post_announcements():
    try:
        response = requests.get(f"{BACKEND_URL}/get_giveaway_announcements")
        data = response.json()
        
        if data.get('success'):
            announcements = data.get('announcements', [])
            for announcement in announcements:
                channel_id = announcement['channel_id']
                message = announcement['message']
                await post_giveaway_announcement(channel_id, message)
        else:
            logger.info("No announcements to post.")
    except Exception as e:
        logger.error(f"Error fetching announcements: {e}")

async def notify_participants_and_winners():
    try:
        response = requests.get(f"{BACKEND_URL}/get_pending_notifications")
        data = response.json()
        
        if data.get('success'):
            notifications = data.get('notifications', [])
            for notification in notifications:
                user_id = notification['user_id']
                message = notification['message']
                if notification['type'] == 'participant':
                    await notify_participant(user_id, message)
                elif notification['type'] == 'winner':
                    await notify_winner(user_id, message)
        else:
            logger.info("No notifications to send.")
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")

async def main() -> None:
    while True:
        await fetch_and_post_announcements()
        await notify_participants_and_winners()
        await asyncio.sleep(60)  # Wait for 60 seconds before the next check

if __name__ == '__main__':
    asyncio.run(main())
