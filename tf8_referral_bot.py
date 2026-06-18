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
                welcome_text = f"""🎉 BIENVENUE AU CONCOURS D'INVITATION !

Ton code : <code>{referral_code}</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 COMMENT ÇA MARCHE :

1️⃣ <b>Partage ton lien</b>
https://t.me/TF8invitationbot?start={referral_code}

2️⃣ <b>Chaque ami qui se join = +100 points ⭐</b>

3️⃣ <b>Échange tes points en récompenses</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 <b>COMMANDES DISPONIBLES :</b>

/mystats - Voir tes statistiques
/leaderboard - Classement top 10
/redeem 100 - Convertir 100 points
/help - Aide complète

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 <b>RÉCOMPENSES :</b>

100 ⭐ = 10€ crédit
500 ⭐ = 100€ crédit
1000 ⭐ = 500€ prize

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ Partage ton code et commence à gagner !"""
                
                bot.send_message(user_id, welcome_text, parse_mode="HTML")
                return
            
            # If param is 'help' - show full help
            elif param == 'help':
                conn.close()
                help_text = """📚 <b>AIDE COMPLÈTE</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>🎁 COMMENT PARTICIPER :</b>

1️⃣ Rejoignez le concours
2️⃣ Récupérez votre code unique
3️⃣ Partagez votre lien avec des amis
4️⃣ Gagnez des points à chaque invitation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>📊 COMMANDES PRINCIPALES :</b>

<code>/start</code> - Démarrer
<code>/mystats</code> - Voir ton code et tes stats
<code>/leaderboard</code> - Top 10 invitants
<code>/redeem 100</code> - Convertir 100 points

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>💰 SYSTÈME DE POINTS :</b>

Chaque ami qui se joint via ton lien = +100 ⭐

<b>🏆 RÉCOMPENSES :</b>
100 ⭐ = 10€
500 ⭐ = 100€
1000 ⭐ = 500€

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>❓ QUESTIONS FRÉQUENTES :</b>

Q: Combien de temps pour les points ?
R: Immédiat !

Q: Puis-je rediriger plusieurs fois ?
R: Oui, pas de limite !

Q: Comment je récupère mon argent ?
R: Via la commande /redeem

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Besoin d'aide ? Tape /mystats pour commencer !"""
                
                bot.send_message(user_id, help_text, parse_mode="HTML")
                return
            
            # If param is 'leaderboard' - show leaderboard
            elif param == 'leaderboard':
                try:
                    c.execute("SELECT username, invites, points FROM users ORDER BY invites DESC LIMIT 10")
                    users = c.fetchall()
                    conn.close()
                    
                    leaderboard_text = "<b>🏆 TOP 10 INVITANTS</b>\n\n"
                    
                    if users:
                        for i, (username, invites, points) in enumerate(users, 1):
                            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
                            leaderboard_text += f"{medal} <b>@{username}</b>\n   {invites} invites • {points} ⭐\n\n"
                    else:
                        leaderboard_text += "Pas encore de participants"
                    
                    bot.send_message(user_id, leaderboard_text, parse_mode="HTML")
                    return
                except Exception as e:
                    logger.error(f"Leaderboard error: {e}")
                    bot.send_message(user_id, "❌ Erreur lors du leaderboard")
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
                                   f"✅ @{username} a rejoint via ton lien !\n+1 invite • +100 ⭐")
                except:
                    pass
            
            conn.commit()
        else:
            c.execute("SELECT referral_code FROM users WHERE user_id = ?", (user_id,))
            referral_code = c.fetchone()[0]
        
        conn.close()
        
        message_text = f"""🎁 BIENVENUE AU CONCOURS D'INVITATION !

Ton code : <code>{referral_code}</code>

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
1000 ⭐ = 500€"""
        
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
            stats = f"""📊 TES STATISTIQUES

Code : <code>{code}</code>
Invitations : {invites}
Points : {points} ⭐

💰 Récompenses disponibles :
100 ⭐ = 10€
500 ⭐ = 100€
1000 ⭐ = 500€

Partage ton lien :
https://t.me/TF8invitationbot?start={code}

Commande : /redeem 100"""
            bot.send_message(user_id, stats, parse_mode="HTML")
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
            text="🎁 Rejoindre le concours",
            url="https://t.me/TF8invitationbot?start=join"
        )
        
        # Button to see leaderboard
        leaderboard_button = telebot.types.InlineKeyboardButton(
            text="🏆 Leaderboard",
            url="https://t.me/TF8invitationbot?start=leaderboard"
        )
        
        # Button for help
        help_button = telebot.types.InlineKeyboardButton(
            text="❓ Aide",
            url="https://t.me/TF8invitationbot?start=help"
        )
        
        # Add buttons to markup
        markup.add(join_button)
        markup.add(leaderboard_button, help_button)
        
        # Message content
        message_text = """🎁 <b>CONCOURS D'INVITATION</b>

Participez et gagnez jusqu'à <b>500€ de récompenses ! 🏆</b>

<b>💰 COMMENT ÇA MARCHE :</b>

1️⃣ Rejoignez le concours
2️⃣ Partagez votre code d'invitation
3️⃣ Chaque ami qui se joint = +100 points ⭐
4️⃣ Échangez vos points contre des récompenses

<b>🏆 RÉCOMPENSES :</b>

100 ⭐ = 10€ crédit
500 ⭐ = 100€ crédit
1000 ⭐ = 500€ prize

<b>👇 Cliquez sur le bouton ci-dessous pour commencer !</b>"""
        
        # Send the message with buttons
        bot.send_message(channel_id, message_text, 
                        parse_mode="HTML", 
                        reply_markup=markup)
        
        # Confirm to the user
        bot.reply_to(message, "✅ Message avec boutons envoyé dans le canal !")
        
    except Exception as e:
        logger.error(f"Setup channel error: {e}")
        bot.reply_to(message, f"❌ Erreur : {str(e)}")

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

# Admin command - post invitation button to channel
@bot.message_handler(commands=['announce'])
def announce(message):
    """Post the invitation button to the channel"""
    
    # Only admins can use this
    user_id = message.from_user.id
    ADMIN_IDS = [user_id]  # Change avec tes IDs admin
    
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Tu n'as pas la permission")
        return
    
    try:
        # Créer le bouton
        markup = telebot.types.InlineKeyboardMarkup()
        
        # Bouton qui ouvre le bot en DM avec /start=join
        button = telebot.types.InlineKeyboardButton(
            text="🎁 Rejoindre le concours",
            url="https://t.me/TF8invitationbot?start=join"
        )
        markup.add(button)
        
        # Message avec le bouton
        message_text = """🎉 CONCOURS D'INVITATION - TF8

Gagne des points en invitant tes amis !

💰 COMMENT ÇA MARCHE :
• Clique sur le bouton ci-dessous
• Reçois ton code d'invitation unique
• Partage-le avec tes amis
• +100 points par ami ⭐
• Échange tes points en récompenses

🏆 RÉCOMPENSES :
100 ⭐ = 10€
500 ⭐ = 100€
1000 ⭐ = 500€

C'est parti ! 🚀"""
        
        bot.send_message(message.chat.id, message_text, reply_markup=markup)
        bot.send_message(message.from_user.id, "✅ Bouton posté dans le canal !")
        
    except Exception as e:
        logger.error(f"Announce error: {e}")
        bot.reply_to(message, f"❌ Erreur : {str(e)}")

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
