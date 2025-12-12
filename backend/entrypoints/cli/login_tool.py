import asyncio
import logging
import sys
import os

# Ensure tools can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.infrastructure.browser.steel_browser import browser_engine
from backend.infrastructure.browser.auth_repo import auth_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def manual_login():
    """
    Interactive tool for manual login.
    1. Opens Browser (Steel).
    2. Lets user log in interactively.
    3. Saves state to AuthManager.
    """
    print("Welcome to the Agent Login Tool!")
    site_tag = input("Enter the site tag (e.g., 'twitter', 'reddit', 'xueqiu'): ").strip()
    if not site_tag:
        print("Site tag is required.")
        return

    print(f"\nPhase 1: Launching Browser for {site_tag}...")
    try:
        details = await browser_engine.initialize_session()
        print(f"\n==========================================")
        print(f"🔥 BROWSER LIVE AT: {details['viewer_url']}")
        print(f"==========================================")
        print("1. Open the URL above in your browser.")
        print(f"2. Navigate to the target site.")
        print("3. Log in manually.")
        print("4. Come back here and press ENTER when logged in.")
        
        page = await browser_engine.get_page()
        # Optionally pre-navigate
        if site_tag in ['twitter', 'x']:
            await page.goto("https://x.com/i/flow/login")
        elif site_tag == 'xueqiu':
            await page.goto("https://xueqiu.com")
            
        input("\n>>> Press ENTER to SAVE SESSION Cookies... <<<")
        
        print(f"Phase 2: Saving cookies for {site_tag}...")
        context = browser_engine._current_context
        if await auth_manager.save_state(context, site_tag):
             print(f"✅ SUCCESS! Session saved for {site_tag}.")
        else:
             print("❌ Failed to save session.")
             
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Closing browser...")
        await browser_engine.close()

if __name__ == "__main__":
    asyncio.run(manual_login())
