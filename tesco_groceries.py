"""
Tesco.ie Grocery Automation Script

Automatically logs into Tesco.ie, searches for groceries from a list,
adds them to cart, and returns the cart URL.
"""

import asyncio
import os
import urllib.parse
from dotenv import load_dotenv
from browser_use import Agent, Browser, ChatBrowserUse

# Load environment variables
load_dotenv()


# Grocery list - edit this with items you want to order
GROCERIES = [
    "milk 2L",
    "wholemeal bread",
    "bananas 1kg",
    "cheddar cheese",
    "eggs dozen",
    "butter",
    "chicken breast",
    "tomatoes",
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
    # Validate required environment variables
    browser_use_api_key = os.getenv("BROWSER_USE_API_KEY")
    cloud_profile_id = os.getenv("BROWSER_USE_PROFILE_ID")  # Optional: your existing profile ID
    tesco_email = os.getenv("TESCO_EMAIL")
    tesco_password = os.getenv("TESCO_PASSWORD")
    
    if not browser_use_api_key:
        raise ValueError(
            "BROWSER_USE_API_KEY environment variable is required.\n"
            "Get your API key at: https://cloud.browser-use.com/settings?tab=api-keys\n"
            "Set it with: export BROWSER_USE_API_KEY=your-api-key"
        )
    
    if not tesco_email or not tesco_password:
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
    
    # Initialize browser with cloud, domain restrictions, and profile
    browser_kwargs = {
        "use_cloud": True,
        "allowed_domains": ['tesco.ie'],  # Restrict to Tesco Ireland only
    }
    
    # Add profile ID if provided
    if cloud_profile_id:
        browser_kwargs["cloud_profile_id"] = cloud_profile_id
    
    browser = Browser(**browser_kwargs)
    
    # Initialize LLM
    llm = ChatBrowserUse()
    
    # Create task prompt
    task_prompt = create_task_prompt(grocery_list)
    
    # Initialize agent with sensitive data
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
    
    if print_output:
        print("🤖 Agent initialized, starting execution...")
        print("⏳ This may take several minutes...")
        print("-" * 60)
    
    # Variable to store live URL
    live_url_captured = False
    
    # Callback to capture live URL on first step (after browser starts)
    async def on_step_start(agent_instance):
        nonlocal live_url_captured
        if not live_url_captured and agent_instance.browser_session and print_output:
            # Try to get live URL from browser session's CDP URL
            cdp_url = agent_instance.browser_session.cdp_url
            if cdp_url and 'wss://' in cdp_url:
                cdp_part = cdp_url.replace('wss://', '')
                # URL encode the CDP URL part for the live URL
                encoded_cdp = urllib.parse.quote(f"https://{cdp_part}", safe='')
                live_url = f"https://live.browser-use.com?wss={encoded_cdp}"
                print(f"\n👀 Watch the browser live at:")
                print(f"   {live_url}\n")
                live_url_captured = True
    
    # Run agent with callback to capture live URL
    history = await agent.run(
        max_steps=150,  # Allow enough steps for login + multiple searches
        on_step_start=on_step_start,
    )
    
    # Get final result
    result = history.final_result()
    
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
                    break
    
    return result


async def main():
    """Main function for CLI usage - runs with default grocery list."""
    result = await run_groceries(GROCERIES, print_output=True)
    return result


if __name__ == '__main__':
    asyncio.run(main())
