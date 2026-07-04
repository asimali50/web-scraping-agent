"""Amazon Agent - Extract product metadata and detect official websites"""

import asyncio
import re
from typing import Optional

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.core.config import get_config
from src.core.exceptions import (
    AmazonException,
    AmazonProductNotFound,
    AmazonTimeoutException,
    BrandMismatchException,
)
from src.core.models import AmazonProductData
from src.services.logger_service import get_logger

logger = get_logger(__name__)


class AmazonAgent:
    """Extract metadata from Amazon product pages"""

    def __init__(self):
        """Initialize Amazon agent"""
        self.timeout_ms = get_config().get("scraping.amazon.timeout_seconds", 8) * 1000
        self.max_retries = get_config().get("scraping.amazon.max_retries", 2)

    async def extract(
        self,
        page: Page,
        url: str,
        expected_brand: Optional[str] = None,
    ) -> AmazonProductData:
        """Extract product metadata from Amazon page"""
        start_time = asyncio.get_event_loop().time()

        try:
            await self._navigate_to_product(page, url)
            metadata = await self._extract_metadata(page)

            if expected_brand:
                if not self._brand_matches(metadata["brand"], expected_brand):
                    raise BrandMismatchException(
                        f"Brand mismatch: expected '{expected_brand}', got '{metadata['brand']}'"
                    )

            website = await self._detect_official_website(page, metadata)
            execution_time = asyncio.get_event_loop().time() - start_time

            return AmazonProductData(
                product_name=metadata.get("product_name", ""),
                brand=metadata.get("brand", ""),
                category=metadata.get("category", ""),
                store_name=metadata.get("store_name"),
                brand_store_url=metadata.get("brand_store_url"),
                manufacturer=metadata.get("manufacturer"),
                official_website=website,
                about_section_url=metadata.get("about_section_url"),
                extraction_time=execution_time,
            )

        except AmazonException:
            raise
        except PlaywrightTimeoutError as e:
            raise AmazonTimeoutException(f"Amazon page load timeout: {e}")
        except Exception as e:
            logger.error(f"Amazon extraction error: {e}")
            raise AmazonException(f"Failed to extract Amazon metadata: {e}")

    async def _navigate_to_product(self, page: Page, url: str) -> None:
        """Navigate to Amazon product page and wait for load"""
        try:
            logger.debug(f"Navigating to Amazon URL: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)

            await page.wait_for_selector(
                "h1 span[data-feature-name='title']",
                timeout=self.timeout_ms
            )

            logger.debug("Amazon page loaded successfully")

        except PlaywrightTimeoutError:
            raise AmazonTimeoutException(f"Timeout navigating to {url}")
        except Exception as e:
            raise AmazonException(f"Failed to navigate to Amazon URL: {e}")

    async def _extract_metadata(self, page: Page) -> dict:
        """Extract product metadata from page"""
        metadata = {}

        try:
            product_name = await page.locator("h1 span[data-feature-name='title']").text_content()
            metadata["product_name"] = product_name.strip() if product_name else ""

            brand = await self._extract_brand(page)
            metadata["brand"] = brand

            category = await self._extract_category(page)
            metadata["category"] = category

            store_info = await self._extract_store_info(page)
            metadata.update(store_info)

            logger.debug(f"Extracted metadata: {metadata}")
            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            raise AmazonProductNotFound(f"Failed to extract product metadata: {e}")

    async def _extract_brand(self, page: Page) -> str:
        """Extract brand name from product details"""
        try:
            brand_elements = await page.locator(
                "tr td:has-text('Brand') + td"
            ).all()

            if brand_elements:
                brand_text = await brand_elements[0].text_content()
                return brand_text.strip() if brand_text else ""

            return ""

        except Exception as e:
            logger.warning(f"Error extracting brand: {e}")
            return ""

    async def _extract_category(self, page: Page) -> str:
        """Extract product category"""
        try:
            breadcrumb = await page.locator(
                "ul.a-unordered-list li:last-child a"
            ).text_content()

            if breadcrumb:
                return breadcrumb.strip()

            return ""

        except Exception as e:
            logger.warning(f"Error extracting category: {e}")
            return ""

    async def _extract_store_info(self, page: Page) -> dict:
        """Extract store name, brand store URL, and manufacturer"""
        info = {}

        try:
            store_name_elem = await page.locator(
                "a[data-feature-name='bylineInfo']"
            ).text_content()

            if store_name_elem:
                info["store_name"] = store_name_elem.strip()

            brand_store_link = await page.locator(
                "a[href*='stores']"
            ).first.get_attribute("href")

            if brand_store_link and "amazon" in brand_store_link:
                info["brand_store_url"] = self._normalize_url(brand_store_link)

            manufacturer = await page.locator(
                "tr td:has-text('Manufacturer') + td"
            ).first.text_content()

            if manufacturer:
                info["manufacturer"] = manufacturer.strip()

            return info

        except Exception as e:
            logger.debug(f"Error extracting store info: {e}")
            return info

    async def _detect_official_website(self, page: Page, metadata: dict) -> Optional[str]:
        """Detect official manufacturer website on Amazon page"""
        try:
            website_urls = await self._find_urls_in_details(page)

            if website_urls:
                for url in website_urls:
                    if not self._is_amazon_url(url):
                        return url

            return None

        except Exception as e:
            logger.debug(f"Error detecting official website: {e}")
            return None

    async def _find_urls_in_details(self, page: Page) -> list:
        """Find URLs in product details section"""
        urls = []

        try:
            links = await page.locator("a").all()

            for link in links:
                href = await link.get_attribute("href")
                if href and self._is_valid_website_url(href):
                    urls.append(href)

            return urls

        except Exception as e:
            logger.debug(f"Error finding URLs in details: {e}")
            return []

    def _brand_matches(self, detected_brand: str, expected_brand: str) -> bool:
        """Check if detected brand matches expected brand"""
        if not detected_brand or not expected_brand:
            return True

        detected_norm = detected_brand.lower().strip()
        expected_norm = expected_brand.lower().strip()

        if detected_norm == expected_norm:
            return True

        if detected_norm in expected_norm or expected_norm in detected_norm:
            return True

        detected_clean = re.sub(r'[^\w]', '', detected_norm)
        expected_clean = re.sub(r'[^\w]', '', expected_norm)

        return detected_clean == expected_clean

    def _is_valid_website_url(self, url: str) -> bool:
        """Check if URL appears to be a valid website"""
        if not url:
            return False

        url_clean = url.split('?')[0].split('#')[0]

        return (
            url_clean.startswith('http://') or
            url_clean.startswith('https://') or
            url_clean.startswith('www.')
        )

    def _is_amazon_url(self, url: str) -> bool:
        """Check if URL is Amazon domain"""
        return 'amazon' in url.lower()

    def _normalize_url(self, url: str) -> str:
        """Normalize URL to absolute form"""
        if url.startswith('http'):
            return url
        if url.startswith('/'):
            return f"https://www.amazon.com{url}"
        if url.startswith('www.'):
            return f"https://{url}"
        return url
