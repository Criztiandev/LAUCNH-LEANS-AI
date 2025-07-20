"""
Tests for data cleaning and deduplication utilities.
"""
import pytest
from app.utils.data_cleaner import DataCleaner
from app.scrapers.base_scraper import CompetitorData, FeedbackData


class TestDataCleaner:
    """Test cases for DataCleaner."""
    
    def test_clean_competitors_basic(self):
        """Test basic competitor cleaning."""
        competitors = [
            CompetitorData(
                name="  Test Company  ",
                description="A great software company",
                website="https://example.com",
                estimated_users=1000,
                confidence_score=0.8,
                source="test"
            )
        ]
        
        cleaned = DataCleaner.clean_competitors(competitors)
        
        assert len(cleaned) == 1
        assert cleaned[0].name == "Test Company"
        assert cleaned[0].description == "A great software company"
        assert cleaned[0].website == "https://example.com"
        assert cleaned[0].confidence_score == 0.8
    
    def test_clean_competitors_removes_invalid(self):
        """Test that invalid competitors are removed."""
        competitors = [
            CompetitorData(name="", source="test"),  # Empty name
            CompetitorData(name="A", source="test"),  # Too short name
            CompetitorData(name="Valid Company", source="test"),  # Valid
            CompetitorData(name="Another Valid", description="Short", source="test")  # Short description
        ]
        
        cleaned = DataCleaner.clean_competitors(competitors)
        
        assert len(cleaned) == 2
        assert cleaned[0].name == "Valid Company"
        assert cleaned[1].name == "Another Valid"
        assert cleaned[1].description is None  # Short description removed
    
    def test_clean_competitors_cleans_urls(self):
        """Test URL cleaning."""
        competitors = [
            CompetitorData(name="Company1", website="example.com", source="test"),
            CompetitorData(name="Company2", website="https://example2.com", source="test"),
            CompetitorData(name="Company3", website="invalid-url", source="test")
        ]
        
        cleaned = DataCleaner.clean_competitors(competitors)
        
        assert cleaned[0].website == "https://example.com"
        assert cleaned[1].website == "https://example2.com"
        assert cleaned[2].website is None
    
    def test_deduplicate_competitors_by_name(self):
        """Test competitor deduplication by name."""
        competitors = [
            CompetitorData(name="Test Company", source="test1"),
            CompetitorData(name="TEST COMPANY", source="test2"),  # Same name, different case
            CompetitorData(name="Different Company", source="test3")
        ]
        
        cleaned = DataCleaner.clean_competitors(competitors)
        
        assert len(cleaned) == 2
        names = [c.name for c in cleaned]
        assert "Test Company" in names
        assert "Different Company" in names
    
    def test_deduplicate_competitors_by_website(self):
        """Test competitor deduplication by website."""
        competitors = [
            CompetitorData(name="Company1", website="https://example.com", source="test1"),
            CompetitorData(name="Company2", website="https://www.example.com", source="test2"),  # Same domain
            CompetitorData(name="Company3", website="https://different.com", source="test3")
        ]
        
        cleaned = DataCleaner.clean_competitors(competitors)
        
        assert len(cleaned) == 2
        websites = [c.website for c in cleaned if c.website]
        assert len(websites) == 2
    
    def test_clean_feedback_basic(self):
        """Test basic feedback cleaning."""
        feedback_list = [
            FeedbackData(
                text="  This is great feedback!  ",
                sentiment="positive",
                sentiment_score=0.8,
                source="test"
            )
        ]
        
        cleaned = DataCleaner.clean_feedback(feedback_list)
        
        assert len(cleaned) == 1
        assert cleaned[0].text == "This is great feedback!"
        assert cleaned[0].sentiment == "positive"
        assert cleaned[0].sentiment_score == 0.8
    
    def test_clean_feedback_removes_invalid(self):
        """Test that invalid feedback is removed."""
        feedback_list = [
            FeedbackData(text="", source="test"),  # Empty text
            FeedbackData(text="Hi", source="test"),  # Too short
            FeedbackData(text="This is valid feedback", source="test"),  # Valid
            FeedbackData(text="Another valid feedback", sentiment="invalid", source="test")  # Invalid sentiment
        ]
        
        cleaned = DataCleaner.clean_feedback(feedback_list)
        
        assert len(cleaned) == 2
        assert cleaned[0].text == "This is valid feedback"
        assert cleaned[1].text == "Another valid feedback"
        assert cleaned[1].sentiment is None  # Invalid sentiment removed
    
    def test_deduplicate_feedback(self):
        """Test feedback deduplication."""
        feedback_list = [
            FeedbackData(text="This is great!", source="test1"),
            FeedbackData(text="THIS IS GREAT!", source="test2"),  # Same text, different case
            FeedbackData(text="This is different feedback", source="test3")
        ]
        
        cleaned = DataCleaner.clean_feedback(feedback_list)
        
        assert len(cleaned) == 2
        texts = [f.text for f in cleaned]
        assert "This is great!" in texts
        assert "This is different feedback" in texts
    
    def test_clean_text(self):
        """Test text cleaning utility."""
        text = "  Hello\n\nWorld  \t  "
        cleaned = DataCleaner._clean_text(text)
        assert cleaned == "Hello World"
    
    def test_clean_url(self):
        """Test URL cleaning utility."""
        assert DataCleaner._clean_url("example.com") == "https://example.com"
        assert DataCleaner._clean_url("https://example.com") == "https://example.com"
        assert DataCleaner._clean_url("invalid") is None
        assert DataCleaner._clean_url("") is None
    
    def test_clean_revenue(self):
        """Test revenue cleaning utility."""
        assert DataCleaner._clean_revenue("$1M annually") == "$1M annually"
        assert DataCleaner._clean_revenue("1 million") == "1 million"
        assert DataCleaner._clean_revenue("No revenue info") is None
        assert DataCleaner._clean_revenue("") is None
    
    def test_normalize_for_comparison(self):
        """Test text normalization for comparison."""
        text1 = "Test Company, Inc."
        text2 = "test company inc"
        
        norm1 = DataCleaner._normalize_for_comparison(text1)
        norm2 = DataCleaner._normalize_for_comparison(text2)
        
        assert norm1 == norm2
    
    def test_normalize_url_for_comparison(self):
        """Test URL normalization for comparison."""
        url1 = "https://www.example.com"
        url2 = "https://example.com"
        
        norm1 = DataCleaner._normalize_url_for_comparison(url1)
        norm2 = DataCleaner._normalize_url_for_comparison(url2)
        
        assert norm1 == norm2 == "example.com"