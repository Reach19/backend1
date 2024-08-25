from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import asyncio
import os
import threading

# Initialize Telegram bot
TELEGRAM_API_TOKEN = '7514207604:AAE_p_eFFQ3yOoNn-GSvTSjte2l8UEHl7b8'
application = Application.builder().token(TELEGRAM_API_TOKEN).build()

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome to the Giveaway Bot!")

async def create(update: Update, context: CallbackContext):
    # Extract data from the message and create a giveaway
    await update.message.reply_text("Giveaway created successfully!")

async def join(update: Update, context: CallbackContext):
    # Extract data from the message and join a giveaway
    await update.message.reply_text("You have joined the giveaway!")

def main():
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('create', create))
    application.add_handler(CommandHandler('join', join))

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    bot_thread = threading.Thread(target=main)
    bot_thread.start()
