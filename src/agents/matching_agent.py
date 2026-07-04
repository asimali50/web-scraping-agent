"""Matching Agent - Intelligent brand and website matching"""

import re
from typing import Optional

from src.core.config import get_config
from src.core.constants import (
    CONFIDENCE_AUTO_SAVE,
    CONFIDENCE_REVIEW,
)
from src.core.exceptions import CacheException
from src.core.models import AmazonProductData, BrandMatch, WebsiteAnalysis
from src.services.logger_service import get_logger

logger = get_logger(__name__)


class MatchingAgent:
    """Intelligent matching of brands and websites"""

    def __init__(self):
        """Initialize matching agent"""
        self.use_claude = get_config().get("claude.use_only_when", "ambiguous")
        self.confidence_auto_save = CONFIDENCE_AUTO_SAVE
        self.confidence_review = CONFIDENCE_REVIEW

    def match(
        self,
        amazon_data: AmazonProductData,
        website_analysis: WebsiteAnalysis,
        sources: list,
    ) -> BrandMatch:
        """
        Match Amazon product with website using deterministic and AI methods

        Args:
            amazon_data: Extracted Amazon product data
            website_analysis: Analyzed website data
            sources: List of sources (amazon, google_page_1, etc)

        Returns:
            BrandMatch with confidence score and reasoning
        """
        try:
            # Calculate deterministic confidence score
            confidence, reasoning = self._calculate_confidence(
                amazon_data,
                website_analysis,
                sources,
            )

            # Determine status based on confidence
            if confidence >= self.confidence_auto_save:
                status = "found"
            elif confidence >= self.confidence_review:
                status = "needs_review"
            else:
                status = "not_found"

            brand_match = BrandMatch(
                brand_name=amazon_data.brand,
                website_url=website_analysis.url,
                confidence=confidence,
                reasoning=reasoning,
                sources=sources,
                claude_verified=False,
                execution_time=amazon_data.extraction_time + website_analysis.extraction_time,
                status=status,
            )

            logger.info(
                f"Match result for {amazon_data.brand}: "
                f"{website_analysis.url} "
                f"(confidence: {confidence}%, status: {status})"
            )

            return brand_match

        except Exception as e:
            logger.error(f"Error matching website: {e}")
            raise CacheException(f"Failed to match website: {e}")

    def _calculate_confidence(
        self,
        amazon_data: AmazonProductData,
        website_analysis: WebsiteAnalysis,
        sources: list,
    ) -> tuple:
        """
        Calculate confidence score using deterministic logic

        Returns:
            Tuple of (confidence_score, reasoning_text)
        """
        score = 0
        factors = []

        # Factor 1: Exact brand name match (30 points)
        if self._brand_name_matches(amazon_data.brand, website_analysis.domain):
            score += 30
            factors.append("Brand name matches domain")
        elif self._brand_name_matches(amazon_data.brand, website_analysis.company_name):
            score += 25
            factors.append("Brand name matches company name")
        elif amazon_data.brand in website_analysis.domain:
            score += 20
            factors.append("Brand found in domain")

        # Factor 2: Logo present (15 points)
        if website_analysis.logo_present:
            score += 15
            factors.append("Logo detected on website")

        # Factor 3: Product category overlap (20 points)
        if self._categories_overlap(amazon_data.category, website_analysis.product_categories):
            score += 20
            factors.append("Product categories match")
        elif website_analysis.product_categories:
            score += 10
            factors.append("Website has product categories")

        # Factor 4: About page present (10 points)
        if website_analysis.about_page_present:
            score += 10
            factors.append("About page present")

        # Factor 5: Contact page present (5 points)
        if website_analysis.contact_page_present:
            score += 5
            factors.append("Contact page present")

        # Factor 6: Brand mentions on page (10 points)
        if website_analysis.brand_mentions > 0:
            score += min(10, website_analysis.brand_mentions)
            factors.append(f"Brand mentioned {website_analysis.brand_mentions} times on page")

        # Factor 7: Domain legitimacy (10 points)
        if self._is_legitimate_domain(website_analysis.domain):
            score += 10
            factors.append("Domain appears legitimate")

        # Factor 8: Source priority (bonus points)
        if "amazon" in sources:
            score += 15
            factors.append("Website found on Amazon")
        elif "google_page_1" in sources:
            score += 8
            factors.append("Found in Google page 1")

        # Cap at 100
        confidence = min(100, score)

        reasoning = "; ".join(factors) if factors else "Insufficient data"

        logger.debug(
            f"Confidence calculation: {score} points -> {confidence}% "
            f"({reasoning})"
        )

        return confidence, reasoning

    def _brand_name_matches(self, brand: str, text: Optional[str]) -> bool:
        """Check if brand name matches text"""
        if not brand or not text:
            return False

        brand_norm = self._normalize_string(brand)
        text_norm = self._normalize_string(text)

        # Exact match
        if brand_norm == text_norm:
            return True

        # One is substring of other
        if brand_norm in text_norm or text_norm in brand_norm:
            return True

        # Check for common abbreviations
        brand_abbr = self._get_abbreviation(brand_norm)
        if brand_abbr and brand_abbr == text_norm:
            return True

        return False

    def _categories_overlap(self, amazon_category: str, website_categories: list) -> bool:
        """Check if categories overlap"""
        if not amazon_category or not website_categories:
            return False

        amazon_cat_norm = self._normalize_string(amazon_category)

        for website_cat in website_categories:
            website_cat_norm = self._normalize_string(website_cat)

            if (
                amazon_cat_norm in website_cat_norm
                or website_cat_norm in amazon_cat_norm
            ):
                return True

        return False

    def _is_legitimate_domain(self, domain: str) -> bool:
        """Check if domain looks legitimate"""
        if not domain:
            return False

        # Exclude obviously fake or suspicious patterns
        suspicious_patterns = [
            "temp",
            "test",
            "fake",
            "demo",
            "example",
            ".xyz",
            ".tk",
            ".ml",
        ]

        domain_lower = domain.lower()

        for pattern in suspicious_patterns:
            if pattern in domain_lower:
                return False

        # Should have at least one dot
        if "." not in domain:
            return False

        return True

    def _normalize_string(self, text: str) -> str:
        """Normalize string for comparison"""
        # Convert to lowercase
        text = text.lower().strip()

        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        return text

    def _get_abbreviation(self, brand: str) -> Optional[str]:
        """Get abbreviation from brand name (first letters)"""
        words = brand.split()

        if len(words) <= 1:
            return None

        abbr = "".join(word[0] for word in words if word)

        return abbr if len(abbr) > 1 else None
