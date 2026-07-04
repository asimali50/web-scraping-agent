"""Test orchestrator end-to-end workflow"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import BrandInput
from src.processors.orchestrator import Orchestrator
from src.services.browser_service import get_browser_service, close_browser_service
from src.services.logger_service import LoggerService, get_logger

logger = get_logger(__name__)


async def test_orchestrator_with_sample_data():
    """Test orchestrator with sample brand data"""
    try:
        # Initialize
        LoggerService.init()
        logger.info("Starting orchestrator test")

        # Initialize browser
        browser = await get_browser_service()
        logger.info("Browser initialized")

        # Create orchestrator
        orchestrator = Orchestrator()
        logger.info("Orchestrator created")

        # Test data - single row
        test_row = BrandInput(
            row_number=1,
            amazon_link="https://www.amazon.com/dp/B09F9BJ9Z9",
            brand_name="Nike",
            website="",
        )

        logger.info(f"Processing test row: {test_row.brand_name}")

        # Process the row
        result = await orchestrator.process_row(test_row, "test-session-001")

        # Display results
        print("\n" + "=" * 80)
        print("ORCHESTRATOR TEST RESULTS")
        print("=" * 80)
        print(f"Row Number:      {result.row_number}")
        print(f"Brand Name:      {result.brand_name}")
        print(f"Status:          {result.status}")
        print(f"Website Found:   {result.website_selected}")
        print(f"Confidence:      {result.confidence:.1f}%")
        print(f"Reason:          {result.reason}")
        print(f"Execution Time:  {result.execution_time:.2f}s")
        print("=" * 80 + "\n")

        logger.info(f"Test completed: {result.status}")

        return result

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise
    finally:
        await close_browser_service()
        logger.info("Browser closed")


def main():
    """Main test entry point"""
    try:
        result = asyncio.run(test_orchestrator_with_sample_data())
        return 0 if result.status in ["found", "needs_review"] else 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
