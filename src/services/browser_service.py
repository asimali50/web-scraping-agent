"""Playwright browser service for managing browser instances"""

import asyncio
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from src.core.config import get_config
from src.core.constants import USER_AGENT
from src.core.exceptions import BrowserException, BrowserLaunchException
from src.services.logger_service import get_logger

logger = get_logger(__name__)


class BrowserService:
    """Manage Playwright browser instances and lifecycle"""

    def __init__(self):
        """Initialize browser service"""
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._playwright = None

    async def initialize(self) -> None:
        """Initialize browser and context"""
        try:
            config = get_config()

            self._playwright = await async_playwright().start()

            # Use system-installed Chrome to avoid download timeouts
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

            self.browser = await self._playwright.chromium.launch(
                executable_path=chrome_path,
                headless=config.get("browser.headless", True),
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                ],
            )

            self.context = await self.browser.new_context(
                viewport={
                    "width": config.get("browser.viewport_width", 1920),
                    "height": config.get("browser.viewport_height", 1080),
                },
                user_agent=config.get("browser.user_agent", USER_AGENT),
                ignore_https_errors=True,
            )

            logger.info("Browser service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise BrowserLaunchException(f"Failed to launch browser: {e}")

    async def create_page(self) -> Page:
        """Create a new page in the browser context"""
        if not self.context:
            raise BrowserException("Browser context not initialized")

        try:
            page = await self.context.new_page()

            config = get_config()
            timeout = config.get("browser.timeout_ms", 30000)
            page.set_default_timeout(timeout)
            page.set_default_navigation_timeout(timeout)

            return page

        except Exception as e:
            logger.error(f"Failed to create page: {e}")
            raise BrowserException(f"Failed to create page: {e}")

    async def close_page(self, page: Page) -> None:
        """Close a page safely"""
        try:
            if page:
                await page.close()
        except Exception as e:
            logger.warning(f"Error closing page: {e}")

    async def close(self) -> None:
        """Close browser and cleanup"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self._playwright:
                await self._playwright.stop()

            logger.info("Browser service closed")

        except Exception as e:
            logger.error(f"Error closing browser service: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


_browser_instance: Optional[BrowserService] = None


async def get_browser_service() -> BrowserService:
    """Get or create global browser service instance"""
    global _browser_instance
    if _browser_instance is None:
        _browser_instance = BrowserService()
        await _browser_instance.initialize()
    return _browser_instance


async def close_browser_service() -> None:
    """Close global browser service"""
    global _browser_instance
    if _browser_instance:
        await _browser_instance.close()
        _browser_instance = None
