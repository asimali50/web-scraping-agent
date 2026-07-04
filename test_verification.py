"""Simplified verification test for system Chrome with agents"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import init_config
from src.services.logger_service import LoggerService, get_logger
from src.services.browser_service import get_browser_service, close_browser_service

logger = get_logger(__name__)


async def test_basic_browser_operations():
    """Test basic browser operations that agents would use"""
    print("\n" + "=" * 60)
    print("Testing Basic Browser Operations")
    print("=" * 60)

    try:
        browser_service = await get_browser_service()
        print("[OK] Browser service initialized")

        # Test 1: Create multiple pages
        page1 = await browser_service.create_page()
        print("[OK] Page 1 created")

        page2 = await browser_service.create_page()
        print("[OK] Page 2 created")

        # Test 2: Navigate to simple site
        print("Navigating page1 to example.com...")
        await page1.goto("https://example.com", wait_until="domcontentloaded", timeout=15000)
        title1 = await page1.title()
        print(f"[OK] Page1 loaded: {title1}")

        # Test 3: Navigate second page while first is loaded
        print("Navigating page2 to google.com...")
        await page2.goto("https://www.google.com", wait_until="domcontentloaded", timeout=15000)
        title2 = await page2.title()
        print(f"[OK] Page2 loaded: {title2}")

        # Test 4: Extract content from page
        print("Extracting content from page1...")
        content_length = len(await page1.content())
        print(f"[OK] Extracted {content_length} characters from page1")

        # Test 5: Close pages
        await browser_service.close_page(page1)
        print("[OK] Page1 closed")

        await browser_service.close_page(page2)
        print("[OK] Page2 closed")

        return True

    except Exception as e:
        print(f"[ERROR] Browser operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_real_website_scraping():
    """Test real website scraping scenarios"""
    print("\n" + "=" * 60)
    print("Testing Real Website Scraping")
    print("=" * 60)

    try:
        browser_service = await get_browser_service()

        # Test Amazon
        print("Testing Amazon page load...")
        page = await browser_service.create_page()
        await page.goto("https://www.amazon.com", wait_until="domcontentloaded", timeout=20000)
        amazon_title = await page.title()
        print(f"[OK] Amazon loaded: {amazon_title}")
        await browser_service.close_page(page)

        # Test Google
        print("Testing Google page load...")
        page = await browser_service.create_page()
        await page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=20000)
        google_title = await page.title()
        print(f"[OK] Google loaded: {google_title}")
        await browser_service.close_page(page)

        return True

    except Exception as e:
        print(f"[ERROR] Real website scraping failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run verification tests"""
    try:
        print("\n" + "=" * 60)
        print("SYSTEM CHROME VERIFICATION TEST")
        print("=" * 60)

        # Initialize
        init_config()
        LoggerService.init()
        logger.info("Verification tests starting")

        results = []

        # Run tests
        results.append(("Basic Browser Operations", await test_basic_browser_operations()))
        results.append(("Real Website Scraping", await test_real_website_scraping()))

        # Summary
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        for test_name, success in results:
            status = "[PASS]" if success else "[FAIL]"
            print(f"{status} {test_name}")

        passed = sum(1 for _, success in results if success)
        total = len(results)
        print(f"\nTotal: {passed}/{total} tests passed")

        # Cleanup
        await close_browser_service()
        logger.info("Browser service closed")

        return all(success for _, success in results)

    except Exception as e:
        logger.error(f"Verification test error: {e}", exc_info=True)
        try:
            await close_browser_service()
        except:
            pass
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
