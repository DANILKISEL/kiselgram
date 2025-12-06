import time
import threading
import secrets


def hash_password(password):
    """Helper function for hashing passwords"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def setup_bots():
    """Initialize bot users"""
    # Import inside function
    from app import db
    from app.models import TelegramBot, User

    bots_data = [
        {'name': 'Weather Bot', 'username': 'weather_bot', 'description': 'Get weather information'},
        {'name': 'News Bot', 'username': 'news_bot', 'description': 'Latest news headlines'},
        {'name': 'Calculator Bot', 'username': 'calc_bot', 'description': 'Mathematical calculations'},
        {'name': 'Kiselgram Help', 'username': 'kiselgram_bot', 'description': 'Official help'}
    ]

    for bot_data in bots_data:
        if not User.query.filter_by(username=bot_data['username']).first():
            bot_user = User(
                username=bot_data['username'],
                password_hash=hash_password(secrets.token_hex(16)) if bot_data[
                                                                          'username'] != "kiselgram_bot" else "kiselgramsupport"
            )
            db.session.add(bot_user)
        if not TelegramBot.query.filter_by(username=bot_data['username']).first():
            telegram_bot = TelegramBot(**bot_data)
            db.session.add(telegram_bot)

    db.session.commit()


def simulate_bot_interaction(app):
    """Simulate bot responses for demonstration - pass app instance"""
    while True:
        try:
            # Use the provided app context
            with app.app_context():
                from app import db
                from app.models import TelegramBot, User, Message

                bots = TelegramBot.query.filter_by(is_active=True).all()

                for bot in bots:
                    bot_user = User.query.filter_by(username=bot.username).first()
                    if not bot_user:
                        continue

                    unread_messages = Message.query.filter_by(
                        receiver_id=bot_user.id,
                        is_read=False
                    ).all()

                    for message in unread_messages:
                        message.is_read = True

                        if bot.username == 'weather_bot':
                            response = "Will be soon! Ask Ilya for the weather!"
                        elif bot.username == 'news_bot':
                            response = "📰 Breaking: Kiselgram now supports media sending! Stay tuned for more updates and also subscribe to our telegram channel: t.me/KiseIgram"
                        elif bot.username == 'calc_bot':
                            try:
                                result = eval(message.content)
                                response = f"🧮 Result: {result}"
                            except:
                                response = "❌ I can only do simple math calculations. Try something like '2+2' or '5*3'."
                        elif bot.username == 'kiselgram_bot':
                            response = "🤖 Welcome to Kiselgram Help! I can assist you with using groups, channels, and other features. What do you need help with?"
                        else:
                            response = "🤖 I'm a bot. How can I help you?"

                        bot_response = Message(
                            content=response,
                            sender_id=bot_user.id,
                            receiver_id=message.sender_id,
                            is_from_telegram=True
                        )
                        db.session.add(bot_response)

                db.session.commit()

            time.sleep(5)

        except Exception as e:
            print(f"Bot simulation error: {e}")
            time.sleep(10)