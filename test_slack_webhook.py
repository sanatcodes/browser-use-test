"""
Quick test script to verify Slack webhook is working on Render
"""
import json
import os
import sys

import httpx

# Your Render URL
RENDER_URL = "https://tesco-bot-4ckg.onrender.com"

def test_health():
    """Test health endpoint"""
    try:
        response = httpx.get(f"{RENDER_URL}/health", timeout=10)
        print(f"✓ Health check: {response.status_code}")
        print(f"  Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_slack_events():
    """Test Slack events endpoint with URL verification"""
    # Slack sends this during setup
    challenge_payload = {
        "type": "url_verification",
        "challenge": "test_challenge_123"
    }
    
    try:
        response = httpx.post(
            f"{RENDER_URL}/slack/events",
            json=challenge_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"\n✓ Slack events endpoint: {response.status_code}")
        print(f"  Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("challenge") == "test_challenge_123":
                print("  ✓ URL verification works!")
                return True
        return False
    except Exception as e:
        print(f"✗ Slack events test failed: {e}")
        return False

def main():
    print(f"Testing Render deployment at: {RENDER_URL}\n")
    print("=" * 60)
    
    health_ok = test_health()
    events_ok = test_slack_events()
    
    print("\n" + "=" * 60)
    print("\nSummary:")
    print(f"  Health endpoint: {'✓ Working' if health_ok else '✗ Not working'}")
    print(f"  Slack events: {'✓ Working' if events_ok else '✗ Not working'}")
    
    if health_ok and events_ok:
        print("\n✅ Server is ready! You can now:")
        print("   1. Update Slack Event Subscriptions URL to:")
        print(f"      {RENDER_URL}/slack/events")
        print("   2. Invite @tesco-bot to a channel")
        print("   3. Test with: @tesco-bot milk, bread")
    else:
        print("\n⚠️  Server issues detected. Check Render logs:")
        print(f"   https://dashboard.render.com/")
        print("\n   Common issues:")
        print("   - Check all environment variables are set")
        print("   - Verify Start Command is: python slack_server.py")
        print("   - Check Render logs for errors")

if __name__ == "__main__":
    main()
