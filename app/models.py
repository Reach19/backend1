from datetime import datetime
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    channels = db.relationship('Channel', backref='owner', lazy=True)
    giveaways = db.relationship('Giveaway', backref='creator', lazy=True)

class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    chat_id = db.Column(db.Integer, unique=True, nullable=False)
    giveaways = db.relationship('Giveaway', backref='channel', lazy=True)

class Giveaway(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bot_username = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    participant_count = db.Column(db.Integer, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    posted = db.Column(db.Boolean, default=False)
    winners = db.Column(db.PickleType, nullable=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    url = db.Column(db.String(200), nullable=True)

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    giveaway_id = db.Column(db.Integer, db.ForeignKey('giveaway.id'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    profile_pic = db.Column(db.String(200), nullable=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
