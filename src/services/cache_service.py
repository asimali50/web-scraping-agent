import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from src.core.config import get_config
from src.core.exceptions import CacheException, DatabaseLockException
from src.core.models import CacheEntry, Checkpoint, ExecutionLog
from src.services.logger_service import get_logger
logger = get_logger(__name__)
class CacheService:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = get_config().get("cache.database_path", "./data/cache.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    def _initialize_database(self) -> None:
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS brand_cache (id INTEGER PRIMARY KEY, brand_normalized TEXT UNIQUE, brand_original TEXT, website_url TEXT, confidence REAL, source TEXT, created_at TIMESTAMP, last_updated TIMESTAMP, search_count INTEGER)""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS execution_log (id INTEGER PRIMARY KEY, row_number INTEGER, brand_name TEXT, amazon_link TEXT, amazon_verified BOOLEAN, google_searched BOOLEAN, website_selected TEXT, confidence REAL, reason TEXT, execution_time REAL, timestamp TIMESTAMP, status TEXT, session_id TEXT)""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS checkpoint (id INTEGER PRIMARY KEY, session_id TEXT UNIQUE, last_completed_row INTEGER, total_rows INTEGER, success_count INTEGER, failure_count INTEGER, created_at TIMESTAMP, last_updated TIMESTAMP)""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS error_history (id INTEGER PRIMARY KEY, session_id TEXT, row_number INTEGER, error_type TEXT, error_message TEXT, retry_count INTEGER, timestamp TIMESTAMP)""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS website_cache (id INTEGER PRIMARY KEY, url TEXT UNIQUE, domain TEXT, verified BOOLEAN, is_official BOOLEAN, product_categories TEXT, last_checked TIMESTAMP, expires_at TIMESTAMP)""")
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_brand_normalized ON brand_cache(brand_normalized)""")
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_execution_session ON execution_log(session_id)""")
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_checkpoint_session ON checkpoint(session_id)""")
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_website_domain ON website_cache(domain)""")
            conn.commit()
            conn.close()
            logger.info(f"Database initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise CacheException(f"Failed to initialize database: {e}")
    def close(self) -> None:
        """Close database connection"""
        try:
            if hasattr(self, 'db_path'):
                logger.debug(f"Database connection closed: {self.db_path}")
        except Exception as e:
            logger.warning(f"Error closing database: {e}")

    def get_cached_brand(self, brand_normalized: str) -> Optional[dict]:
        """Get cached brand result"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT brand_original, website_url, confidence, source, created_at FROM brand_cache WHERE brand_normalized = ? AND datetime(last_updated) > datetime('now', '-30 days')",
                (brand_normalized,)
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'brand_original': row[0],
                    'website_url': row[1],
                    'confidence': row[2],
                    'source': row[3],
                    'created_at': row[4],
                }
            return None
        except Exception as e:
            logger.warning(f"Error retrieving cached brand: {e}")
            return None

    def save_cached_brand(self, brand_normalized: str, brand_original: str, website_url: str, confidence: float, source: str) -> None:
        """Save brand to cache"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            now = datetime.utcnow()

            cursor.execute("""
                INSERT OR REPLACE INTO brand_cache
                (brand_normalized, brand_original, website_url, confidence, source, created_at, last_updated, search_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, (
                    SELECT COALESCE(search_count + 1, 1) FROM brand_cache WHERE brand_normalized = ?
                ))
            """, (brand_normalized, brand_original, website_url, confidence, source, now, now, brand_normalized))

            conn.commit()
            conn.close()
            logger.debug(f"Cached brand: {brand_original} -> {website_url}")
        except Exception as e:
            logger.warning(f"Error caching brand: {e}")

    def save_execution_log(self, log: ExecutionLog, session_id: str) -> None:
        """Save execution log to database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO execution_log
                (row_number, brand_name, amazon_link, amazon_verified, google_searched, website_selected, confidence, reason, execution_time, timestamp, status, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log.row_number,
                log.brand_name,
                log.amazon_link,
                log.amazon_verified,
                log.google_searched,
                log.website_selected,
                log.confidence,
                log.reason,
                log.execution_time,
                log.timestamp,
                log.status,
                session_id
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Error saving execution log: {e}")
