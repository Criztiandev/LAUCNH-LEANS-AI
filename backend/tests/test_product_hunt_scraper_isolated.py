"""
Isolated unit tests for Product Hunt scraper without config dependencies.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
from bs4 import BeautifulSoup
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import directly without config dependencies
from app.scrapers.base_scraper import ScrapingStatus, CompetitorData, ScrapingResult


class TestProductHuntScraperIsolated:
    """Isolated test cases for ProductHuntScraper."""
    
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
    
    @pytest.fixture
    def mock_html_search_results(self):
        """Mock HTML content for search results."""
        return """
        <html>
            <body>
                <div class="styles_item__Dk_nz">
                    <a class="styles_title__HzPeb" href="/posts/test-product-1">Test SaaS Tool</a>
                    <div class="color-lighter-grey fontSize-mobile-12 fontSize-desktop-16 fontSize-tablet-16 fontSize-widescreen-16 fontWeight-400 noOfLines-2">A great SaaS tool for productivity</div>
                    <div class="color-lighter-grey fontSize-12 fontWeight-600 noOfLines-undefined">150</div>
                    <a class="styles_externalLinkIcon__vjPDi" href="/posts/test-product-1/redirect"></a>
                    <a href="/posts/test-product-1" aria-label="Test SaaS Tool"></a>
                </div>
                <div class="styles_item__Dk_nz">
                    <a class="styles_title__HzPeb" href="/posts/test-product-2">Another Tool</a>
                    <div class="color-lighter-grey fontSize-mobile-12 fontSize-desktop-16 fontSize-tablet-16 fontSize-widescreen-16 fontWeight-400 noOfLines-2">Another productivity tool</div>
                    <div class="color-lighter-grey fontSize-12 fontWeight-600 noOfLines-undefined">75</div>
                    <a class="styles_externalLinkIcon__vjPDi" href="/posts/test-product-2/redirect"></a>
                    <a href="/posts/test-product-2" aria-label="Another Tool"></a>
                </div>
            </body>
        </html>
        """
    
    @pytest.fixture
    def mock_html_product_detail(self):
        """Mock HTML content for product detail page."""
        return """
        <html>
            <body>
                <div class="product-detail">
                    <h1>Test SaaS Tool</h1>
                    <div class="product-description-detail">
                        A comprehensive SaaS tool for team productivity and collaboration
                    </div>
                    <a href="https://example.com" class="website-link">Visit Website</a>
                </div>
            </body>
        </html>
        """
    
    def test_init(self, scraper):
        """Test scraper initialization."""
        assert scraper.source_name == "Product Hunt"
        assert scraper.base_url == "https://www.producthunt.com"
        assert scraper.search_url == "https://www.producthunt.com/search"
        assert "User-Agent" in scraper.headers
    
    def test_validate_config(self, scraper):
        """Test configuration validation."""
        assert scraper.validate_config() is True
    
    @pytest.mark.asyncio
    async def test_scrape_success(self, scraper, mock_html_search_results):
        """Test successful scraping operation."""
        # Mock aiohttp session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=mock_html_search_results)
        
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_response
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await scraper.scrape(["productivity", "saas"], "A productivity SaaS tool")
        
        assert result.status == ScrapingStatus.SUCCESS
        assert len(result.competitors) > 0
        assert result.competitors[0].name == "Test SaaS Tool"
        assert result.competitors[0].source == "Product Hunt"
        assert result.metadata["keywords_searched"] == ["productivity", "saas"]
    
    @pytest.mark.asyncio
    async def test_scrape_no_results(self, scraper):
        """Test scraping when no results are found."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html><body></body></html>")
        
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_response
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await scraper.scrape(["nonexistent"], "A nonexistent tool")
        
        assert result.status == ScrapingStatus.FAILED
        assert len(result.competitors) == 0
    
    @pytest.mark.asyncio
    async def test_scrape_http_error(self, scraper):
        """Test scraping when HTTP request fails."""
        mock_response = AsyncMock()
        mock_response.status = 404
        
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_response
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await scraper.scrape(["test"], "A test tool")
        
        assert result.status == ScrapingStatus.FAILED
        assert len(result.competitors) == 0
    
    @pytest.mark.asyncio
    async def test_scrape_exception_handling(self, scraper):
        """Test scraping when an exception occurs."""
        mock_session = AsyncMock()
        mock_session.get.side_effect = Exception("Network error")
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await scraper.scrape(["test"], "A test tool")
        
        assert result.status == ScrapingStatus.FAILED
        assert len(result.competitors) == 0
        assert result.error_message is not None
        assert "Network error" in result.error_message
    
    @pytest.mark.asyncio
    async def test_search_products(self, scraper, mock_html_search_results):
        """Test the _search_products method."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=mock_html_search_results)
        
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_response
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        scraper.session = mock_session
        
        competitors = await scraper._search_products("productivity")
        
        assert len(competitors) == 2
        assert competitors[0].name == "Test SaaS Tool"
        assert competitors[0].description == "A great SaaS tool for productivity"
        assert competitors[0].estimated_users == 1500  # 150 votes * 10
        assert competitors[1].name == "Another Tool"
        assert competitors[1].estimated_users == 750  # 75 votes * 10
    
    def test_extract_competitor_from_card(self, scraper):
        """Test extracting competitor data from HTML card."""
        html = """
        <div class="styles_item__Dk_nz">
            <a class="styles_title__HzPeb" href="/posts/test-product">Amazing SaaS</a>
            <div class="color-lighter-grey fontSize-mobile-12 fontSize-desktop-16 fontSize-tablet-16 fontSize-widescreen-16 fontWeight-400 noOfLines-2">The best productivity tool ever</div>
            <div class="color-lighter-grey fontSize-12 fontWeight-600 noOfLines-undefined">200</div>
            <a class="styles_externalLinkIcon__vjPDi" href="/posts/test-product/redirect"></a>
            <a href="/posts/test-product" aria-label="Amazing SaaS"></a>
        </div>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        card = soup.find('div', class_='styles_item__Dk_nz')
        
        competitor = scraper._extract_competitor_from_card(card, "productivity")
        
        assert competitor is not None
        assert competitor.name == "Amazing SaaS"
        assert competitor.description == "The best productivity tool ever"
        assert competitor.estimated_users == 2000  # 200 votes * 10
        assert competitor.source == "Product Hunt"
        assert competitor.source_url == "https://www.producthunt.com/posts/test-product"
        assert competitor.confidence_score == 0.8
    
    def test_extract_competitor_from_card_minimal_data(self, scraper):
        """Test extracting competitor data with minimal information."""
        html = """
        <div class="styles_item__Dk_nz">
            <a class="styles_title__HzPeb" href="/posts/minimal-product">Minimal Tool</a>
        </div>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        card = soup.find('div', class_='styles_item__Dk_nz')
        
        competitor = scraper._extract_competitor_from_card(card, "test")
        
        assert competitor is not None
        assert competitor.name == "Minimal Tool"
        assert competitor.description is None
        assert competitor.estimated_users is None
        assert competitor.source_url is None  # No aria-label link in minimal case
    
    def test_extract_competitor_from_card_invalid(self, scraper):
        """Test extracting competitor data from invalid card."""
        html = "<div></div>"
        
        soup = BeautifulSoup(html, 'html.parser')
        card = soup.find('div')
        
        competitor = scraper._extract_competitor_from_card(card, "test")
        
        assert competitor is None
    
    @pytest.mark.asyncio
    async def test_enrich_competitor_data(self, scraper, mock_html_product_detail):
        """Test enriching competitor data with additional details."""
        competitor = CompetitorData(
            name="Test Tool",
            description="Basic description",
            source="Product Hunt",
            source_url="https://www.producthunt.com/posts/test-tool",
            estimated_users=1000,
            confidence_score=0.7
        )
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=mock_html_product_detail)
        
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_response
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        scraper.session = mock_session
        
        await scraper._enrich_competitor_data(competitor)
        
        assert competitor.website == "https://example.com"
        assert competitor.estimated_revenue == "$10K+ ARR"  # Based on 1000 users
        assert competitor.confidence_score == 0.9  # Increased after enrichment
    
    @pytest.mark.asyncio
    async def test_enrich_competitor_data_no_url(self, scraper):
        """Test enriching competitor data when no source URL is available."""
        competitor = CompetitorData(
            name="Test Tool",
            source="Product Hunt",
            source_url=None
        )
        
        original_confidence = competitor.confidence_score
        
        await scraper._enrich_competitor_data(competitor)
        
        # Should not change anything if no URL
        assert competitor.confidence_score == original_confidence
        assert competitor.website is None
    
    def test_deduplicate_competitors(self, scraper):
        """Test deduplication of competitors."""
        competitors = [
            CompetitorData(name="Test Tool", source="Product Hunt"),
            CompetitorData(name="test tool", source="Product Hunt"),  # Duplicate (case insensitive)
            CompetitorData(name="Another Tool", source="Product Hunt"),
            CompetitorData(name="Test Tool Pro", source="Product Hunt"),  # Similar but different
            CompetitorData(name="Different Tool", source="Product Hunt"),
        ]
        
        unique_competitors = scraper._deduplicate_competitors(competitors)
        
        # Should remove the exact duplicate but keep similar names
        assert len(unique_competitors) == 4
        names = [c.name for c in unique_competitors]
        assert "Test Tool" in names
        assert "test tool" not in names  # Duplicate removed
        assert "Another Tool" in names
        assert "Test Tool Pro" in names
        assert "Different Tool" in names
    
    @pytest.mark.asyncio
    async def test_rate_limiting_delays(self, scraper, mock_html_search_results):
        """Test that scraper includes delays to respect rate limits."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=mock_html_search_results)
        
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_response
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session), \
             patch('asyncio.sleep') as mock_sleep:
            
            await scraper.scrape(["keyword1", "keyword2"], "Test idea")
            
            # Should have called sleep between keyword searches
            assert mock_sleep.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_session_cleanup(self, scraper):
        """Test that session is properly cleaned up."""
        mock_session = AsyncMock()
        mock_session.get.side_effect = Exception("Test error")
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await scraper.scrape(["test"], "Test idea")
        
        # Session should be closed and set to None
        mock_session.close.assert_called_once()
        assert scraper.session is None