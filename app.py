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
    username = db.Column(db.String(100), nullable=True)  # Optional for public channels
    chat_id = db.Column(db.BigInteger, nullable=True)   # Required for private channels
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Giveaway(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prize_amount = db.Column(db.Float, nullable=False)
    participants_count = db.Column(db.Integer, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    announced = db.Column(db.Boolean, default=False) 

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(100), nullable=False)
    giveaway_id = db.Column(db.Integer, db.ForeignKey('giveaway.id'), nullable=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    message = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'participant' or 'winner'
    sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def add_participant_notification(user_id, giveaway_name):
    notification = Notification(
        user_id=user_id,
        message=f"You have successfully joined the giveaway: {giveaway_name}",
        type='participant'
    )
    db.session.add(notification)
    db.session.commit()

# Function to add a winner notification
def add_winner_notification(user_id, giveaway_name):
    notification = Notification(
        user_id=user_id,
        message=f"Congratulations! You are one of the winners of the giveaway: {giveaway_name}",
        type='winner'
    )
    db.session.add(notification)
    db.session.commit()



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
        chat_id = data.get('chat_id')  # New field for numeric chat_id
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'success': False, 'message': 'Missing user_id'}), 400

        # Convert user_id to integer
        user_id = int(user_id)

        # Check for existing channel
        existing_channel = Channel.query.filter_by(username=username, user_id=user_id).first() if username else Channel.query.filter_by(chat_id=chat_id, user_id=user_id).first()
        if existing_channel:
            return jsonify({'success': False, 'message': 'Channel already exists.'}), 400

        # Create new channel
        channel = Channel(username=username, chat_id=chat_id, user_id=user_id)
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
                            end_date=end_date, channel_id=channel_id, user_id=user_id, announced=False)
        
        db.session.add(giveaway)
        db.session.commit()

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



@app.route('/get_giveaway_announcements', methods=['GET'])
def get_giveaway_announcements():
    try:
        current_time = datetime.now()
        # Assuming Giveaway has a 'announced' flag to track if it's announced
        pending_announcements = Giveaway.query.filter_by(announced=False).filter(Giveaway.end_date > current_time).all()

        announcements = []
        for giveaway in pending_announcements:
            channel_id = giveaway.channel_id
            message = f"🎉 New Giveaway: {giveaway.name}\nPrize: {giveaway.prize_amount}\nEnds: {giveaway.end_date}"
            
            # Add to the list of announcements
            announcements.append({
                'channel_id': channel_id,
                'message': message
            })
            
            # Mark the giveaway as announced
            giveaway.announced = True
            db.session.commit()

        return jsonify({'success': True, 'announcements': announcements})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/get_pending_notifications', methods=['GET'])
def get_pending_notifications():
    try:
        # Assuming you have a Notifications model to track messages that need to be sent
        pending_notifications = Notifications.query.filter_by(sent=False).all()

        notifications = []
        for notification in pending_notifications:
            notifications.append({
                'user_id': notification.user_id,
                'message': notification.message,
                'type': notification.type  # 'participant' or 'winner'
            })
            
            # Mark the notification as sent
            notification.sent = True
            db.session.commit()

        return jsonify({'success': True, 'notifications': notifications})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


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
