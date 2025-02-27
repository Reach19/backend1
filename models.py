from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    telegram_id = Column(String, nullable=False, unique=True)

class Channel(Base):
    __tablename__ = 'channels'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    chat_id = Column(String, nullable=False)
    giveaways = relationship('Giveaway', back_populates='channel')

class Giveaway(Base):
    __tablename__ = 'giveaways'
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False)
    name = Column(String, nullable=False)
    prize_amount = Column(Integer, nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    announced = Column(Boolean, default=False)
    winner_ids = Column(Text, nullable=True)  # A comma-separated list of winner IDs
    channel = relationship('Channel', back_populates='giveaways')
    participants = relationship('Participant', back_populates='giveaway')

class Participant(Base):
    __tablename__ = 'participants'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    giveaway_id = Column(Integer, ForeignKey('giveaways.id'), nullable=False)
    user = relationship('User')
    giveaway = relationship('Giveaway', back_populates='participants')

class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    giveaway_id = Column(Integer, ForeignKey('giveaways.id'), nullable=False)
    message = Column(Text, nullable=False)
    sent = Column(Boolean, default=False)
    user = relationship('User')
    giveaway = relationship('Giveaway')
