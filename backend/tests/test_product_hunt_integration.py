"""
Integration test for Product Hunt scraper to verify it can be instantiated and configured properly.
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.scrapers.base_scraper import ScrapingStatus


class TestProductHuntScraperIntegration:
    """Integration tests for ProductHuntScraper."""
    
    @pytest.fixture
    def scraper_class(self):
        """Import and return the ProductHuntScraper class with mocked dependencies."""
        # Mock the config module before importing
        with patch.dict('sys.modules', {'app.config': MagicMock()}):
            from app.scrapers.product_hunt_scraper import ProductHuntScraper
            return ProductHuntScraper
    
    @pytest.fixture
    def scraper(self, scraper_class):
        """Create a ProductHuntScraper instance for testing."""
        return scraper_class()
    
    def test_scraper_can_be_instantiated(self, scraper):
        """Test that the scraper can be instantiated without errors."""
        assert scraper is not None
        assert scraper.source_name == "Product Hunt"
        assert scraper.validate_config() is True
    
    def test_scraper_has_required_methods(self, scraper):
        """Test that the scraper implements all required methods from BaseScraper."""
        # Check that all abstract methods are implemented
        assert hasattr(scraper, 'scrape')
        assert hasattr(scraper, 'validate_config')
        assert callable(getattr(scraper, 'scrape'))
        assert callable(getattr(scraper, 'validate_config'))
    
    def test_scraper_configuration(self, scraper):
        """Test scraper configuration and settings."""
        assert scraper.base_url == "https://www.producthunt.com"
        assert scraper.search_url == "https://www.producthunt.com/search"
        assert scraper.timeout == 30  # Default timeout
        assert scraper.max_retries == 3  # Default retries
        
        # Test that configuration can be updated
        scraper.set_timeout(60)
        scraper.set_max_retries(5)
        assert scraper.timeout == 60
        assert scraper.max_retries == 5
    
    def test_scraper_headers(self, scraper):
        """Test that scraper has proper headers configured."""
        assert 'User-Agent' in scraper.headers
        assert 'Mozilla' in scraper.headers['User-Agent']  # Should look like a real browser
        assert 'Accept' in scraper.headers
        assert 'Accept-Language' in scraper.headers
    
    def test_scraper_methods_exist(self, scraper):
        """Test that all expected helper methods exist."""
        # Public methods
        assert hasattr(scraper, 'get_source_name')
        assert hasattr(scraper, 'set_timeout')
        assert hasattr(scraper, 'set_max_retries')
        
        # Private helper methods
        assert hasattr(scraper, '_search_products')
        assert hasattr(scraper, '_extract_competitor_from_card')
        assert hasattr(scraper, '_enrich_competitor_data')
        assert hasattr(scraper, '_deduplicate_competitors')
    
    def test_scraper_source_name(self, scraper):
        """Test that scraper returns correct source name."""
        assert scraper.get_source_name() == "Product Hunt"
    
    @pytest.mark.asyncio
    async def test_scrape_method_signature(self, scraper):
        """Test that scrape method has correct signature and returns proper type."""
        # This test just verifies the method can be called without actually making HTTP requests
        # We'll mock the session to avoid network calls
        
        with patch.object(scraper, 'session', None):
            # Mock the session creation and HTTP calls
            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value = mock_session
                mock_session.__aenter__ = MagicMock(return_value=mock_session)
                mock_session.__aexit__ = MagicMock(return_value=None)
                
                # Mock the get method to avoid actual HTTP calls
                mock_response = MagicMock()
                mock_response.status = 404  # This will cause the scraper to return empty results
                mock_session.get.return_value.__aenter__ = MagicMock(return_value=mock_response)
                mock_session.get.return_value.__aexit__ = MagicMock(return_value=None)
                
                # Call the scrape method
                result = await scraper.scrape(["test"], "test idea")
                
                # Verify the result structure
                assert hasattr(result, 'status')
                assert hasattr(result, 'competitors')
                assert hasattr(result, 'feedback')
                assert hasattr(result, 'metadata')
                
                # Should return a valid status
                assert result.status in [ScrapingStatus.SUCCESS, ScrapingStatus.FAILED, ScrapingStatus.PARTIAL_SUCCESS]
                
                # Should return lists
                assert isinstance(result.competitors, list)
                assert isinstance(result.feedback, list)
                
                # Should have metadata
                assert isinstance(result.metadata, dict)
                assert 'source' in result.metadata
                assert result.metadata['source'] == 'Product Hunt'