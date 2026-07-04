"""Sheet Agent - Read and write Excel/Google Sheets"""

from typing import List, Optional, Tuple
import pandas as pd
from pathlib import Path

from src.core.config import get_config
from src.core.exceptions import SheetException, SheetReadException, SheetWriteException
from src.core.models import BrandInput
from src.services.logger_service import get_logger

logger = get_logger(__name__)


class SheetAgent:
    """Handle reading and writing spreadsheet files"""

    def __init__(self):
        """Initialize sheet agent"""
        self.config = get_config()

    def read_excel(self, file_path: str) -> Tuple[List[BrandInput], pd.DataFrame]:
        """
        Read Excel file and extract brand data

        Args:
            file_path: Path to Excel file

        Returns:
            Tuple of (BrandInput list, original DataFrame)
        """
        try:
            logger.info(f"Reading Excel file: {file_path}")

            # Read Excel file
            df = pd.read_excel(file_path, engine='openpyxl')

            logger.info(f"Read {len(df)} rows from Excel")

            # Validate required columns
            required_columns = ['Amazon Product Link', 'Brand Name']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                raise SheetReadException(f"Missing required columns: {missing_columns}")

            # Create BrandInput list
            brand_inputs = []
            for idx, row in df.iterrows():
                amazon_link = str(row['Amazon Product Link']).strip() if pd.notna(row['Amazon Product Link']) else ""
                brand_name = str(row['Brand Name']).strip() if pd.notna(row['Brand Name']) else ""
                website = str(row.get('Website', '')).strip() if pd.notna(row.get('Website', '')) else ""

                if not brand_name or not amazon_link:
                    logger.warning(f"Skipping row {idx + 1}: missing brand or link")
                    continue

                # Collect additional columns
                additional_columns = {}
                for col in df.columns:
                    if col not in required_columns and col != 'Website':
                        additional_columns[col] = row[col]

                brand_input = BrandInput(
                    row_number=idx + 1,
                    amazon_link=amazon_link,
                    brand_name=brand_name,
                    website=website if website else None,
                    additional_columns=additional_columns,
                )

                brand_inputs.append(brand_input)

            logger.info(f"Parsed {len(brand_inputs)} valid rows from Excel")
            return brand_inputs, df

        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise SheetReadException(f"Failed to read Excel file: {e}")

    def write_excel(
        self,
        file_path: str,
        original_df: pd.DataFrame,
        results: dict,
    ) -> None:
        """
        Write results back to Excel file

        Args:
            file_path: Path to Excel file (will be overwritten)
            original_df: Original DataFrame
            results: Dict mapping row_number -> website_url
        """
        try:
            logger.info(f"Writing results to Excel: {file_path}")

            # Create copy of original dataframe
            df = original_df.copy()

            # Update Website column
            for row_idx, row in df.iterrows():
                row_number = row_idx + 1
                if row_number in results:
                    website = results[row_number].get('website_url')
                    if website:
                        df.at[row_idx, 'Website'] = website

            # Write to Excel
            df.to_excel(file_path, index=False, engine='openpyxl')

            logger.info(f"Successfully wrote results to {file_path}")

        except Exception as e:
            logger.error(f"Error writing Excel file: {e}")
            raise SheetWriteException(f"Failed to write Excel file: {e}")

    def read_google_sheet(self, sheet_url: str, sheet_name: Optional[str] = None) -> Tuple[List[BrandInput], pd.DataFrame]:
        """
        Read Google Sheet and extract brand data

        Args:
            sheet_url: Google Sheets URL or share link
            sheet_name: Optional sheet name (defaults to first sheet)

        Returns:
            Tuple of (BrandInput list, DataFrame)
        """
        try:
            logger.info(f"Reading Google Sheet: {sheet_url}")

            # Extract sheet ID from URL
            sheet_id = self._extract_sheet_id(sheet_url)
            if not sheet_id:
                raise SheetReadException("Invalid Google Sheets URL")

            # Construct CSV export URL
            if sheet_name:
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
            else:
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

            logger.debug(f"Fetching from: {csv_url}")

            # Read from CSV export
            df = pd.read_csv(csv_url)

            logger.info(f"Read {len(df)} rows from Google Sheet")

            # Validate required columns
            required_columns = ['Amazon Product Link', 'Brand Name']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                raise SheetReadException(f"Missing required columns: {missing_columns}")

            # Create BrandInput list
            brand_inputs = []
            for idx, row in df.iterrows():
                amazon_link = str(row['Amazon Product Link']).strip() if pd.notna(row['Amazon Product Link']) else ""
                brand_name = str(row['Brand Name']).strip() if pd.notna(row['Brand Name']) else ""
                website = str(row.get('Website', '')).strip() if pd.notna(row.get('Website', '')) else ""

                if not brand_name or not amazon_link:
                    logger.warning(f"Skipping row {idx + 1}: missing brand or link")
                    continue

                # Collect additional columns
                additional_columns = {}
                for col in df.columns:
                    if col not in required_columns and col != 'Website':
                        additional_columns[col] = row[col]

                brand_input = BrandInput(
                    row_number=idx + 1,
                    amazon_link=amazon_link,
                    brand_name=brand_name,
                    website=website if website else None,
                    additional_columns=additional_columns,
                )

                brand_inputs.append(brand_input)

            logger.info(f"Parsed {len(brand_inputs)} valid rows from Google Sheet")
            return brand_inputs, df

        except Exception as e:
            logger.error(f"Error reading Google Sheet: {e}")
            raise SheetReadException(f"Failed to read Google Sheet: {e}")

    def write_google_sheet(
        self,
        sheet_url: str,
        results: dict,
        sheet_name: Optional[str] = None,
    ) -> None:
        """
        Write results back to Google Sheet

        Note: Requires manual authentication and gspread setup

        Args:
            sheet_url: Google Sheets URL
            results: Dict mapping row_number -> result data
            sheet_name: Optional sheet name
        """
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            logger.info(f"Writing results to Google Sheet: {sheet_url}")

            # Load credentials
            creds_path = self.config.get("sheets.google_sheets_credentials_path", "./credentials.json")
            if not Path(creds_path).exists():
                raise SheetWriteException(
                    f"Google Sheets credentials not found at {creds_path}. "
                    "Please set up authentication."
                )

            # Authenticate
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
            client = gspread.authorize(creds)

            # Extract sheet ID
            sheet_id = self._extract_sheet_id(sheet_url)
            worksheet = client.open_by_key(sheet_id)

            # Get sheet
            if sheet_name:
                sheet = worksheet.worksheet(sheet_name)
            else:
                sheet = worksheet.sheet1

            # Find Website column
            headers = sheet.row_values(1)
            website_col = None
            for idx, header in enumerate(headers, 1):
                if header == 'Website':
                    website_col = idx
                    break

            if not website_col:
                raise SheetWriteException("Website column not found in Google Sheet")

            # Update cells
            for row_number, result_data in results.items():
                website = result_data.get('website_url')
                if website:
                    sheet.update_cell(row_number, website_col, website)

            logger.info(f"Successfully wrote results to Google Sheet")

        except ImportError:
            raise SheetWriteException("gspread not installed. Run: pip install gspread")
        except Exception as e:
            logger.error(f"Error writing Google Sheet: {e}")
            raise SheetWriteException(f"Failed to write Google Sheet: {e}")

    def _extract_sheet_id(self, sheet_url: str) -> Optional[str]:
        """Extract sheet ID from Google Sheets URL"""
        import re

        # Pattern: /d/{id}/ or ?usp=sharing with id before it
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', sheet_url)
        if match:
            return match.group(1)

        return None
