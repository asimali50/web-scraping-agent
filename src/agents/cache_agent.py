"""Cache Agent - Brand deduplication and caching"""

import re
from typing import Optional

from src.core.models import BrandMatch, CacheEntry
from src.core.exceptions import CacheException
from src.services.cache_service import CacheService
from src.services.logger_service import get_logger

logger = get_logger(__name__)


class CacheAgent:
    """Handle brand caching and deduplication"""

    def __init__(self, cache_service: CacheService):
        """Initialize cache agent"""
        self.cache = cache_service

    def normalize_brand_name(self, brand_name: str) -> str:
        """
        Normalize brand name for deduplication

        Handles:
        - Case variations (Nike, NIKE, nike)
        - Special characters (Nike®, Nike™)
        - Spaces and punctuation

        Args:
            brand_name: Original brand name

        Returns:
            Normalized brand name
        """
        if not brand_name:
            return ""

        # Convert to lowercase
        normalized = brand_name.lower().strip()

        # Remove common trademark symbols
        normalized = re.sub(r'[®™©]', '', normalized)

        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', normalized)

        # Remove punctuation except hyphens and underscores
        normalized = re.sub(r'[^\w\s\-]', '', normalized)

        logger.debug(f"Normalized '{brand_name}' -> '{normalized}'")

        return normalized

    def get_cached_result(self, brand_name: str) -> Optional[BrandMatch]:
        """
        Get cached result for brand if available

        Args:
            brand_name: Brand name to look up

        Returns:
            BrandMatch if found in cache, None otherwise
        """
        try:
            normalized = self.normalize_brand_name(brand_name)

            if not normalized:
                return None

            logger.debug(f"Checking cache for: {normalized}")

            cache_entry = self.cache.get_cached_brand(normalized)

            if not cache_entry:
                logger.debug(f"Cache miss for: {normalized}")
                return None

            logger.info(f"Cache hit for {brand_name}: {cache_entry['website_url']}")

            # Convert cache entry to BrandMatch
            brand_match = BrandMatch(
                brand_name=brand_name,
                website_url=cache_entry['website_url'],
                confidence=cache_entry['confidence'],
                reasoning=f"Retrieved from cache (source: {cache_entry['source']})",
                sources=["cache", cache_entry['source']],
                claude_verified=False,
                execution_time=0.0,
                status="found" if cache_entry['confidence'] >= 95 else "needs_review",
            )

            return brand_match

        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
            return None

    def save_result(
        self,
        brand_name: str,
        brand_match: BrandMatch,
    ) -> None:
        """
        Save result to cache

        Args:
            brand_name: Original brand name
            brand_match: BrandMatch result to cache
        """
        try:
            normalized = self.normalize_brand_name(brand_name)

            if not normalized or not brand_match.website_url:
                logger.debug("Skipping cache save: invalid data")
                return

            logger.debug(f"Saving to cache: {normalized} -> {brand_match.website_url}")

            # Determine primary source
            source = brand_match.sources[0] if brand_match.sources else "unknown"

            self.cache.save_cached_brand(
                normalized,
                brand_name,
                brand_match.website_url,
                brand_match.confidence,
                source
            )
            logger.info(f"Cached result for {brand_name}: {brand_match.website_url}")

        except Exception as e:
            logger.error(f"Cache save error: {e}")
            raise CacheException(f"Failed to save cache: {e}")

    def is_duplicate_brand(self, brand_name_1: str, brand_name_2: str) -> bool:
        """
        Check if two brand names refer to the same brand

        Args:
            brand_name_1: First brand name
            brand_name_2: Second brand name

        Returns:
            True if brands appear to be duplicates
        """
        if not brand_name_1 or not brand_name_2:
            return False

        norm_1 = self.normalize_brand_name(brand_name_1)
        norm_2 = self.normalize_brand_name(brand_name_2)

        # Exact match after normalization
        if norm_1 == norm_2:
            return True

        # One is substring of other
        if norm_1 in norm_2 or norm_2 in norm_1:
            return True

        return False
