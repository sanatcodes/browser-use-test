"""
Tesco.ie Grocery Automation Script

Automatically logs into Tesco.ie, searches for groceries from a list,
adds them to cart, and returns the cart URL.
"""

import asyncio
import os
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
from browser_use import Agent, Browser, ChatBrowserUse

# Load environment variables
load_dotenv()


def log_info(message: str, **kwargs):
    """Log informational message with timestamp"""
    timestamp = datetime.utcnow().isoformat()
    if kwargs:
        import json
        data_str = json.dumps(kwargs)
        print(f"[{timestamp}] TESCO_INFO: {message} {data_str}")
    else:
        print(f"[{timestamp}] TESCO_INFO: {message}")


def log_error(message: str, **kwargs):
    """Log error message with timestamp"""
    timestamp = datetime.utcnow().isoformat()
    if kwargs:
        import json
        data_str = json.dumps(kwargs)
        print(f"[{timestamp}] TESCO_ERROR: {message} {data_str}")
    else:
        print(f"[{timestamp}] TESCO_ERROR: {message}")


# Grocery list - edit this with items you want to order
GROCERIES = [
    "milk 2L",
    "wholemeal bread",
]


def format_grocery_list(items: list[str]) -> str:
    """Format grocery list as numbered items for the prompt."""
    return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))


def create_task_prompt(grocery_items: list[str]) -> str:
    """Create the detailed task prompt for the agent."""
    formatted_list = format_grocery_list(grocery_items)
    
    prompt = f"""GOAL: Log into Tesco.ie, add groceries to cart, and provide the cart URL.

IMPORTANT SECURITY NOTE:
- You have access to TESCO_EMAIL and TESCO_PASSWORD via secret injection
- NEVER print, display, or output these credentials in any form
- Use them only for logging in

EXECUTION STEPS:

1. NAVIGATE & LOGIN:
   - Navigate to https://www.tesco.ie/groceries/
   - Accept cookies if prompted
   - Click "Sign in" or "Login" button
   - Enter the email from TESCO_EMAIL secret
   - Enter the password from TESCO_PASSWORD secret
   - Submit login form
   - Wait for successful login confirmation

2. SEARCH AND ADD ITEMS:
   For each item in the list below, perform these steps:
   - Use the search bar to search for the item
   - Wait for search results to load
   - If the item is found:
     * Click on the best matching product (typically the first result)
     * Click "Add to trolley" or "Add to basket" button
     * Wait for confirmation that item was added
     * If quantity needs adjustment, set it to 1 (unless specified in item name)
   - If the item is NOT found or out of stock:
     * Note it in your memory and continue to the next item
   - Return to search for the next item

GROCERY LIST:
{formatted_list}

3. NAVIGATE TO CART:
   - After processing all items, click on the cart/trolley icon
   - Navigate to the cart/basket page
   - Wait for the cart page to fully load

4. FINAL OUTPUT:
   - Extract the current cart page URL
   - Provide output in this exact format:
     CART_URL: [the full URL of the cart page]
   - List any items that could not be added (not found or out of stock)
   - DO NOT proceed to checkout
   - DO NOT place the order

STOP CONDITIONS:
- Stop at the cart page after all items are processed
- Do not proceed beyond viewing the cart
- Do not enter payment or delivery details
"""
    return prompt


