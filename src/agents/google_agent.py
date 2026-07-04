"""Google Search Agent - Search for official brand websites"""

import asyncio
import re
from typing import List, Optional
from urllib.parse import urlparse

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.core.config import get_config
from src.core.constants import (
    GOOGLE_SEARCH_DELAY,
    IGNORED_DOMAINS,
    MAX_GOOGLE_PAGES,
    MAX_GOOGLE_SEARCHES,
)
from src.core.exceptions import GoogleException, GoogleTimeoutException, GoogleBlockedException
from src.core.models import SearchCandidate
from src.services.logger_service import get_logger

logger = get_logger(__name__)


class GoogleAgent:
    """Search Google for official brand websites"""

    def __init__(self):
        """Initialize Google agent"""
        self.timeout_ms = get_config().get("scraping.google.timeout_seconds", 15) * 1000
        self.max_searches = get_config().get("scraping.google.max_searches", 3)
        self.search_delay = get_config().get("scraping.google.search_delay_seconds", 2)
        self.max_pages = MAX_GOOGLE_PAGES

    async def search(
        self,
        page: Page,
        brand_name: str,
        product_category: Optional[str] = None,
    ) -> List[SearchCandidate]:
        """
        Search Google for brand websites

        Args:
            page: Playwright page instance
            brand_name: Brand name to search for
            product_category: Optional product category for better results

        Returns:
            List of SearchCandidate results
        """
        candidates = []
        searches_performed = 0

        try:
            # Search 1: Brand + Official Website
            if searches_performed < self.max_searches:
                results = await self._perform_search(
                    page,
                    f'"{brand_name}" official website',
                )
                candidates.extend(results)
                searches_performed += 1

                if self._has_high_confidence_result(candidates):
                    return candidates

                await asyncio.sleep(self.search_delay)

            # Search 2: Brand + Manufacturer
            if searches_performed < self.max_searches:
                results = await self._perform_search(
                    page,
                    f'"{brand_name}" manufacturer',
                )
                candidates.extend(results)
                searches_performed += 1

                if self._has_high_confidence_result(candidates):
                    return candidates

                await asyncio.sleep(self.search_delay)

            # Search 3: Brand only (fallback)
            if searches_performed < self.max_searches:
                results = await self._perform_search(page, brand_name)
                candidates.extend(results)
                searches_performed += 1

            return candidates

        except GoogleBlockedException:
            logger.warning(f"Google blocked search for {brand_name}")
            raise
        except Exception as e:
            logger.error(f"Google search error: {e}")
            raise GoogleException(f"Failed to search Google: {e}")

    async def _perform_search(self, page: Page, query: str) -> List[SearchCandidate]:
        """Perform a single Google search"""
        candidates = []

        try:
            logger.debug(f"Searching Google for: {query}")

            # Navigate to Google
            await page.goto("https://www.google.com/", wait_until="domcontentloaded", timeout=self.timeout_ms)

            # Check for CAPTCHA
            if await self._detect_captcha(page):
                raise GoogleBlockedException("Google CAPTCHA detected")

            # Enter search query
            search_box = page.locator("input[name='q']")
            await search_box.click()
            await search_box.fill(query)
            await search_box.press("Enter")

            # Wait for results
            await asyncio.sleep(2)

            # Extract results from pages
            for page_num in range(1, self.max_pages + 1):
                page_results = await self._extract_results(page)

                if not page_results:
                    break

                candidates.extend(page_results)

                # Stop if we have enough results
                if len(candidates) >= 5:
                    break

                # Go to next page if available
                if page_num < self.max_pages:
                    next_button = page.locator("a[aria-label='Next page']").first
                    if next_button:
                        await next_button.click()
                        await asyncio.sleep(1)

            logger.debug(f"Found {len(candidates)} candidates for query: {query}")
            return candidates

        except PlaywrightTimeoutError:
            raise GoogleTimeoutException(f"Timeout searching for: {query}")
        except GoogleBlockedException:
            raise
        except Exception as e:
            logger.warning(f"Error performing search: {e}")
            return candidates

    async def _detect_captcha(self, page: Page) -> bool:
        """Detect if Google shows CAPTCHA"""
        try:
            captcha_markers = await page.locator(
                "iframe[src*='recaptcha'], div[data-captcha-id]"
            ).count()

            return captcha_markers > 0

        except Exception:
            return False

    async def _extract_results(self, page: Page) -> List[SearchCandidate]:
        """Extract search results from current page"""
        candidates = []
        rank = 1

        try:
            # Get all search result divs
            results = await page.locator("div[data-sokoban-container] div[data-sokoban-feature]").all()

            for result in results:
                try:
                    # Extract title
                    title_elem = await result.locator("h3").text_content()
                    if not title_elem:
                        continue

                    title = title_elem.strip()

                    # Extract URL
                    link_elem = await result.locator("a").first.get_attribute("href")
                    if not link_elem:
                        continue

                    url = self._clean_url(link_elem)

                    # Extract snippet
                    snippet_elem = await result.locator("span[data-mh] span").text_content()
                    snippet = snippet_elem.strip() if snippet_elem else ""

                    # Filter ignored domains
                    if self._is_ignored_domain(url):
                        logger.debug(f"Skipping ignored domain: {url}")
                        continue

                    # Filter non-website results
                    if not self._is_likely_website(url, title):
                        continue

                    candidate = SearchCandidate(
                        url=url,
                        title=title,
                        snippet=snippet,
                        source="google_page_1",
                        rank=rank,
                    )

                    candidates.append(candidate)
                    rank += 1

                    if len(candidates) >= 5:
                        break

                except Exception as e:
                    logger.debug(f"Error extracting result: {e}")
                    continue

            return candidates

        except Exception as e:
            logger.warning(f"Error extracting results: {e}")
            return candidates

    def _clean_url(self, url: str) -> str:
        """Clean and normalize URL from Google result"""
        # Remove Google redirect parameters
        if "/url?q=" in url:
            url = url.split("/url?q=")[1].split("&")[0]

        # Remove tracking parameters
        url = re.sub(r'[\?&](utm|fbclid|gclid).*$', '', url)

        return url

    def _is_ignored_domain(self, url: str) -> bool:
        """Check if URL is in ignored domains list"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "").lower()

            return any(ignored in domain for ignored in IGNORED_DOMAINS)

        except Exception:
            return False

    def _is_likely_website(self, url: str, title: str) -> bool:
        """Check if URL appears to be an official website"""
        url_lower = url.lower()
        title_lower = title.lower()

        # Exclude common non-website results
        exclude_patterns = [
            "youtube.com",
            "facebook.com",
            "instagram.com",
            "linkedin.com",
            "twitter.com",
            "pinterest.com",
            "reddit.com",
            "wikipedia.org",
            "news",
            "blog",
            "forum",
            "review",
            "store",
            "amazon",
            "ebay",
            "walmart",
        ]

        for pattern in exclude_patterns:
            if pattern in url_lower or pattern in title_lower:
                return False

        # Check for website-like indicators
        return url_lower.startswith("http") or url_lower.startswith("www")

    def _has_high_confidence_result(self, candidates: List[SearchCandidate]) -> bool:
        """Check if we have a high-confidence result to stop searching"""
        if not candidates:
            return False

        # If first result has "official" in title or snippet, it's likely good
        first = candidates[0]
        confidence_keywords = ["official", "brand", "manufacturer"]

        for keyword in confidence_keywords:
            if keyword in first.title.lower() or keyword in first.snippet.lower():
                return True

        return False
