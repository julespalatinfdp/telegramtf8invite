import telebot
import sqlite3
from datetime import datetime
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token depuis variable d'environnement
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

bot = telebot.TeleBot(BOT_TOKEN)

# Database setup
def init_db():
    try:
        conn = sqlite3.connect('referral.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            referral_code TEXT UNIQUE,
            invites INTEGER DEFAULT 0,
            points INTEGER DEFAULT 0,
            joined_date TIMESTAMP
        )''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

init_db()

# Start command - handles regular start, referral links, and button clicks
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"User_{user_id}"
    
    try:
        conn = sqlite3.connect('referral.db')
        c = conn.cursor()
        
        referral_code = None
        invited_by = None
        
        # Parse arguments for referral code or join parameter
        args = message.text.split()
        if len(args) > 1:
            param = args[1]
            
            # If param is 'join', user came from the button - show full welcome
            if param == 'join':
                # Check/create user
                c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                user = c.fetchone()
                
                if not user:
                    referral_code = f"{username}_{user_id}"
                    c.execute('''INSERT INTO users (user_id, username, referral_code, joined_date)
                                 VALUES (?, ?, ?, ?)''',
                              (user_id, username, referral_code, datetime.now()))
                    conn.commit()
                else:
                    c.execute("SELECT referral_code FROM users WHERE user_id = ?", (user_id,))
                    referral_code = c.fetchone()[0]
                
                conn.close()
                
                # Full welcome message with commands
                welcome_text = f"""🎉 WELCOME TO THE INVITATION CONTEST !

Your code : <code>{referral_code}</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 HOW IT WORKS :

1️⃣ <b>Share your link</b>
https://t.me/TF8invitationbot?start={referral_code}

2️⃣ <b>Each friend who joins = +100 points ⭐</b>

3️⃣ <b>Exchange your points for rewards</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 <b>AVAILABLE COMMANDS :</b>

/mystats - View your statistics
/leaderboard - Top 10 ranking
/redeem 100 - Convert 100 points
/help - Full help

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 <b>REWARDS :</b>

100 ⭐ = €10 credit
500 ⭐ = €100 credit
1000 ⭐ = €500 prize

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ Share your code and start earning !"""
                
                bot.send_message(user_id, welcome_text, parse_mode="HTML")
                return
            
            # If param is 'help' - show full help
            elif param == 'help':
                conn.close()
                help_text = """📚 <b>FULL HELP</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>🎁 HOW TO PARTICIPATE :</b>

1️⃣ Join the contest
2️⃣ Get your unique code
3️⃣ Share your link with friends
4️⃣ Earn points for each invitation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>📊 MAIN COMMANDS :</b>

<code>/start</code> - Start
<code>/mystats</code> - View your code and stats
<code>/leaderboard</code> - Top 10 invitants
<code>/redeem 100</code> - Convert 100 points

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>💰 POINTS SYSTEM :</b>

Each friend who joins via your link = +100 ⭐

<b>🏆 REWARDS :</b>
100 ⭐ = €10
500 ⭐ = €100
1000 ⭐ = €500

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>❓ FREQUENTLY ASKED QUESTIONS :</b>

Q: How long to receive points ?
R: Immediately !

Q: Can I share multiple times ?
R: Yes, no limit !

Q: How do I get my money ?
R: Use the /redeem command

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Need help ? Tap /mystats to start !"""
                
                bot.send_message(user_id, help_text, parse_mode="HTML")
                return
            
            # If param is 'leaderboard' - show leaderboard
            elif param == 'leaderboard':
                try:
                    c.execute("SELECT username, invites, points FROM users ORDER BY invites DESC LIMIT 10")
                    users = c.fetchall()
                    conn.close()
                    
                    leaderboard_text = "<b>🏆 TOP 10 INVITERS</b>\n\n"
                    
                    if users:
                        for i, (username, invites, points) in enumerate(users, 1):
                            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
                            leaderboard_text += f"{medal} <b>@{username}</b>\n   {invites} invites • {points} ⭐\n\n"
                    else:
                        leaderboard_text += "No participants yet"
                    
                    bot.send_message(user_id, leaderboard_text, parse_mode="HTML")
                    return
                except Exception as e:
                    logger.error(f"Leaderboard error: {e}")
                    bot.send_message(user_id, "❌ Error loading leaderboard")
                    return
            
            # Otherwise, it's a referral code
            referrer_code = param
            c.execute("SELECT user_id FROM users WHERE referral_code = ?", (referrer_code,))
            referrer = c.fetchone()
            
            if referrer:
                invited_by = referrer[0]
        
        # Check if user exists
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()
        
        if not user:
            # Create new user
            referral_code = f"{username}_{user_id}"
            c.execute('''INSERT INTO users (user_id, username, referral_code, joined_date)
                         VALUES (?, ?, ?, ?)''',
                      (user_id, username, referral_code, datetime.now()))
            
            # Update referrer if exists
            if invited_by:
                c.execute("""UPDATE users SET invites = invites + 1, points = points + 100 
                             WHERE user_id = ?""", (invited_by,))
                
                # Notify referrer
                try:
                    bot.send_message(invited_by, 
                                   f"✅ @{username} joined via your link !\n+1 invite • +100 ⭐")
                except:
                    pass
            
            conn.commit()
        else:
            c.execute("SELECT referral_code FROM users WHERE user_id = ?", (user_id,))
            referral_code = c.fetchone()[0]
        
        conn.close()
        
        message_text = f"""🎁 WELCOME TO THE INVITATION CONTEST !

Your code : <code>{referral_code}</code>

💰 HOW IT WORKS :
1. Share your invitation link
2. Each friend who joins = +100 points ⭐
3. Exchange your points for rewards

Your link :
https://t.me/TF8invitationbot?start={referral_code}

📊 Commands :
/leaderboard - View the ranking
/mystats - Your statistics
/redeem 100 - Convert points
/help - Full help

🏆 REWARDS :
100 ⭐ = €10
500 ⭐ = €100
1000 ⭐ = €500"""
        
        bot.send_message(user_id, message_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Start command error: {e}")
        bot.send_message(message.chat.id, f"❌ Erreur: {str(e)}")

# Leaderboard command
@bot.message_handler(commands=['leaderboard'])
def leaderboard(message):
    try:
        conn = sqlite3.connect('referral.db')
        c = conn.cursor()
        
        c.execute("SELECT username, invites, points FROM users ORDER BY invites DESC LIMIT 10")
        users = c.fetchall()
        conn.close()
        
        leaderboard_text = "🏆 TOP 10 INVITERS\n\n"
        
        if users:
            for i, (username, invites, points) in enumerate(users, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
                leaderboard_text += f"{medal} @{username}\n   {invites} invites • {points} ⭐\n\n"
        else:
            leaderboard_text += "No participants yet"
        
        bot.send_message(message.chat.id, leaderboard_text)
        
    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        bot.send_message(message.chat.id, "❌ Error loading leaderboard")

# My stats command
@bot.message_handler(commands=['mystats'])
def my_stats(message):
    user_id = message.from_user.id
    
    try:
        conn = sqlite3.connect('referral.db')
        c = conn.cursor()
        c.execute("SELECT referral_code, invites, points FROM users WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        conn.close()
        
        if user_data:
            code, invites, points = user_data
            stats = f"""📊 YOUR STATISTICS

Code : <code>{code}</code>
Invitations : {invites}
Points : {points} ⭐

💰 Available rewards :
100 ⭐ = €10
500 ⭐ = €100
1000 ⭐ = €500

Share your link :
https://t.me/TF8invitationbot?start={code}

Command : /redeem 100"""
            bot.send_message(user_id, stats, parse_mode="HTML")
        else:
            bot.send_message(user_id, "❌ You are not registered. Type /start first.")
        
    except Exception as e:
        logger.error(f"Mystats error: {e}")
        bot.send_message(message.chat.id, "❌ Error")

# Redeem command
@bot.message_handler(commands=['redeem'])
def redeem(message):
    user_id = message.from_user.id
    args = message.text.split()
    
    if len(args) < 2:
        bot.reply_to(message, "Usage : /redeem 100\n(replace 100 with the number of points)")
        return
    
    try:
        points_to_redeem = int(args[1])
    except ValueError:
        bot.reply_to(message, "❌ Invalid number")
        return
    
    if points_to_redeem <= 0:
        bot.reply_to(message, "❌ The number must be positive")
        return
    
    try:
        conn = sqlite3.connect('referral.db')
        c = conn.cursor()
        
        c.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        
        if not result:
            bot.reply_to(message, "❌ You are not registered. Type /start")
            conn.close()
            return
        
        current_points = result[0]
        
        if current_points < points_to_redeem:
            bot.reply_to(message, f"❌ You only have {current_points} points")
            conn.close()
            return
        
        # Conversion: 100 points = €10
        reward_value = (points_to_redeem / 100) * 10
        
        c.execute("UPDATE users SET points = points - ? WHERE user_id = ?", 
                  (points_to_redeem, user_id))
        conn.commit()
        conn.close()
        
        message_text = f"""
✅ Redemption validated !

Points converted : -{points_to_redeem}
Value : €{reward_value}

Thank you for participating ! 🎉
Your credit will be applied within 24 hours.
        """
        
        bot.reply_to(message, message_text)
        
    except Exception as e:
        logger.error(f"Redeem error: {e}")
        bot.reply_to(message, "❌ Error during conversion")

# Setup channel command - sends message with buttons to the channel
@bot.message_handler(commands=['setup_channel'])
def setup_channel(message):
    """Send the contest announcement with buttons to the channel"""
    try:
        # Get the channel ID from the message (for group/channel)
        channel_id = message.chat.id
        
        # Create inline buttons
        markup = telebot.types.InlineKeyboardMarkup()
        
        # Button to join the contest
        join_button = telebot.types.InlineKeyboardButton(
            text="🎁 Join the contest",
            url="https://t.me/TF8invitationbot?start=join"
        )
        
        # Button to see leaderboard
        leaderboard_button = telebot.types.InlineKeyboardButton(
            text="🏆 Leaderboard",
            url="https://t.me/TF8invitationbot?start=leaderboard"
        )
        
        # Button for help
        help_button = telebot.types.InlineKeyboardButton(
            text="❓ Help",
            url="https://t.me/TF8invitationbot?start=help"
        )
        
        # Add buttons to markup
        markup.add(join_button)
        markup.add(leaderboard_button, help_button)
        
        # Message content
        message_text = """🎁 <b>INVITATION CONTEST</b>

Participate and win up to <b>€500 in rewards ! 🏆</b>

<b>💰 HOW IT WORKS :</b>

1️⃣ Join the contest
2️⃣ Share your invitation code
3️⃣ Each friend who joins = +100 points ⭐
4️⃣ Exchange your points for rewards

<b>🏆 REWARDS :</b>

100 ⭐ = €10 credit
500 ⭐ = €100 credit
1000 ⭐ = €500 prize

<b>👇 Click the button below to start !</b>"""
        
        # Send the message with buttons
        bot.send_message(channel_id, message_text, 
                        parse_mode="HTML", 
                        reply_markup=markup)
        
        # Confirm to the user
        bot.reply_to(message, "✅ Message with buttons sent to the channel !")
        
    except Exception as e:
        logger.error(f"Setup channel error: {e}")
        bot.reply_to(message, f"❌ Error : {str(e)}")

# Help command
@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
📚 FULL HELP

/start - Start and get your invitation code
/mystats - View your statistics
/leaderboard - Ranking of best inviters
/redeem <points> - Convert your points to reward

💡 EXAMPLE :
/redeem 100 → converts 100 points to €10

🤝 SHARE YOUR LINK :
Each friend who joins = +100 points ⭐

Issues ? Contact support.
    """
    bot.send_message(message.chat.id, help_text)

# Default handler
@bot.message_handler(func=lambda message: True)
def default_handler(message):
    bot.reply_to(message, "I don't understand this command. Type /help for help.")

# Admin command - post invitation button to channel
@bot.message_handler(commands=['announce'])
def announce(message):
    """Post the invitation button to the channel"""
    
    # Only admins can use this
    user_id = message.from_user.id
    ADMIN_IDS = [user_id]  # Change with your admin IDs
    
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ You don't have permission")
        return
    
    try:
        # Create the button
        markup = telebot.types.InlineKeyboardMarkup()
        
        # Button that opens the bot in DM with /start=join
        button = telebot.types.InlineKeyboardButton(
            text="🎁 Join the contest",
            url="https://t.me/TF8invitationbot?start=join"
        )
        markup.add(button)
        
        # Message with the button
        message_text = """🎉 INVITATION CONTEST - TF8

Earn points by inviting your friends !

💰 HOW IT WORKS :
• Click the button below
• Receive your unique invitation code
• Share it with your friends
• +100 points per friend ⭐
• Exchange your points for rewards

🏆 REWARDS :
100 ⭐ = €10
500 ⭐ = €100
1000 ⭐ = €500

Let's go ! 🚀"""
        
        bot.send_message(message.chat.id, message_text, reply_markup=markup)
        bot.send_message(message.from_user.id, "✅ Button posted in the channel !")
        
    except Exception as e:
        logger.error(f"Announce error: {e}")
        bot.reply_to(message, f"❌ Error : {str(e)}")

# Health check endpoint (pour Railway)
@bot.message_handler(commands=['ping'])
def ping(message):
    bot.reply_to(message, "🟢 Bot is alive!")

# Main
if __name__ == "__main__":
    logger.info("Starting TF8 Referral Bot...")
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logger.error(f"Bot error: {e}")
