"""Integration test for all agents with system Chrome - corrected version"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import init_config
from src.services.logger_service import LoggerService, get_logger
from src.services.browser_service import get_browser_service, close_browser_service
from src.services.cache_service import CacheService
from src.agents.amazon_agent import AmazonAgent
from src.agents.google_agent import GoogleAgent
from src.agents.website_agent import WebsiteAgent
from src.agents.cache_agent import CacheAgent

logger = get_logger(__name__)


async def test_cache_agent():
    """Test cache agent"""
    print("\n" + "=" * 60)
    print("Testing Cache Agent")
    print("=" * 60)

    try:
        cache_service = CacheService()
        agent = CacheAgent(cache_service)

        # Test cache operations
        print("Testing cache store and retrieve...")

        test_data = {"product": "Apple", "category": "Electronics"}
        test_key = "test_product_apple"

        await agent.store(test_key, test_data)
        print("[OK] Cache store successful")

        result = await agent.retrieve(test_key)
        if result and result.get("product") == "Apple":
            print("[OK] Cache retrieve successful")
            return True
        else:
            print("[WARNING] Cache data mismatch")
            return False

    except Exception as e:
        print(f"[ERROR] Cache agent failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_website_agent():
    """Test website extraction agent"""
    print("\n" + "=" * 60)
    print("Testing Website Verification Agent")
    print("=" * 60)

    try:
        browser_service = await get_browser_service()
        page = await browser_service.create_page()
        agent = WebsiteAgent()

        # Test verifying a simple website
        print("Testing website verification for example.com...")
        result = await agent.verify(page, "https://example.com", expected_brand="Example")

        if result:
            print(f"[OK] Website verification successful")
            print(f"    Brand match: {result.brand_match}")
            print(f"    Content confidence: {result.content_confidence}")
            await browser_service.close_page(page)
            return True
        else:
            print("[WARNING] No results returned")
            await browser_service.close_page(page)
            return False

    except Exception as e:
        print(f"[ERROR] Website agent failed: {e}")
        import traceback
        traceback.print_exc()
        try:
            await browser_service.close_page(page)
        except:
            pass
        return False


async def test_google_agent():
    """Test Google search agent"""
    print("\n" + "=" * 60)
    print("Testing Google Search Agent")
    print("=" * 60)

    try:
        browser_service = await get_browser_service()
        page = await browser_service.create_page()
        agent = GoogleAgent()

        # Test searching
        print("Testing Google search for Apple...")
        results = await agent.search(page, brand_name="Apple", product_category="Electronics")

        if results:
            print(f"[OK] Google search successful")
            print(f"    Found {len(results)} results")
            if len(results) > 0:
                print(f"    First result: {results[0].url[:60]}")
            await browser_service.close_page(page)
            return True
        else:
            print("[WARNING] No results returned")
            await browser_service.close_page(page)
            return False

    except Exception as e:
        print(f"[ERROR] Google agent failed: {e}")
        import traceback
        traceback.print_exc()
        try:
            await browser_service.close_page(page)
        except:
            pass
        return False


async def test_amazon_agent():
    """Test Amazon agent"""
    print("\n" + "=" * 60)
    print("Testing Amazon Agent")
    print("=" * 60)

    try:
        browser_service = await get_browser_service()
        page = await browser_service.create_page()
        agent = AmazonAgent()

        # Use a real Amazon product URL
        amazon_url = "https://www.amazon.com/Apple-AirPods-Charging-Latest-Model/dp/B07PYLT6DN"

        print(f"Testing Amazon extraction from real product page...")
        result = await agent.extract(page, amazon_url, expected_brand="Apple")

        if result:
            print(f"[OK] Amazon extraction successful")
            print(f"    Product: {result.product_name[:60]}")
            print(f"    Brand: {result.brand}")
            print(f"    Official Website: {result.official_website}")
            await browser_service.close_page(page)
            return True
        else:
            print("[WARNING] No results returned")
            await browser_service.close_page(page)
            return False

    except Exception as e:
        print(f"[ERROR] Amazon agent failed: {e}")
        import traceback
        traceback.print_exc()
        try:
            await browser_service.close_page(page)
        except:
            pass
        return False


async def main():
    """Run all agent integration tests"""
    try:
        print("\n" + "=" * 60)
        print("AGENT INTEGRATION TEST SUITE")
        print("System Chrome Integration")
        print("=" * 60)

        # Initialize
        init_config()
        LoggerService.init()
        logger.info("Integration tests starting")

        # Initialize browser service
        browser = await get_browser_service()
        logger.info("Browser service initialized with system Chrome")

        results = []

        # Run agent tests
        results.append(("Cache Agent", await test_cache_agent()))
        results.append(("Website Agent", await test_website_agent()))
        results.append(("Google Agent", await test_google_agent()))
        results.append(("Amazon Agent", await test_amazon_agent()))

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        for agent_name, success in results:
            status = "[PASS]" if success else "[FAIL]"
            print(f"{status} {agent_name}")

        passed = sum(1 for _, success in results if success)
        total = len(results)
        print(f"\nTotal: {passed}/{total} tests passed")

        # Cleanup
        await close_browser_service()
        logger.info("Browser service closed")

        return all(success for _, success in results)

    except Exception as e:
        logger.error(f"Integration test error: {e}", exc_info=True)
        await close_browser_service()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
