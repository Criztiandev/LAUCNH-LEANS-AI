"""
Base scraper abstract class defining the interface for all scrapers.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ScrapingStatus(Enum):
    """Status of scraping operation."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


@dataclass
class CompetitorData:
    """Data structure for competitor information."""
    name: str
    description: Optional[str] = None
    website: Optional[str] = None
    estimated_users: Optional[int] = None
    estimated_revenue: Optional[str] = None
    pricing_model: Optional[str] = None
    source: str = ""
    source_url: Optional[str] = None
    confidence_score: float = 0.0


@dataclass
class FeedbackData:
    """Data structure for user feedback information."""
    text: str
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    source: str = ""
    source_url: Optional[str] = None
    author_info: Optional[Dict[str, Any]] = None


@dataclass
class ScrapingResult:
    """Result of a scraping operation."""
    status: ScrapingStatus
    competitors: List[CompetitorData]
    feedback: List[FeedbackData]
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""
    
    def __init__(self, source_name: str):
        """Initialize the scraper with a source name."""
        self.source_name = source_name
        self.max_retries = 3
        self.timeout = 30
    
    @abstractmethod
    async def scrape(self, keywords: List[str], idea_text: str) -> ScrapingResult:
        """
        Scrape data based on keywords and idea text.
        
        Args:
            keywords: List of extracted keywords from the idea
            idea_text: Original idea text for context
            
        Returns:
            ScrapingResult containing competitors and feedback data
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate that the scraper is properly configured.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    def get_source_name(self) -> str:
        """Get the name of this scraping source."""
        return self.source_name
    
    def set_timeout(self, timeout: int) -> None:
        """Set the timeout for scraping operations."""
        self.timeout = timeout
    
    def set_max_retries(self, retries: int) -> None:
        """Set the maximum number of retries for failed requests."""
        self.max_retries = retries