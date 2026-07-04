"""Custom exceptions for the application"""


class BrandScraperException(Exception):
    """Base exception for all scraper errors"""
    pass


class AmazonException(BrandScraperException):
    """Amazon-related exceptions"""
    pass


class AmazonTimeoutException(AmazonException):
    """Amazon page load timeout"""
    pass


class AmazonProductNotFound(AmazonException):
    """Product not found on Amazon"""
    pass


class BrandMismatchException(AmazonException):
    """Brand name doesn't match expected brand"""
    pass


class GoogleException(BrandScraperException):
    """Google search exceptions"""
    pass


class GoogleTimeoutException(GoogleException):
    """Google search timeout"""
    pass


class GoogleBlockedException(GoogleException):
    """Google blocked the request (CAPTCHA, etc.)"""
    pass


class WebsiteException(BrandScraperException):
    """Website verification exceptions"""
    pass


class WebsiteTimeoutException(WebsiteException):
    """Website load timeout"""
    pass


class WebsiteParseException(WebsiteException):
    """Failed to parse website content"""
    pass


class BrowserException(BrandScraperException):
    """Browser-related exceptions"""
    pass


class BrowserLaunchException(BrowserException):
    """Failed to launch browser"""
    pass


class BrowserConnectionException(BrowserException):
    """Lost connection to browser"""
    pass


class CacheException(BrandScraperException):
    """Cache/database exceptions"""
    pass


class DatabaseLockException(CacheException):
    """Database is locked"""
    pass


class ConfigException(BrandScraperException):
    """Configuration loading exceptions"""
    pass


class SheetException(BrandScraperException):
    """Spreadsheet operations exceptions"""
    pass


class SheetReadException(SheetException):
    """Failed to read spreadsheet"""
    pass


class SheetWriteException(SheetException):
    """Failed to write to spreadsheet"""
    pass


class TimeBudgetException(BrandScraperException):
    """Exceeded time budget for operation"""
    pass
