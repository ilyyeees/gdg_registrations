# GDG ENSIA Automated Onboarding System

This system automatically sends welcome emails to accepted team members and verifies them on Discord with role assignment.

## ⚠️ IMPORTANT: Before Running

### 1. Update `config.py` with the correct VERIFICATION_CHANNEL_ID

- Open Discord
- Go to User Settings > App Settings > Advanced
- Enable **Developer Mode**
- Right-click your **#verification** channel
- Click **Copy ID**
- Paste this ID in `config.py` as `VERIFICATION_CHANNEL_ID`

### 2. Update the Robotics Role ID (if needed)

- In `config.py`, update the Robotics role_id with your actual Discord role ID

### 3. Prepare Your CSV Files

You need to place your CSV files in the main directory:

- `Registrations.xlsx - IT_AI_Accepted.csv`
- `Registrations.xlsx - IT_Web Development_Accepted.csv`
- `Registrations.xlsx - IT_Mobile Development_Accepted.csv`
- `Registrations.xlsx - IT_Robotics_Accepted.csv`
- `Registrations.xlsx - Marketing_Accepted.csv`
- `Registrations.xlsx - Design_Accepted.csv`
- `Registrations.xlsx - Event_Accepted.csv`
- `Registrations.xlsx - Relex_Accepted.csv`

**CSV Format:** Each CSV must have columns: `email`, `firstName`, `lastName`

### 4. Update HTML Templates

Open each HTML file in the `Registrations emails/` folder and ensure:

- Replace any hardcoded names with `{{FIRST_NAME}}`
- Add `{{VERIFICATION_TOKEN}}` where you want the token to appear
- Any Discord invite links should be present (they'll be auto-replaced)

## 📧 Step 1: Send Welcome Emails

Activate the virtual environment and run the email script:

```bash
source venv/bin/activate
python send_invites.py
```

This will:

- ✅ Create a database (`member_database.db`)
- ✅ Generate unique tokens for each member
- ✅ Send personalized welcome emails
- ✅ Store member info in the database

**Note:** The script will skip users already in the database, so you can run it multiple times safely.

## 🤖 Step 2: Start the Discord Bot

In a **new terminal window**, activate the venv and start the bot:

```bash
source venv/bin/activate
python bot.py
```

Keep this terminal running! The bot needs to be online to verify members.

You should see:

```
Logged in as [Your Bot Name]
Bot is online and ready to verify members.
------
```

## 🎯 How Members Get Verified

1. Member receives email with their unique verification token
2. Member joins Discord server using the invite link
3. Member goes to the **#verification** channel
4. Member types: `!verify [their_token]`
5. Bot automatically assigns them their team role and welcomes them!

## 🔧 Troubleshooting

### Bot can't assign roles

- Make sure the bot's role is **higher** than the roles it needs to assign in Discord's role hierarchy
- Check that the bot has "Manage Roles" permission

### Emails not sending

- Double-check your `EMAIL_PASSWORD` is the 16-character App Password (not your regular Gmail password)
- Make sure 2-Step Verification is enabled on your Google account

### "Token is invalid"

- The token is case-sensitive
- Make sure there are no extra spaces when copying

### Role IDs not working

- Verify Developer Mode is enabled in Discord
- Make sure you copied the correct role IDs

## 📁 Files Overview

- `config.py` - All your configuration (passwords, tokens, role IDs)
- `send_invites.py` - Script to send emails and populate database
- `bot.py` - Discord bot that handles verification
- `member_database.db` - SQLite database (created automatically)
- `acceptance-*.html` - Email templates for each team

## 🔒 Security Notes

- **NEVER** commit `config.py` to GitHub (it contains secrets!)
- Keep `member_database.db` private (contains user emails)
- Your bot token and email password should remain confidential
