from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError  # Corrected import: SQLAlchemyError is now imported
from flask_cors import CORS
from flask_migrate import Migrate
from datetime import datetime, timezone
import random
import traceback
import logging
import requests
import os  # Make sure os is imported for environment variables

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://yabetsma.github.io"], "methods": ["POST", "GET", "OPTIONS"], "allow_headers": ["Content-Type"]}})

# Configuring the SQLAlchemy Database URI and initializing the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.ggxkqovbruyvfhdfkasw:dk22POZZTvc4HC4W@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate

# ----------------------- Database Models (models.py - Integrated into app.py) -----------------------

from sqlalchemy import Column, String, Integer, Text, BigInteger, Float, DateTime, Boolean, ForeignKey

class User(db.Model):
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Text, nullable=False, unique=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    username = Column(String, nullable=True, unique=True)
    channels = db.relationship('Channel', backref='user', lazy=True) # Relationship for channels
    giveaways = db.relationship('Giveaway', backref='user', lazy=True) # Relationship for giveaways
    participants = db.relationship('Participant', backref='user', lazy=True) # Relationship for participants
    notifications = db.relationship('Notification', backref='user', lazy=True) # Relationship for notifications
    winners = db.relationship('Winner', backref='user', lazy=True) # Relationship for winners


class Channel(db.Model):
    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=True)  # Optional for public channels
    chat_id = Column(BigInteger, nullable=True)   # Required for private channels
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    giveaways = db.relationship('Giveaway', backref='channel', lazy=True) # Relationship for giveaways


