"""
Test integration of Product Hunt scraper with the scraping service.
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestProductHuntServiceIntegration:
    """Test Product Hunt scraper integration with scraping service."""
    
    @pytest.fixture
    def scraping_service(self):
        """Create a scraping service instance."""
        from app.services.scraping_service import ScrapingService
        return ScrapingService()
    
    @pytest.fixture
    def product_hunt_scraper(self):
        """Create a Product Hunt scraper instance with mocked config."""
        with patch.dict('sys.modules', {'app.config': MagicMock()}):
            from app.scrapers.product_hunt_scraper import ProductHuntScraper
            return ProductHuntScraper()
    
    def test_product_hunt_scraper_registration(self, scraping_service, product_hunt_scraper):
        """Test that Product Hunt scraper can be registered with the service."""
        # Initially no scrapers registered
        assert len(scraping_service.get_registered_scrapers()) == 0
        
        # Register the Product Hunt scraper
        scraping_service.register_scraper(product_hunt_scraper)
        
        # Should now have one scraper registered
        registered_scrapers = scraping_service.get_registered_scrapers()
        assert len(registered_scrapers) == 1
        assert "Product Hunt" in registered_scrapers
    
    def test_product_hunt_scraper_validation(self, scraping_service, product_hunt_scraper):
        """Test that Product Hunt scraper passes validation."""
        # Product Hunt scraper should validate successfully
        assert product_hunt_scraper.validate_config() is True
        
        # Should be able to register without issues
        scraping_service.register_scraper(product_hunt_scraper)
        assert "Product Hunt" in scraping_service.get_registered_scrapers()
    
    def test_multiple_scrapers_registration(self, scraping_service, product_hunt_scraper):
        """Test registering multiple scrapers including Product Hunt."""
        # Create a mock scraper for comparison
        mock_scraper = MagicMock()
        mock_scraper.validate_config.return_value = True
        mock_scraper.get_source_name.return_value = "Mock Scraper"
        
        # Register both scrapers
        scraping_service.register_scraper(product_hunt_scraper)
        scraping_service.register_scraper(mock_scraper)
        
        # Should have both registered
        registered_scrapers = scraping_service.get_registered_scrapers()
        assert len(registered_scrapers) == 2
        assert "Product Hunt" in registered_scrapers
        assert "Mock Scraper" in registered_scrapers
    
    def test_scraper_interface_compliance(self, product_hunt_scraper):
        """Test that Product Hunt scraper implements the required interface."""
        from app.scrapers.base_scraper import BaseScraper
        
        # Should be an instance of BaseScraper
        assert isinstance(product_hunt_scraper, BaseScraper)
        
        # Should implement required methods
        assert hasattr(product_hunt_scraper, 'scrape')
        assert hasattr(product_hunt_scraper, 'validate_config')
        assert hasattr(product_hunt_scraper, 'get_source_name')
        
        # Methods should be callable
        assert callable(product_hunt_scraper.scrape)
        assert callable(product_hunt_scraper.validate_config)
        assert callable(product_hunt_scraper.get_source_name)
        
        # Should return expected values
        assert product_hunt_scraper.get_source_name() == "Product Hunt"
        assert product_hunt_scraper.validate_config() is True