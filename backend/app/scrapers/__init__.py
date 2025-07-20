"""
Scrapers package for various data sources.
"""

from .base_scraper import BaseScraper, ScrapingResult, ScrapingStatus, CompetitorData, FeedbackData
from .product_hunt_scraper import ProductHuntScraper
from .google_play_store_scraper import GooglePlayStoreScraper

__all__ = [
    'BaseScraper',
    'ScrapingResult', 
    'ScrapingStatus',
    'CompetitorData',
    'FeedbackData',
    'ProductHuntScraper',
    'GooglePlayStoreScraper'
]