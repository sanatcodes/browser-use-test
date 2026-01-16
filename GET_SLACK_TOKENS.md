# How to Get Slack Tokens

## SLACK_BOT_TOKEN

### Step 1: Go to Your Slack App
1. Visit [api.slack.com/apps](https://api.slack.com/apps)
2. Click on your **"tesco bot"** app (or whichever app you created)

### Step 2: Install the App (if not already done)
1. In the left sidebar, click **"OAuth & Permissions"**
2. Scroll down to **"Scopes"** section
3. Under **"Bot Token Scopes"**, make sure you have:
   - `app_mentions:read`
   - `chat:write`
   - `channels:history` (optional but recommended)

4. Scroll to the top and click **"Install to Workspace"** (or "Reinstall to Workspace")
5. Click **"Allow"** to authorize the app

### Step 3: Copy the Bot Token
1. After installation, you'll see **"OAuth Tokens for Your Workspace"**
2. Find **"Bot User OAuth Token"**
3. It starts with `xoxb-` followed by numbers and letters
4. Click **"Copy"** to copy the token

**This is your `SLACK_BOT_TOKEN`** ✅

---

## SLACK_SIGNING_SECRET

### Step 1: Go to Basic Information
1. In your Slack app dashboard (api.slack.com/apps)
2. Click on your **"tesco bot"** app
3. In the left sidebar, click **"Basic Information"**

### Step 2: Get Signing Secret
1. Scroll down to **"App Credentials"** section
2. Find **"Signing Secret"**
3. Click **"Show"** to reveal it
4. Copy the secret (it's a long string of letters and numbers)

**This is your `SLACK_SIGNING_SECRET`** ✅

---

## Add to Render

Once you have both tokens:

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Select your **tesco-bot** service
3. Go to **"Environment"** tab
4. Add or update these variables:

```
SLACK_BOT_TOKEN = xoxb-your-actual-token-here
SLACK_SIGNING_SECRET = your-actual-secret-here
```

5. Click **"Save Changes"**
6. Render will automatically redeploy with the new variables

---

## Quick Checklist

- [ ] Created Slack app at api.slack.com/apps
- [ ] Added bot scopes: `app_mentions:read`, `chat:write`
- [ ] Installed app to workspace
- [ ] Copied Bot User OAuth Token (starts with `xoxb-`)
- [ ] Copied Signing Secret from Basic Information
- [ ] Added both to Render environment variables
- [ ] Triggered redeploy (or it auto-deployed)

---

## Test After Adding Tokens

Run the test script again:
```bash
python test_slack_webhook.py
```

You should see:
```
✓ Health check: 200
  Response: {"status":"ok"}
```

Then update your Slack Event Subscriptions URL and test!

---

## Important Notes

- **Never commit tokens to Git!** They're in `.env` which is gitignored
- The bot token gives access to your Slack workspace - keep it secure
- If you regenerate the token, you'll need to update it in Render
- Tokens don't expire unless you manually regenerate them
