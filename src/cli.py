"""CLI Interface - Command-line interface for the application"""

import asyncio
import argparse
from pathlib import Path
from uuid import uuid4

from src.core.config import init_config
from src.processors.batch_processor import BatchProcessor
from src.processors.report_generator import ReportGenerator
from src.services.browser_service import get_browser_service, close_browser_service
from src.services.logger_service import LoggerService, get_logger

logger = get_logger(__name__)


class CLI:
    """Command-line interface"""

    def __init__(self):
        """Initialize CLI"""
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            prog='brand-website-scraper',
            description='Automated brand website detection from Amazon products',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Process Excel file
  python -m src.cli --input products.xlsx --workers 3

  # Process Google Sheet
  python -m src.cli --sheet "https://docs.google.com/spreadsheets/d/..." --workers 5

  # Process with custom output
  python -m src.cli --input products.xlsx --output results.xlsx

  # Show version
  python -m src.cli --version
            """
        )

        # Input options
        input_group = parser.add_mutually_exclusive_group(required=True)
        input_group.add_argument(
            '-i', '--input',
            type=str,
            help='Path to input Excel file (.xlsx)'
        )
        input_group.add_argument(
            '-s', '--sheet',
            type=str,
            help='Google Sheets URL or share link'
        )

        # Processing options
        parser.add_argument(
            '-w', '--workers',
            type=int,
            default=3,
            help='Number of concurrent workers (default: 3)'
        )

        # Output options
        parser.add_argument(
            '-o', '--output',
            type=str,
            help='Path to output file (defaults to input_results.xlsx)'
        )
        parser.add_argument(
            '--logs-dir',
            type=str,
            default='./logs',
            help='Directory for log files (default: ./logs)'
        )

        # Feature options
        parser.add_argument(
            '--skip-browser',
            action='store_true',
            help='Skip browser initialization (for testing)'
        )
        parser.add_argument(
            '--report',
            action='store_true',
            default=True,
            help='Generate summary report (default: True)'
        )
        parser.add_argument(
            '--detailed-report',
            action='store_true',
            help='Generate detailed report with all results'
        )

        # Misc options
        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s 1.0.0'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose logging'
        )

        return parser

    async def run(self, args) -> int:
        """
        Run the application

        Args:
            args: Parsed command-line arguments

        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            # Initialize config
            init_config()
            LoggerService.init()

            session_id = str(uuid4())
            logger.info(f"Starting session: {session_id}")

            # Display banner
            self._print_banner()

            # Validate inputs
            if args.input and not Path(args.input).exists():
                logger.error(f"Input file not found: {args.input}")
                print(f"Error: Input file not found: {args.input}")
                return 1

            # Initialize batch processor
            processor = BatchProcessor(max_workers=args.workers)
            logger.info(f"Batch processor initialized with {args.workers} workers")

            # Process input
            if args.input:
                print(f"\nProcessing Excel file: {args.input}")
                logger.info(f"Processing Excel file: {args.input}")
                stats = await self._process_excel(
                    processor,
                    args.input,
                    session_id,
                    args.output,
                    args.skip_browser,
                )
            else:
                print(f"\nProcessing Google Sheet: {args.sheet}")
                logger.info(f"Processing Google Sheet: {args.sheet}")
                stats = await self._process_google_sheet(
                    processor,
                    args.sheet,
                    session_id,
                    args.skip_browser,
                )

            # Generate reports
            if args.report or args.detailed_report:
                self._generate_reports(
                    stats,
                    session_id,
                    args.logs_dir,
                    args.report,
                    args.detailed_report,
                )

            # Display summary
            self._print_summary(stats)

            logger.info(f"Session {session_id} completed successfully")
            print(f"\n[OK] Processing complete! Session ID: {session_id}")

            return 0

        except KeyboardInterrupt:
            logger.warning("Interrupted by user")
            print("\n\nInterrupted by user")
            return 130
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            print(f"\n[ERROR] Error: {e}")
            return 1

    async def _process_excel(
        self,
        processor: BatchProcessor,
        input_file: str,
        session_id: str,
        output_file: str,
        skip_browser: bool,
    ):
        """Process Excel file"""
        try:
            if not skip_browser:
                await get_browser_service()

            stats = await processor.process_excel(
                input_file,
                session_id,
                output_file,
            )

            if not skip_browser:
                await close_browser_service()

            return stats

        except Exception as e:
            logger.error(f"Error processing Excel: {e}")
            raise

    async def _process_google_sheet(
        self,
        processor: BatchProcessor,
        sheet_url: str,
        session_id: str,
        skip_browser: bool,
    ):
        """Process Google Sheet"""
        try:
            if not skip_browser:
                await get_browser_service()

            stats = await processor.process_google_sheet(
                sheet_url,
                session_id,
            )

            if not skip_browser:
                await close_browser_service()

            return stats

        except Exception as e:
            logger.error(f"Error processing Google Sheet: {e}")
            raise

    def _generate_reports(
        self,
        stats,
        session_id: str,
        logs_dir: str,
        summary: bool,
        detailed: bool,
    ) -> None:
        """Generate reports"""
        try:
            reporter = ReportGenerator(logs_dir)

            if summary:
                summary_file = reporter.generate_summary_report(
                    stats,
                    session_id,
                )
                print(f"Summary report: {summary_file}")

            if detailed:
                detailed_file = reporter.generate_detailed_report(
                    [],
                    stats,
                    session_id,
                )
                print(f"Detailed report: {detailed_file}")

        except Exception as e:
            logger.warning(f"Error generating reports: {e}")

    @staticmethod
    def _print_banner() -> None:
        """Print application banner"""
        banner = """
================================================================================
                   BRAND WEBSITE SCRAPER v1.0.0
                 Automated Manufacturer Website Detection
================================================================================
        """
        print(banner)

    @staticmethod
    def _print_summary(stats) -> None:
        """Print processing summary"""
        summary = f"""
================================================================================
                          PROCESSING SUMMARY
================================================================================

  Total Rows:              {stats.processed_rows:>6}
  Found:                   {stats.found_count:>6}  ({stats.success_rate:>5.1f}%)
  Needs Review:            {stats.review_count:>6}
  Not Found:               {stats.not_found_count:>6}
  Errors:                  {stats.error_count:>6}

  Total Time:              {stats.total_time:>6.2f}s
  Average Time/Row:        {stats.average_time_per_row:>6.2f}s
  Processing Rate:         {stats.processed_rows / stats.total_time * 60:>6.1f} rows/minute

================================================================================
        """
        print(summary)


async def main():
    """Main entry point"""
    cli = CLI()
    args = cli.parser.parse_args()
    exit_code = await cli.run(args)
    return exit_code


def cli_main():
    """Synchronous wrapper for CLI main"""
    try:
        exit_code = asyncio.run(main())
        return exit_code
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        return 130


if __name__ == '__main__':
    exit_code = cli_main()
    exit(exit_code)
