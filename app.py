from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from flask_cors import CORS
from flask_migrate import Migrate
from datetime import datetime, timezone
import random
import traceback 
import logging

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://yabetsma.github.io"]}})

# Configuring the SQLAlchemy Database URI and initializing the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.ggxkqovbruyvfhdfkasw:dk22POZZTvc4HC4W@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate

# Define the User model
# models.py

from sqlalchemy import Column, String, Integer, Text

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.Text, nullable=False, unique=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)     
    username = db.Column(db.String, nullable=True, unique=True) 


# Define the Channel model
class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=True)  # Optional for public channels
    chat_id = db.Column(db.BigInteger, nullable=True)  # Required for private channels
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Define the Giveaway model
class Giveaway(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prize_amount = db.Column(db.Float, nullable=False)
    participants_count = db.Column(db.Integer, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    announced = db.Column(db.Boolean, default=False)  # For giveaway announcement
    winners_announced = db.Column(db.Boolean, default=False)  # New column for winner announcement

# Define other models...


# Define the Participant model
class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    giveaway_id = db.Column(db.Integer, db.ForeignKey('giveaway.id'), nullable=False)

# Define the Notification model
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'participant' or 'winner'
    sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Define the Winner model
class Winner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    giveaway_id = db.Column(db.Integer, db.ForeignKey('giveaway.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prize_amount = db.Column(db.Float, nullable=False)  # New field to store the prize amount for each winner
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notified = db.Column(db.Boolean, default=False)


# Utility function to add a notification
def add_notification(user_id, message, notif_type):
    notification = Notification(
        user_id=user_id,
        message=message,
        type=notif_type
    )
    db.session.add(notification)
    db.session.commit()

# Endpoint to initialize a user
@app.route('/init_user', methods=['POST'])
def init_user():
    try:
        data = request.get_json()
        telegram_id = str(data.get('telegram_id'))  # Ensure it's treated as a string
        first_name = data.get('first_name')  # Get first name
        last_name = data.get('last_name')    # Get last name
        username = data.get('username')

        if not telegram_id:
            return jsonify({'success': False, 'message': 'Missing telegram_id'}), 400

        # Check if the user already exists
        user = User.query.filter_by(telegram_id=telegram_id).first()

        if not user:
            # If not, create a new user
            user = User(telegram_id=telegram_id, first_name=first_name, last_name=last_name, username=username)
            db.session.add(user)
            db.session.commit()
        else:
            # Update the user's name if it already exists
            user.first_name = first_name
            user.last_name = last_name
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
        chat_id = data.get('chat_id')  # Numeric chat_id
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'success': False, 'message': 'Missing user_id'}), 400

        existing_channel = Channel.query.filter_by(chat_id=chat_id, user_id=user_id).first()
        if existing_channel:
            return jsonify({'success': False, 'message': 'Channel already exists.'}), 400

        channel = Channel(username=username, chat_id=chat_id, user_id=user_id)
        db.session.add(channel)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Channel added successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Endpoint to get channels for a specific user
@app.route('/get_user_channels', methods=['GET'])
def get_user_channels():
    try: # Keep the try block, but enhance error logging
        user_id_str = request.args.get('user_id')

        if not user_id_str:
            return jsonify({'success': False, 'message': 'Missing user_id parameter'}), 400

        try:
            user_id = int(user_id_str) # Convert user_id to integer
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid user_id format. Must be an integer.'}), 400

        channels = Channel.query.filter_by(user_id=user_id).all()
        if not channels:
            return jsonify({'success': False, 'message': 'No channels found for this user.'}), 404

        channel_list = [{'id': channel.id, 'username': channel.username} for channel in channels]
        return jsonify({'success': True, 'channels': channel_list})

    except Exception as e:
        error_message = str(e)
        trace = traceback.format_exc() # Get the full traceback
        logger.error(f"Error in /get_user_channels: {error_message}\nTraceback:\n{trace}") # Log detailed error
        return jsonify({'success': False, 'message': 'Backend error fetching channels', 'error': error_message}), 500
    
# Endpoint to create a giveaway
@app.route('/create_giveaway', methods=['POST'])
def create_giveaway():
    try:
        data = request.get_json()
        end_date_str = data.get('end_date')

        name = data.get('name')
        prize_amount = data.get('prize_amount')
        participants_count = data.get('participants_count')
        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00')) # Handles ISO string
        channel_id = data.get('channel_id')
        user_id = data.get('user_id')

        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        else:
            end_date = end_date.astimezone(timezone.utc)

        if not all([name, prize_amount, participants_count, end_date, channel_id, user_id]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        giveaway = Giveaway(
            name=name, 
            prize_amount=prize_amount, 
            participants_count=participants_count,
            end_date=end_date, 
            channel_id=channel_id, 
            user_id=user_id,
            announced=False
        )
        
        db.session.add(giveaway)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Giveaway created successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Endpoint to join a giveaway
@app.route('/join_giveaway', methods=['POST'])
def join_giveaway():
    try:
        data = request.get_json()
        telegram_id = str(data.get('telegram_id'))  # Convert to string
        giveaway_id = data.get('giveaway_id')

        if not telegram_id or not giveaway_id:
            return jsonify({'success': False, 'message': 'Missing telegram_id or giveaway_id'}), 400

        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        participant = Participant.query.filter_by(user_id=user.id, giveaway_id=giveaway_id).first()
        if participant:
            return jsonify({'success': False, 'message': 'Already joined this giveaway'}), 400

        participant = Participant(user_id=user.id, giveaway_id=giveaway_id)
        db.session.add(participant)
        db.session.commit()

        add_notification(user.id, f"You have successfully joined the giveaway: {Giveaway.query.get(giveaway_id).name}", 'participant')

        return jsonify({'success': True, 'message': 'Successfully joined the giveaway!'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error occurred: ' + str(e)}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': 'Unexpected error: ' + str(e)}), 500

# Function to select winners
def select_winners(giveaway_id, number_of_winners):
    giveaway = Giveaway.query.get(giveaway_id)
    if not giveaway:
        return {"error": "Giveaway not found"}

    participants = Participant.query.filter_by(giveaway_id=giveaway_id).all()
    if len(participants) < number_of_winners:
        return {"error": "Not enough participants"}

    selected_winners = random.sample(participants, number_of_winners)
    winner_ids = []

    for participant in selected_winners:
        winner = Winner(giveaway_id=giveaway.id, user_id=participant.user_id)
        db.session.add(winner)
        winner_ids.append(participant.user_id)

        # Add a notification for the winner
        add_notification(participant.user_id, f"Congratulations! You have won the giveaway: {giveaway.name}", 'winner')

    db.session.commit()
    return {"success": True, "winner_ids": winner_ids}

# Endpoint to get winners of a giveaway
@app.route('/api/giveaway/<int:giveaway_id>/winners', methods=['GET'])
def get_winners(giveaway_id):
    try:
        giveaway = Giveaway.query.get(giveaway_id)
        if not giveaway:
            return jsonify({'success': False, 'message': 'Giveaway not found'}), 404

        # Query to get winners along with their user details
        winners = db.session.query(Winner, User).join(User, Winner.user_id == User.id).filter(Winner.giveaway_id == giveaway_id).all()

        # Create a list of winners with their first and last names
        winner_list = [{
            'id': winner.Winner.id,
            'user_id': winner.User.id,
            'first_name': winner.User.first_name,
            'last_name': winner.User.last_name,
            'giveaway_id': winner.Winner.giveaway_id,
            'notified': winner.Winner.notified
        } for winner in winners]

        return jsonify({'success': True, 'winners': winner_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/payment_method', methods=['POST'])
def add_payment_method():
    data = request.get_json()
    user_id = data.get('user_id')
    payment_method = data.get('payment_method')

    try:
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Save the payment method for the user (you can store this in a new database field)
        user.payment_method = payment_method
        db.session.commit()

        return jsonify({'success': True, 'message': 'Payment method added successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Function to send scheduled notifications for ending giveaways
def check_and_send_notifications():
    giveaways = Giveaway.query.filter(Giveaway.end_date <= datetime.utcnow(), Giveaway.announced == False).all()

    for giveaway in giveaways:
        select_winners(giveaway.id, 1)
        giveaway.announced = True
        db.session.commit()

# Endpoint to fetch user notifications
@app.route('/user_notifications', methods=['GET'])
def user_notifications():
    try:
        user_id = request.args.get('user_id')

        if not user_id:
            return jsonify({'success': False, 'message': 'Missing user_id parameter'}), 400

        notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()

        notification_list = [{'id': notif.id, 'message': notif.message, 'type': notif.type, 'sent': notif.sent} for notif in notifications]

        return jsonify({'success': True, 'notifications': notification_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)