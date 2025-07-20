"""
Unit tests for Google scraper.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import json
import os

from app.scrapers.google_scraper import GoogleScraper
from app.scrapers.base_scraper import ScrapingStatus, CompetitorData, FeedbackData


class TestGoogleScraper:
    """Test cases for Google scraper."""
    
    @pytest.fixture
    def scraper(self):
        """Create a Google scraper instance for testing."""
        return GoogleScraper()
    
    @pytest.fixture
    def mock_search_results(self):
        """Create mock search results for testing."""
        return {
            "query": "project management software",
            "organic_results": [
                {
                    "title": "Asana | Work Management Platform for Teams",
                    "link": "https://asana.com/",
                    "snippet": "Asana is the work management platform teams use to stay focused on the goals, projects, and daily tasks that grow business."
                },
                {
                    "title": "Monday.com: Work OS for Any Workflow",
                    "link": "https://monday.com/",
                    "snippet": "monday.com Work OS is the project management software that helps you and your team plan, execute, and track projects and workflows in one collaborative space."
                },
                {
                    "title": "Trello vs Asana: Which Project Management Tool is Better?",
                    "link": "https://www.example.com/trello-vs-asana",
                    "snippet": "Compare Trello and Asana to find the best project management tool for your team. Trello offers a visual Kanban approach while Asana provides more comprehensive features."
                },
                {
                    "title": "What is Project Management Software? Definition and Guide",
                    "link": "https://www.example.com/what-is-pm-software",
                    "snippet": "Project management software helps teams plan, organize, and manage their work. Learn about different types and features of PM tools."
                }
            ],
            "featured_snippet": "The best project management software includes Asana, Monday.com, ClickUp, Trello, and Jira. These tools help teams organize tasks, track progress, and collaborate effectively.",
            "knowledge_panel": None,
            "related_searches": [
                "best project management software",
                "free project management tools",
                "project management software comparison",
                "asana vs monday"
            ]
        }
    
    def test_initialization(self, scraper):
        """Test scraper initialization."""
        assert scraper.source_name == "Google"
        assert scraper.base_url == "https://www.google.com/search"
        assert len(scraper.user_agents) > 0
        assert isinstance(scraper.competitor_patterns, list)
    
    def test_generate_search_queries(self, scraper):
        """Test search query generation."""
        keywords = ["project management", "team collaboration", "task tracking"]
        idea_text = "A project management tool for remote teams to track tasks and collaborate effectively."
        
        queries = scraper._generate_search_queries(keywords, idea_text)
        
        assert len(queries) > 0
        assert "project management software" in queries
        assert "team collaboration tool" in queries
        assert any("alternatives" in q for q in queries)
        assert any("best" in q for q in queries)
    
    def test_extract_product_type(self, scraper):
        """Test product type extraction."""
        idea_text = "A project management software for remote teams to track tasks and collaborate effectively."
        keywords = ["project management", "team collaboration", "task tracking"]
        
        product_type = scraper._extract_product_type(idea_text, keywords)
        
        assert product_type == "project management"
    
    def test_is_likely_competitor(self, scraper):
        """Test competitor identification."""
        # Positive case - likely competitor
        assert scraper._is_likely_competitor(
            "Asana | Work Management Platform",
            "Asana is the work management platform teams use to stay focused on goals and tasks.",
            "project management software"
        ) is True
        
        # Negative case - not a competitor
        assert scraper._is_likely_competitor(
            "What is Project Management? Definition and Guide",
            "Learn about project management methodologies and best practices.",
            "project management guide"
        ) is False
    
    def test_extract_company_name(self, scraper):
        """Test company name extraction."""
        # Test with standard format
        assert scraper._extract_company_name(
            "Asana | Work Management Platform",
            "https://asana.com/"
        ) == "Asana"
        
        # Test with domain extraction
        assert scraper._extract_company_name(
            "Work Management Platform for Teams",
            "https://monday.com/"
        ) == "Monday"
    
    def test_calculate_competitor_confidence(self, scraper):
        """Test competitor confidence calculation."""
        # High confidence case
        high_confidence = scraper._calculate_competitor_confidence(
            "Asana vs Monday.com: Which is Better?",
            "Compare Asana and Monday.com project management tools.",
            "project management software alternatives"
        )
        assert high_confidence > 0.7
        
        # Lower confidence case
        lower_confidence = scraper._calculate_competitor_confidence(
            "Project Management Tools",
            "Find the right project management tool for your team.",
            "project management software"
        )
        assert lower_confidence < high_confidence
    
    def test_extract_pricing_model(self, scraper):
        """Test pricing model extraction."""
        assert scraper._extract_pricing_model(
            "Offers both free and premium plans with advanced features."
        ) == "Freemium"
        
        assert scraper._extract_pricing_model(
            "Monthly subscription starting at $9.99 per user."
        ) == "Subscription"
        
        assert scraper._extract_pricing_model(
            "Free to use with unlimited projects."
        ) == "Free"
    
    def test_contains_feedback_indicators(self, scraper):
        """Test feedback indicator detection."""
        assert scraper._contains_feedback_indicators(
            "Asana Review 2023",
            "Our team's experience using Asana for project management."
        ) is True
        
        assert scraper._contains_feedback_indicators(
            "Project Management Definition",
            "What is project management and why is it important?"
        ) is False
    
    def test_analyze_sentiment(self, scraper):
        """Test sentiment analysis."""
        # Positive sentiment
        sentiment, score = scraper._analyze_sentiment(
            "Asana is a great tool with excellent features. We love using it for our team projects."
        )
        assert sentiment == "positive"
        assert score > 0
        
        # Negative sentiment
        sentiment, score = scraper._analyze_sentiment(
            "Trello is terrible for complex projects. We had many issues with its limited functionality."
        )
        assert sentiment == "negative"
        assert score < 0
        
        # Neutral sentiment
        sentiment, score = scraper._analyze_sentiment(
            "Project management tools help teams organize tasks and track progress."
        )
        assert sentiment == "neutral"
        assert score == 0.0
    
    def test_deduplicate_competitors(self, scraper):
        """Test competitor deduplication."""
        competitors = [
            CompetitorData(
                name="Asana",
                description="Work management platform",
                website="https://asana.com",
                source="Google",
                source_url="https://example.com/1",
                confidence_score=0.8
            ),
            CompetitorData(
                name="asana",  # Same name, different case
                description="Project management tool",
                website="https://asana.com",
                source="Google",
                source_url="https://example.com/2",
                confidence_score=0.7
            ),
            CompetitorData(
                name="Monday",
                description="Work OS platform",
                website="https://monday.com",
                source="Google",
                source_url="https://example.com/3",
                confidence_score=0.9
            )
        ]
        
        unique_competitors = scraper._deduplicate_competitors(competitors)
        
        assert len(unique_competitors) == 2
        # Should keep the one with higher confidence
        asana = next(c for c in unique_competitors if c.name.lower() == "asana")
        assert asana.confidence_score == 0.8
    
    def test_deduplicate_feedback(self, scraper):
        """Test feedback deduplication."""
        feedback = [
            FeedbackData(
                text="Asana is a great tool for project management.",
                sentiment="positive",
                sentiment_score=0.7,
                source="Google",
                source_url="https://example.com/1"
            ),
            FeedbackData(
                text="Asana   is a   great tool for project management.",  # Same text with different spacing
                sentiment="positive",
                sentiment_score=0.7,
                source="Google",
                source_url="https://example.com/2"
            ),
            FeedbackData(
                text="Monday.com offers better visualization features.",
                sentiment="positive",
                sentiment_score=0.6,
                source="Google",
                source_url="https://example.com/3"
            )
        ]
        
        unique_feedback = scraper._deduplicate_feedback(feedback)
        
        assert len(unique_feedback) == 2
    
    @pytest.mark.asyncio
    async def test_extract_competitors_from_search_results(self, scraper, mock_search_results):
        """Test extracting competitors from search results."""
        competitors = scraper._extract_competitors(mock_search_results, "project management software")
        
        assert len(competitors) >= 2
        
        # Check for specific competitors
        competitor_names = [c.name.lower() for c in competitors]
        assert "asana" in competitor_names
        assert "monday" in competitor_names
    
    @pytest.mark.asyncio
    async def test_extract_feedback_from_search_results(self, scraper, mock_search_results):
        """Test extracting feedback from search results."""
        feedback = scraper._extract_feedback(mock_search_results, "project management software")
        
        assert len(feedback) >= 1
        
        # Featured snippet should be included as feedback
        assert any("best project management software" in f.text.lower() for f in feedback)
    
    @pytest.mark.asyncio
    @patch('app.scrapers.google_scraper.GoogleScraper._execute_search')
    async def test_scrape_success(self, mock_execute_search, scraper, mock_search_results):
        """Test successful scraping."""
        # Setup mock
        mock_execute_search.return_value = mock_search_results
        
        # Execute scrape
        result = await scraper.scrape(
            ["project management", "team collaboration", "task tracking"],
            "A project management tool for remote teams to track tasks and collaborate effectively."
        )
        
        # Verify results
        assert result.status in [ScrapingStatus.SUCCESS, ScrapingStatus.PARTIAL_SUCCESS]
        assert len(result.competitors) > 0
        assert len(result.feedback) > 0
        assert "keywords_searched" in result.metadata
        assert result.metadata["source"] == "Google"
    
    @pytest.mark.asyncio
    @patch('app.scrapers.google_scraper.GoogleScraper._execute_search')
    async def test_scrape_with_exception(self, mock_execute_search, scraper):
        """Test scraping with exception."""
        # Setup mock to raise exception
        mock_execute_search.side_effect = Exception("Search failed")
        
        # Execute scrape
        result = await scraper.scrape(
            ["project management"],
            "A project management tool"
        )
        
        # Verify results
        assert result.status == ScrapingStatus.FAILED
        assert len(result.competitors) == 0
        assert len(result.feedback) == 0
        assert "Search failed" in result.error_message


@pytest.mark.integration
class TestGoogleScraperIntegration:
    """Integration tests for Google scraper (requires internet connection)."""
    
    @pytest.fixture
    def scraper(self):
        """Create a Google scraper instance for integration testing."""
        return GoogleScraper()
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.environ.get('SKIP_EXTERNAL_API_TESTS') == 'true',
                       reason="Skipping tests that require external API calls")
    async def test_real_google_search(self, scraper):
        """Test scraping with real Google search (may be rate limited)."""
        # Use a simple, non-controversial query to avoid issues
        result = await scraper.scrape(
            ["weather app"],
            "A weather forecasting application for mobile devices"
        )
        
        # Should get some results if Google search is working and not blocked
        # But we don't assert success since Google might block the request
        assert result.metadata is not None
        assert "source" in result.metadata
        assert result.metadata["source"] == "Google"