# Tesco Bot Setup Guide

Quick reference for setting up your Slack-triggered Tesco grocery bot.

## What You Need from Slack

### 1. Create Slack App (5 minutes)

1. Visit [api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App** → **From scratch**
3. Name: `tesco bot`
4. Select your workspace

### 2. Configure App

#### Event Subscriptions
- Go to **Event Subscriptions** → Enable Events
- Request URL: `https://your-app.onrender.com/slack/events` (update after deploying to Render)
- Bot Events: Add `app_mention`
- Save Changes

#### OAuth & Permissions
- Go to **OAuth & Permissions**
- Bot Token Scopes: Add `app_mentions:read` and `chat:write`
- Click **Install to Workspace**
- Copy the **Bot User OAuth Token** (starts with `xoxb-`)

#### Get Signing Secret
- Go to **Basic Information**
- Copy **Signing Secret** from App Credentials

## What You Need from Your Side

### Environment Variables for Render

```
SLACK_SIGNING_SECRET=<from Slack App → Basic Information>
SLACK_BOT_TOKEN=<from Slack App → OAuth & Permissions>
BROWSER_USE_API_KEY=<from cloud.browser-use.com>
TESCO_EMAIL=<your Tesco.ie email>
TESCO_PASSWORD=<your Tesco.ie password>
BROWSER_USE_PROFILE_ID=<optional: your profile ID>
```

## Deploy to Render

1. Go to [render.com](https://render.com)
2. New → Web Service
3. Connect your GitHub repo
4. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python slack_server.py`
   - Add all environment variables above
5. Deploy
6. Copy your Render URL (e.g., `https://tesco-bot.onrender.com`)
7. Update Slack Event Subscriptions URL with your Render URL

## Usage

In Slack:
```
@tesco-bot milk 2L, bread, bananas, cheese
```

The bot will:
1. Acknowledge immediately
2. Run automation (2-5 minutes)
3. Reply with cart URL

## Testing Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SLACK_SIGNING_SECRET=your-secret
export SLACK_BOT_TOKEN=your-token
export BROWSER_USE_API_KEY=your-key
export TESCO_EMAIL=your-email
export TESCO_PASSWORD=your-password

# Run server
python slack_server.py

# Use ngrok to expose locally
ngrok http 8000
# Update Slack Event URL to ngrok URL
```

## Files Created

- `slack_server.py` - Slack bot server
- `tesco_groceries.py` - Refactored with `run_groceries()` function
- `requirements.txt` - Dependencies
- `README.md` - Full documentation
- `.gitignore` - Git ignore file

## Next Steps

1. Create Slack app and get credentials
2. Deploy to Render with environment variables
3. Update Slack Event Subscriptions URL
4. Invite `@tesco-bot` to a channel
5. Test with: `@tesco-bot milk, bread`

That's it! 🎉
