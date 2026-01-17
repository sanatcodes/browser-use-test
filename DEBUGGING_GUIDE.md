# Debugging Guide for Slack Bot on Render

## Overview
This guide explains the comprehensive logging added to help debug the Slack bot when running on Render.

## What Was Added

### 1. **Structured Logging Functions**

Three logging functions were added to both `slack_server.py` and `tesco_groceries.py`:

- `log_info()` - General informational messages
- `log_error()` - Error messages with context
- `log_debug()` - Detailed debugging information

All logs include:
- ISO timestamp
- Log level (INFO/ERROR/DEBUG)
- Message
- Optional JSON-formatted key-value pairs

### 2. **Slack Server Logging (`slack_server.py`)**

**Startup Logs:**
- Environment variable detection (what's loaded, what's missing)
- Credentials validation (with lengths and prefixes for debugging)

**Request Logs:**
- Every incoming request to `/slack/events`
- Request body details (length, headers)
- Signature verification steps and results
- Event type and ID
- Whether events were already processed

**Processing Logs:**
- Parsed grocery items
- User and channel information
- Slack API call results
- Background task creation

**Automation Logs:**
- When automation starts
- Browser initialization
- LLM initialization
- Agent execution progress
- Cart URL extraction
- Error details with stack traces

### 3. **Tesco Automation Logging (`tesco_groceries.py`)**

**Environment Checks:**
- API key presence
- Profile ID detection
- Tesco credentials validation

**Browser Automation:**
- Browser initialization success/failure
- LLM initialization
- Agent setup
- Step-by-step execution (with step counter)
- Live browser URL
- Final result extraction
- Cart URL detection

### 4. **Enhanced Health Check**

The `/health` endpoint now returns:
```json
{
  "status": "ok",
  "has_slack_token": true,
  "has_signing_secret": true
}
```

### 5. **New Root Endpoint**

A new root endpoint (`/`) shows service info:
```json
{
  "service": "Tesco Slack Bot",
  "status": "running",
  "endpoints": {
    "/slack/events": "POST - Slack Events API",
    "/health": "GET - Health check"
  }
}
```

## How to Read Render Logs

### 1. **Check Startup**

Look for these logs when the service starts:
```
[timestamp] INFO: 🚀 Starting Slack Bot Server
[timestamp] DEBUG: Environment loaded {"env_file_exists": false}
[timestamp] DEBUG: Slack credentials loaded {"has_signing_secret": true, ...}
[timestamp] INFO: 🔧 Validating environment variables
[timestamp] INFO: ✅ Environment variables validated
[timestamp] INFO: 🌐 Starting server on port 10000
```

If you see errors here, environment variables are missing.

### 2. **Check Incoming Requests**

When Slack sends a message:
```
[timestamp] INFO: 📨 Received request to /slack/events
[timestamp] DEBUG: Request details {"body_length": 123, "has_timestamp": true, ...}
[timestamp] DEBUG: Verifying Slack signature {"has_secret": true, ...}
[timestamp] INFO: ✅ Slack signature verified
[timestamp] DEBUG: Parsed JSON body {"event_type": "event_callback"}
```

If signature verification fails, check your `SLACK_SIGNING_SECRET`.

### 3. **Check Event Processing**

Look for:
```
[timestamp] INFO: 📬 Received event callback {"event_id": "...", "event_type": "app_mention"}
[timestamp] INFO: 👤 App mention received {"user": "U123", "channel": "C456", "text": "..."}
[timestamp] DEBUG: Parsed grocery list {"items": ["milk", "bread"], "count": 2}
[timestamp] INFO: Sending acknowledgment to Slack
[timestamp] INFO: 🚀 Creating background task for automation
```

### 4. **Check Automation Progress**

