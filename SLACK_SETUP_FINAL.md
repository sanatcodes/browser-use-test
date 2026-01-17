# Final Slack Setup - Update Event URL

## Your Correct Render URL

```
https://browser-use-test-5mb4.onrender.com
```

## Steps to Configure Slack

### 1. Update Event Subscriptions

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click on your **"tesco bot"** app
3. In the left sidebar, click **"Event Subscriptions"**
4. Set Request URL to:
   ```
   https://browser-use-test-5mb4.onrender.com/slack/events
   ```
5. Slack will send a verification request - it should show a **green checkmark** ✓
6. Click **"Save Changes"**

### 2. Verify Bot is Installed

1. In your Slack app settings, go to **"Install App"**
2. Make sure it says "Installed to workspace"
3. If not, click **"Install to Workspace"** and authorize

### 3. Invite Bot to Channel

In your Slack workspace:
1. Go to the channel where you want to use the bot
2. Type: `/invite @tesco-bot`
3. Or add via channel settings → Integrations → Add apps

### 4. Test!

In the channel where you invited the bot:
```
@tesco-bot milk, bread, bananas
```

You should get:
1. Immediate acknowledgment: "🛒 Starting your Tesco order..."
2. After a few minutes: Cart URL and results

## Troubleshooting

### If Slack shows "This URL did not respond with the value of the challenge parameter"

- Make sure the URL is exactly: `https://browser-use-test-5mb4.onrender.com/slack/events`
- Check Render logs for errors
- The server should show a POST request when Slack sends the verification

### If bot doesn't respond to mentions

- Check that bot is invited to the channel (you should see it in the member list)
- Check Render logs for incoming requests when you mention the bot
- Verify Event Subscriptions is enabled and saved

### Check if it's working

Run this test:
```bash
curl -X POST https://browser-use-test-5mb4.onrender.com/slack/events \
  -H "Content-Type: application/json" \
  -d '{"type":"url_verification","challenge":"test123"}'
```

Should return: `{"challenge":"test123"}`

## Your URLs Summary

- ❌ Old (wrong): `https://tesco-bot-4ckg.onrender.com`
- ✅ Correct: `https://browser-use-test-5mb4.onrender.com`
- ✅ Health check: `https://browser-use-test-5mb4.onrender.com/health`
- ✅ Slack events: `https://browser-use-test-5mb4.onrender.com/slack/events`
