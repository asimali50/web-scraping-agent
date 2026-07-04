"""Test script to verify real website scraping"""

import asyncio
from playwright.async_api import async_playwright

async def test_amazon():
    """Test Amazon page scraping"""
    try:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

        async with async_playwright() as p:
            print("\n--- Testing Amazon ---")
            browser = await p.chromium.launch(
                executable_path=chrome_path,
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                ],
            )

            context = await browser.new_context()
            page = await context.new_page()

            print("Navigating to Amazon...")
            await page.goto("https://www.amazon.com", wait_until="domcontentloaded", timeout=30000)

            title = await page.title()
            print(f"[OK] Amazon loaded! Title: {title}")

            # Extract some content
            content = await page.content()
            if "amazon" in content.lower():
                print("[OK] Amazon content extracted successfully")
            else:
                print("[WARNING] Could not verify Amazon content")

            await context.close()
            await browser.close()
            return True

    except Exception as e:
        print(f"[ERROR] Amazon test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_google_search():
    """Test Google search functionality"""
    try:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

        async with async_playwright() as p:
            print("\n--- Testing Google Search ---")
            browser = await p.chromium.launch(
                executable_path=chrome_path,
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                ],
            )

            context = await browser.new_context()
            page = await context.new_page()

            print("Navigating to Google...")
            await page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=30000)

            title = await page.title()
            print(f"[OK] Google loaded! Title: {title}")

            # Try to search for something
            search_box = await page.query_selector("input[name='q']")
            if search_box:
                print("[OK] Google search box found")
                await search_box.fill("test")
                print("[OK] Search term entered")
            else:
                print("[WARNING] Could not find Google search box")

            content = await page.content()
            if "google" in content.lower():
                print("[OK] Google content extracted successfully")

            await context.close()
            await browser.close()
            return True

    except Exception as e:
        print(f"[ERROR] Google search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_website_extraction():
    """Test extracting website content"""
    try:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

        async with async_playwright() as p:
            print("\n--- Testing Website Content Extraction ---")
            browser = await p.chromium.launch(
                executable_path=chrome_path,
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                ],
            )

            context = await browser.new_context()
            page = await context.new_page()

            # Test a simple website
            print("Navigating to example.com...")
            await page.goto("https://example.com", wait_until="domcontentloaded", timeout=30000)

            # Extract multiple elements
            title = await page.title()
            print(f"[OK] Title extracted: {title}")

            headings = await page.query_selector_all("h1")
            print(f"[OK] Found {len(headings)} h1 headings")

            paragraphs = await page.query_selector_all("p")
            print(f"[OK] Found {len(paragraphs)} paragraphs")

            # Extract text content
            body_text = await page.inner_text("body")
            if body_text and len(body_text) > 0:
                print(f"[OK] Extracted {len(body_text)} characters of body text")

            await context.close()
            await browser.close()
            return True

    except Exception as e:
        print(f"[ERROR] Website extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("REAL WEBSITE TESTING")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Amazon", await test_amazon()))
    results.append(("Google Search", await test_google_search()))
    results.append(("Website Extraction", await test_website_extraction()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {test_name}")

    all_passed = all(success for _, success in results)
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
