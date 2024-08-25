from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.elaqzrcvbknbzvbkdwgp:iCcxsx4TpDLdwqzq@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define models
class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    creator_id = db.Column(db.Integer, nullable=False)

class Giveaway(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prize_amount = db.Column(db.Integer, nullable=False)
    participants_count = db.Column(db.Integer, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'), nullable=False)

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    giveaway_id = db.Column(db.Integer, db.ForeignKey('giveaway.id'), nullable=False)

@app.route('/add_channel', methods=['POST'])
def add_channel():
    data = request.json
    username = data.get('username')
    creator_id = data.get('creator_id')
    
    if not username or not creator_id:
        return jsonify({'success': False, 'message': 'Missing username or creator_id'}), 400

    # Check if channel already exists
    existing_channel = Channel.query.filter_by(username=username).first()
    if existing_channel:
        return jsonify({'success': False, 'message': 'Channel already exists'}), 400
    
    new_channel = Channel(username=username, creator_id=creator_id)
    db.session.add(new_channel)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Channel added successfully'}), 200

@app.route('/create_giveaway', methods=['POST'])
def create_giveaway():
    data = request.json
    name = data.get('name')
    prize_amount = data.get('prize_amount')
    participants_count = data.get('participants_count')
    end_date = data.get('end_date')
    channel_id = data.get('channel_id')

    if not name or not prize_amount or not participants_count or not end_date or not channel_id:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    new_giveaway = Giveaway(
        name=name,
        prize_amount=prize_amount,
        participants_count=participants_count,
        end_date=end_date,
        channel_id=channel_id
    )
    db.session.add(new_giveaway)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Giveaway created successfully'}), 200

@app.route('/get_channels', methods=['GET'])
def get_channels():
    channels = Channel.query.all()
    channels_list = [{'id': c.id, 'username': c.username} for c in channels]
    return jsonify({'success': True, 'channels': channels_list}), 200

@app.route('/get_pending_notifications', methods=['GET'])
def get_pending_notifications():
    # Dummy data for notification fetching, adapt as needed
    notifications = [{'user_id': 12345, 'message': 'Congratulations! You are a participant.', 'type': 'participant'}]
    return jsonify({'success': True, 'notifications': notifications}), 200

if __name__ == '__main__':
    app.run(debug=True)
