from telegram import Bot
from telegram.error import TelegramError
from app.config import Config

# Initialize Telegram bot
bot = Bot(token=Config.TELEGRAM_API_TOKEN)

def check_bot_admin(channel_username):
    try:
        chat = bot.get_chat(channel_username)
        admins = bot.get_chat_administrators(chat.id)
        bot_is_admin = any(admin.user.id == bot.get_me().id for admin in admins)
        return chat.id, bot_is_admin
    except TelegramError as e:
        raise Exception(f"Error checking bot admin status: {e}")

def post_to_channel(chat_id, message):
    try:
        bot.send_message(chat_id=chat_id, text=message)
    except TelegramError as e:
        raise Exception(f"Error posting to channel: {e}")

def post_winners_to_channel(chat_id, message):
    try:
        bot.send_message(chat_id=chat_id, text=message)
    except TelegramError as e:
        raise Exception(f"Error posting winners to channel: {e}")

