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

# Start command - handles both regular start and referral deep links
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"User_{user_id}"
    
    try:
        conn = sqlite3.connect('referral.db')
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()
        
        referral_code = None
        invited_by = None
        
        # Parse arguments for referral code
        args = message.text.split()
        if len(args) > 1:
            referrer_code = args[1]
            
            # Check if referrer exists
            c.execute("SELECT user_id FROM users WHERE referral_code = ?", (referrer_code,))
            referrer = c.fetchone()
            
            if referrer:
                invited_by = referrer[0]
        
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
                                   f"✅ @{username} a rejoint via ton lien !\n+1 invite • +100 ⭐")
                except:
                    pass
            
            conn.commit()
        else:
            c.execute("SELECT referral_code FROM users WHERE user_id = ?", (user_id,))
            referral_code = c.fetchone()[0]
        
        conn.close()
        
        message_text = f"""
🎁 BIENVENUE AU CONCOURS D'INVITATION !

Ton code : `{referral_code}`

💰 COMMENT ÇA MARCHE :
1. Partage ton lien d'invitation
2. Chaque ami qui se join = +100 points ⭐
3. Échange tes points en récompenses

Ton lien :
https://t.me/TF8invitationbot?start={referral_code}

📊 Commandes :
/leaderboard - Voir le classement
/mystats - Tes statistiques
/redeem 100 - Convertir points
/help - Aide complète

🏆 RÉCOMPENSES :
100 ⭐ = 10€
500 ⭐ = 100€
1000 ⭐ = 500€
        """
        
        bot.send_message(user_id, message_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Start command error: {e}")
        bot.send_message(message.chat.id, "❌ Erreur. Réessaie /start")

# Leaderboard command
@bot.message_handler(commands=['leaderboard'])
def leaderboard(message):
    try:
        conn = sqlite3.connect('referral.db')
        c = conn.cursor()
        
        c.execute("SELECT username, invites, points FROM users ORDER BY invites DESC LIMIT 10")
        users = c.fetchall()
        conn.close()
        
        leaderboard_text = "🏆 TOP 10 INVITANTS\n\n"
        
        if users:
            for i, (username, invites, points) in enumerate(users, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
                leaderboard_text += f"{medal} @{username}\n   {invites} invites • {points} ⭐\n\n"
        else:
            leaderboard_text += "Pas encore de participants"
        
        bot.send_message(message.chat.id, leaderboard_text)
        
    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        bot.send_message(message.chat.id, "❌ Erreur lors du leaderboard")

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
            stats = f"""
📊 TES STATISTIQUES

Code : `{code}`
Invitations : {invites}
Points : {points} ⭐

💰 Récompenses disponibles :
100 ⭐ = 10€
500 ⭐ = 100€
1000 ⭐ = 500€

Partage ton lien :
https://t.me/TF8invitationbot?start={code}

Commande : /redeem 100
            """
            bot.send_message(user_id, stats, parse_mode="Markdown")
        else:
            bot.send_message(user_id, "❌ Tu n'es pas enregistré. Tape /start d'abord.")
        
    except Exception as e:
        logger.error(f"Mystats error: {e}")
        bot.send_message(message.chat.id, "❌ Erreur")

# Redeem command
@bot.message_handler(commands=['redeem'])
def redeem(message):
    user_id = message.from_user.id
    args = message.text.split()
    
    if len(args) < 2:
        bot.reply_to(message, "Usage : /redeem 100\n(remplace 100 par le nombre de points)")
        return
    
    try:
        points_to_redeem = int(args[1])
    except ValueError:
        bot.reply_to(message, "❌ Nombre invalide")
        return
    
    if points_to_redeem <= 0:
        bot.reply_to(message, "❌ Le nombre doit être positif")
        return
    
    try:
        conn = sqlite3.connect('referral.db')
        c = conn.cursor()
        
        c.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        
        if not result:
            bot.reply_to(message, "❌ Tu n'es pas enregistré. Tape /start")
            conn.close()
            return
        
        current_points = result[0]
        
        if current_points < points_to_redeem:
            bot.reply_to(message, f"❌ Tu as seulement {current_points} points")
            conn.close()
            return
        
        # Conversion: 100 points = 10€
        reward_value = (points_to_redeem / 100) * 10
        
        c.execute("UPDATE users SET points = points - ? WHERE user_id = ?", 
                  (points_to_redeem, user_id))
        conn.commit()
        conn.close()
        
        message_text = f"""
✅ Redemption validée !

Points convertis : -{points_to_redeem}
Valeur : {reward_value}€

Merci pour ta participation ! 🎉
Ton crédit sera appliqué dans 24h.
        """
        
        bot.reply_to(message, message_text)
        
    except Exception as e:
        logger.error(f"Redeem error: {e}")
        bot.reply_to(message, "❌ Erreur lors de la conversion")

# Help command
@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
📚 AIDE COMPLÈTE

/start - Démarrer et obtenir ton code d'invitation
/mystats - Voir tes statistiques
/leaderboard - Classement des meilleurs invitants
/redeem <points> - Convertir tes points en reward

💡 EXEMPLE :
/redeem 100 → convertit 100 points en 10€

🤝 PARTAGE TON LIEN :
Chaque ami qui se joint = +100 points ⭐

Des problèmes ? Contacte le support.
    """
    bot.send_message(message.chat.id, help_text)

# Default handler
@bot.message_handler(func=lambda message: True)
def default_handler(message):
    bot.reply_to(message, "Je ne comprends pas cette commande. Tape /help pour l'aide.")

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
