"""
Tests for base scraper abstract class and data structures.
"""
import pytest
from app.scrapers.base_scraper import (
    BaseScraper, ScrapingResult, ScrapingStatus, 
    CompetitorData, FeedbackData
)


class MockScraper(BaseScraper):
    """Mock scraper for testing."""
    
    def __init__(self, source_name: str = "mock", should_validate: bool = True):
        super().__init__(source_name)
        self.should_validate = should_validate
    
    async def scrape(self, keywords, idea_text):
        """Mock scrape implementation."""
        return ScrapingResult(
            status=ScrapingStatus.SUCCESS,
            competitors=[
                CompetitorData(
                    name="Mock Competitor",
                    description="A mock competitor",
                    source=self.source_name
                )
            ],
            feedback=[
                FeedbackData(
                    text="Mock feedback",
                    source=self.source_name
                )
            ]
        )
    
    def validate_config(self):
        """Mock validation."""
        return self.should_validate


class TestBaseScraper:
    """Test cases for BaseScraper abstract class."""
    
    def test_scraper_initialization(self):
        """Test scraper initialization."""
        scraper = MockScraper("test_source")
        
        assert scraper.get_source_name() == "test_source"
        assert scraper.max_retries == 3
        assert scraper.timeout == 30
    
    def test_scraper_configuration(self):
        """Test scraper configuration methods."""
        scraper = MockScraper()
        
        scraper.set_timeout(60)
        assert scraper.timeout == 60
        
        scraper.set_max_retries(5)
        assert scraper.max_retries == 5
    
    @pytest.mark.asyncio
    async def test_scraper_scrape_method(self):
        """Test scraper scrape method."""
        scraper = MockScraper()
        
        result = await scraper.scrape(["test"], "test idea")
        
        assert isinstance(result, ScrapingResult)
        assert result.status == ScrapingStatus.SUCCESS
        assert len(result.competitors) == 1
        assert len(result.feedback) == 1
        assert result.competitors[0].name == "Mock Competitor"
        assert result.feedback[0].text == "Mock feedback"
    
    def test_scraper_validate_config(self):
        """Test scraper configuration validation."""
        valid_scraper = MockScraper(should_validate=True)
        invalid_scraper = MockScraper(should_validate=False)
        
        assert valid_scraper.validate_config() is True
        assert invalid_scraper.validate_config() is False


class TestScrapingDataStructures:
    """Test cases for scraping data structures."""
    
    def test_competitor_data_creation(self):
        """Test CompetitorData creation."""
        competitor = CompetitorData(
            name="Test Company",
            description="A test company",
            website="https://example.com",
            estimated_users=1000,
            estimated_revenue="$1M",
            pricing_model="Freemium",
            source="test",
            source_url="https://source.com",
            confidence_score=0.8
        )
        
        assert competitor.name == "Test Company"
        assert competitor.description == "A test company"
        assert competitor.website == "https://example.com"
        assert competitor.estimated_users == 1000
        assert competitor.estimated_revenue == "$1M"
        assert competitor.pricing_model == "Freemium"
        assert competitor.source == "test"
        assert competitor.source_url == "https://source.com"
        assert competitor.confidence_score == 0.8
    
    def test_competitor_data_defaults(self):
        """Test CompetitorData with default values."""
        competitor = CompetitorData(name="Test Company")
        
        assert competitor.name == "Test Company"
        assert competitor.description is None
        assert competitor.website is None
        assert competitor.estimated_users is None
        assert competitor.estimated_revenue is None
        assert competitor.pricing_model is None
        assert competitor.source == ""
        assert competitor.source_url is None
        assert competitor.confidence_score == 0.0
    
    def test_feedback_data_creation(self):
        """Test FeedbackData creation."""
        feedback = FeedbackData(
            text="Great product!",
            sentiment="positive",
            sentiment_score=0.9,
            source="test",
            source_url="https://source.com",
            author_info={"username": "testuser"}
        )
        
        assert feedback.text == "Great product!"
        assert feedback.sentiment == "positive"
        assert feedback.sentiment_score == 0.9
        assert feedback.source == "test"
        assert feedback.source_url == "https://source.com"
        assert feedback.author_info == {"username": "testuser"}
    
    def test_feedback_data_defaults(self):
        """Test FeedbackData with default values."""
        feedback = FeedbackData(text="Test feedback")
        
        assert feedback.text == "Test feedback"
        assert feedback.sentiment is None
        assert feedback.sentiment_score is None
        assert feedback.source == ""
        assert feedback.source_url is None
        assert feedback.author_info is None
    
    def test_scraping_result_creation(self):
        """Test ScrapingResult creation."""
        competitors = [CompetitorData(name="Test Company")]
        feedback = [FeedbackData(text="Test feedback")]
        
        result = ScrapingResult(
            status=ScrapingStatus.SUCCESS,
            competitors=competitors,
            feedback=feedback,
            error_message=None,
            metadata={"test": "data"}
        )
        
        assert result.status == ScrapingStatus.SUCCESS
        assert len(result.competitors) == 1
        assert len(result.feedback) == 1
        assert result.error_message is None
        assert result.metadata == {"test": "data"}
    
    def test_scraping_result_with_error(self):
        """Test ScrapingResult with error."""
        result = ScrapingResult(
            status=ScrapingStatus.FAILED,
            competitors=[],
            feedback=[],
            error_message="Test error"
        )
        
        assert result.status == ScrapingStatus.FAILED
        assert len(result.competitors) == 0
        assert len(result.feedback) == 0
        assert result.error_message == "Test error"
    
    def test_scraping_status_enum(self):
        """Test ScrapingStatus enum values."""
        assert ScrapingStatus.SUCCESS.value == "success"
        assert ScrapingStatus.PARTIAL_SUCCESS.value == "partial_success"
        assert ScrapingStatus.FAILED.value == "failed"