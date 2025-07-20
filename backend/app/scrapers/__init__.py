"""
Scrapers package for various data sources.
"""

from .base_scraper import BaseScraper, ScrapingResult, ScrapingStatus, CompetitorData, FeedbackData
from .product_hunt_scraper import ProductHuntScraper
from .reddit_scraper import RedditScraper
from .google_scraper import GoogleScraper
from .google_play_store_scraper import GooglePlayStoreScraper
from .app_store_scraper import AppStoreScraper
from .microsoft_store_scraper import MicrosoftStoreScraper

__all__ = [
    'BaseScraper',
    'ScrapingResult', 
    'ScrapingStatus',
    'CompetitorData',
    'FeedbackData',
    'ProductHuntScraper',
    'RedditScraper',
    'GoogleScraper',
    'GooglePlayStoreScraper',
    'AppStoreScraper',
    'MicrosoftStoreScraper'
]