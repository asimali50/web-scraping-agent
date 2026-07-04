"""Main entry point for the Brand Website Scraper application"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

from src.core.config import init_config
from src.services.browser_service import close_browser_service, get_browser_service
from src.services.cache_service import CacheService
from src.services.logger_service import LoggerService, get_logger

logger = get_logger(__name__)


async def main():
    """Main application entry point"""
    try:
        init_config()

        LoggerService.init()

        logger.info("=" * 80)
        logger.info("Brand Website Scraper - Starting Application")
        logger.info("=" * 80)

        cache = CacheService()
        logger.info("Cache service initialized")

        browser = await get_browser_service()
        logger.info("Browser service initialized")

        session_id = str(uuid4())
        logger.info(f"Session ID: {session_id}")

        print("\n" + "=" * 80)
        print("BRAND WEBSITE SCRAPER")
        print("=" * 80)
        print(f"Session: {session_id}")
        print("Version: 1.0.0")
        print("\nPhase 2: Project Skeleton initialized successfully!")
        print("\nCore Components:")
        print("  [+] Configuration System (YAML + Environment)")
        print("  [+] Logging System (Loguru)")
        print("  [+] Database System (SQLite)")
        print("  [+] Browser Service (Playwright)")
        print("  [+] Data Models (Pydantic)")
        print("\nNext Steps:")
        print("  1. Phase 3: Amazon Agent Implementation")
        print("  2. Phase 4: Google Search Agent")
        print("  3. Phase 5: Website Verification Agent")
        print("=" * 80 + "\n")

        await close_browser_service()
        logger.info("Application closed successfully")

    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)


def main_sync():
    """Synchronous wrapper for async main"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Application interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main_sync()
