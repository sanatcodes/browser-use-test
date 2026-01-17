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
from datetime import datetime

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from tesco_groceries import run_groceries


def log_info(message: str, **kwargs):
    """Log informational message with timestamp"""
    timestamp = datetime.utcnow().isoformat()
    data_str = json.dumps(kwargs) if kwargs else ""
    print(f"[{timestamp}] INFO: {message} {data_str}")


def log_error(message: str, **kwargs):
    """Log error message with timestamp"""
    timestamp = datetime.utcnow().isoformat()
    data_str = json.dumps(kwargs) if kwargs else ""
    print(f"[{timestamp}] ERROR: {message} {data_str}")


def log_debug(message: str, **kwargs):
    """Log debug message with timestamp"""
    timestamp = datetime.utcnow().isoformat()
    data_str = json.dumps(kwargs) if kwargs else ""
    print(f"[{timestamp}] DEBUG: {message} {data_str}")


# Load environment variables
load_dotenv()

log_info("🚀 Starting Slack Bot Server")
log_debug("Environment loaded", env_file_exists=os.path.exists(".env"))

# Initialize FastAPI app
app = FastAPI(title="Tesco Bot")

# In-memory set to track processed event IDs (prevents duplicate runs on Slack retries)
processed_events = set()

# Slack configuration
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

log_debug("Slack credentials loaded",
          has_signing_secret=bool(SLACK_SIGNING_SECRET),
          signing_secret_length=len(SLACK_SIGNING_SECRET) if SLACK_SIGNING_SECRET else 0,
          has_bot_token=bool(SLACK_BOT_TOKEN),
          bot_token_prefix=SLACK_BOT_TOKEN[:10] if SLACK_BOT_TOKEN else None)


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
    log_debug("Verifying Slack signature",
              has_secret=bool(SLACK_SIGNING_SECRET),
              has_timestamp=bool(timestamp),
              has_signature=bool(signature))
    
    if not SLACK_SIGNING_SECRET:
        log_error("No SLACK_SIGNING_SECRET configured")
        return False
    
    # Handle missing or empty headers
    if not timestamp or not signature:
        log_error("Missing timestamp or signature header")
        return False
    
    # Check timestamp to prevent replay attacks
    try:
        timestamp_int = int(timestamp)
        time_diff = abs(time.time() - timestamp_int)
        if time_diff > 60 * 5:
            log_error("Timestamp too old", time_diff_seconds=time_diff)
            return False
    except (ValueError, TypeError) as e:
        log_error("Invalid timestamp format", error=str(e))
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
    is_valid = hmac.compare_digest(expected_signature, signature)
    log_debug("Signature verification result", valid=is_valid)
    return is_valid


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
    log_info("Posting to Slack", channel=channel, has_thread=bool(thread_ts))
    
    if not SLACK_BOT_TOKEN:
        log_error("SLACK_BOT_TOKEN not set, skipping Slack message")
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
            log_debug("Sending Slack API request")
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if not result.get("ok"):
                log_error("Slack API error", error=result.get('error'), response=result)
            else:
                log_info("Message posted to Slack successfully")
        except Exception as e:
            log_error("Failed to post to Slack", error=str(e), error_type=type(e).__name__)


async def run_grocery_automation_background(grocery_list: list[str], channel: str, thread_ts: str):
    """
    Run grocery automation in background and post result to Slack.
    
    Args:
        grocery_list: List of grocery items
        channel: Slack channel ID
        thread_ts: Thread timestamp
    """
    log_info("🤖 Starting grocery automation in background",
             item_count=len(grocery_list),
             items=grocery_list[:5])
    
    try:
        # Run the automation with callback to capture live URL
        log_info("🌐 Launching browser automation")
        
        # Callback to capture and send live URL to Slack
        async def send_live_url(live_url: str):
            await post_to_slack(
                channel,
                f"👀 Watch the automation live:\n{live_url}",
                thread_ts
            )
        
        result = await run_groceries(grocery_list, print_output=False, live_url_callback=send_live_url)
        log_info("✅ Automation completed", result_length=len(result))
        
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
            log_info("Cart created successfully", cart_url=cart_url, missing_items=len(missing_items))
        else:
            response_text = f"❌ Order failed. Result:\n{result}"
            log_error("No cart URL found in result")
        
        # Post result to Slack
        await post_to_slack(channel, response_text, thread_ts)
        log_info("🎉 Automation workflow completed")
        
    except Exception as e:
        error_msg = f"❌ Error running automation: {str(e)}"
        log_error("Automation failed", error=str(e), error_type=type(e).__name__)
        import traceback
        log_error("Stack trace", trace=traceback.format_exc())
        await post_to_slack(channel, error_msg, thread_ts)


