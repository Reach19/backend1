from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_cors import CORS
from flask_migrate import Migrate
import os
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuring the SQLAlchemy Database URI and initializing the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.elaqzrcvbknbzvbkdwgp:iCcxsx4TpDLdwqzq@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate

# Defining the Channel and Giveaway models
class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    creator_id = db.Column(db.String(100), nullable=False)

class Giveaway(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prize_amount = db.Column(db.Float, nullable=False)
    participants_count = db.Column(db.Integer, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'), nullable=False)
    creator_id = db.Column(db.String(100), nullable=False)

@app.route('/')
def index():
    return "Backend is running"

# Endpoint to add a channel
@app.route('/add_channel', methods=['POST'])
def add_channel():
    try:
        data = request.get_json()
        username = data.get('username')
        creator_id = data.get('creator_id')

        if not username or not creator_id:
            return jsonify({'success': False, 'message': 'Missing username or creator_id'}), 400

        # Check if the bot is an admin in the channel
        bot_token = os.getenv('TELEGRAM_API_TOKEN')
        if not bot_token:
            return jsonify({'success': False, 'message': 'Bot token is missing.'}), 500

        bot_user_id = bot_token.split(':')[0]  # Extract the bot user ID from the token
        chat_member_url = f'https://api.telegram.org/bot{bot_token}/getChatMember'
        response = requests.get(chat_member_url, params={
            'chat_id': f'@{username}',
            'user_id': bot_user_id
        })

        if response.status_code != 200:
            return jsonify({'success': False, 'message': 'Failed to verify bot status in the channel.'}), 500

        chat_member_data = response.json().get('result', {})
        if 'administrator' not in chat_member_data.get('status', ''):
            return jsonify({'success': False, 'message': 'Bot is not an admin in the channel'}), 403

        channel = Channel(username=username, creator_id=creator_id)
        db.session.add(channel)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Channel added successfully!'})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Channel already exists or another error occurred.'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Endpoint to get channels for a specific creator
@app.route('/get_channels', methods=['GET'])
def get_channels():
    try:
        creator_id = request.args.get('creator_id')
        if not creator_id:
            return jsonify({'success': False, 'message': 'Missing creator_id parameter'}), 400
        
        channels = Channel.query.filter_by(creator_id=creator_id).all()
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
        creator_id = data.get('creator_id')

        if not name or not prize_amount or not participants_count or not end_date or not channel_id or not creator_id:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        giveaway = Giveaway(name=name, prize_amount=prize_amount, participants_count=participants_count,
                            end_date=end_date, channel_id=channel_id, creator_id=creator_id)
        
        db.session.add(giveaway)
        db.session.commit()

        # Send giveaway announcement to the channel
        channel = Channel.query.get(channel_id)
        bot_token = os.getenv('TELEGRAM_API_TOKEN')
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

# Run the Flask app
if __name__ == '__main__':
    app.run()
