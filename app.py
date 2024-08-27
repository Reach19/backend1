from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_cors import CORS
from flask_migrate import Migrate
import os
import requests
import random
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuring the SQLAlchemy Database URI and initializing the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.ggxkqovbruyvfhdfkasw:dk22POZZTvc4HC4W@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate

# Defining the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(100), nullable=False, unique=True)  # Store as String

class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Giveaway(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prize_amount = db.Column(db.Float, nullable=False)
    participants_count = db.Column(db.Integer, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(100), nullable=False)
    giveaway_id = db.Column(db.Integer, db.ForeignKey('giveaway.id'), nullable=False)

@app.route('/init_user', methods=['POST'])
def init_user():
    try:
        data = request.get_json()
        telegram_id = data.get('telegram_id')

        if not telegram_id:
            return jsonify({'success': False, 'message': 'Missing telegram_id'}), 400

        # Ensure telegram_id is treated as a string
        telegram_id_str = str(telegram_id)

        user = User.query.filter_by(telegram_id=telegram_id_str).first()
        if not user:
            user = User(telegram_id=telegram_id_str)
            db.session.add(user)
            db.session.commit()

        return jsonify({'success': True, 'user_id': user.id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Endpoint to add a channel
@app.route('/add_channel', methods=['POST'])
def add_channel():
    try:
        data = request.get_json()
        username = data.get('username')
        user_id = data.get('user_id')

        if not username or not user_id:
            return jsonify({'success': False, 'message': 'Missing username or user_id'}), 400

        # Ensure user_id is treated as an integer
        user_id = int(user_id)

        channel = Channel.query.filter_by(username=username, user_id=user_id).first()
        if channel:
            return jsonify({'success': False, 'message': 'Channel already exists.'}), 400

        channel = Channel(username=username, user_id=user_id)
        db.session.add(channel)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Channel added successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Endpoint to get channels for a specific creator
@app.route('/get_user_channels', methods=['GET'])
def get_user_channels():
    try:
        user_id = request.args.get('user_id')

        if not user_id:
            return jsonify({'success': False, 'message': 'Missing user_id parameter'}), 400

        # Ensure user_id is treated as an integer
        user_id = int(user_id)

        channels = Channel.query.filter_by(user_id=user_id).all()
        if not channels:
            return jsonify({'success': False, 'message': 'No channels found.'}), 404

        channel_list = [{'id': channel.id, 'username': channel.username} for channel in channels]
        return jsonify({'success': True, 'channels': channel_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Endpoint to create a giveaway
@app.route('/create_giveaway', methods=['POST'])
def create_giveaway():
    try:
        data = request.get_json()

        name = data.get('name')
        prize_amount = data.get('prize_amount')
        participants_count = data.get('participants_count')
        end_date = data.get('end_date')
        channel_id = data.get('channel_id')
        user_id = data.get('user_id')

        if not name or not prize_amount or not participants_count or not end_date or not channel_id or not user_id:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        giveaway = Giveaway(name=name, prize_amount=prize_amount, participants_count=participants_count,
                            end_date=end_date, channel_id=channel_id, user_id=user_id)
        
        db.session.add(giveaway)
        db.session.commit()

        # Send giveaway announcement to the channel
        channel = Channel.query.get(channel_id)
        if not channel:
            return jsonify({'success': False, 'message': 'Channel not found'}), 404

        bot_token = os.getenv('TELEGRAM_API_TOKEN')
        if not bot_token:
            return jsonify({'success': False, 'message': 'Telegram API token is not configured'}), 500
        
        send_message_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        
        message = (f"🎉 New Giveaway! 🎉\n\n"
                   f"Name: {name}\n"
                   f"Prize: ${prize_amount}\n"
                   f"Participants: {participants_count}\n"
                   f"Ends on: {end_date}\n\n"
                   f"Join now to win!")

        requests.post(send_message_url, data={
            'chat_id': f'@{channel.username}',
            'text': message
        })

        return jsonify({'success': True, 'message': 'Giveaway created and announced!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Endpoint to handle joining a giveaway
@app.route('/join_giveaway', methods=['POST'])
def join_giveaway():
    try:
        data = request.get_json()
        telegram_id = data.get('telegram_id')
        giveaway_id = data.get('giveaway_id')

        if not telegram_id or not giveaway_id:
            return jsonify({'success': False, 'message': 'Missing telegram_id or giveaway_id'}), 400

        telegram_id_str = str(telegram_id)
        giveaway_id_int = int(giveaway_id)

        participant = Participant.query.filter_by(telegram_id=telegram_id_str, giveaway_id=giveaway_id_int).first()
        if participant:
            return jsonify({'success': False, 'message': 'Already joined this giveaway'}), 400

        participant = Participant(telegram_id=telegram_id_str, giveaway_id=giveaway_id_int)
        db.session.add(participant)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Successfully joined the giveaway!'})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'You have already joined this giveaway.'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Additional function to announce the giveaway
def announce_giveaway(channel_id, giveaway_id, giveaway_name, prize, end_date):
    try:
        bot_token = '7514207604:AAE_p_eFFQ3yOoNn-GSvTSjte2l8UEHl7b8'
        join_url = f'https://t.me/giveaway_setota_bot/Giveaway?giveaway_id={giveaway_id}'
        message = (f"🎉 New Giveaway Alert! 🎉\n\n"
                   f"Name: {giveaway_name}\n"
                   f"Prize: ${prize}\n"
                   f"Ends on: {end_date}\n\n"
                   f"Join here: {join_url}")
        
        response = requests.post(
            f'https://api.telegram.org/bot{bot_token}/sendMessage',
            data={'chat_id': channel_id, 'text': message}
        )
        response.raise_for_status()
    except Exception as e:
        print(f"Error announcing giveaway: {e}")

@app.route('/select_winners', methods=['POST'])
def select_winners():
    try:
        data = request.get_json()
        giveaway_id = data.get('giveaway_id')

        if not giveaway_id:
            return jsonify({'success': False, 'message': 'Missing giveaway_id'}), 400

        giveaway_id_int = int(giveaway_id)
        giveaway = Giveaway.query.get(giveaway_id_int)

        if not giveaway:
            return jsonify({'success': False, 'message': 'Giveaway not found'}), 404

        # Ensure the giveaway has ended
        if giveaway.end_date > datetime.now():
            return jsonify({'success': False, 'message': 'Giveaway is not yet ended'}), 400

        participants = Participant.query.filter_by(giveaway_id=giveaway_id_int).all()
        if not participants:
            return jsonify({'success': False, 'message': 'No participants found'}), 404

        # Randomly select winners
        winner_count = min(giveaway.participants_count, len(participants))
        winners = random.sample(participants, winner_count)

        # Announce winners
        channel = Channel.query.get(giveaway.channel_id)
        if not channel:
            return jsonify({'success': False, 'message': 'Channel not found'}), 404

        bot_token = '7514207604:AAE_p_eFFQ3yOoNn-GSvTSjte2l8UEHl7b8'
        join_url = f'https://t.me/giveaway_setota_bot/Giveaway?giveaway_id={giveaway_id_int}'
        winner_text = "\n".join([f"Winner: {p.telegram_id}" for p in winners])
        message = (f"🏆 Giveaway Winners! 🏆\n\n"
                   f"{winner_text}\n\n"
                   f"Thank you all for participating! Stay tuned for more giveaways.\n\n"
                   f"Join our bot: {join_url}")

        send_message_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        requests.post(send_message_url, data={
            'chat_id': f'@{channel.username}',
            'text': message
        })

        return jsonify({'success': True, 'message': 'Winners selected and announced!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
# Run the Flask app
if __name__ == '__main__':
    app.run()
