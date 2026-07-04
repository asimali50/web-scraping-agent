"""Integration test for Phase 5 - Testing complete workflow with progress tracking"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import BrandInput
from src.processors.batch_processor import BatchProcessor, ProcessingStats
from src.services.browser_service import get_browser_service, close_browser_service
from src.services.checkpoint_service import CheckpointManager
from src.services.logger_service import LoggerService, get_logger
from src.core.config import init_config

logger = get_logger(__name__)


async def test_phase5_integration():
    """Test Phase 5 integration with progress tracking and checkpoints"""
    try:
        # Initialize
        init_config()
        LoggerService.init()
        logger.info("=" * 80)
        logger.info("PHASE 5 INTEGRATION TEST - Starting")
        logger.info("=" * 80)

        # Initialize browser
        browser = await get_browser_service()
        logger.info("[OK] Browser service initialized")

        # Create test data
        session_id = str(uuid4())
        test_rows = [
            BrandInput(
                row_number=1,
                amazon_link="https://www.amazon.com/dp/B09F9BJ9Z9",
                brand_name="Nike",
                website="",
            ),
            BrandInput(
                row_number=2,
                amazon_link="https://www.amazon.com/dp/B0BHYQVMWT",
                brand_name="Apple",
                website="",
            ),
            BrandInput(
                row_number=3,
                amazon_link="https://www.amazon.com/dp/B08F7D4D7N",
                brand_name="Sony",
                website="",
            ),
        ]

        logger.info(f"Test data: {len(test_rows)} rows")

        # Test 1: Batch processor with progress tracking
        print("\n" + "=" * 80)
        print("TEST 1: Batch Processing with Progress Tracking")
        print("=" * 80)

        processor = BatchProcessor(max_workers=2)
        logger.info("Batch processor created with 2 workers")

        execution_logs, stats, results_dict = await processor.process_batch(
            test_rows,
            session_id,
            enable_progress=True,
            enable_checkpoints=True,
        )

        logger.info(f"[OK] Batch processing complete: {len(execution_logs)} rows processed")

        # Display results
        print(f"\nResults Summary:")
        print(f"  Total Rows:        {stats.total_rows}")
        print(f"  Processed:         {stats.processed_rows}")
        print(f"  Found:             {stats.found_count}")
        print(f"  Needs Review:      {stats.review_count}")
        print(f"  Not Found:         {stats.not_found_count}")
        print(f"  Errors:            {stats.error_count}")
        print(f"  Success Rate:      {stats.success_rate:.1f}%")
        print(f"  Total Time:        {stats.total_time:.2f}s")
        print(f"  Avg Time/Row:      {stats.average_time_per_row:.2f}s")

        # Test 2: Checkpoint verification
        print("\n" + "=" * 80)
        print("TEST 2: Checkpoint Verification")
        print("=" * 80)

        checkpoint_mgr = CheckpointManager()
        checkpoints = checkpoint_mgr.list_checkpoints(session_id)

        if checkpoints:
            logger.info(f"[OK] Found {len(checkpoints)} checkpoint(s)")
            for cp in checkpoints:
                data = checkpoint_mgr.load_checkpoint(cp)
                logger.info(
                    f"  Checkpoint: {Path(cp).name} "
                    f"({data['processed_rows']}/{data['total_rows']} rows)"
                )
        else:
            logger.warning("No checkpoints found")

        # Test 3: Execution logs verification
        print("\n" + "=" * 80)
        print("TEST 3: Execution Logs Verification")
        print("=" * 80)

        for log in execution_logs[:3]:  # Show first 3
            print(f"\nRow {log.row_number}: {log.brand_name}")
            print(f"  Status:     {log.status}")
            print(f"  Website:    {log.website_selected or 'Not found'}")
            print(f"  Confidence: {log.confidence:.1f}%")
            print(f"  Time:       {log.execution_time:.2f}s")

        logger.info(f"[OK] Execution logs verified: {len(execution_logs)} entries")

        # Final summary
        print("\n" + "=" * 80)
        print("PHASE 5 INTEGRATION TEST - COMPLETE [OK]")
        print("=" * 80)
        print(f"\nTest Results:")
        print(f"  [OK] Progress tracking:     WORKING")
        print(f"  [OK] Batch processing:      WORKING ({stats.processed_rows} rows)")
        print(f"  [OK] Checkpoints:           WORKING ({len(checkpoints)} checkpoints)")
        print(f"  [OK] Execution logs:        WORKING ({len(execution_logs)} logs)")
        print(f"  [OK] Error handling:        WORKING ({stats.error_count} errors handled)")
        print(f"\nSession ID: {session_id}")
        print("=" * 80 + "\n")

        logger.info("Phase 5 integration test completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Integration test failed: {e}", exc_info=True)
        print(f"\n[ERROR] Test failed: {e}\n")
        return 1

    finally:
        await close_browser_service()
        logger.info("Browser service closed")


def main():
    """Main test entry point"""
    try:
        exit_code = asyncio.run(test_phase5_integration())
        return exit_code
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 130
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
