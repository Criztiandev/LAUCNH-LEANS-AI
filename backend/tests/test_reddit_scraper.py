"""
Unit tests for Reddit scraper.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from datetime import datetime

from app.scrapers.reddit_scraper import RedditScraper
from app.scrapers.base_scraper import ScrapingStatus, CompetitorData, FeedbackData


class TestRedditScraper:
    """Test cases for Reddit scraper."""
    
    @pytest.fixture
    def scraper(self):
        """Create a Reddit scraper instance for testing."""
        return RedditScraper()
    
    @pytest.fixture
    def mock_reddit_post(self):
        """Create a mock Reddit post object."""
        post = Mock()
        post.title = "Looking for a good project management tool"
        post.selftext = "I need something that can handle team collaboration and task tracking. Any recommendations?"
        post.score = 15
        post.num_comments = 8
        post.created_utc = 1640995200  # 2022-01-01
        post.permalink = "/r/startups/comments/test123/looking_for_pm_tool/"
        post.author = Mock()
        post.author.__str__ = Mock(return_value="testuser")
        post.subreddit = Mock()
        post.subreddit.__str__ = Mock(return_value="startups")
        
        # Mock comments
        comment1 = Mock()
        comment1.body = "I really love Asana for project management. It's been great for our team."
        comment1.score = 5
        comment1.created_utc = 1640995300
        comment1.author = Mock()
        comment1.author.__str__ = Mock(return_value="commenter1")
        
        comment2 = Mock()
        comment2.body = "Trello is terrible, too basic and limited functionality."
        comment2.score = 3
        comment2.created_utc = 1640995400
        comment2.author = Mock()
        comment2.author.__str__ = Mock(return_value="commenter2")
        
        # Mock comments list with replace_more method
        comments_mock = Mock()
        comments_mock.__iter__ = Mock(return_value=iter([comment1, comment2]))
        comments_mock.__getitem__ = Mock(side_effect=lambda x: [comment1, comment2][x])
        comments_mock.replace_more = Mock()
        post.comments = comments_mock
        
        return post
    
    @pytest.fixture
    def mock_subreddit(self, mock_reddit_post):
        """Create a mock subreddit object."""
        subreddit = Mock()
        subreddit.search = Mock(return_value=[mock_reddit_post])
        return subreddit
    
    @pytest.fixture
    def mock_reddit_client(self, mock_subreddit):
        """Create a mock Reddit client."""
        reddit = Mock()
        reddit.subreddit = Mock(return_value=mock_subreddit)
        reddit.user.me = Mock(return_value=Mock())
        return reddit
    
    def test_initialization(self, scraper):
        """Test scraper initialization."""
        assert scraper.source_name == "Reddit"
        assert scraper.reddit is None
        assert len(scraper.relevant_subreddits) > 0
        assert "SaaS" in scraper.relevant_subreddits
        assert "startups" in scraper.relevant_subreddits
    
    @patch.dict('os.environ', {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    @patch('app.scrapers.reddit_scraper.praw.Reddit')
    def test_validate_config_success(self, mock_praw, scraper):
        """Test successful configuration validation."""
        mock_reddit = Mock()
        mock_reddit.user.me = Mock(return_value=Mock())
        mock_praw.return_value = mock_reddit
        
        result = scraper.validate_config()
        
        assert result is True
        mock_praw.assert_called_once()
    
    def test_validate_config_missing_env_vars(self, scraper):
        """Test configuration validation with missing environment variables."""
        with patch.dict('os.environ', {}, clear=True):
            result = scraper.validate_config()
            assert result is False
    
    @patch.dict('os.environ', {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    @patch('app.scrapers.reddit_scraper.praw.Reddit')
    def test_validate_config_api_failure(self, mock_praw, scraper):
        """Test configuration validation with API failure."""
        mock_reddit = Mock()
        mock_reddit.user.me = Mock(side_effect=Exception("API Error"))
        mock_praw.return_value = mock_reddit
        
        result = scraper.validate_config()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_scrape_invalid_config(self, scraper):
        """Test scraping with invalid configuration."""
        with patch.object(scraper, 'validate_config', return_value=False):
            result = await scraper.scrape(['project management'], 'Need a PM tool')
            
            assert result.status == ScrapingStatus.FAILED
            assert "configuration is invalid" in result.error_message
            assert len(result.competitors) == 0
            assert len(result.feedback) == 0
    
    @pytest.mark.asyncio
    @patch.dict('os.environ', {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    async def test_scrape_success(self, scraper, mock_reddit_client):
        """Test successful scraping."""
        with patch.object(scraper, 'validate_config', return_value=True):
            with patch.object(scraper, '_initialize_reddit'):
                scraper.reddit = mock_reddit_client
                
                # Mock the search method to return limited results
                with patch.object(scraper, '_search_keyword_discussions') as mock_search:
                    mock_feedback = [
                        FeedbackData(
                            text="Asana is great for project management",
                            sentiment="positive",
                            sentiment_score=0.7,
                            source="Reddit",
                            source_url="https://reddit.com/test",
                            author_info={"username": "testuser"}
                        )
                    ]
                    mock_search.return_value = mock_feedback
                    
                    result = await scraper.scrape(['project management'], 'Need a PM tool')
                    
                    assert result.status == ScrapingStatus.SUCCESS
                    assert len(result.feedback) > 0
                    assert result.metadata['source'] == 'Reddit'
    
    def test_extract_post_feedback(self, scraper, mock_reddit_post):
        """Test extracting feedback from a Reddit post."""
        feedback = scraper._extract_post_feedback(mock_reddit_post, "project management")
        
        assert len(feedback) == 1
        assert feedback[0].text.startswith("Looking for a good project management tool")
        assert feedback[0].source == "Reddit"
        assert feedback[0].source_url == "https://reddit.com/r/startups/comments/test123/looking_for_pm_tool/"
        assert feedback[0].author_info['username'] == "testuser"
        assert feedback[0].author_info['subreddit'] == "startups"
    
    def test_extract_comment_feedback(self, scraper, mock_reddit_post):
        """Test extracting feedback from Reddit comments."""
        feedback = scraper._extract_comment_feedback(mock_reddit_post, "project management")
        
        assert len(feedback) == 2
        
        # Check positive comment
        positive_feedback = next(f for f in feedback if "Asana" in f.text)
        assert positive_feedback.sentiment == "positive"
        assert positive_feedback.sentiment_score > 0
        assert positive_feedback.author_info['username'] == "commenter1"
        
        # Check negative comment
        negative_feedback = next(f for f in feedback if "Trello" in f.text)
        assert negative_feedback.sentiment == "negative"
        assert negative_feedback.sentiment_score < 0
        assert negative_feedback.author_info['username'] == "commenter2"
    
    def test_analyze_sentiment_positive(self, scraper):
        """Test sentiment analysis for positive text."""
        text = "This tool is amazing and I love using it. Great features!"
        sentiment, score = scraper._analyze_sentiment(text)
        
        assert sentiment == "positive"
        assert score > 0
    
    def test_analyze_sentiment_negative(self, scraper):
        """Test sentiment analysis for negative text."""
        text = "This is terrible and useless. Worst tool ever, hate it!"
        sentiment, score = scraper._analyze_sentiment(text)
        
        assert sentiment == "negative"
        assert score < 0
    
    def test_analyze_sentiment_neutral(self, scraper):
        """Test sentiment analysis for neutral text."""
        text = "This is a tool for project management. It has features."
        sentiment, score = scraper._analyze_sentiment(text)
        
        assert sentiment == "neutral"
        assert score == 0.0
    
    def test_deduplicate_feedback(self, scraper):
        """Test feedback deduplication."""
        feedback = [
            FeedbackData(text="This is a great tool", sentiment="positive", source="Reddit"),
            FeedbackData(text="This is a great tool", sentiment="positive", source="Reddit"),  # Duplicate
            FeedbackData(text="This   is   a   great   tool", sentiment="positive", source="Reddit"),  # Similar
            FeedbackData(text="Different feedback here", sentiment="neutral", source="Reddit")
        ]
        
        unique_feedback = scraper._deduplicate_feedback(feedback)
        
        assert len(unique_feedback) == 2
        assert "This is a great tool" in unique_feedback[0].text
        assert "Different feedback here" in unique_feedback[1].text
    
    def test_extract_competitor_mentions(self, scraper):
        """Test extracting competitor mentions from feedback."""
        feedback = [
            FeedbackData(
                text="I use Asana for project management and it works great",
                sentiment="positive",
                sentiment_score=0.7,
                source="Reddit",
                source_url="https://reddit.com/test1"
            ),
            FeedbackData(
                text="Try Trello, it's good for small teams",
                sentiment="positive",
                sentiment_score=0.5,
                source="Reddit",
                source_url="https://reddit.com/test2"
            ),
            FeedbackData(
                text="I recommend Asana, it's excellent for collaboration",
                sentiment="positive",
                sentiment_score=0.8,
                source="Reddit", 
                source_url="https://reddit.com/test3"
            )
        ]
        
        competitors = scraper._extract_competitor_mentions(feedback, ["project management"])
        
        # Debug: print what was found
        print(f"Found competitors: {[c.name for c in competitors]}")
        
        assert len(competitors) >= 1  # Should find at least Asana
        asana_competitor = next((c for c in competitors if c.name == "Asana"), None)
        assert asana_competitor is not None
        assert asana_competitor.source == "Reddit"
        assert "Mentioned" in asana_competitor.description
        assert asana_competitor.confidence_score > 0.3
    
    @pytest.mark.asyncio
    async def test_scrape_with_exception(self, scraper):
        """Test scraping with unexpected exception."""
        with patch.object(scraper, 'validate_config', side_effect=Exception("Unexpected error")):
            result = await scraper.scrape(['test'], 'test idea')
            
            assert result.status == ScrapingStatus.FAILED
            assert "Unexpected error" in result.error_message
            assert len(result.competitors) == 0
            assert len(result.feedback) == 0
    
    def test_get_source_name(self, scraper):
        """Test getting source name."""
        assert scraper.get_source_name() == "Reddit"
    
    def test_set_timeout(self, scraper):
        """Test setting timeout."""
        scraper.set_timeout(60)
        assert scraper.timeout == 60
    
    def test_set_max_retries(self, scraper):
        """Test setting max retries."""
        scraper.set_max_retries(5)
        assert scraper.max_retries == 5


@pytest.mark.integration
class TestRedditScraperIntegration:
    """Integration tests for Reddit scraper (requires actual Reddit API credentials)."""
    
    @pytest.fixture
    def scraper(self):
        """Create a Reddit scraper instance for integration testing."""
        return RedditScraper()
    
    @pytest.mark.asyncio
    async def test_real_reddit_scraping(self, scraper):
        """Test scraping with real Reddit API (requires credentials)."""
        import os
        
        if not all([
            'REDDIT_CLIENT_ID' in os.environ,
            'REDDIT_CLIENT_SECRET' in os.environ
        ]):
            pytest.skip("Reddit API credentials not available")
        
        if not scraper.validate_config():
            pytest.skip("Reddit API not properly configured")
        
        result = await scraper.scrape(['SaaS'], 'A project management tool for teams')
        
        # Should get some results if Reddit API is working
        assert result.status in [ScrapingStatus.SUCCESS, ScrapingStatus.PARTIAL_SUCCESS]
        assert result.metadata is not None
        assert 'source' in result.metadata
        assert result.metadata['source'] == 'Reddit'