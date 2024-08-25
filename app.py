from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.elaqzrcvbknbzvbkdwgp:iCcxsx4TpDLdwqzq@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define models directly in app.py

class Channel(db.Model):
    __tablename__ = 'channels'

    id = db.Column(db.Integer, primary_key=True, index=True)
    username = db.Column(db.String, unique=True, index=True)
    creator_id = db.Column(db.Integer, index=True)

    def __repr__(self):
        return f"<Channel(id={self.id}, username={self.username}, creator_id={self.creator_id})>"

class Giveaway(db.Model):
    __tablename__ = 'giveaways'

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, index=True)
    prize_amount = db.Column(db.Integer)
    participants_count = db.Column(db.Integer)
    end_date = db.Column(db.DateTime)
    channel_id = db.Column(db.Integer, db.ForeignKey('channels.id'))

    channel = db.relationship("Channel", back_populates="giveaways")
    participants = db.relationship("Participant", back_populates="giveaway")

    def __repr__(self):
        return (f"<Giveaway(id={self.id}, name={self.name}, prize_amount={self.prize_amount}, "
                f"participants_count={self.participants_count}, end_date={self.end_date}, "
                f"channel_id={self.channel_id})>")

class Participant(db.Model):
    __tablename__ = 'participants'

    id = db.Column(db.Integer, primary_key=True, index=True)
    username = db.Column(db.String, index=True)
    giveaway_id = db.Column(db.Integer, db.ForeignKey('giveaways.id'))

    giveaway = db.relationship("Giveaway", back_populates="participants")

    def __repr__(self):
        return f"<Participant(id={self.id}, username={self.username}, giveaway_id={self.giveaway_id})>"

# Define routes

@app.route('/add_channel', methods=['POST'])
def add_channel():
    data = request.json
    username = data.get('username')
    creator_id = data.get('creator_id')
    if not username or not creator_id:
        return jsonify({'success': False, 'message': 'Invalid data'}), 400
    
    try:
        channel = Channel(username=username, creator_id=creator_id)
        db.session.add(channel)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Channel added successfully'}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/create_giveaway', methods=['POST'])
def create_giveaway():
    data = request.json
    name = data.get('name')
    prize_amount = data.get('prize_amount')
    participants_count = data.get('participants_count')
    end_date = datetime.fromisoformat(data.get('end_date'))
    channel_id = data.get('channel_id')
    
    if not name or not prize_amount or not participants_count or not end_date or not channel_id:
        return jsonify({'success': False, 'message': 'Invalid data'}), 400
    
    try:
        giveaway = Giveaway(
            name=name,
            prize_amount=prize_amount,
            participants_count=participants_count,
            end_date=end_date,
            channel_id=channel_id
        )
        db.session.add(giveaway)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Giveaway created successfully'}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/join_giveaway/<int:giveaway_id>', methods=['POST'])
def join_giveaway(giveaway_id):
    data = request.json
    username = data.get('username')
    
    if not username:
        return jsonify({'success': False, 'message': 'Invalid data'}), 400

    try:
        giveaway = Giveaway.query.get(giveaway_id)
        if not giveaway:
            return jsonify({'success': False, 'message': 'Giveaway not found'}), 404
        
        participant = Participant(username=username, giveaway_id=giveaway_id)
        db.session.add(participant)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Successfully joined the giveaway'}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables
    app.run(debug=True)