@app.post("/slack/events")
async def slack_events(request: Request):
    """
    Handle Slack Events API callbacks.
    """
    log_info("📨 Received request to /slack/events")
    
    # Get request body and headers
    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")
    
    log_debug("Request details",
              body_length=len(body),
              has_timestamp=bool(timestamp),
              has_signature=bool(signature))
    
    # Verify Slack signature
    if not verify_slack_signature(body, timestamp, signature):
        log_error("❌ Invalid Slack signature - rejecting request")
        return Response(status_code=401, content="Invalid signature")
    
    log_info("✅ Slack signature verified")
    
    # Parse JSON body
    try:
        data = json.loads(body)
        log_debug("Parsed JSON body", event_type=data.get("type"))
    except json.JSONDecodeError as e:
        log_error("Invalid JSON in request body", error=str(e))
        return Response(status_code=400, content="Invalid JSON")
    
    # Handle URL verification challenge
    if data.get("type") == "url_verification":
        challenge = data.get("challenge")
        log_info("🔐 Responding to URL verification challenge", challenge=challenge)
        return JSONResponse({"challenge": challenge})
    
    # Handle event callback
    if data.get("type") == "event_callback":
        event = data.get("event", {})
        event_id = data.get("event_id")
        event_type = event.get("type")
        
        log_info("📬 Received event callback",
                 event_id=event_id,
                 event_type=event_type)
        
        # Check if we've already processed this event
        if event_id in processed_events:
            log_info("⏭️ Event already processed, skipping", event_id=event_id)
            return Response(status_code=200)
        
        # Mark event as processed
        processed_events.add(event_id)
        log_debug("Processed events count", count=len(processed_events))
        
        # Handle app_mention event
        if event_type == "app_mention":
            text = event.get("text", "")
            channel = event.get("channel")
            thread_ts = event.get("ts")
            user = event.get("user")
            
            log_info("👤 App mention received",
                     user=user,
                     channel=channel,
                     text=text[:100])
            
            # Parse grocery list from message
            grocery_list = parse_grocery_list(text)
            log_debug("Parsed grocery list", items=grocery_list, count=len(grocery_list))
            
            if not grocery_list:
                # No items found, send help message
                log_info("No grocery items found, sending help message")
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
            
            log_info("Sending acknowledgment to Slack")
            await post_to_slack(
                channel,
                f"🛒 Starting your Tesco order for: {items_text}\n⏳ This will take a few minutes...",
                thread_ts
            )
            
            # Run automation in background
            log_info("🚀 Creating background task for automation")
            asyncio.create_task(
                run_grocery_automation_background(grocery_list, channel, thread_ts)
            )
            
            log_info("✅ Request handled, returning 200")
            return Response(status_code=200)
        else:
            log_info("Event type not handled", event_type=event_type)
    else:
        log_info("Request type not handled", request_type=data.get("type"))
    
    return Response(status_code=200)


@app.get("/health")
async def health():
    """Health check endpoint."""
    log_debug("Health check requested")
    return {
        "status": "ok",
        "has_slack_token": bool(SLACK_BOT_TOKEN),
        "has_signing_secret": bool(SLACK_SIGNING_SECRET)
    }


@app.get("/")
async def root():
    """Root endpoint with status info."""
    log_debug("Root endpoint requested")
    return {
        "service": "Tesco Slack Bot",
        "status": "running",
        "endpoints": {
            "/slack/events": "POST - Slack Events API",
            "/health": "GET - Health check"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    log_info("🔧 Validating environment variables")
    
    # Validate required environment variables
    if not SLACK_SIGNING_SECRET:
        log_error("❌ SLACK_SIGNING_SECRET environment variable is required")
        raise ValueError("SLACK_SIGNING_SECRET environment variable is required")
    if not SLACK_BOT_TOKEN:
        log_error("❌ SLACK_BOT_TOKEN environment variable is required")
        raise ValueError("SLACK_BOT_TOKEN environment variable is required")
    
    log_info("✅ Environment variables validated")
    
    # Run server
    port = int(os.getenv("PORT", 8000))
    log_info(f"🌐 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
