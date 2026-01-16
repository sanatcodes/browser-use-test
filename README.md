# Tesco Bot - Slack-Triggered Grocery Automation

Automate your Tesco.ie grocery shopping by mentioning `@tesco-bot` in Slack with your grocery list!

## Features

- 🛒 Automated grocery ordering on Tesco.ie
- 💬 Slack bot integration via `@tesco-bot` mentions
- 🔗 Returns cart URL when complete
- ☁️ Runs on Render (or any hosting platform)
- 🔒 Secure credential handling

## Quick Start

### 1. Set Up Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App**
2. Choose **From scratch** and name it `tesco bot`
3. Select your workspace and click **Create App**

#### Configure Event Subscriptions

1. In your app settings, go to **Event Subscriptions**
2. Enable Events and set Request URL to: `https://your-render-app.onrender.com/slack/events`
   - Replace `your-render-app` with your actual Render app URL
3. Under **Subscribe to bot events**, add:
   - `app_mention`
   - `message.channels` (if needed)
4. Click **Save Changes**

#### Configure OAuth & Permissions

1. Go to **OAuth & Permissions** in the sidebar
2. Under **Scopes** → **Bot Token Scopes**, add:
   - `app_mentions:read`
   - `chat:write`
   - `channels:history` (if needed)
3. Scroll up and click **Install to Workspace**
4. Authorize the app
5. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

#### Get Signing Secret

1. Go to **Basic Information** in the sidebar
2. Under **App Credentials**, find **Signing Secret**
3. Click **Show** and copy the secret

### 2. Get Browser Use Credentials

1. Go to [cloud.browser-use.com/settings?tab=api-keys](https://cloud.browser-use.com/settings?tab=api-keys)
2. Create or copy your API key
3. (Optional) Create a browser profile and copy the profile ID

### 3. Deploy to Render

#### Create Web Service

1. Go to [render.com](https://render.com) and sign up/log in
2. Click **New +** → **Web Service**
3. Connect your GitHub repository (or use manual deploy)
4. Configure the service:
   - **Name**: `tesco-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python slack_server.py`

#### Set Environment Variables

In the Render dashboard, add these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `SLACK_SIGNING_SECRET` | From Slack App → Basic Information | `abc123...` |
| `SLACK_BOT_TOKEN` | From Slack App → OAuth & Permissions | `xoxb-...` |
| `BROWSER_USE_API_KEY` | From Browser Use Cloud | `bu-...` |
| `TESCO_EMAIL` | Your Tesco.ie login email | `you@example.com` |
| `TESCO_PASSWORD` | Your Tesco.ie password | `yourpassword` |
| `BROWSER_USE_PROFILE_ID` | (Optional) Browser profile ID | `67887261-...` |
| `PORT` | (Optional) Server port | `8000` |

#### Deploy

1. Click **Create Web Service**
2. Wait for deployment to complete
3. Copy your app URL (e.g., `https://tesco-bot.onrender.com`)
4. Go back to Slack App → **Event Subscriptions** and update the Request URL with your Render URL

### 4. Invite Bot to Channel

1. Go to the Slack channel where you want to use the bot
2. Type `/invite @tesco-bot` or add the bot via channel settings
3. The bot is now ready to use!

## Usage

### Mention the Bot with Grocery List

In any channel where the bot is present, mention it with your grocery list:

```
@tesco-bot milk 2L, wholemeal bread, bananas 1kg, cheddar cheese, butter
```

Or use newlines:

```
@tesco-bot
milk 2L
wholemeal bread
bananas 1kg
```

### Bot Response

The bot will:
1. Acknowledge your request immediately
2. Run the automation (takes a few minutes)
3. Reply with the cart URL and any items that couldn't be added

Example response:
```
✅ Your Tesco order is ready!

🛒 Cart URL: https://www.tesco.ie/groceries/en-IE/trolley

⚠️ Some items couldn't be added:
• eggs dozen (Failed to add due to dynamic indexing issues)
```

## Local Development

### Run CLI Version

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export BROWSER_USE_API_KEY=your-key
export TESCO_EMAIL=your-email
export TESCO_PASSWORD=your-password

# Run script
python tesco_groceries.py
```

### Run Slack Server Locally

```bash
# Set all environment variables (including Slack credentials)
export SLACK_SIGNING_SECRET=your-secret
export SLACK_BOT_TOKEN=your-token
export BROWSER_USE_API_KEY=your-key
export TESCO_EMAIL=your-email
export TESCO_PASSWORD=your-password

# Run server
python slack_server.py

# In another terminal, use ngrok to expose local server
ngrok http 8000

# Update Slack Event Subscriptions URL to your ngrok URL
```

## Troubleshooting

### Bot doesn't respond

- Check that the bot is invited to the channel
- Verify Event Subscriptions URL is correct in Slack app settings
- Check Render logs for errors
- Ensure all environment variables are set correctly

### Authentication fails

- Verify `TESCO_EMAIL` and `TESCO_PASSWORD` are correct
- Check if Tesco.ie account is active
- Try using a browser profile ID to maintain session

### Items not added

- Some items may have dynamic page elements that are hard to click
- Check the bot's response for specific items that failed
- The cart URL is still provided with successfully added items

## Security Notes

- Never commit `.env` files or credentials to git
- Use environment variables for all sensitive data
- Slack signatures are verified on all incoming requests
- Credentials are injected securely via browser-use sensitive_data

## Files

- `tesco_groceries.py` - Core automation script (CLI + reusable function)
- `slack_server.py` - Slack Events API server
- `requirements.txt` - Python dependencies
- `.env.example` - Example environment variables (create your own `.env`)

## License

MIT

## Support

For issues or questions, open an issue on GitHub.
