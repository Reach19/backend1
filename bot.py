import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import asyncio

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Telegram bot
TELEGRAM_API_TOKEN = '7514207604:AAE_p_eFFQ3yOoNn-GSvTSjte2l8UEHl7b8'

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome to the Giveaway Bot!")
    logger.info(f"User {update.effective_user.id} started the bot.")

async def create(update: Update, context: CallbackContext):
    await update.message.reply_text("Giveaway created successfully!")
    logger.info(f"User {update.effective_user.id} created a giveaway.")

async def join(update: Update, context: CallbackContext):
    await update.message.reply_text("You have joined the giveaway!")
    logger.info(f"User {update.effective_user.id} joined a giveaway.")

async def run_bot():
    # Initialize the application
    application = Application.builder().token(TELEGRAM_API_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('create', create))
    application.add_handler(CommandHandler('join', join))

    await application.initialize()

    # Start polling for updates
    await application.start()
    
    logger.info("Bot started. Waiting for updates...")

    # Keep the bot running with idle()
    try:
        await asyncio.Event().wait()  # Keeps the bot running indefinitely
    except KeyboardInterrupt:
        logger.info("Bot interrupted and stopping...")
    finally:
        await application.stop()
        logger.info("Bot stopped.")

def main():
    # Run the bot
    try:
        asyncio.run(run_bot())
    except RuntimeError as e:
        if "Cannot close a running event loop" in str(e):
            # Skip closing the event loop as it's already running
            logger.warning("Attempted to close a running event loop.")
        else:
            logger.error("An unexpected RuntimeError occurred.", exc_info=True)
            raise

if __name__ == '__main__':
    main()

