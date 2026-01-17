"""
Slack Bot Server for Tesco Grocery Automation

Listens for @tesco-bot mentions and triggers grocery automation.
"""

import asyncio
import hashlib
import hmac
import json
import os
import time
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from tesco_groceries import run_groceries

# region agent log - startup env check
def _log_debug(location, message, data, hypothesis_id):
    try:
        with open('/Users/sthukral/Documents/GitHub/browser-use-test/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": hypothesis_id, "location": location, "message": message, "data": data, "timestamp": int(time.time() * 1000)}) + '\n')
    except: pass
# endregion

# region agent log - before load_dotenv
_log_debug("slack_server.py:23", "Environment before load_dotenv", {
    "all_env_keys": list(os.environ.keys()),
    "has_SLACK_BOT_TOKEN": "SLACK_BOT_TOKEN" in os.environ,
    "has_SLACK_SIGNING_SECRET": "SLACK_SIGNING_SECRET" in os.environ,
    "SLACK_BOT_TOKEN_value": os.environ.get("SLACK_BOT_TOKEN", "NOT_SET")[:20] + "..." if os.environ.get("SLACK_BOT_TOKEN") else "NOT_SET",
    "similar_keys": [k for k in os.environ.keys() if 'SLACK' in k.upper() or 'BOT' in k.upper() or 'TOKEN' in k.upper()]
}, "A,B,D")
# endregion

# Load environment variables
load_dotenv()

# region agent log - after load_dotenv
_log_debug("slack_server.py:24", "Environment after load_dotenv", {
    "has_SLACK_BOT_TOKEN": "SLACK_BOT_TOKEN" in os.environ,
    "has_SLACK_SIGNING_SECRET": "SLACK_SIGNING_SECRET" in os.environ,
    "SLACK_BOT_TOKEN_value": os.environ.get("SLACK_BOT_TOKEN", "NOT_SET")[:20] + "..." if os.environ.get("SLACK_BOT_TOKEN") else "NOT_SET",
    "dotenv_file_exists": os.path.exists(".env")
}, "D")
# endregion

# Initialize FastAPI app
app = FastAPI(title="Tesco Bot")

# In-memory set to track processed event IDs (prevents duplicate runs on Slack retries)
processed_events = set()

# Slack configuration
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

# region agent log - after getenv
_log_debug("slack_server.py:32", "After os.getenv calls", {
    "SLACK_SIGNING_SECRET": "SET" if SLACK_SIGNING_SECRET else "NONE",
    "SLACK_SIGNING_SECRET_len": len(SLACK_SIGNING_SECRET) if SLACK_SIGNING_SECRET else 0,
    "SLACK_BOT_TOKEN": "SET" if SLACK_BOT_TOKEN else "NONE",
    "SLACK_BOT_TOKEN_len": len(SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else 0,
    "SLACK_BOT_TOKEN_first_chars": SLACK_BOT_TOKEN[:10] if SLACK_BOT_TOKEN else "NONE"
}, "A,B,E")
# endregion


def verify_slack_signature(request_body: bytes, timestamp: str, signature: str) -> bool:
    """
    Verify that the request came from Slack by validating the signature.
    
    Args:
        request_body: Raw request body
        timestamp: X-Slack-Request-Timestamp header
        signature: X-Slack-Signature header
    
    Returns:
        bool: True if signature is valid, False otherwise
    """
    if not SLACK_SIGNING_SECRET:
        return False
    
    # Handle missing or empty headers
    if not timestamp or not signature:
        return False
    
    # Check timestamp to prevent replay attacks
    try:
        timestamp_int = int(timestamp)
        if abs(time.time() - timestamp_int) > 60 * 5:
            return False
    except (ValueError, TypeError):
        return False
    
    # Create signature base string
    sig_basestring = f"v0:{timestamp}:{request_body.decode('utf-8')}"
    
    # Calculate expected signature
    expected_signature = 'v0=' + hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(expected_signature, signature)


def parse_grocery_list(text: str) -> list[str]:
    """
    Parse grocery list from message text.
    Supports comma-separated or newline-separated items.
    
    Args:
        text: Message text containing grocery items
    
    Returns:
        list[str]: List of grocery items
    """
    # Remove bot mention from text
    text = text.strip()
    
    # Remove @tesco-bot or <@USERID> mentions
    import re
    text = re.sub(r'<@[A-Z0-9]+>', '', text)
    text = re.sub(r'@tesco-bot', '', text, flags=re.IGNORECASE)
    text = text.strip()
    
    # Split by comma or newline
    if ',' in text:
        items = [item.strip() for item in text.split(',') if item.strip()]
    else:
        items = [item.strip() for item in text.split('\n') if item.strip()]
    
    return items


async def post_to_slack(channel: str, text: str, thread_ts: Optional[str] = None):
    """
    Post a message to Slack channel.
    
    Args:
        channel: Channel ID
        text: Message text
        thread_ts: Thread timestamp (for threading replies)
    """
    if not SLACK_BOT_TOKEN:
        print("⚠️ SLACK_BOT_TOKEN not set, skipping Slack message")
        return
    
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": channel,
        "text": text
    }
    
    if thread_ts:
        payload["thread_ts"] = thread_ts
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            if not result.get("ok"):
                print(f"❌ Slack API error: {result.get('error')}")
        except Exception as e:
            print(f"❌ Failed to post to Slack: {e}")


async def run_grocery_automation_background(grocery_list: list[str], channel: str, thread_ts: str):
    """
    Run grocery automation in background and post result to Slack.
    
    Args:
        grocery_list: List of grocery items
        channel: Slack channel ID
        thread_ts: Thread timestamp
    """
    try:
        # Run the automation
        result = await run_groceries(grocery_list, print_output=False)
        
        # Format result for Slack
        lines = result.split('\n')
        cart_url = None
        missing_items = []
        
        for line in lines:
            if line.strip().startswith("CART_URL:"):
                cart_url = line.split("CART_URL:", 1)[1].strip()
            elif "could not be added" in line.lower() or "unavailable" in line.lower():
                missing_items.append(line.strip())
        
        # Build response message
        if cart_url:
            response_text = f"✅ Your Tesco order is ready!\n\n🛒 Cart URL: {cart_url}"
            if missing_items:
                response_text += f"\n\n⚠️ Some items couldn't be added:\n" + "\n".join(f"• {item}" for item in missing_items)
        else:
            response_text = f"❌ Order failed. Result:\n{result}"
        
        # Post result to Slack
        await post_to_slack(channel, response_text, thread_ts)
        
    except Exception as e:
        error_msg = f"❌ Error running automation: {str(e)}"
        print(error_msg)
        await post_to_slack(channel, error_msg, thread_ts)


@app.post("/slack/events")
async def slack_events(request: Request):
    """
    Handle Slack Events API callbacks.
    """
    # Get request body and headers
    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")
    
    # Verify Slack signature
    if not verify_slack_signature(body, timestamp, signature):
        return Response(status_code=401, content="Invalid signature")
    
    # Parse JSON body
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return Response(status_code=400, content="Invalid JSON")
    
    # Handle URL verification challenge
    if data.get("type") == "url_verification":
        return JSONResponse({"challenge": data.get("challenge")})
    
    # Handle event callback
    if data.get("type") == "event_callback":
        event = data.get("event", {})
        event_id = data.get("event_id")
        
        # Check if we've already processed this event
        if event_id in processed_events:
            return Response(status_code=200)
        
        # Mark event as processed
        processed_events.add(event_id)
        
        # Handle app_mention event
        if event.get("type") == "app_mention":
            text = event.get("text", "")
            channel = event.get("channel")
            thread_ts = event.get("ts")
            
            # Parse grocery list from message
            grocery_list = parse_grocery_list(text)
            
            if not grocery_list:
                # No items found, send help message
                await post_to_slack(
                    channel,
                    "👋 Hi! Please mention me with a grocery list.\n\nExample: `@tesco-bot milk, bread, bananas`",
                    thread_ts
                )
                return Response(status_code=200)
            
            # Send acknowledgment
            items_text = ", ".join(grocery_list[:5])
            if len(grocery_list) > 5:
                items_text += f" and {len(grocery_list) - 5} more..."
            
            await post_to_slack(
                channel,
                f"🛒 Starting your Tesco order for: {items_text}\n⏳ This will take a few minutes...",
                thread_ts
            )
            
            # Run automation in background
            asyncio.create_task(
                run_grocery_automation_background(grocery_list, channel, thread_ts)
            )
            
            return Response(status_code=200)
    
    return Response(status_code=200)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    
    # region agent log - validation point
    _log_debug("slack_server.py:260", "At validation point", {
        "SLACK_SIGNING_SECRET_is_truthy": bool(SLACK_SIGNING_SECRET),
        "SLACK_BOT_TOKEN_is_truthy": bool(SLACK_BOT_TOKEN),
        "SLACK_SIGNING_SECRET_type": type(SLACK_SIGNING_SECRET).__name__,
        "SLACK_BOT_TOKEN_type": type(SLACK_BOT_TOKEN).__name__,
        "SLACK_SIGNING_SECRET_repr": repr(SLACK_SIGNING_SECRET)[:50],
        "SLACK_BOT_TOKEN_repr": repr(SLACK_BOT_TOKEN)[:50]
    }, "E")
    # endregion
    
    # Validate required environment variables
    if not SLACK_SIGNING_SECRET:
        # region agent log - signing secret failed
        _log_debug("slack_server.py:262", "SLACK_SIGNING_SECRET validation failed", {
            "value": repr(SLACK_SIGNING_SECRET),
            "all_env_vars": {k: v[:20] + "..." if len(v) > 20 else v for k, v in os.environ.items() if 'SLACK' in k or 'TOKEN' in k or 'SECRET' in k}
        }, "A,B")
        # endregion
        raise ValueError("SLACK_SIGNING_SECRET environment variable is required")
    if not SLACK_BOT_TOKEN:
        # region agent log - bot token failed
        _log_debug("slack_server.py:264", "SLACK_BOT_TOKEN validation failed", {
            "value": repr(SLACK_BOT_TOKEN),
            "all_env_vars": {k: v[:20] + "..." if len(v) > 20 else v for k, v in os.environ.items() if 'SLACK' in k or 'TOKEN' in k or 'SECRET' in k}
        }, "A,B,C")
        # endregion
        raise ValueError("SLACK_BOT_TOKEN environment variable is required")
    
    # Run server
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
