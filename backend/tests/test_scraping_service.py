"""
Tests for scraping service orchestration.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from app.services.scraping_service import ScrapingService
from app.scrapers.base_scraper import (
    BaseScraper, ScrapingResult, ScrapingStatus, 
    CompetitorData, FeedbackData
)


class MockSuccessfulScraper(BaseScraper):
    """Mock scraper that always succeeds."""
    
    def __init__(self, source_name: str, delay: float = 0.1):
        super().__init__(source_name)
        self.delay = delay
    
    async def scrape(self, keywords, idea_text):
        await asyncio.sleep(self.delay)
        return ScrapingResult(
            status=ScrapingStatus.SUCCESS,
            competitors=[
                CompetitorData(
                    name=f"{self.source_name} Competitor",
                    description=f"Competitor from {self.source_name}",
                    source=self.source_name,
                    confidence_score=0.8
                )
            ],
            feedback=[
                FeedbackData(
                    text=f"Feedback from {self.source_name}",
                    sentiment="positive",
                    source=self.source_name
                )
            ]
        )
    
    def validate_config(self):
        return True


class MockFailingScraper(BaseScraper):
    """Mock scraper that always fails."""
    
    def __init__(self, source_name: str):
        super().__init__(source_name)
    
    async def scrape(self, keywords, idea_text):
        raise Exception(f"Scraping failed for {self.source_name}")
    
    def validate_config(self):
        return True


class MockPartialScraper(BaseScraper):
    """Mock scraper that returns partial success."""
    
    def __init__(self, source_name: str):
        super().__init__(source_name)
    
    async def scrape(self, keywords, idea_text):
        return ScrapingResult(
            status=ScrapingStatus.PARTIAL_SUCCESS,
            competitors=[
                CompetitorData(
                    name=f"{self.source_name} Partial Competitor",
                    source=self.source_name
                )
            ],
            feedback=[],
            error_message="Some data could not be retrieved"
        )
    
    def validate_config(self):
        return True


class MockInvalidScraper(BaseScraper):
    """Mock scraper with invalid configuration."""
    
    def __init__(self, source_name: str):
        super().__init__(source_name)
    
    async def scrape(self, keywords, idea_text):
        return ScrapingResult(
            status=ScrapingStatus.SUCCESS,
            competitors=[],
            feedback=[]
        )
    
    def validate_config(self):
        return False


class TestScrapingService:
    """Test cases for ScrapingService."""
    
    def test_service_initialization(self):
        """Test service initialization."""
        service = ScrapingService()
        
        assert len(service.scrapers) == 0
        assert service.max_concurrent_scrapers == 6
        assert service.total_timeout == 300
    
    def test_register_valid_scraper(self):
        """Test registering a valid scraper."""
        service = ScrapingService()
        scraper = MockSuccessfulScraper("test_source")
        
        service.register_scraper(scraper)
        
        assert len(service.scrapers) == 1
        assert service.get_registered_scrapers() == ["test_source"]
    
    def test_register_invalid_scraper(self):
        """Test registering an invalid scraper."""
        service = ScrapingService()
        scraper = MockInvalidScraper("invalid_source")
        
        service.register_scraper(scraper)
        
        assert len(service.scrapers) == 0
        assert service.get_registered_scrapers() == []
    
    def test_register_multiple_scrapers(self):
        """Test registering multiple scrapers."""
        service = ScrapingService()
        
        scrapers = [
            MockSuccessfulScraper("source1"),
            MockSuccessfulScraper("source2"),
            MockSuccessfulScraper("source3")
        ]
        
        for scraper in scrapers:
            service.register_scraper(scraper)
        
        assert len(service.scrapers) == 3
        registered_names = service.get_registered_scrapers()
        assert "source1" in registered_names
        assert "source2" in registered_names
        assert "source3" in registered_names
    
    @pytest.mark.asyncio
    async def test_scrape_all_sources_success(self):
        """Test successful scraping from all sources."""
        service = ScrapingService()
        
        # Register multiple successful scrapers
        scrapers = [
            MockSuccessfulScraper("source1"),
            MockSuccessfulScraper("source2")
        ]
        
        for scraper in scrapers:
            service.register_scraper(scraper)
        
        result = await service.scrape_all_sources("Test SaaS idea", "validation_123")
        
        assert isinstance(result, dict)
        assert 'competitors' in result
        assert 'feedback' in result
        assert 'metadata' in result
        
        # Should have data from both sources
        assert len(result['competitors']) == 2
        assert len(result['feedback']) == 2
        
        # Check metadata
        metadata = result['metadata']
        assert metadata['validation_id'] == "validation_123"
        assert metadata['sources_attempted'] == 2
        assert metadata['sources_successful'] == 2
        assert metadata['sources_failed'] == 0
        assert len(metadata['successful_sources']) == 2
    
    @pytest.mark.asyncio
    async def test_scrape_all_sources_with_failures(self):
        """Test scraping with some failures."""
        service = ScrapingService()
        
        # Register mix of successful and failing scrapers
        scrapers = [
            MockSuccessfulScraper("success_source"),
            MockFailingScraper("failing_source"),
            MockPartialScraper("partial_source")
        ]
        
        for scraper in scrapers:
            service.register_scraper(scraper)
        
        result = await service.scrape_all_sources("Test idea", "validation_123")
        
        # Should still return results from successful scrapers
        assert len(result['competitors']) >= 1  # At least from successful and partial
        assert len(result['feedback']) >= 1    # At least from successful
        
        # Check metadata
        metadata = result['metadata']
        assert metadata['sources_attempted'] == 3
        assert metadata['sources_successful'] == 1
        assert metadata['sources_partial'] == 1
        assert metadata['sources_failed'] == 1
    
    @pytest.mark.asyncio
    async def test_scrape_all_sources_no_scrapers(self):
        """Test scraping with no registered scrapers."""
        service = ScrapingService()
        
        result = await service.scrape_all_sources("Test idea", "validation_123")
        
        assert len(result['competitors']) == 0
        assert len(result['feedback']) == 0
        assert 'error' in result['metadata']
        assert result['metadata']['error'] == 'No scrapers registered'
    
    @pytest.mark.asyncio
    async def test_scrape_all_sources_timeout(self):
        """Test scraping timeout handling."""
        service = ScrapingService()
        service.total_timeout = 0.1  # Very short timeout
        
        # Register scraper with longer delay than timeout
        scraper = MockSuccessfulScraper("slow_source", delay=0.2)
        service.register_scraper(scraper)
        
        result = await service.scrape_all_sources("Test idea", "validation_123")
        
        # Should return timeout result
        assert len(result['competitors']) == 0
        assert len(result['feedback']) == 0
        assert 'error' in result['metadata']
        assert 'timeout' in result['metadata']['error'].lower()
    
    @pytest.mark.asyncio
    async def test_parallel_scraping_concurrency(self):
        """Test that scrapers run in parallel."""
        service = ScrapingService()
        
        # Register multiple scrapers with delays
        scrapers = [
            MockSuccessfulScraper("source1", delay=0.1),
            MockSuccessfulScraper("source2", delay=0.1),
            MockSuccessfulScraper("source3", delay=0.1)
        ]
        
        for scraper in scrapers:
            service.register_scraper(scraper)
        
        import time
        start_time = time.time()
        
        result = await service.scrape_all_sources("Test idea", "validation_123")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # If running in parallel, total time should be close to 0.1s, not 0.3s
        assert total_time < 0.2  # Allow some overhead
        
        # Should have results from all scrapers
        assert len(result['competitors']) == 3
        assert len(result['feedback']) == 3
    
    @pytest.mark.asyncio
    async def test_data_cleaning_and_deduplication(self):
        """Test that data is cleaned and deduplicated."""
        service = ScrapingService()
        
        # Create scraper that returns duplicate data
        class DuplicateDataScraper(BaseScraper):
            def __init__(self, source_name):
                super().__init__(source_name)
            
            async def scrape(self, keywords, idea_text):
                return ScrapingResult(
                    status=ScrapingStatus.SUCCESS,
                    competitors=[
                        CompetitorData(name="Duplicate Company", source=self.source_name),
                        CompetitorData(name="DUPLICATE COMPANY", source=self.source_name),  # Same name, different case
                        CompetitorData(name="Unique Company", source=self.source_name)
                    ],
                    feedback=[
                        FeedbackData(text="Great product!", source=self.source_name),
                        FeedbackData(text="GREAT PRODUCT!", source=self.source_name),  # Same text, different case
                        FeedbackData(text="Different feedback", source=self.source_name)
                    ]
                )
            
            def validate_config(self):
                return True
        
        scraper = DuplicateDataScraper("test_source")
        service.register_scraper(scraper)
        
        result = await service.scrape_all_sources("Test idea", "validation_123")
        
        # Should have deduplicated data
        assert len(result['competitors']) == 2  # Duplicates removed
        assert len(result['feedback']) == 2     # Duplicates removed
    
    def test_create_empty_result(self):
        """Test empty result creation."""
        service = ScrapingService()
        result = service._create_empty_result()
        
        assert len(result['competitors']) == 0
        assert len(result['feedback']) == 0
        assert 'error' in result['metadata']
    
    def test_create_timeout_result(self):
        """Test timeout result creation."""
        service = ScrapingService()
        service.register_scraper(MockSuccessfulScraper("test"))
        
        from datetime import datetime
        start_time = datetime.utcnow()
        result = service._create_timeout_result(start_time)
        
        assert len(result['competitors']) == 0
        assert len(result['feedback']) == 0
        assert 'timeout' in result['metadata']['error'].lower()
        assert result['metadata']['sources_failed'] == 1
    
    def test_create_error_result(self):
        """Test error result creation."""
        service = ScrapingService()
        service.register_scraper(MockSuccessfulScraper("test"))
        
        from datetime import datetime
        start_time = datetime.utcnow()
        result = service._create_error_result("Test error", start_time)
        
        assert len(result['competitors']) == 0
        assert len(result['feedback']) == 0
        assert result['metadata']['error'] == "Test error"
        assert result['metadata']['sources_failed'] == 1