class Giveaway(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    prize_amount = Column(Float, nullable=False)
    participants_count = Column(Integer, nullable=False)
    end_date = Column(DateTime, nullable=False)
    channel_id = Column(Integer, ForeignKey('channel.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    announced = Column(Boolean, default=False)  # For giveaway announcement
    winners_announced = Column(Boolean, default=False)  # New column for winner announcement
    participants_rel = db.relationship('Participant', backref='giveaway', lazy=True) # Relationship for participants
    winners_rel = db.relationship('Winner', backref='giveaway', lazy=True) # Relationship for winners


class Participant(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    giveaway_id = Column(Integer, ForeignKey('giveaway.id'), nullable=False)


class Notification(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    message = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False)  # 'participant' or 'winner'
    sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Winner(db.Model):
    id = Column(Integer, primary_key=True)
    giveaway_id = Column(Integer, ForeignKey('giveaway.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    prize_amount = Column(Float, nullable=False)  # New field to store the prize amount for each winner
    created_at = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False)

# ----------------------- Utility function -----------------------

# Utility function to add a notification
def add_notification(user_id, message, notif_type):
    notification = Notification(
        user_id=user_id,
        message=message,
        type=notif_type
    )
    db.session.add(notification)
    db.session.commit()

# ----------------------- Endpoints -----------------------

# Endpoint to initialize a user
@app.route('/init_user', methods=['POST'])
def init_user():
    try:
        data = request.get_json()
        telegram_id = str(data.get('telegram_id'))  # Ensure it's treated as a string
        first_name = data.get('first_name')  # Get first name
        last_name = data.get('last_name')     # Get last name
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



# Endpoint to add channels (multiple at once)
@app.route('/add_channel', methods=['POST'])
def add_channel():
    try:
        data = request.get_json()
        usernames = data.get('usernames') # Expecting a list of usernames
        chat_ids = data.get('chat_ids')    # Expecting a list of chat_ids (numeric)
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'success': False, 'message': 'Missing user_id'}), 400

        if not usernames and not chat_ids:
            return jsonify({'success': False, 'message': 'Must provide either usernames or chat_ids or both.'}), 400

        if not isinstance(usernames, list) and usernames is not None:
            return jsonify({'success': False, 'message': 'Usernames must be a list or null.'}), 400
        if not isinstance(chat_ids, list) and chat_ids is not None:
            return jsonify({'success': False, 'message': 'Chat IDs must be a list or null.'}), 400

        added_channels_count = 0
        failed_channels = []

        # Process usernames if provided
        if usernames:
            for username in usernames:
                if username: # Ensure username is not empty
                    existing_channel_username = Channel.query.filter_by(username=username, user_id=user_id).first()
                    if not existing_channel_username:
                        channel = Channel(username=username, user_id=user_id) # Create channel with username, chat_id will be null if not provided
                        db.session.add(channel)
                        added_channels_count += 1
                    else:
                        failed_channels.append({'identifier': username, 'message': f'Channel "@{username}" already exists.'}) # **Updated message here!**

        # Process chat_ids if provided
        if chat_ids:
            for chat_id in chat_ids:
                if chat_id: # Ensure chat_id is not empty
                    existing_channel_chat_id = Channel.query.filter_by(chat_id=chat_id, user_id=user_id).first()
                    if not existing_channel_chat_id:
                        channel = Channel(chat_id=chat_id, user_id=user_id) # Create channel with chat_id, username will be null if not provided
                        db.session.add(channel)
                        added_channels_count += 1
                    else:
                        failed_channels.append({'identifier': str(chat_id), 'message': f'Channel with chat ID "{chat_id}" already exists.'}) # Updated message for chat_id as well

        db.session.commit()

        if failed_channels:
            return jsonify({
                'success': False,
                'message': f'Successfully added {added_channels_count} channels, but {len(failed_channels)} channels could not be added due to errors.',
                'failed_channels': failed_channels
            }), 207 # 207 Multi-Status, for partial success

        return jsonify({'success': True, 'message': f'Successfully added {added_channels_count} channels!'})

    except Exception as e:
        db.session.rollback()
        error_message = str(e)
        trace = traceback.format_exc()
        logger.error(f"Error in /add_channel: {error_message}\nTraceback:\n{trace}")
        return jsonify({'success': False, 'message': 'Error adding channels', 'error': error_message}), 500

# Endpoint to get channels for a specific user
@app.route('/get_user_channels', methods=['GET'])
def get_user_channels():
    try:  # Keep the try block, but enhance error logging
        user_id_str = request.args.get('user_id')

        if not user_id_str:
            return jsonify({'success': False, 'message': 'Missing user_id parameter'}), 400

        try:
            user_id = int(user_id_str)  # Convert user_id to integer
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid user_id format. Must be an integer.'}), 400

        channels = Channel.query.filter_by(user_id=user_id).all()
        if not channels:
            return jsonify({'success': False, 'message': 'No channels found for this user.'}), 404

        channel_list = [{'id': channel.id, 'username': channel.username} for channel in channels]
        return jsonify({'success': True, 'channels': channel_list})

    except Exception as e:
        error_message = str(e)
        trace = traceback.format_exc()  # Get the full traceback
        logger.error(f"Error in /get_user_channels: {error_message}\nTraceback:\n{trace}")  # Log detailed error
        return jsonify({'success': False, 'message': 'Backend error fetching channels', 'error': error_message}), 500

# Endpoint to get giveaway details by ID
@app.route('/get_giveaway_details', methods=['GET'])
def get_giveaway_details():
    giveaway_id = request.args.get('giveaway_id')
    if not giveaway_id:
        return jsonify({'success': False, 'message': 'Giveaway ID is required.'}), 400  # Bad Request

    try:
        giveaway_id_int = int(giveaway_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid giveaway ID format.'}), 400  # Bad Request

    giveaway = Giveaway.query.get(giveaway_id_int)  # Use .query.get() for direct ID lookup

    if giveaway:
        giveaway_data = {
            'id': giveaway.id,
            'name': giveaway.name,
            'prize_amount': giveaway.prize_amount,
            'participants_count': giveaway.participants_count,
            'end_date': giveaway.end_date.isoformat(),  # Format datetime to ISO string
            'channel_id': giveaway.channel_id,
            'user_id': giveaway.user_id,
            'announced': giveaway.announced,
            'winners_announced': giveaway.winners_announced
        }
        return jsonify({'success': True, 'giveaway': giveaway_data})
    else:
        return jsonify({'success': False, 'message': 'Giveaway not found.'}), 404  # Not Found


# Endpoint to create a giveaway
@app.route('/create_giveaway', methods=['POST'])
def create_giveaway():
    try:
        data = request.get_json()
        end_date_str = data.get('end_date')

        name = data.get('name')
        prize_amount = data.get('prize_amount')
        participants_count = data.get('participants_count')
        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))  # Handles ISO string
        channel_ids_list = data.get('channel_ids') # Expecting a list of channel IDs now
        user_id = data.get('user_id')

        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        else:
            end_date = end_date.astimezone(timezone.utc)

        if not all([name, prize_amount, participants_count, end_date, channel_ids_list, user_id]): # Validating for channel_ids_list now
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        if not isinstance(channel_ids_list, list) or not channel_ids_list: # Ensure channel_ids is a non-empty list
            return jsonify({'success': False, 'message': 'channel_ids must be a non-empty list'}), 400

        channel_ids_str = ','.join(map(str, channel_ids_list)) # Convert list of channel IDs to comma-separated string

        giveaway = Giveaway(
            name=name,
            prize_amount=prize_amount,
            participants_count=participants_count,
            end_date=end_date,
            channel_ids=channel_ids_str, # Storing comma-separated string of channel IDs
            user_id=user_id,
            announced=False
        )

        db.session.add(giveaway)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Giveaway created successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Endpoint to join a giveaway
@app.route('/join_giveaway_action', methods=['POST'])  # Corrected endpoint name to match JS
def join_giveaway_action():  # Corrected function name to match endpoint
    try:
        data = request.get_json()
        user_id = data.get('user_id')  # Expecting user_id as integer now (from localStorage)
        giveaway_id = data.get('giveaway_id')

        if not user_id or not giveaway_id:
            return jsonify({'success': False, 'message': 'Missing user_id or giveaway_id'}), 400

        user = User.query.get(user_id)  # Use .query.get() to fetch user by ID (integer)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        giveaway = Giveaway.query.get(giveaway_id)  # Use .query.get() to fetch giveaway by ID (integer)
        if not giveaway:
            return jsonify({'success': False, 'message': 'Giveaway not found'}), 404

        if giveaway.end_date <= datetime.utcnow():  # Check if giveaway end date is in the past
            return jsonify({'success': False, 'message': 'This giveaway has ended and cannot be joined.'}), 400

        participant = Participant.query.filter_by(user_id=user.id, giveaway_id=giveaway_id).first()
        if participant:
            return jsonify({'success': False, 'message': 'Already joined this giveaway'}), 400

        participant = Participant(user_id=user.id, giveaway_id=giveaway_id)
        db.session.add(participant)
        db.session.commit()

        add_notification(user.id, f"You have successfully joined the giveaway: {giveaway.name}", 'participant')

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
        winner = Winner(giveaway_id=giveaway.id, user_id=participant.user_id, prize_amount=giveaway.prize_amount / number_of_winners) # divide prize
        db.session.add(winner)
        winner_ids.append(participant.user_id)

        # Add a notification for the winner
        add_notification(participant.user_id, f"Congratulations! You have won the giveaway: {giveaway.name} and prize: {giveaway.prize_amount / number_of_winners}!", 'winner') # mention prize

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
            'notified': winner.Winner.notified,
            'prize_amount': winner.Winner.prize_amount # Include prize amount in winner info
        } for winner in winners]

        return jsonify({'success': True, 'winners': winner_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/payment_method', methods=['POST'])
def add_payment_method(): # This endpoint is currently a placeholder, consider its actual functionality and database integration
    data = request.get_json()
    user_id = data.get('user_id')
    payment_method = data.get('payment_method')

    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Placeholder: You can decide how to store payment method. Currently not saving to DB
        # user.payment_method = payment_method  # Uncomment to save to User model if you add payment_method column
        # db.session.commit()

        return jsonify({'success': True, 'message': 'Payment method is noted (not saved in this version).'}), 200 # Updated message to reflect current state
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Function to send scheduled notifications for ending giveaways (To be implemented with a scheduler like APScheduler or Celery)
def check_and_send_notifications(): # This function is still a placeholder for scheduled tasks
    giveaways = Giveaway.query.filter(Giveaway.end_date <= datetime.utcnow(), Giveaway.announced == False).all()

    for giveaway in giveaways:
        winners_data = select_winners(giveaway.id, 1) # Select 1 winner for now
        if winners_data.get("success"): # Check if winner selection was successful
            giveaway.announced = True
            db.session.commit()
            logger.info(f"Winners selected and announced for giveaway ID: {giveaway.id}. Winners: {winners_data.get('winner_ids')}")
        else:
            logger.error(f"Error selecting winners for giveaway ID: {giveaway.id}. Error: {winners_data.get('error')}")


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

# --- Verification Endpoint (Corrected and implemented with Telegram Bot API) ---
BOT_TOKEN = "7514207604:AAE_p_eFFQ3yOoNn-GSvTSjte2l8UEHl7b8" # **IMPORTANT: Replace with your actual bot token!**
TELEGRAM_BOT_API_BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

@app.route('/verify_giveaway_bot_admin', methods=['POST'])
def verify_giveaway_bot_admin():
    try:
        data = request.get_json()
        channel_username = data.get('channel_username')
        bot_username = data.get('bot_username') # You are also sending bot_username from frontend

        if not channel_username:
            return jsonify({'success': False, 'message': 'Missing channel_username'}), 400
        if not bot_username: # It's good to validate bot_username too, even if you hardcode it on frontend
            return jsonify({'success': False, 'message': 'Missing bot_username'}), 400

        get_chat_url = f"{TELEGRAM_BOT_API_BASE_URL}/getChat?username={channel_username}" # For public channels, use username
        response_chat = requests.get(get_chat_url)
        response_chat.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        chat_data = response_chat.json()

        if not chat_data['ok']:
            return jsonify({'success': False, 'message': f"Error fetching channel info: {chat_data.get('description', 'Unknown error')}"}), 400
        chat_id = chat_data['result']['id']

        get_member_url = f"{TELEGRAM_BOT_API_BASE_URL}/getChatMember?chat_id={chat_id}&user_id={bot_username}" # Use bot_username as user_id to check bot's status
        response_member = requests.get(get_member_url)
        response_member.raise_for_status()
        member_data = response_member.json()

        if not member_data['ok']:
            return jsonify({'success': False, 'message': f"Error fetching bot member info: {member_data.get('description', 'Unknown error')}"}), 400

        status = member_data['result']['status']
        is_admin = status in ['administrator', 'creator'] # Check if status is admin or creator

        if is_admin:
            return jsonify({'success': True, 'message': f"Giveaway bot is an admin in the channel {channel_username}!"})
        else:
            return jsonify({'success': False, 'message': f"Giveaway bot is NOT an admin in the channel {channel_username}. Status: {status}"})


    except requests.exceptions.RequestException as e:  # Catch request-related errors (network, timeouts, etc.)
        error_message = str(e)
        logger.error(f"Request error in /verify_giveaway_bot_admin: {error_message}")
        return jsonify({'success': False, 'message': 'Error communicating with Telegram API', 'error': error_message}), 502  # 502 Bad Gateway for API errors

    except Exception as e:
        error_message = str(e)
        trace = traceback.format_exc()
        logger.error(f"Error in /verify_giveaway_bot_admin: {error_message}\nTraceback:\n{trace}")
        return jsonify({'success': False, 'message': 'Backend error verifying bot admin status', 'error': error_message}), 500
# --- End of Verification Endpoint ---


if __name__ == '__main__':
    app.run(debug=True)