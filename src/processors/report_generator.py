"""Report Generator - Create execution logs and reports"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List

from src.core.models import ExecutionLog
from src.processors.batch_processor import ProcessingStats
from src.services.logger_service import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """Generate execution reports and logs"""

    def __init__(self, output_dir: str = "./logs"):
        """
        Initialize report generator

        Args:
            output_dir: Directory for output reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_execution_log(
        self,
        execution_logs: List[ExecutionLog],
        session_id: str,
    ) -> str:
        """
        Save execution log as CSV

        Args:
            execution_logs: List of ExecutionLog entries
            session_id: Session ID for filename

        Returns:
            Path to saved CSV file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"execution_log_{session_id}_{timestamp}.csv"
            filepath = self.output_dir / filename

            logger.info(f"Saving execution log to: {filepath}")

            # Define CSV columns
            fieldnames = [
                'row_number',
                'brand_name',
                'amazon_link',
                'amazon_verified',
                'google_searched',
                'website_selected',
                'confidence',
                'reason',
                'execution_time',
                'status',
                'timestamp',
            ]

            # Write CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for log in execution_logs:
                    writer.writerow({
                        'row_number': log.row_number,
                        'brand_name': log.brand_name,
                        'amazon_link': log.amazon_link,
                        'amazon_verified': log.amazon_verified,
                        'google_searched': log.google_searched,
                        'website_selected': log.website_selected,
                        'confidence': f"{log.confidence:.2f}",
                        'reason': log.reason,
                        'execution_time': f"{log.execution_time:.2f}",
                        'status': log.status,
                        'timestamp': log.timestamp.isoformat(),
                    })

            logger.info(f"Saved {len(execution_logs)} log entries to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error saving execution log: {e}")
            raise

    def generate_summary_report(
        self,
        stats: ProcessingStats,
        session_id: str,
    ) -> str:
        """
        Generate summary report

        Args:
            stats: ProcessingStats from batch processing
            session_id: Session ID for filename

        Returns:
            Path to saved report file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_report_{session_id}_{timestamp}.txt"
            filepath = self.output_dir / filename

            logger.info(f"Generating summary report: {filepath}")

            # Generate report content
            report = f"""
================================================================================
BRAND WEBSITE DETECTION - SUMMARY REPORT
================================================================================

Session ID:     {session_id}
Timestamp:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

PROCESSING RESULTS
─────────────────────────────────────────────────────────────────────────────

Total Rows:             {stats.total_rows}
Processed Rows:         {stats.processed_rows}

OUTCOMES:
  [+] Found:             {stats.found_count:>6} ({self._percentage(stats.found_count, stats.processed_rows):.1f}%)
  [!] Needs Review:      {stats.review_count:>6} ({self._percentage(stats.review_count, stats.processed_rows):.1f}%)
  [-] Not Found:         {stats.not_found_count:>6} ({self._percentage(stats.not_found_count, stats.processed_rows):.1f}%)
  [E] Errors:            {stats.error_count:>6} ({self._percentage(stats.error_count, stats.processed_rows):.1f}%)

SUCCESS RATE:           {stats.success_rate:.1f}%

PERFORMANCE
─────────────────────────────────────────────────────────────────────────────

Total Processing Time:  {stats.total_time:.2f} seconds
Average Time per Row:   {stats.average_time_per_row:.2f} seconds
Processing Rate:        {self._calculate_rate(stats.processed_rows, stats.total_time):.1f} rows/minute

EFFICIENCY
─────────────────────────────────────────────────────────────────────────────

Rows per Second:        {stats.processed_rows / stats.total_time if stats.total_time > 0 else 0:.2f}
Estimated Time for:
  1,000 rows:           {self._estimate_time(stats.average_time_per_row, 1000):.1f} minutes
  5,000 rows:           {self._estimate_time(stats.average_time_per_row, 5000):.1f} minutes
  10,000 rows:          {self._estimate_time(stats.average_time_per_row, 10000):.1f} minutes

================================================================================
"""

            # Write report
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)

            logger.info(f"Summary report saved to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
            raise

    def generate_detailed_report(
        self,
        execution_logs: List[ExecutionLog],
        stats: ProcessingStats,
        session_id: str,
    ) -> str:
        """
        Generate detailed report with all results

        Args:
            execution_logs: List of ExecutionLog entries
            stats: ProcessingStats from batch processing
            session_id: Session ID for filename

        Returns:
            Path to saved report file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"detailed_report_{session_id}_{timestamp}.txt"
            filepath = self.output_dir / filename

            logger.info(f"Generating detailed report: {filepath}")

            # Start with summary
            summary_section = f"""
================================================================================
DETAILED PROCESSING REPORT
================================================================================

Session ID:     {session_id}
Timestamp:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY STATISTICS
─────────────────────────────────────────────────────────────────────────────
Found:          {stats.found_count}
Review:         {stats.review_count}
Not Found:      {stats.not_found_count}
Errors:         {stats.error_count}
Total:          {stats.processed_rows}
Success Rate:   {stats.success_rate:.1f}%
================================================================================

DETAILED RESULTS
─────────────────────────────────────────────────────────────────────────────
"""

            # Group by status
            found_results = [log for log in execution_logs if log.status == "found"]
            review_results = [log for log in execution_logs if log.status == "needs_review"]
            not_found_results = [log for log in execution_logs if log.status == "not_found"]
            error_results = [log for log in execution_logs if log.status in ["error", "amazon_failed", "google_failed"]]

            report = summary_section

            # Add Found section
            if found_results:
                report += f"\nFOUND ({len(found_results)} results)\n"
                report += "─" * 80 + "\n"
                for log in found_results[:20]:  # Show first 20
                    report += f"Row {log.row_number}: {log.brand_name}\n"
                    report += f"  Website: {log.website_selected}\n"
                    report += f"  Confidence: {log.confidence:.1f}%\n"
                    report += f"  Time: {log.execution_time:.2f}s\n\n"
                if len(found_results) > 20:
                    report += f"... and {len(found_results) - 20} more\n\n"

            # Add Review section
            if review_results:
                report += f"\nNEEDS REVIEW ({len(review_results)} results)\n"
                report += "─" * 80 + "\n"
                for log in review_results[:20]:  # Show first 20
                    report += f"Row {log.row_number}: {log.brand_name}\n"
                    report += f"  Website: {log.website_selected}\n"
                    report += f"  Confidence: {log.confidence:.1f}%\n"
                    report += f"  Reason: {log.reason}\n\n"
                if len(review_results) > 20:
                    report += f"... and {len(review_results) - 20} more\n\n"

            # Add Not Found section
            if not_found_results:
                report += f"\nNOT FOUND ({len(not_found_results)} results)\n"
                report += "─" * 80 + "\n"
                for log in not_found_results[:10]:  # Show first 10
                    report += f"Row {log.row_number}: {log.brand_name}\n"
                    report += f"  Reason: {log.reason}\n\n"
                if len(not_found_results) > 10:
                    report += f"... and {len(not_found_results) - 10} more\n\n"

            # Add Errors section
            if error_results:
                report += f"\nERRORS ({len(error_results)} results)\n"
                report += "─" * 80 + "\n"
                for log in error_results[:10]:  # Show first 10
                    report += f"Row {log.row_number}: {log.brand_name}\n"
                    report += f"  Error: {log.reason}\n\n"
                if len(error_results) > 10:
                    report += f"... and {len(error_results) - 10} more\n\n"

            report += "\n" + "=" * 80 + "\n"

            # Write report
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)

            logger.info(f"Detailed report saved to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error generating detailed report: {e}")
            raise

    @staticmethod
    def _percentage(count: int, total: int) -> float:
        """Calculate percentage"""
        return (count / total * 100) if total > 0 else 0.0

    @staticmethod
    def _calculate_rate(rows: int, seconds: float) -> float:
        """Calculate processing rate (rows per minute)"""
        return (rows / seconds * 60) if seconds > 0 else 0.0

    @staticmethod
    def _estimate_time(avg_time_per_row: float, total_rows: int) -> float:
        """Estimate processing time in minutes"""
        return (avg_time_per_row * total_rows) / 60
