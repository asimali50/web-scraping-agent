"""Test script to verify browser launch with system Chrome"""

import asyncio
from playwright.async_api import async_playwright

async def test_browser_launch():
    """Test launching browser with system-installed Chrome"""
    try:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

        async with async_playwright() as p:
            print("Starting Playwright...")

            print(f"Launching Chromium with executable at: {chrome_path}")
            browser = await p.chromium.launch(
                executable_path=chrome_path,
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                ],
            )

            print("[OK] Browser launched successfully!")

            # Create a context and page
            context = await browser.new_context()
            page = await context.new_page()

            print("[OK] Page created successfully!")

            # Try to navigate to a simple page
            print("Testing navigation to example.com...")
            await page.goto("https://example.com", wait_until="domcontentloaded")

            title = await page.title()
            print(f"[OK] Successfully navigated! Page title: {title}")

            # Clean up
            await context.close()
            await browser.close()

            print("\n[SUCCESS] All tests passed! Browser is working correctly.")
            return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_browser_launch())
    exit(0 if success else 1)
