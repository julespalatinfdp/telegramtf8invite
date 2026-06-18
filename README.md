# TF8 Telegram Referral Bot

Bot Telegram de concours d'invitation avec système de points et leaderboard.

## 🚀 Deployment sur Railway

### Prérequis
- Compte Railway.app (gratuit)
- Compte GitHub
- Token Telegram Bot (tu as : `8858099521:AAEPfDknvo8QAGv7ws4IJ4eArPbh3mdAnzk`)

### Étapes de deployment

1. **Crée un repo GitHub**
   ```bash
   git init
   git add .
   git commit -m "TF8 Referral Bot"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/tf8-referral-bot.git
   git push -u origin main
   ```

2. **Va sur railway.app**
   - Login avec GitHub
   - Clique "New Project"
   - Sélectionne "Deploy from GitHub repo"
   - Connecte ton repo `tf8-referral-bot`

3. **Ajoute la variable d'environnement**
   - Va dans "Variables"
   - Ajoute : `BOT_TOKEN` = `8858099521:AAEPfDknvo8QAGv7ws4IJ4eArPbh3mdAnzk`

4. **Deploy**
   - Railway deploy automatiquement
   - Attend 2-3 min
   - Clique "View Logs" pour vérifier

### Fichiers inclus
- `tf8_referral_bot.py` - Code principal du bot
- `requirements.txt` - Dépendances Python
- `Procfile` - Config Railway

## 📋 Commandes du bot

- `/start` - Enregistrement et obtenir le code d'invitation
- `/mystats` - Voir tes stats (invites, points)
- `/leaderboard` - Classement top 10
- `/redeem <points>` - Convertir points en récompense
- `/help` - Aide complète

## 💰 Système de points

- +100 points par invitation
- 100 points = 10€ crédit
- 500 points = 100€ crédit
- 1000 points = 500€ prize

## 🔒 Sécurité

- Token stocké en variable d'environnement (jamais en dur)
- Database SQLite locale (automatique)
- Pas de données sensibles en git

## 📞 Support

En cas de problème :
1. Vérifie les logs Railway
2. Redéploie le projet
3. Vérifie que le token est correct
