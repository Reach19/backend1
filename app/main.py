from flask import Flask, render_template, request, jsonify
from app import db
from app.models import User, Channel, Giveaway, Participant
from datetime import datetime
import random
from app.bot import check_bot_admin, post_to_channel, post_winners_to_channel

app = Flask(__name__)
app.config.from_object('app.config.Config')
db.init_app(app)

@app.route('/')
def home():
    return render_template('home.html', channels=Channel.query.all())

@app.route('/add_channel', methods=['POST'])
def add_channel():
    channel_username = request.form['channel_username']
    try:
        chat_id, bot_is_admin = check_bot_admin(channel_username)
        if bot_is_admin:
            new_channel = Channel(username=channel_username, chat_id=chat_id)
            db.session.add(new_channel)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Channel added successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Bot is not an admin in this channel. Please make the bot an admin and try again.'}), 403
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/create_giveaway', methods=['POST'])
def create_giveaway():
    channel_username = request.form['channel']
    giveaway_name = request.form['giveaway_name']
    prize_amount = float(request.form['prize_amount'])
    participants_count = int(request.form['participants_count'])
    end_date = datetime.fromisoformat(request.form['end_date'])
    
    selected_channel = Channel.query.filter_by(username=channel_username).first()
    
    if selected_channel:
        new_giveaway = Giveaway(
            bot_username=request.form['bot_username'],
            amount=prize_amount,
            participant_count=participants_count,
            end_date=end_date,
            channel_id=selected_channel.id,
            user_id=1  # Adjust as needed
        )
        db.session.add(new_giveaway)
        db.session.commit()

        message = (
            f"🎉 New Giveaway Alert! 🎉\n\n"
            f"💰 Amount: {new_giveaway.amount} Birr\n"
            f"👥 Participants: {new_giveaway.participant_count}\n"
            f"🕒 Ends on: {new_giveaway.end_date.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Join now and stand a chance to win!"
        )
        try:
            post_to_channel(selected_channel.chat_id, message)
        except Exception as e:
            return jsonify({'success': False, 'message': f'Failed to post giveaway to channel: {str(e)}'}), 500
        
        new_giveaway.url = f"https://t.me/giveaway_setota_bot/Giveaway/giveaway/{new_giveaway.id}"
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Giveaway created successfully!'})
    else:
        return jsonify({'success': False, 'message': 'Channel not found.'}), 404

@app.route('/announce_winners/<int:giveaway_id>', methods=['GET'])
def announce_winners(giveaway_id):
    giveaway = Giveaway.query.get_or_404(giveaway_id)
    participants = Participant.query.filter_by(giveaway_id=giveaway_id).all()

    winners = random.sample(participants, min(giveaway.participant_count, len(participants)))

    giveaway.winners = [winner.id for winner in winners]
    db.session.commit()

    winner_list = "\n".join([f"@{winner.username}" for winner in winners])
    message = (
        f"🎉 Congratulations to the winners of our recent giveaway! 🎉\n\n"
        f"The following participants were randomly selected:\n\n"
        f"{winner_list}\n\n"
        f"View more details here: {giveaway.url}"
    )
    try:
        post_winners_to_channel(giveaway.channel_id, message)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to post winners to channel: {str(e)}'}), 500

    return jsonify({'success': True, 'winners': [{'username': winner.username} for winner in winners]})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure all tables are created
    app.run(host='0.0.0.0', port=5000, debug=True)
