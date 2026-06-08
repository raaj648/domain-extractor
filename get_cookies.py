"""
Logs into member.expireddomains.net and prints all cookies.
Run: python get_cookies.py
"""
import asyncio
from playwright.async_api import async_playwright

USERNAME = "khan648"
PASSWORD = "mzmz4WKXET"
LOGIN_URL = "https://member.expireddomains.net/"

async def main():
    async with async_playwright() as p:
        # Launch headful so we can see what happens
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        print(f"\n[1] Navigating to {LOGIN_URL}...")
        await page.goto(LOGIN_URL, wait_until="networkidle")
        print(f"    Page title: {await page.title()}")

        # Try to find login form inputs
        print("\n[2] Looking for login form...")
        try:
            # Fill username
            await page.fill('input[name="username"], input[name="user"], input[type="text"]', USERNAME)
            print("    Filled username")

            # Fill password
            await page.fill('input[name="password"], input[type="password"]', PASSWORD)
            print("    Filled password")

            # Submit
            await page.click('input[type="submit"], button[type="submit"], button:has-text("Log"), button:has-text("Sign")')
            print("    Clicked login button")

            # Wait for navigation
            await page.wait_for_load_state("networkidle")
            print(f"    Redirected to: {page.url}")
        except Exception as e:
            print(f"    Form interaction error: {e}")

        print("\n[3] Waiting 2 seconds for session cookies to settle...")
        await asyncio.sleep(2)

        # Dump ALL cookies from the context
        cookies = await context.cookies()

        print("\n" + "="*65)
        print("  ALL COOKIES AFTER LOGIN")
        print("="*65)

        for c in cookies:
            print(f"\n  Name    : {c['name']}")
            print(f"  Value   : {c['value']}")
            print(f"  Domain  : {c['domain']}")
            print(f"  Path    : {c['path']}")
            print(f"  HttpOnly: {c['httpOnly']}")
            print(f"  Secure  : {c['secure']}")
            print(f"  Expires : {c.get('expires', 'Session')}")
            print(f"  SameSite: {c.get('sameSite', 'N/A')}")

        # Also show just name=value pairs for easy copy-paste
        print("\n" + "="*65)
        print("  QUICK COPY — name=value pairs:")
        print("="*65)
        for c in cookies:
            print(f"  {c['name']} = {c['value']}")

        print("\n[4] Keeping browser open for 10s so you can inspect manually...")
        await asyncio.sleep(10)
        await browser.close()

asyncio.run(main())
