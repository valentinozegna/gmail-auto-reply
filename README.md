# Gmail Auto-Reply Bot

Monitors your Gmail inbox and automatically replies to emails from a specific sender with 2-3 second latency.

**Perfect for**: Hack challenges, competitions, or automated email responses where speed matters.

---

## Complete Setup Guide (From Scratch)

This guide assumes you have **nothing installed** and walks you through everything step-by-step.

---

## Part 1: Install Prerequisites (5-10 minutes)

### Step 1: Install Homebrew (macOS/Linux)

**macOS users:**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the instructions at the end to add Homebrew to your PATH.

**Linux users:** Follow instructions at <https://brew.sh>

**Windows users:** Use [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) first, then install Homebrew.

### Step 2: Install Python 3.14

```bash
brew install python@3.14
```

Verify installation:

```bash
python3 --version
# Should show: Python 3.14.x or higher
```

### Step 3: Clone This Repository

```bash
# Navigate to where you want the project
cd ~/Developer  # or wherever you keep projects

# Clone the repo (replace with your actual repo URL)
git clone <your-repo-url>
cd icandoit
```

Don't have git? Install it:

```bash
brew install git
```

### Step 4: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Your terminal prompt should now show (venv)
```

### Step 5: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `google-auth` - Google authentication
- `google-auth-oauthlib` - OAuth2 flow
- `google-api-python-client` - Gmail API

---

## Part 2: Set Up Google Cloud Project (10 minutes)

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** at the top
3. Click **"New Project"**
   - Project name: `Gmail Auto-Reply` (or any name)
   - Click **"Create"**
4. Wait for project to be created (takes ~30 seconds)
5. Make sure the new project is selected (check top bar)

### Step 2: Enable Gmail API

1. In the search bar at the top, type **"Gmail API"**
2. Click on **"Gmail API"** in the results
3. Click the blue **"Enable"** button
4. Wait for it to enable (~10 seconds)

### Step 3: Configure OAuth Consent Screen

1. In the left sidebar, click **"OAuth consent screen"**
2. Choose **"External"** user type
3. Click **"Create"**

**Fill out the form:**
- **App name**: `Gmail Auto-Reply`
- **User support email**: Your email
- **Developer contact email**: Your email
- Click **"Save and Continue"**

**Scopes page:**
- Click **"Add or Remove Scopes"**
- In the filter box, paste: `https://mail.google.com/`
- Check the box for **"<https://mail.google.com/>"** (full Gmail access)
- Click **"Update"**
- Click **"Save and Continue"**

