"""Streamlit Web App for Brand Website Scraper"""

import asyncio
import io
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import init_config
from src.core.models import BrandInput
from src.processors.batch_processor import BatchProcessor
from src.processors.report_generator import ReportGenerator
from src.services.browser_service import get_browser_service, close_browser_service
from src.services.logger_service import LoggerService, get_logger

# Load environment variables
load_dotenv()

# Initialize logger
logger = get_logger(__name__)

# Page config
st.set_page_config(
    page_title="Brand Website Scraper",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .subheader {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)


class StreamlitBrandScraper:
    """Streamlit interface for Brand Website Scraper"""

    def __init__(self):
        """Initialize the scraper"""
        self.session_id = str(uuid4())
        self.initialized = False

    def initialize(self):
        """Initialize configuration and services"""
        if not self.initialized:
            try:
                init_config()
                LoggerService.init()
                self.initialized = True
                logger.info(f"Streamlit app initialized with session: {self.session_id}")
            except Exception as e:
                logger.error(f"Initialization error: {e}")
                st.error(f"Initialization error: {e}")

    def render_header(self):
        """Render header section"""
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(
                '<p class="main-header">🔍 Brand Website Scraper</p>',
                unsafe_allow_html=True
            )
            st.markdown(
                '<p class="subheader">Automated manufacturer website detection from Amazon products</p>',
                unsafe_allow_html=True
            )

        with col2:
            st.info(f"Session: {self.session_id[:8]}...")

    def render_sidebar(self):
        """Render sidebar configuration"""
        st.sidebar.header("⚙️ Configuration")

        workers = st.sidebar.slider(
            "Concurrent Workers",
            min_value=1,
            max_value=10,
            value=3,
            help="Number of concurrent processing workers"
        )

        enable_browser = st.sidebar.checkbox(
            "Enable Browser (Playwright)",
            value=True,
            help="Disable for testing without browser automation"
        )

        generate_report = st.sidebar.checkbox(
            "Generate Reports",
            value=True,
            help="Generate summary and detailed reports"
        )

        st.sidebar.divider()
        st.sidebar.header("📊 About")
        st.sidebar.info(
            """
            **Brand Website Scraper v1.0**

            This tool helps you:
            - Upload product lists from Amazon
            - Automatically detect brand websites
            - Verify brand information
            - Export comprehensive results

            **Features:**
            - Multi-agent orchestration
            - Real-time progress tracking
            - Error recovery & checkpoints
            - Excel export with results
            """
        )

        return workers, enable_browser, generate_report

    def render_upload_section(self):
        """Render file upload section"""
        st.header("📤 Upload Product List")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Upload Excel File")
            uploaded_file = st.file_uploader(
                "Choose an Excel file (.xlsx)",
                type=['xlsx'],
                help="Excel file with product information from Amazon"
            )

        with col2:
            st.markdown("### File Format")
            st.info(
                """
                Expected columns:
                - **ASIN** (Amazon product ID)
                - **Brand** (product brand)
                - **Amazon Link** (product URL)

                Or import sample data to test
                """
            )

        return uploaded_file

    def render_sample_data_section(self):
        """Render sample data options"""
        st.divider()
        st.subheader("Or Try with Sample Data")

        if st.button("📋 Load Sample Products", use_container_width=True):
            sample_data = {
                'ASIN': ['B001234567', 'B002345678', 'B003456789'],
                'Brand': ['TechBrand', 'SportCo', 'HomeWorks'],
                'Amazon Link': [
                    'https://amazon.com/TechBrand-Product-123/dp/B001234567',
                    'https://amazon.com/SportCo-Gear-456/dp/B002345678',
                    'https://amazon.com/HomeWorks-Tools-789/dp/B003456789'
                ]
            }
            df = pd.DataFrame(sample_data)
            st.session_state.sample_df = df
            st.success("Sample data loaded! Click 'Process Now' to get started.")

        if 'sample_df' in st.session_state:
            st.dataframe(st.session_state.sample_df, use_container_width=True)

    async def process_data(self, df, workers, enable_browser, generate_report):
        """Process the input data"""
        try:
            # Validate dataframe
            required_cols = ['ASIN', 'Brand', 'Amazon Link']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                st.error(f"Missing required columns: {', '.join(missing_cols)}")
                return None

            # Convert to BrandInput objects
            rows = []
            for idx, row in df.iterrows():
                try:
                    brand_input = BrandInput(
                        row_number=idx,
                        asin=str(row.get('ASIN', '')).strip(),
                        brand_name=str(row.get('Brand', '')).strip(),
                        amazon_link=str(row.get('Amazon Link', '')).strip(),
                    )
                    rows.append(brand_input)
                except Exception as e:
                    logger.warning(f"Skipping row {idx}: {e}")
                    continue

            if not rows:
                st.error("No valid rows to process")
                return None

            st.info(f"Loaded {len(rows)} products. Starting processing...")

            # Initialize browser if needed
            if enable_browser:
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.text("Initializing browser...")
                try:
                    await get_browser_service()
                except Exception as e:
                    logger.warning(f"Browser initialization warning: {e}")
                    st.warning(f"Browser initialization: {e}")

            # Create batch processor
            processor = BatchProcessor(max_workers=workers)

            # Process batch with progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_placeholder = st.empty()

            # Run batch processing
            execution_logs, stats, results_dict = await processor.process_batch(
                rows=rows,
                session_id=self.session_id,
                enable_progress=True,
                enable_checkpoints=True,
            )

            # Update results dataframe
            results_df = df.copy()
            for row_num, result in results_dict.items():
                if row_num < len(results_df):
                    results_df.loc[row_num, 'Website URL'] = result.get('website_url', 'N/A')
                    results_df.loc[row_num, 'Confidence'] = result.get('confidence', 0)
                    results_df.loc[row_num, 'Status'] = result.get('status', 'N/A')

            # Close browser if needed
            if enable_browser:
                try:
                    await close_browser_service()
                except Exception as e:
                    logger.warning(f"Browser close warning: {e}")

            return {
                'execution_logs': execution_logs,
                'stats': stats,
                'results_dict': results_dict,
                'results_df': results_df,
            }

        except Exception as e:
            logger.error(f"Processing error: {e}", exc_info=True)
            st.error(f"Processing error: {str(e)}")
            return None

    def render_results(self, result_data):
        """Render results section"""
        st.header("📊 Processing Results")

        stats = result_data['stats']
        execution_logs = result_data['execution_logs']
        results_df = result_data['results_df']

        # Summary statistics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Processed", stats.processed_rows)

        with col2:
            st.metric("✅ Found", stats.found_count,
                     delta=f"{stats.success_rate:.1f}%")

        with col3:
            st.metric("❓ Needs Review", stats.review_count)

        with col4:
            st.metric("❌ Not Found", stats.not_found_count)

        with col5:
            st.metric("⚠️ Errors", stats.error_count)

        # Processing time
        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Time", f"{stats.total_time:.2f}s")

        with col2:
            st.metric("Avg Time/Row", f"{stats.average_time_per_row:.2f}s")

        # Results table
        st.divider()
        st.subheader("Detailed Results")
        st.dataframe(results_df, use_container_width=True)

        # Export options
        st.divider()
        st.subheader("📥 Export Results")

        col1, col2, col3 = st.columns(3)

        # Excel export
        with col1:
            excel_buffer = io.BytesIO()
            results_df.to_excel(excel_buffer, index=False, sheet_name='Results')
            excel_buffer.seek(0)

            st.download_button(
                label="📊 Download Excel",
                data=excel_buffer,
                file_name=f"scraping_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        # CSV export
        with col2:
            csv_data = results_df.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV",
                data=csv_data,
                file_name=f"scraping_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        # Execution logs
        with col3:
            logs_json = "\n".join([str(log) for log in execution_logs])
            st.download_button(
                label="📋 Download Logs",
                data=logs_json,
                file_name=f"execution_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )

    def run(self):
        """Run the Streamlit app"""
        self.initialize()
        self.render_header()

        workers, enable_browser, generate_report = self.render_sidebar()

        uploaded_file = self.render_upload_section()
        self.render_sample_data_section()

        st.divider()
        st.header("🚀 Start Processing")

        # Determine if we have data to process
        df_to_process = None

        if uploaded_file:
            try:
                df_to_process = pd.read_excel(uploaded_file)
                st.success(f"✅ Loaded {len(df_to_process)} rows from upload")
            except Exception as e:
                st.error(f"Error reading file: {e}")
                return

        elif 'sample_df' in st.session_state:
            df_to_process = st.session_state.sample_df

        if df_to_process is not None:
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                if st.button("▶️ Process Now", use_container_width=True, type="primary"):
                    with st.spinner("Processing... This may take a few minutes."):
                        try:
                            # Run async processing
                            result = asyncio.run(
                                self.process_data(
                                    df_to_process,
                                    workers,
                                    enable_browser,
                                    generate_report
                                )
                            )

                            if result:
                                st.session_state.last_result = result
                                st.success("✅ Processing complete!")

                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                            logger.error(f"App error: {e}", exc_info=True)

            with col2:
                if st.button("🔄 Clear", use_container_width=True):
                    if 'sample_df' in st.session_state:
                        del st.session_state.sample_df
                    st.rerun()

            with col3:
                st.info(f"Workers: {workers}")

            # Display results if available
            if 'last_result' in st.session_state:
                self.render_results(st.session_state.last_result)

        else:
            st.info("👆 Please upload an Excel file or load sample data to get started")


def main():
    """Main entry point"""
    app = StreamlitBrandScraper()
    app.run()


if __name__ == "__main__":
    main()
