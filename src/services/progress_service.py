"""Progress tracking service for batch processing"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

from src.services.logger_service import get_logger

logger = get_logger(__name__)


@dataclass
class ProgressSnapshot:
    """Snapshot of current progress"""
    total_rows: int
    processed_rows: int
    found_count: int = 0
    review_count: int = 0
    not_found_count: int = 0
    error_count: int = 0
    start_time: float = field(default_factory=time.time)
    last_update: datetime = field(default_factory=datetime.now)
    current_brand: str = ""

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds"""
        return time.time() - self.start_time

    @property
    def processing_rate(self) -> float:
        """Get processing rate (rows per minute)"""
        if self.elapsed_seconds == 0:
            return 0.0
        return (self.processed_rows / self.elapsed_seconds) * 60

    @property
    def average_time_per_row(self) -> float:
        """Get average time per row"""
        if self.processed_rows == 0:
            return 0.0
        return self.elapsed_seconds / self.processed_rows

    @property
    def estimated_remaining_seconds(self) -> float:
        """Estimate time remaining"""
        remaining_rows = self.total_rows - self.processed_rows
        if self.average_time_per_row == 0:
            return 0.0
        return remaining_rows * self.average_time_per_row

    @property
    def estimated_completion_time(self) -> datetime:
        """Estimate when processing will complete"""
        from datetime import timedelta
        return datetime.now() + timedelta(seconds=self.estimated_remaining_seconds)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.processed_rows == 0:
            return 0.0
        return (self.found_count / self.processed_rows) * 100

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if self.total_rows == 0:
            return 0.0
        return (self.processed_rows / self.total_rows) * 100


class ProgressTracker:
    """Track and report batch processing progress"""

    def __init__(self, total_rows: int, update_interval_seconds: float = 5.0):
        """
        Initialize progress tracker

        Args:
            total_rows: Total number of rows to process
            update_interval_seconds: How often to log progress updates
        """
        self.total_rows = total_rows
        self.update_interval_seconds = update_interval_seconds
        self.snapshot = ProgressSnapshot(total_rows=total_rows, processed_rows=0)
        self._last_logged = time.time()
        self._callbacks: Dict[str, Any] = {}

    def register_callback(self, event: str, callback) -> None:
        """
        Register callback for progress events

        Args:
            event: Event name (row_processed, batch_complete, etc.)
            callback: Callable that receives progress snapshot
        """
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    async def _emit_event(self, event: str) -> None:
        """Emit progress event"""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.snapshot)
                else:
                    callback(self.snapshot)

    async def record_row_processed(
        self,
        brand_name: str,
        status: str,
        execution_time: float,
    ) -> None:
        """
        Record that a row was processed

        Args:
            brand_name: Brand name processed
            status: Result status (found, not_found, needs_review, error)
            execution_time: Time taken to process
        """
        self.snapshot.processed_rows += 1
        self.snapshot.current_brand = brand_name
        self.snapshot.last_update = datetime.now()

        # Update counts
        if status == "found":
            self.snapshot.found_count += 1
        elif status == "needs_review":
            self.snapshot.review_count += 1
        elif status == "not_found":
            self.snapshot.not_found_count += 1
        elif status == "error":
            self.snapshot.error_count += 1

        await self._emit_event("row_processed")

        # Log progress periodically
        if time.time() - self._last_logged >= self.update_interval_seconds:
            self._log_progress()
            self._last_logged = time.time()

    def _log_progress(self) -> None:
        """Log current progress"""
        s = self.snapshot
        logger.info(
            f"Progress: {s.processed_rows}/{s.total_rows} "
            f"({s.completion_percentage:.1f}%) | "
            f"Found: {s.found_count}, Review: {s.review_count}, "
            f"Not Found: {s.not_found_count}, Errors: {s.error_count} | "
            f"Rate: {s.processing_rate:.1f} rows/min | "
            f"ETA: {s.estimated_completion_time.strftime('%H:%M:%S')}"
        )

    def get_progress(self) -> ProgressSnapshot:
        """Get current progress snapshot"""
        return self.snapshot

    def format_progress_bar(self, width: int = 50) -> str:
        """
        Format progress as ASCII bar

        Args:
            width: Width of progress bar in characters

        Returns:
            Formatted progress bar string
        """
        s = self.snapshot
        percent = s.completion_percentage
        filled = int(width * percent / 100)
        bar = "█" * filled + "░" * (width - filled)

        return (
            f"[{bar}] {s.completion_percentage:.1f}% "
            f"({s.processed_rows}/{s.total_rows})"
        )

    def format_summary(self) -> str:
        """Format progress summary for display"""
        s = self.snapshot

        hours, remainder = divmod(int(s.elapsed_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)

        eta_hours, eta_remainder = divmod(int(s.estimated_remaining_seconds), 3600)
        eta_minutes, eta_seconds = divmod(eta_remainder, 60)

        return f"""
================================================================================
                         BATCH PROCESSING PROGRESS
================================================================================

  Total Rows:             {s.total_rows:>6}
  Processed:              {s.processed_rows:>6}  ({s.completion_percentage:>5.1f}%)

  Found:                  {s.found_count:>6}  ({s.success_rate:>5.1f}% success rate)
  Needs Review:           {s.review_count:>6}
  Not Found:              {s.not_found_count:>6}
  Errors:                 {s.error_count:>6}

  Elapsed Time:           {hours:>02d}:{minutes:>02d}:{seconds:>02d}
  Avg Time/Row:           {s.average_time_per_row:>6.2f}s
  Processing Rate:        {s.processing_rate:>6.1f} rows/min

  Estimated Remaining:    {eta_hours:>02d}:{eta_minutes:>02d}:{eta_seconds:>02d}
  Est. Completion:        {s.estimated_completion_time.strftime('%H:%M:%S')}

  Current Brand:          {s.current_brand:<60}

================================================================================
"""
