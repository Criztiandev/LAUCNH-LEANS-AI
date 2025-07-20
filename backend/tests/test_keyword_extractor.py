"""
Tests for keyword extraction utility.
"""
import pytest
from app.utils.keyword_extractor import KeywordExtractor


class TestKeywordExtractor:
    """Test cases for KeywordExtractor."""
    
    def test_extract_keywords_basic(self):
        """Test basic keyword extraction."""
        idea_text = "A SaaS platform for project management and team collaboration"
        keywords = KeywordExtractor.extract_keywords(idea_text)
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert 'saas' in keywords
        assert 'platform' in keywords
        assert 'project' in keywords
        assert 'management' in keywords
    
    def test_extract_keywords_filters_stop_words(self):
        """Test that stop words are filtered out."""
        idea_text = "This is a great idea for the best software solution"
        keywords = KeywordExtractor.extract_keywords(idea_text)
        
        # Stop words should not be in results
        stop_words_in_results = [word for word in keywords if word in KeywordExtractor.STOP_WORDS]
        assert len(stop_words_in_results) == 0
        
        # But meaningful words should be
        assert 'great' in keywords
        assert 'idea' in keywords
        assert 'software' in keywords
        assert 'solution' in keywords
    
    def test_extract_keywords_prioritizes_business_terms(self):
        """Test that business-related keywords are prioritized."""
        idea_text = "A mobile app for restaurants with analytics dashboard"
        keywords = KeywordExtractor.extract_keywords(idea_text)
        
        # Business keywords should appear early in the list
        business_keywords_found = [word for word in keywords if word in KeywordExtractor.BUSINESS_KEYWORDS]
        assert len(business_keywords_found) > 0
        
        # 'app', 'analytics', 'dashboard' should be prioritized
        assert 'app' in keywords[:5]
        assert 'analytics' in keywords[:5]
        assert 'dashboard' in keywords[:5]
    
    def test_extract_keywords_max_limit(self):
        """Test that max_keywords parameter works."""
        idea_text = "A comprehensive enterprise software solution for business process automation and workflow management"
        keywords = KeywordExtractor.extract_keywords(idea_text, max_keywords=5)
        
        assert len(keywords) <= 5
    
    def test_extract_keywords_empty_input(self):
        """Test handling of empty input."""
        assert KeywordExtractor.extract_keywords("") == []
        assert KeywordExtractor.extract_keywords(None) == []
        assert KeywordExtractor.extract_keywords("   ") == []
    
    def test_extract_keywords_special_characters(self):
        """Test handling of special characters."""
        idea_text = "A SaaS platform for e-commerce & online retail businesses!"
        keywords = KeywordExtractor.extract_keywords(idea_text)
        
        assert 'saas' in keywords
        assert 'platform' in keywords
        assert 'commerce' in keywords
        assert 'online' in keywords
        assert 'retail' in keywords
        assert 'businesses' in keywords
    
    def test_clean_text(self):
        """Test text cleaning functionality."""
        text = "  Hello, World!  This is a TEST.  "
        cleaned = KeywordExtractor._clean_text(text)
        
        assert cleaned == "hello world this is a test"
    
    def test_extract_words(self):
        """Test word extraction."""
        text = "hello world test-case another_word"
        words = KeywordExtractor._extract_words(text)
        
        assert 'hello' in words
        assert 'world' in words
        assert 'test' in words
        assert 'case' in words
        assert 'another_word' in words
    
    def test_score_words(self):
        """Test word scoring."""
        words = ['saas', 'platform', 'the', 'and', 'business', 'saas']
        scored = KeywordExtractor._score_words(words)
        
        # Should be list of tuples (word, score)
        assert all(isinstance(item, tuple) and len(item) == 2 for item in scored)
        
        # Stop words should not be included
        scored_words = [word for word, score in scored]
        assert 'the' not in scored_words
        assert 'and' not in scored_words
        
        # 'saas' appears twice and is a business keyword, should have high score
        saas_score = next((score for word, score in scored if word == 'saas'), 0)
        platform_score = next((score for word, score in scored if word == 'platform'), 0)
        
        assert saas_score > platform_score  # saas appears twice and is business keyword