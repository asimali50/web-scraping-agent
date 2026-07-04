"""Website Verification Agent - Verify and analyze candidate websites"""

import asyncio
from typing import Optional

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.core.config import get_config
from src.core.exceptions import WebsiteException, WebsiteTimeoutException
from src.core.models import WebsiteAnalysis
from src.services.logger_service import get_logger

logger = get_logger(__name__)


class WebsiteAgent:
    """Verify and analyze candidate websites"""

    def __init__(self):
        """Initialize website agent"""
        self.timeout_ms = get_config().get("scraping.website_verification.timeout_seconds", 5) * 1000
        self.verify_ssl = get_config().get("scraping.website_verification.verify_ssl", True)

    async def verify(
        self,
        page: Page,
        url: str,
        expected_brand: Optional[str] = None,
        product_category: Optional[str] = None,
    ) -> WebsiteAnalysis:
        """
        Verify and analyze a candidate website

        Args:
            page: Playwright page instance
            url: URL to verify
            expected_brand: Expected brand name
            product_category: Expected product category

        Returns:
            WebsiteAnalysis with extracted information
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Navigate to website
            await self._navigate_to_website(page, url)

            # Extract website information
            analysis = await self._analyze_website(page, url, expected_brand, product_category)
            analysis.extraction_time = asyncio.get_event_loop().time() - start_time

            logger.debug(f"Website analysis complete for {url}: {analysis}")
            return analysis

        except WebsiteException:
            raise
        except PlaywrightTimeoutError:
            raise WebsiteTimeoutException(f"Timeout loading website: {url}")
        except Exception as e:
            logger.error(f"Website verification error: {e}")
            raise WebsiteException(f"Failed to verify website: {e}")

    async def _navigate_to_website(self, page: Page, url: str) -> None:
        """Navigate to website and wait for load"""
        try:
            # Ensure URL has protocol
            if not url.startswith("http"):
                url = f"https://{url}"

            logger.debug(f"Navigating to: {url}")

            await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)

            # Wait for body to be visible
            await page.wait_for_selector("body", timeout=self.timeout_ms)

            logger.debug(f"Website loaded: {url}")

        except PlaywrightTimeoutError:
            raise WebsiteTimeoutException(f"Timeout loading website: {url}")
        except Exception as e:
            raise WebsiteException(f"Failed to navigate to website: {e}")

    async def _analyze_website(
        self,
        page: Page,
        url: str,
        expected_brand: Optional[str] = None,
        product_category: Optional[str] = None,
    ) -> WebsiteAnalysis:
        """Analyze website for brand and product information"""
        try:
            domain = self._extract_domain(url)

            # Count brand mentions
            brand_mentions = 0
            if expected_brand:
                brand_mentions = await self._count_brand_mentions(page, expected_brand)

            # Check for logo
            logo_present = await self._detect_logo(page)

            # Extract product categories
            categories = await self._extract_product_categories(page)

            # Extract company information
            company_name = await self._extract_company_name(page)

            # Check for About page
            about_present = await self._check_about_page_present(page)

            # Check for Contact page
            contact_present = await self._check_contact_page_present(page)

            return WebsiteAnalysis(
                url=url,
                domain=domain,
                brand_mentions=brand_mentions,
                logo_present=logo_present,
                product_categories=categories,
                company_name=company_name,
                about_page_present=about_present,
                contact_page_present=contact_present,
                extraction_time=0.0,
            )

        except Exception as e:
            logger.error(f"Error analyzing website: {e}")
            raise WebsiteException(f"Failed to analyze website: {e}")

    async def _count_brand_mentions(self, page: Page, brand_name: str) -> int:
        """Count how many times brand is mentioned on page"""
        try:
            # Get page content
            content = await page.content()

            # Case-insensitive count
            brand_lower = brand_name.lower()
            count = content.lower().count(brand_lower)

            logger.debug(f"Found {count} mentions of '{brand_name}'")
            return count

        except Exception as e:
            logger.warning(f"Error counting brand mentions: {e}")
            return 0

    async def _detect_logo(self, page: Page) -> bool:
        """Check if page has a logo/branding"""
        try:
            # Look for common logo selectors
            logo_selectors = [
                "img[alt*='logo' i]",
                "img[src*='logo' i]",
                ".logo img",
                "#logo img",
                "header img:first-child",
            ]

            for selector in logo_selectors:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        logger.debug("Logo detected")
                        return True
                except Exception:
                    continue

            return False

        except Exception as e:
            logger.debug(f"Error detecting logo: {e}")
            return False

    async def _extract_product_categories(self, page: Page) -> list:
        """Extract product categories from page"""
        categories = []

        try:
            # Look for category links or sections
            category_selectors = [
                "a[href*='category' i]",
                "a[href*='products' i]",
                "nav a",
                ".categories a",
            ]

            for selector in category_selectors:
                try:
                    elements = await page.locator(selector).all()
                    for elem in elements[:5]:  # Limit to 5
                        text = await elem.text_content()
                        if text:
                            category = text.strip()
                            if category and category not in categories:
                                categories.append(category)
                except Exception:
                    continue

            logger.debug(f"Extracted categories: {categories}")
            return categories

        except Exception as e:
            logger.debug(f"Error extracting categories: {e}")
            return []

    async def _extract_company_name(self, page: Page) -> Optional[str]:
        """Extract company name from About or footer"""
        try:
            # Try to find company name in common locations
            selectors = [
                "meta[property='og:site_name']",
                "meta[name='author']",
                ".company-name",
                ".footer-company",
                "footer strong:first-child",
            ]

            for selector in selectors:
                try:
                    if "meta" in selector:
                        company = await page.locator(selector).get_attribute("content")
                    else:
                        company = await page.locator(selector).text_content()

                    if company:
                        company = company.strip()
                        if company:
                            logger.debug(f"Extracted company name: {company}")
                            return company
                except Exception:
                    continue

            return None

        except Exception as e:
            logger.debug(f"Error extracting company name: {e}")
            return None

    async def _check_about_page_present(self, page: Page) -> bool:
        """Check if website has About page or section"""
        try:
            # Look for About links
            about_selectors = [
                "a[href*='about' i]",
                "a:text-matches('About', 'i')",
                ".about-us",
            ]

            for selector in about_selectors:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        logger.debug("About page detected")
                        return True
                except Exception:
                    continue

            return False

        except Exception as e:
            logger.debug(f"Error checking About page: {e}")
            return False

    async def _check_contact_page_present(self, page: Page) -> bool:
        """Check if website has Contact page or section"""
        try:
            # Look for Contact links
            contact_selectors = [
                "a[href*='contact' i]",
                "a:text-matches('Contact', 'i')",
                ".contact-us",
                "a[href*='mailto:']",
            ]

            for selector in contact_selectors:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        logger.debug("Contact page detected")
                        return True
                except Exception:
                    continue

            return False

        except Exception as e:
            logger.debug(f"Error checking Contact page: {e}")
            return False

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            return domain

        except Exception:
            return url