**Test users page:**
- Click **"Add Users"**
- Enter **your Gmail address** (the one you'll monitor)
- Click **"Add"**
- Click **"Save and Continue"**

Click **"Back to Dashboard"**

### Step 4: Create OAuth2 Credentials

1. In the left sidebar, click **"Credentials"**
2. Click **"+ Create Credentials"** at the top
3. Select **"OAuth client ID"**
4. Application type: **"Desktop app"**
5. Name: `Gmail Auto-Reply Desktop`
6. Click **"Create"**

**Download the credentials:**
1. A popup shows your Client ID and Secret
2. Click **"Download JSON"**
3. Save the file as `credentials.json` in your `icandoit` folder

**Important:** The file must be named exactly `credentials.json` and placed in the same folder as `main.py`.

---

## Part 3: Configure the Script (2 minutes)

### Step 1: Create Your Config File

```bash
# Make sure you're in the icandoit folder
cd ~/Developer/icandoit  # adjust path if needed

# Copy the example config
cp config.py.example config.py
```

### Step 2: Edit config.py

**Open `config.py` in a text editor** and update these two settings:

```python
# The email address you want to monitor responses from
TARGET_SENDER_EMAIL = 'their.email@example.com'  # ← Change this!

# The auto-reply message to send
AUTO_REPLY_MESSAGE = 'I can do it'  # ← Change this if you want!
```

**Example:**

```python
TARGET_SENDER_EMAIL = '<senders_email>@gmail.com'
AUTO_REPLY_MESSAGE = 'Got it! I can do it.'
```

**Save the file** - that's it!

**Note:** The script will automatically detect which Gmail account you're using when you authenticate in the next step.

---

## Part 4: Run the Script (5 minutes)

### Step 1: Start the Monitor

```bash
# Make sure you're in the icandoit folder
cd ~/Developer/icandoit  # adjust path if needed

# Activate virtual environment
source venv/bin/activate

# Run the script
python main.py
```

### Step 2: Complete OAuth Authorization (First Time Only)

When you run the script for the first time:

1. **Browser opens automatically** with Google sign-in
2. **Sign in** with the Gmail account you want to monitor
3. You'll see a warning: **"Google hasn't verified this app"**
   - Click **"Advanced"**
   - Click **"Go to Gmail Auto-Reply (unsafe)"**
4. Review permissions and click **"Allow"**
5. You'll see: **"The authentication flow has completed"**
6. **Close the browser tab**

The script will save your token to `token.json` and start monitoring.

### Step 3: Verify It's Running

You should see:

```
============================================================
Gmail Auto-Reply Monitor
============================================================

[1/3] Authenticating with Gmail...
  ✓ Authenticated as: your.email@gmail.com

[2/3] Monitoring for emails from: <senders_email>@gmail.com
  ✓ Using IMAP IDLE (2-3 second latency)
  ✓ Auto-reply message: 'Got it! I can do it.'

[3/3] Connecting to Gmail IMAP...
  ✓ Connected to Gmail IMAP

============================================================
MONITORING ACTIVE - 2025-11-21 14:30:45
============================================================
Waiting for emails... (Press Ctrl+C to stop)
```

**The script is now running!** Leave this terminal window open.

---

## Part 5: Test It

### Send a Test Email

1. From `<senders_email>@gmail.com` (or your configured address), send an email to your monitored Gmail account
2. Watch the script output

You should see:

```
[14:30:52] New activity detected!
  → Found 1 new message(s) from <senders_email>@gmail.com
  → From: <senders_email>@gmail.com
  → Subject: Test message
  → Sending auto-reply...
  ✓ Reply sent! Message ID: 18d3a4b2f8c1234
```

**Check the sender's inbox** - they should receive "I can do it" within 2-3 seconds!

---

## Running in Background

To keep the script running when you close the terminal:

```bash
# Start in background
nohup python main.py > output.log 2>&1 &

# Check if running
ps aux | grep gmail_auto_reply

# Stop it
pkill -f main.py
```

---

## Stopping the Script

**In the terminal:**
Press `Ctrl+C` to stop gracefully.

**If running in background:**

```bash
pkill -f main.py
```

---

## How It Works

```
┌─────────────┐
│   Gmail     │ ← New email arrives
│   Server    │
└──────┬──────┘
       │
       │ IMAP IDLE push notification (instant)
       │
       ▼
┌─────────────┐
│ Your Script │ ← Detects email in 2-3 seconds
│  (Running)  │
└──────┬──────┘
       │
       │ Gmail API
       │
       ▼
┌─────────────┐
│  Send Reply │ → "I can do it"
│   to Sender │
└─────────────┘
```

**Key Technologies:**
- **IMAP IDLE**: Persistent connection for instant notifications
- **Gmail API**: Sends replies with proper threading
- **OAuth2**: Secure authentication (no password needed)

**Latency: 2-3 seconds** from email arrival to reply sent.

---

## Files Explained

```
icandoit/
├── main.py    # Main script
├── config.py.example      # Example config (copy to config.py)
├── config.py             # YOUR SETTINGS (you create this!)
├── requirements.txt       # Python dependencies
├── credentials.json       # OAuth2 client credentials (YOU PROVIDE)
├── token.json            # Access token (AUTO-GENERATED)
├── .gitignore            # Protects secrets from git
├── README.md             # This file
└── venv/                 # Virtual environment (local only)
```

**Important:**
- `config.py.example` - Template config (included in repo)
- `config.py` - Copy from example and edit with your settings
- `credentials.json` - Download from Google Cloud Console (never commit to git)
- `token.json` - Auto-generated on first run (never commit to git)

All sensitive files are already in `.gitignore` for safety.

---

## Troubleshooting

### "config.py not found"

You forgot to create your config file. Go back to **Part 3, Step 1**:

```bash
cp config.py.example config.py
```

Then edit `config.py` with your settings.

### "credentials.json not found"

You forgot to download the OAuth2 credentials from Google Cloud Console. Go back to **Part 2, Step 4**.

### "Access blocked: Gmail Auto-Reply has not completed the Google verification process"

Your Gmail account isn't added as a test user.

**Fix:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **"OAuth consent screen"**
4. Scroll to **"Test users"**
5. Click **"Add Users"**
6. Add your Gmail address
7. Try running the script again

### "Authentication failed" or "Invalid credentials"

Delete `token.json` and run the script again to re-authenticate:

```bash
rm token.json
python main.py
```

### Script crashes or "Connection error"

**Check internet connection:**

```bash
ping gmail.google.com
```

**The script auto-reconnects** every 5 seconds if there's a connection issue. Just wait.

### No auto-reply sent

**Checklist:**
1. Is the script running? Check the terminal.
2. Is the sender's email exactly `<senders_email>@gmail.com`? (case-sensitive in script config)
3. Check the terminal output for errors
4. Make sure the email is arriving in your **Inbox** (not spam/other folders)

### "ModuleNotFoundError: No module named 'google'"

You forgot to activate the virtual environment or install dependencies:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Script is slow or not detecting emails

IMAP IDLE should detect emails in 2-3 seconds. If it's slower:

1. Check your internet speed
2. Gmail IMAP might be throttling (rare)
3. Make sure no other email clients are connected with IDLE

---

## Security & Privacy

**What access does this script have?**
- Full access to your Gmail account (required for IMAP IDLE + sending)
- Can read, send, delete emails
- Scope: `https://mail.google.com/` (full Gmail access)

**Is it safe?**
- OAuth2 tokens are stored locally in `token.json`
- Tokens can be revoked anytime: <https://myaccount.google.com/permissions>
- The script only auto-replies to ONE specific sender
- Open source - you can audit all the code

**Best practices:**
- Never commit `credentials.json` or `token.json` to git
- Don't share these files with anyone
- Keep your OAuth consent screen in "Testing" mode (not published)
- Add only trusted test users

**To revoke access:**
1. Go to <https://myaccount.google.com/permissions>
2. Find "Gmail Auto-Reply"
3. Click "Remove Access"
4. Delete `token.json` from your local folder

---

## Customization

### Change Target Sender or Reply Message

Simply edit `config.py`:

```python
TARGET_SENDER_EMAIL = 'different.email@example.com'
AUTO_REPLY_MESSAGE = 'Your custom reply message here'
```

Restart the script for changes to take effect.

### Monitor Multiple Senders

Current version only supports one sender. To monitor multiple, you'd need to modify the `search_unseen_from()` function or run multiple instances.

### Add Conditions (Time-based, Subject filters, etc.)

Modify the logic in the `monitor_inbox()` function around line 365 where it checks:

```python
if from_addr == TARGET_SENDER_EMAIL.lower():
```

Add your custom conditions here.

---

## FAQ

**Q: Can I run this on Windows?**
A: Yes, but you need to use WSL2 (Windows Subsystem for Linux) or adapt the commands for Windows PowerShell.

**Q: Does this work with Gmail aliases?**
A: Yes, it monitors the main Gmail account. Emails sent to aliases will trigger auto-replies.

**Q: Can I reply to multiple people?**
A: Currently one sender only. You'd need to modify the code or run multiple instances.

**Q: What if my computer goes to sleep?**
A: The script will disconnect but auto-reconnect when the computer wakes up. For 24/7 operation, run in background with `nohup`.

**Q: Does this violate Gmail's Terms of Service?**
A: No. This uses official Gmail APIs and OAuth2. It's the same method used by email clients like Thunderbird.

**Q: Can Google see my emails?**
A: Your emails stay between you and Gmail. Google's OAuth consent tells you exactly what access you're granting.

**Q: Why not use Gmail filters?**
A: Gmail filters can only auto-reply once per 4 days to the same sender. This script has no such limit and is faster.

---


## Support

Having issues? Check:
1. This README troubleshooting section
2. Make sure you followed ALL steps
3. Check that files are in the correct locations
4. Verify your Python version is 3.14+

Still stuck? Double-check:
- Virtual environment is activated (`source venv/bin/activate`)
- `credentials.json` is in the same folder as the script
- You added your email as a test user in Google Cloud Console
- You're using the correct Gmail account

---

## License

MIT License - Feel free to modify and use for your own projects!

---

**Built for speed.** ⚡ **Responds in 2-3 seconds.** 🚀
