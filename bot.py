# bot.py

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import Channel, Giveaway, Participant, db
import os

TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN', '7514207604:AAE_p_eFFQ3yOoNn-GSvTSjte2l8UEHl7b8')

engine = create_engine(os.getenv('SQLALCHEMY_DATABASE_URI', 'postgresql://postgres.elaqzrcvbknbzvbkdwgp:iCcxsx4TpDLdwqzq@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'))
Session = sessionmaker(bind=engine)
session = Session()

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome! Use /create_giveaway to start a giveaway.')

def create_giveaway(update: Update, context: CallbackContext) -> None:
    # Implement your giveaway creation logic
    update.message.reply_text('Please provide giveaway details.')

def join_giveaway(update: Update, context: CallbackContext) -> None:
    giveaway_id = context.args[0]
    user = update.message.from_user.username
    if not user:
        update.message.reply_text('Could not retrieve your username.')
        return
    
    giveaway = session.query(Giveaway).get(giveaway_id)
    if giveaway:
        participant = Participant(username=user, giveaway_id=giveaway.id)
        session.add(participant)
        session.commit()
        update.message.reply_text(f'You have joined giveaway {giveaway_id}.')
    else:
        update.message.reply_text('Giveaway not found.')

def announce_winners(update: Update, context: CallbackContext) -> None:
    # Fetch winners from the database and announce them
    update.message.reply_text('Winners have been announced.')

def main() -> None:
    updater = Updater(TELEGRAM_API_TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('create_giveaway', create_giveaway))
    dispatcher.add_handler(CommandHandler('join_giveaway', join_giveaway))
    dispatcher.add_handler(CommandHandler('announce_winners', announce_winners))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
