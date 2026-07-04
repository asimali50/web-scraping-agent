"""Batch Processor - Process multiple rows concurrently"""

import asyncio
import time
from typing import List, Dict, Optional
from dataclasses import dataclass

from src.agents.sheet_agent import SheetAgent
from src.core.config import get_config
from src.core.models import BrandInput, ExecutionLog
from src.processors.orchestrator import Orchestrator
from src.services.browser_service import get_browser_service, close_browser_service
from src.services.cache_service import CacheService
from src.services.checkpoint_service import CheckpointManager
from src.services.progress_service import ProgressTracker
from src.services.logger_service import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessingStats:
    """Statistics for processing batch"""
    total_rows: int
    processed_rows: int
    found_count: int
    not_found_count: int
    review_count: int
    error_count: int
    total_time: float
    average_time_per_row: float

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.processed_rows == 0:
            return 0.0
        return (self.found_count / self.processed_rows) * 100


class BatchProcessor:
    """Process multiple rows concurrently"""

    def __init__(self, max_workers: int = 3):
        """
        Initialize batch processor

        Args:
            max_workers: Number of concurrent workers
        """
        self.max_workers = max_workers
        self.orchestrator = Orchestrator()
        self.sheet_agent = SheetAgent()
        self.config = get_config()

    async def process_batch(
        self,
        rows: List[BrandInput],
        session_id: str,
        enable_progress: bool = True,
        enable_checkpoints: bool = True,
    ) -> tuple:
        """
        Process batch of rows concurrently with progress tracking

        Args:
            rows: List of BrandInput rows to process
            session_id: Session ID for logging
            enable_progress: Enable progress tracking
            enable_checkpoints: Enable checkpoint creation

        Returns:
            Tuple of (execution_logs, stats, results_dict)
        """
        start_time = time.time()

        logger.info(f"Starting batch processing: {len(rows)} rows with {self.max_workers} workers")

        # Initialize progress tracker
        progress = ProgressTracker(total_rows=len(rows)) if enable_progress else None
        checkpoint_mgr = CheckpointManager() if enable_checkpoints else None

        # Create task queue
        execution_logs: List[ExecutionLog] = []
        results_dict: Dict[int, Dict] = {}

        # Process rows with semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_workers)

        async def process_with_semaphore(row: BrandInput):
            async with semaphore:
                try:
                    row_start = time.time()
                    log = await self.orchestrator.process_row(row, session_id)
                    execution_time = time.time() - row_start
                    log.execution_time = execution_time

                    execution_logs.append(log)

                    # Store result for writing back to sheet
                    results_dict[row.row_number] = {
                        'website_url': log.website_selected,
                        'confidence': log.confidence,
                        'status': log.status,
                    }

                    # Update progress
                    if progress:
                        await progress.record_row_processed(
                            brand_name=row.brand_name,
                            status=log.status,
                            execution_time=execution_time,
                        )

                except Exception as e:
                    logger.error(f"Error processing row {row.row_number}: {e}")
                    error_log = ExecutionLog(
                        row_number=row.row_number,
                        brand_name=row.brand_name,
                        amazon_link=row.amazon_link,
                        reason=f"Processing error: {str(e)}",
                        execution_time=0.0,
                        status="error",
                    )
                    execution_logs.append(error_log)

                    # Update progress for error
                    if progress:
                        await progress.record_row_processed(
                            brand_name=row.brand_name,
                            status="error",
                            execution_time=0.0,
                        )

        # Run all tasks concurrently
        tasks = [process_with_semaphore(row) for row in rows]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Create final checkpoint
        if checkpoint_mgr:
            checkpoint_mgr.create_checkpoint(
                session_id=session_id,
                batch_name=f"batch_{session_id}",
                total_rows=len(rows),
                processed_rows=len(execution_logs),
                execution_logs=execution_logs,
                config={"max_workers": self.max_workers},
            )

        # Calculate statistics
        total_time = time.time() - start_time
        stats = self._calculate_stats(execution_logs, len(rows), total_time)

        # Display final progress
        if progress:
            print(progress.format_summary())

        logger.info(
            f"Batch processing complete: {stats.found_count} found, "
            f"{stats.not_found_count} not found, {stats.error_count} errors "
            f"in {total_time:.2f}s ({stats.average_time_per_row:.2f}s/row)"
        )

        return execution_logs, stats, results_dict

    def _calculate_stats(
        self,
        execution_logs: List[ExecutionLog],
        total_rows: int,
        total_time: float,
    ) -> ProcessingStats:
        """Calculate processing statistics"""
        found_count = sum(1 for log in execution_logs if log.status == "found")
        not_found_count = sum(1 for log in execution_logs if log.status == "not_found")
        review_count = sum(1 for log in execution_logs if log.status == "needs_review")
        error_count = sum(1 for log in execution_logs if log.status in ["error", "amazon_failed", "google_failed"])

        average_time = total_time / len(execution_logs) if execution_logs else 0.0

        return ProcessingStats(
            total_rows=total_rows,
            processed_rows=len(execution_logs),
            found_count=found_count,
            not_found_count=not_found_count,
            review_count=review_count,
            error_count=error_count,
            total_time=total_time,
            average_time_per_row=average_time,
        )

    async def process_excel(
        self,
        file_path: str,
        session_id: str,
        output_file: Optional[str] = None,
    ) -> ProcessingStats:
        """
        Process Excel file end-to-end

        Args:
            file_path: Path to input Excel file
            session_id: Session ID for tracking
            output_file: Optional output file path (defaults to input with _results suffix)

        Returns:
            ProcessingStats with results
        """
        try:
            logger.info(f"Processing Excel file: {file_path}")

            # Read input file
            rows, original_df = self.sheet_agent.read_excel(file_path)
            logger.info(f"Loaded {len(rows)} rows from {file_path}")

            # Process batch
            execution_logs, stats, results_dict = await self.process_batch(rows, session_id)

            # Write results
            if output_file is None:
                # Generate output filename
                from pathlib import Path
                input_path = Path(file_path)
                output_file = str(input_path.parent / f"{input_path.stem}_results.xlsx")

            self.sheet_agent.write_excel(output_file, original_df, results_dict)
            logger.info(f"Results written to: {output_file}")

            # Save execution logs to database
            cache = CacheService()
            for log in execution_logs:
                cache.save_execution_log(log, session_id)

            return stats

        except Exception as e:
            logger.error(f"Error processing Excel file: {e}")
            raise

    async def process_google_sheet(
        self,
        sheet_url: str,
        session_id: str,
        sheet_name: Optional[str] = None,
    ) -> ProcessingStats:
        """
        Process Google Sheet end-to-end

        Args:
            sheet_url: Google Sheets URL or share link
            session_id: Session ID for tracking
            sheet_name: Optional sheet name

        Returns:
            ProcessingStats with results
        """
        try:
            logger.info(f"Processing Google Sheet: {sheet_url}")

            # Read input sheet
            rows, original_df = self.sheet_agent.read_google_sheet(sheet_url, sheet_name)
            logger.info(f"Loaded {len(rows)} rows from Google Sheet")

            # Process batch
            execution_logs, stats, results_dict = await self.process_batch(rows, session_id)

            # Write results back to Google Sheet
            self.sheet_agent.write_google_sheet(sheet_url, results_dict, sheet_name)
            logger.info(f"Results written to Google Sheet")

            # Save execution logs to database
            cache = CacheService()
            for log in execution_logs:
                cache.save_execution_log(log, session_id)

            return stats

        except Exception as e:
            logger.error(f"Error processing Google Sheet: {e}")
            raise

    async def run_with_browser(
        self,
        input_file: str,
        session_id: str,
        output_file: Optional[str] = None,
    ) -> ProcessingStats:
        """
        Run batch processing with browser initialization

        Args:
            input_file: Path to input Excel file
            session_id: Session ID for tracking
            output_file: Optional output file path

        Returns:
            ProcessingStats with results
        """
        try:
            # Initialize browser
            await get_browser_service()
            logger.info("Browser service initialized")

            # Process file
            stats = await self.process_excel(input_file, session_id, output_file)

            return stats

        finally:
            # Clean up browser
            await close_browser_service()
            logger.info("Browser service closed")
