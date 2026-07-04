"""Orchestrator - Coordinates agents and manages workflow"""

import asyncio
import time
from typing import Optional

from src.agents.amazon_agent import AmazonAgent
from src.agents.cache_agent import CacheAgent
from src.agents.google_agent import GoogleAgent
from src.agents.matching_agent import MatchingAgent
from src.agents.website_agent import WebsiteAgent
from src.core.config import get_config
from src.core.constants import (
    HARD_TIME_LIMIT,
    SOFT_TIME_LIMIT,
    STATUS_AMAZON_FAILED,
    STATUS_GOOGLE_FAILED,
    STATUS_FOUND,
    STATUS_NOT_FOUND,
    STATUS_TIMEOUT,
)
from src.core.exceptions import (
    AmazonException,
    BrandMismatchException,
    GoogleException,
    TimeBudgetException,
    WebsiteException,
)
from src.core.models import BrandInput, BrandMatch, ExecutionLog
from src.services.browser_service import get_browser_service
from src.services.cache_service import CacheService
from src.services.logger_service import get_logger

logger = get_logger(__name__)


class Orchestrator:
    """Orchestrate brand website detection workflow"""

    def __init__(self):
        """Initialize orchestrator"""
        self.amazon_agent = AmazonAgent()
        self.google_agent = GoogleAgent()
        self.website_agent = WebsiteAgent()
        self.matching_agent = MatchingAgent()
        self.cache_service = CacheService()
        self.cache_agent = CacheAgent(self.cache_service)

    async def process_row(
        self,
        row: BrandInput,
        session_id: str,
    ) -> ExecutionLog:
        """
        Process a single row: extract from Amazon, search Google, verify website

        Args:
            row: Input row with brand name and Amazon link
            session_id: Session ID for logging

        Returns:
            ExecutionLog with results
        """
        start_time = time.time()
        execution_log = ExecutionLog(
            row_number=row.row_number,
            brand_name=row.brand_name,
            amazon_link=row.amazon_link,
            reason="Processing started",
            execution_time=0.0,
            status="Processing",
        )

        try:
            logger.info(f"Processing row {row.row_number}: {row.brand_name}")

            # Step 1: Check cache
            cached_result = self.cache_agent.get_cached_result(row.brand_name)
            if cached_result:
                execution_log.website_selected = cached_result.website_url
                execution_log.confidence = cached_result.confidence
                execution_log.reason = f"Cached result: {cached_result.reasoning}"
                execution_log.status = STATUS_FOUND
                execution_log.execution_time = time.time() - start_time
                logger.info(f"Row {row.row_number}: Using cached result")
                return execution_log

            # Step 2: Extract from Amazon
            try:
                browser_service = await get_browser_service()
                page = await browser_service.create_page()
                amazon_data = await self._execute_with_timeout(
                    self.amazon_agent.extract(page, row.amazon_link, row.brand_name),
                    SOFT_TIME_LIMIT,
                    f"Amazon extraction for {row.brand_name}",
                )
                await browser_service.close_page(page)

                execution_log.amazon_verified = True
                logger.debug(f"Row {row.row_number}: Amazon extracted - {amazon_data.brand}")

                # If website found on Amazon, use it
                if amazon_data.official_website:
                    execution_log.website_selected = amazon_data.official_website
                    execution_log.confidence = 98.0
                    execution_log.reason = "Official website found on Amazon product page"
                    execution_log.status = STATUS_FOUND
                    execution_log.execution_time = time.time() - start_time

                    # Cache the result
                    brand_match = BrandMatch(
                        brand_name=row.brand_name,
                        website_url=amazon_data.official_website,
                        confidence=98.0,
                        reasoning="From Amazon",
                        sources=["amazon"],
                        status=STATUS_FOUND,
                        execution_time=amazon_data.extraction_time,
                    )
                    self.cache_agent.save_result(row.brand_name, brand_match)

                    logger.info(
                        f"Row {row.row_number}: Found website on Amazon: "
                        f"{amazon_data.official_website}"
                    )
                    return execution_log

            except BrandMismatchException as e:
                logger.warning(f"Row {row.row_number}: Brand mismatch - {e}")
                execution_log.reason = str(e)
                execution_log.status = STATUS_AMAZON_FAILED
                execution_log.execution_time = time.time() - start_time
                return execution_log
            except AmazonException as e:
                logger.warning(f"Row {row.row_number}: Amazon error - {e}")
                execution_log.reason = f"Amazon error: {str(e)}"
                execution_log.status = STATUS_AMAZON_FAILED
                execution_log.execution_time = time.time() - start_time
                # Continue to Google search
                amazon_data = None

            if not amazon_data:
                execution_log.reason = "Proceeding to Google search"

            # Step 3: Search Google
            try:
                browser_service = await get_browser_service()
                page = await browser_service.create_page()
                search_candidates = await self._execute_with_timeout(
                    self.google_agent.search(page, row.brand_name),
                    SOFT_TIME_LIMIT,
                    f"Google search for {row.brand_name}",
                )
                await browser_service.close_page(page)

                execution_log.google_searched = True

                if not search_candidates:
                    execution_log.website_selected = None
                    execution_log.confidence = 0.0
                    execution_log.reason = "No results found on Google"
                    execution_log.status = STATUS_NOT_FOUND
                    execution_log.execution_time = time.time() - start_time
                    logger.info(f"Row {row.row_number}: No Google results")
                    return execution_log

                logger.debug(
                    f"Row {row.row_number}: Found {len(search_candidates)} "
                    f"Google candidates"
                )

            except GoogleException as e:
                logger.warning(f"Row {row.row_number}: Google error - {e}")
                execution_log.reason = f"Google error: {str(e)}"
                execution_log.status = STATUS_GOOGLE_FAILED
                execution_log.execution_time = time.time() - start_time
                return execution_log

            # Step 4: Verify websites
            best_match = None
            best_confidence = 0.0

            for candidate in search_candidates[:3]:  # Test top 3
                try:
                    browser_service = await get_browser_service()
                    page = await browser_service.create_page()
                    website_analysis = await self._execute_with_timeout(
                        self.website_agent.verify(
                            page,
                            candidate.url,
                            row.brand_name,
                        ),
                        5,
                        f"Website verification for {candidate.url}",
                    )
                    await browser_service.close_page(page)

                    # Match Amazon data with website if available
                    if amazon_data:
                        brand_match = self.matching_agent.match(
                            amazon_data,
                            website_analysis,
                            ["google"] + candidate.source.split("_"),
                        )
                    else:
                        # Simplified matching without Amazon data
                        brand_match = BrandMatch(
                            brand_name=row.brand_name,
                            website_url=candidate.url,
                            confidence=self._simple_confidence_check(
                                row.brand_name,
                                website_analysis,
                            ),
                            reasoning="Google search result verified",
                            sources=["google"],
                            status=STATUS_FOUND if best_confidence >= 80 else STATUS_NOT_FOUND,
                            execution_time=website_analysis.extraction_time,
                        )

                    if brand_match.confidence > best_confidence:
                        best_confidence = brand_match.confidence
                        best_match = brand_match

                    if best_confidence >= 95:
                        break  # Found high-confidence match

                except WebsiteException as e:
                    logger.debug(f"Row {row.row_number}: Failed to verify {candidate.url}: {e}")
                    continue
                except Exception as e:
                    logger.debug(f"Row {row.row_number}: Error processing candidate: {e}")
                    continue

            # Step 5: Finalize result
            if best_match and best_confidence >= 80:
                execution_log.website_selected = best_match.website_url
                execution_log.confidence = best_match.confidence
                execution_log.reason = best_match.reasoning
                execution_log.status = best_match.status
                execution_log.execution_time = time.time() - start_time

                # Cache the result
                self.cache_agent.save_result(row.brand_name, best_match)

                logger.info(
                    f"Row {row.row_number}: Match found with {best_confidence}% confidence: "
                    f"{best_match.website_url}"
                )
            else:
                execution_log.website_selected = None
                execution_log.confidence = best_confidence if best_confidence > 0 else 0.0
                execution_log.reason = "No suitable website found"
                execution_log.status = STATUS_NOT_FOUND
                execution_log.execution_time = time.time() - start_time
                logger.info(f"Row {row.row_number}: No suitable website found")

            return execution_log

        except Exception as e:
            logger.error(f"Row {row.row_number}: Unexpected error: {e}", exc_info=True)
            execution_log.reason = f"Unexpected error: {str(e)}"
            execution_log.status = "error"
            execution_log.execution_time = time.time() - start_time
            return execution_log

    async def _execute_with_timeout(
        self,
        coro,
        timeout_seconds: float,
        operation_name: str,
    ):
        """Execute coroutine with timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout: {operation_name}")
            raise TimeBudgetException(f"Timeout in {operation_name}")

    def _simple_confidence_check(self, brand_name: str, website_analysis) -> float:
        """Simple confidence check without Amazon data"""
        confidence = 0.0

        if brand_name.lower() in website_analysis.domain.lower():
            confidence += 50
        elif website_analysis.company_name and brand_name.lower() in website_analysis.company_name.lower():
            confidence += 40

        if website_analysis.logo_present:
            confidence += 20

        if website_analysis.about_page_present:
            confidence += 10

        if website_analysis.contact_page_present:
            confidence += 10

        if website_analysis.brand_mentions > 0:
            confidence += 10

        return min(100, confidence)
