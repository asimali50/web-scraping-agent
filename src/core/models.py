"""Pydantic data models for the application"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BrandInput(BaseModel):
    """Input row from spreadsheet"""
    row_number: int
    amazon_link: str
    brand_name: str
    website: Optional[str] = None
    additional_columns: Dict[str, Any] = Field(default_factory=dict)


class AmazonProductData(BaseModel):
    """Extracted Amazon product metadata"""
    product_name: str
    brand: str
    category: str
    store_name: Optional[str] = None
    brand_store_url: Optional[str] = None
    manufacturer: Optional[str] = None
    official_website: Optional[str] = None
    about_section_url: Optional[str] = None
    extraction_time: float


class SearchCandidate(BaseModel):
    """Website candidate from search"""
    url: str
    title: str
    snippet: str
    source: str
    rank: int


class WebsiteAnalysis(BaseModel):
    """Analyzed website data"""
    url: str
    domain: str
    brand_mentions: int = 0
    logo_present: bool = False
    product_categories: List[str] = Field(default_factory=list)
    company_name: Optional[str] = None
    about_page_present: bool = False
    contact_page_present: bool = False
    extraction_time: float


class BrandMatch(BaseModel):
    """Final match result"""
    brand_name: str
    website_url: str
    confidence: float
    reasoning: str
    sources: List[str]
    claude_verified: bool = False
    execution_time: float
    status: str


class ExecutionLog(BaseModel):
    """Log entry for every row"""
    row_number: int
    brand_name: str
    amazon_link: Optional[str] = None
    amazon_verified: bool = False
    google_searched: bool = False
    website_selected: Optional[str] = None
    confidence: float = 0.0
    reason: str
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str


class Checkpoint(BaseModel):
    """Session checkpoint for resume support"""
    session_id: str
    last_completed_row: int
    total_rows: int
    success_count: int = 0
    failure_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class CacheEntry(BaseModel):
    """Brand cache entry"""
    brand_normalized: str
    brand_original: str
    website_url: str
    confidence: float
    source: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    search_count: int = 1