The automation will log:
```
[timestamp] INFO: 🤖 Starting grocery automation in background {"item_count": 2, ...}
[timestamp] TESCO_INFO: 🚀 Starting run_groceries function {"item_count": 2}
[timestamp] TESCO_INFO: Checking environment variables {"has_api_key": true, ...}
[timestamp] TESCO_INFO: Initializing browser {"use_cloud": true, ...}
[timestamp] TESCO_INFO: ✅ Browser initialized successfully
[timestamp] TESCO_INFO: Initializing LLM
[timestamp] TESCO_INFO: ✅ LLM initialized successfully
[timestamp] TESCO_INFO: 🏃 Starting agent execution {"max_steps": 150}
[timestamp] TESCO_INFO: Step 1 starting
[timestamp] TESCO_INFO: Step 2 starting
...
[timestamp] TESCO_INFO: ✅ Agent execution completed {"total_steps": 45}
[timestamp] TESCO_INFO: Final result obtained {"result_length": 234}
[timestamp] INFO: Cart created successfully {"cart_url": "...", "missing_items": 0}
[timestamp] INFO: 🎉 Automation workflow completed
```

### 5. **Check for Errors**

Error logs will include:
- Error message
- Error type
- Stack trace (for exceptions)

Example:
```
[timestamp] ERROR: Agent execution failed {"error": "...", "error_type": "TimeoutError"}
[timestamp] ERROR: Stack trace {"trace": "..."}
```

## Common Issues and What to Look For

### Issue: No logs after "INFO: 📨 Received request"

**Symptom:** Server receives request but nothing happens
**Look for:** 
- Signature verification failure
- JSON parsing errors
- Missing timestamps/signatures

### Issue: Logs stop after "Creating background task"

**Symptom:** Task is created but no automation logs appear
**Look for:**
- Missing `BROWSER_USE_API_KEY`
- Missing Tesco credentials
- Browser initialization failures

### Issue: Steps start but stop early

**Symptom:** See "Step 1 starting" but not many more steps
**Look for:**
- Browser errors
- LLM errors
- API rate limits
- Network timeouts

### Issue: No cart URL in result

**Symptom:** Automation completes but no cart URL
**Look for:**
- "No cart URL found in result" error
- Check the final result in logs
- May indicate agent couldn't complete the task

## Testing Locally

Run the logging test:
```bash
cd /path/to/browser-use-test
source venv/bin/activate
python test_logging.py
```

This will verify:
- All environment variables are set
- Logging functions work correctly
- Output format is correct

## Viewing Render Logs

### Real-time:
1. Go to https://dashboard.render.com
2. Select your service
3. Click "Logs" tab
4. Watch logs in real-time

### Filter logs:
- Search for "ERROR" to find errors
- Search for "TESCO_INFO" to see automation progress
- Search for "app_mention" to see when bot is triggered
- Search for "Cart created" to see successful completions

## Next Steps if Bot is Still Not Working

1. **Check the startup logs** - Are all environment variables set?
2. **Test the /health endpoint** - Visit `https://your-app.onrender.com/health`
3. **Look for incoming requests** - Do you see "📨 Received request" when you message the bot?
4. **Check signature verification** - Does it pass or fail?
5. **Look for background task creation** - Is the task being created?
6. **Check for automation start** - Do you see "🚀 Starting run_groceries function"?
7. **Monitor step progress** - Are steps progressing or stuck?

## Key Log Markers to Search For

- `🚀 Starting Slack Bot Server` - Service started
- `📨 Received request` - Slack sent a request
- `✅ Slack signature verified` - Authentication passed
- `👤 App mention received` - Bot was mentioned
- `🚀 Creating background task` - Automation starting
- `🤖 Starting grocery automation` - Automation running
- `Step X starting` - Progress tracking
- `Cart created successfully` - Success!
- `ERROR:` - Something went wrong
- `TESCO_ERROR:` - Automation error

## Additional Debug Endpoint

You can also visit the root URL to check if the service is running:
```
GET https://your-app.onrender.com/
```

Should return:
```json
{
  "service": "Tesco Slack Bot",
  "status": "running",
  "endpoints": {...}
}
```