async def run_groceries(grocery_list: list[str], print_output: bool = True) -> str:
    """
    Run the Tesco grocery automation with a dynamic grocery list.
    
    Args:
        grocery_list: List of grocery items to order
        print_output: Whether to print progress to console (default: True)
    
    Returns:
        str: Result message with cart URL and any missing items
    """
    log_info("🚀 Starting run_groceries function", item_count=len(grocery_list))
    
    # Validate required environment variables
    browser_use_api_key = os.getenv("BROWSER_USE_API_KEY")
    cloud_profile_id = os.getenv("BROWSER_USE_PROFILE_ID")  # Optional: your existing profile ID
    tesco_email = os.getenv("TESCO_EMAIL")
    tesco_password = os.getenv("TESCO_PASSWORD")
    
    log_info("Checking environment variables",
             has_api_key=bool(browser_use_api_key),
             has_profile_id=bool(cloud_profile_id),
             has_email=bool(tesco_email),
             has_password=bool(tesco_password))
    
    if not browser_use_api_key:
        log_error("Missing BROWSER_USE_API_KEY")
        raise ValueError(
            "BROWSER_USE_API_KEY environment variable is required.\n"
            "Get your API key at: https://cloud.browser-use.com/settings?tab=api-keys\n"
            "Set it with: export BROWSER_USE_API_KEY=your-api-key"
        )
    
    if not tesco_email or not tesco_password:
        log_error("Missing Tesco credentials")
        raise ValueError(
            "TESCO_EMAIL and TESCO_PASSWORD environment variables are required.\n"
            "Set them with:\n"
            "  export TESCO_EMAIL=your-email@example.com\n"
            "  export TESCO_PASSWORD=your-password"
        )
    
    if print_output:
        print(f"🛒 Starting Tesco grocery automation...")
        print(f"📝 Processing {len(grocery_list)} items")
        print(f"🌐 Target site: tesco.ie")
        if cloud_profile_id:
            print(f"👤 Using browser profile: {cloud_profile_id}")
        print("-" * 60)
    
    log_info("Initializing browser", use_cloud=True, allowed_domains=['tesco.ie'])
    
    # Initialize browser with cloud, domain restrictions, and profile
    browser_kwargs = {
        "use_cloud": True,
        "allowed_domains": ['tesco.ie'],  # Restrict to Tesco Ireland only
    }
    
    # Add profile ID if provided
    if cloud_profile_id:
        browser_kwargs["cloud_profile_id"] = cloud_profile_id
    
    try:
        browser = Browser(**browser_kwargs)
        log_info("✅ Browser initialized successfully")
    except Exception as e:
        log_error("Failed to initialize browser", error=str(e), error_type=type(e).__name__)
        raise
    
    # Initialize LLM
    log_info("Initializing LLM")
    try:
        llm = ChatBrowserUse()
        log_info("✅ LLM initialized successfully")
    except Exception as e:
        log_error("Failed to initialize LLM", error=str(e), error_type=type(e).__name__)
        raise
    
    # Create task prompt
    task_prompt = create_task_prompt(grocery_list)
    log_info("Task prompt created", prompt_length=len(task_prompt))
    
    # Initialize agent with sensitive data
    log_info("Initializing agent")
    try:
        agent = Agent(
            task=task_prompt,
            llm=llm,
            browser=browser,
            use_vision=True,  # Enable vision to see page elements
            use_thinking=False,
            flash_mode=False,
            highlight_elements=True,  # Highlight interactive elements
            sensitive_data={
                "TESCO_EMAIL": tesco_email,
                "TESCO_PASSWORD": tesco_password,
            }
        )
        log_info("✅ Agent initialized successfully")
    except Exception as e:
        log_error("Failed to initialize agent", error=str(e), error_type=type(e).__name__)
        raise
    
    if print_output:
        print("🤖 Agent initialized, starting execution...")
        print("⏳ This may take several minutes...")
        print("-" * 60)
    
    # Variable to store live URL
    live_url_captured = False
    step_count = 0
    
    # Callback to capture live URL on first step (after browser starts)
    async def on_step_start(agent_instance):
        nonlocal live_url_captured, step_count
        step_count += 1
        log_info(f"Step {step_count} starting")
        
        if not live_url_captured and agent_instance.browser_session:
            # Try to get live URL from browser session's CDP URL
            cdp_url = agent_instance.browser_session.cdp_url
            if cdp_url and 'wss://' in cdp_url:
                cdp_part = cdp_url.replace('wss://', '')
                # URL encode the CDP URL part for the live URL
                encoded_cdp = urllib.parse.quote(f"https://{cdp_part}", safe='')
                live_url = f"https://live.browser-use.com?wss={encoded_cdp}"
                log_info("📺 Live browser URL available", url=live_url)
                if print_output:
                    print(f"\n👀 Watch the browser live at:")
                    print(f"   {live_url}\n")
                live_url_captured = True
    
    # Run agent with callback to capture live URL
    log_info("🏃 Starting agent execution", max_steps=150)
    try:
        history = await agent.run(
            max_steps=150,  # Allow enough steps for login + multiple searches
            on_step_start=on_step_start,
        )
        log_info("✅ Agent execution completed", total_steps=step_count)
    except Exception as e:
        log_error("Agent execution failed", error=str(e), error_type=type(e).__name__)
        import traceback
        log_error("Stack trace", trace=traceback.format_exc())
        raise
    
    # Get final result
    result = history.final_result()
    log_info("Final result obtained", result_length=len(result))
    
    if print_output:
        print("\n" + "=" * 60)
        print("✅ AUTOMATION COMPLETE")
        print("=" * 60)
        print("\n📄 Final Result:")
        print(result)
        print("\n" + "=" * 60)
        
        # Extract and highlight cart URL if present
        if "CART_URL:" in result:
            lines = result.split('\n')
            for line in lines:
                if line.strip().startswith("CART_URL:"):
                    cart_url = line.split("CART_URL:", 1)[1].strip()
                    print(f"\n🛒 Your cart is ready at:")
                    print(f"   {cart_url}")
                    print("\n💡 Open this URL to review and complete your order.")
                    log_info("Cart URL extracted", cart_url=cart_url)
                    break
    
    return result


async def main():
    """Main function for CLI usage - runs with default grocery list."""
    result = await run_groceries(GROCERIES, print_output=True)
    return result


if __name__ == '__main__':
    asyncio.run(main())
