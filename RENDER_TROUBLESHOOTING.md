# Render Deployment Troubleshooting

## Current Issue: 404 Not Found

The server is returning 404 errors, which means either:
1. The app isn't starting correctly
2. The routes aren't being registered
3. There's a configuration issue

## Steps to Fix

### 1. Check Render Logs

Go to your Render dashboard:
- https://dashboard.render.com/
- Select your `tesco-bot` service
- Click on "Logs" tab
- Look for errors during startup

Common errors to look for:
- `ModuleNotFoundError` - Missing dependencies
- `ValueError` - Missing environment variables
- Port binding issues

### 2. Verify Build & Start Commands

In Render dashboard → Settings:

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
python slack_server.py
```

### 3. Verify Environment Variables

In Render dashboard → Environment:

Required variables:
- ✓ `SLACK_SIGNING_SECRET`
- ✓ `SLACK_BOT_TOKEN`
- ✓ `BROWSER_USE_API_KEY`
- ✓ `TESCO_EMAIL`
- ✓ `TESCO_PASSWORD`

Optional:
- `BROWSER_USE_PROFILE_ID`
- `PORT` (Render sets this automatically)

### 4. Check requirements.txt

Make sure your `requirements.txt` is committed and includes:
```
python-dotenv==1.2.1
browser-use==0.11.3
openai==2.15.0
fastapi==0.115.6
uvicorn[standard]==0.34.0
httpx==0.28.1
```

### 5. Verify File Structure

Your repo should have:
```
.
├── slack_server.py
├── tesco_groceries.py
├── requirements.txt
├── README.md
└── .gitignore
```

### 6. Manual Deploy Trigger

If files were recently pushed:
1. Go to Render dashboard
2. Click "Manual Deploy" → "Deploy latest commit"
3. Wait for build to complete
4. Check logs for errors

## Testing After Fix

Once deployed, run this test:

```bash
# Test health endpoint
curl https://tesco-bot-4ckg.onrender.com/health

# Should return: {"status":"ok"}
```

Or use the test script:
```bash
python test_slack_webhook.py
```

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'fastapi'"
**Solution:** 
- Ensure `requirements.txt` is in root directory
- Verify Build Command is: `pip install -r requirements.txt`
- Trigger manual deploy

### Issue: "ValueError: SLACK_SIGNING_SECRET environment variable is required"
**Solution:**
- Add missing environment variables in Render dashboard
- Redeploy after adding variables

### Issue: Port binding errors
**Solution:**
- Don't set `PORT` manually - Render sets it automatically
- The code uses `int(os.getenv("PORT", 8000))` which handles this

### Issue: App starts but routes return 404
**Solution:**
- Check if `slack_server.py` is the main file being run
- Verify Start Command is exactly: `python slack_server.py`
- Check logs for FastAPI startup messages

## Expected Startup Logs

When working correctly, you should see:
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000 (Press CTRL+C to quit)
```

## Next Steps After Fix

1. Test endpoints:
   ```bash
   curl https://tesco-bot-4ckg.onrender.com/health
   # Should return: {"status":"ok"}
   ```

2. Update Slack Event Subscriptions:
   - Go to https://api.slack.com/apps
   - Select your app
   - Event Subscriptions → Request URL
   - Set to: `https://tesco-bot-4ckg.onrender.com/slack/events`
   - Slack will verify with a challenge request

3. Test in Slack:
   - Invite bot to channel: `/invite @tesco-bot`
   - Send test: `@tesco-bot milk, bread`

## Still Having Issues?

1. Check Render status page: https://status.render.com/
2. Review Render logs carefully for specific error messages
3. Try deploying a minimal test (just health endpoint)
4. Contact Render support if infrastructure issues

## Quick Verification Checklist

- [ ] Files committed to GitHub
- [ ] Render service created and linked to repo
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `python slack_server.py`
- [ ] All environment variables set
- [ ] Latest commit deployed
- [ ] Logs show successful startup
- [ ] Health endpoint returns 200
- [ ] Slack Event URL updated
