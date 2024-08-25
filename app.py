# app.py

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'postgresql://postgres.elaqzrcvbknbzvbkdwgp:iCcxsx4TpDLdwqzq@aws-0-eu-central-1.pooler.supabase.com:6543/postgres')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    creator_id = db.Column(db.Integer, nullable=False)

class Giveaway(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    prize_amount = db.Column(db.Integer, nullable=False)
    participants_count = db.Column(db.Integer, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'), nullable=False)
    channel = db.relationship('Channel', backref=db.backref('giveaways', lazy=True))

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    giveaway_id = db.Column(db.Integer, db.ForeignKey('giveaway.id'), nullable=False)
    giveaway = db.relationship('Giveaway', backref=db.backref('participants', lazy=True))

@app.route('/get_channels', methods=['GET'])
def get_channels():
    channels = Channel.query.all()
    return jsonify({'channels': [{'id': ch.id, 'username': ch.username} for ch in channels]})

@app.route('/add_channel', methods=['POST'])
def add_channel():
    data = request.json
    try:
        new_channel = Channel(username=data['channel_username'], creator_id=data['creator_id'])
        db.session.add(new_channel)
        db.session.commit()
        return jsonify({'message': 'Channel added successfully'})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Channel already exists'}), 400

@app.route('/create_giveaway', methods=['POST'])
def create_giveaway():
    data = request.json
    new_giveaway = Giveaway(
        name=data['giveaway_name'],
        prize_amount=data['prize_amount'],
        participants_count=data['participants_count'],
        end_date=data['end_date'],
        channel_id=data['channel_id']
    )
    db.session.add(new_giveaway)
    db.session.commit()
    return jsonify({'message': 'Giveaway created successfully'})

@app.route('/get_giveaways', methods=['GET'])
def get_giveaways():
    giveaways = Giveaway.query.all()
    return jsonify({'giveaways': [{'id': gv.id, 'name': gv.name, 'prize_amount': gv.prize_amount} for gv in giveaways]})

@app.route('/join_giveaway', methods=['POST'])
def join_giveaway():
    data = request.json
    giveaway = Giveaway.query.get(data['giveaway_id'])
    user = request.headers.get('X-User-Username')  # Fetch username from request header
    if giveaway and user:
        participant = Participant(username=user, giveaway_id=giveaway.id)
        db.session.add(participant)
        db.session.commit()
        return jsonify({'message': 'Successfully joined giveaway'})
    return jsonify({'message': 'Giveaway not found or user not authenticated'}), 404

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
