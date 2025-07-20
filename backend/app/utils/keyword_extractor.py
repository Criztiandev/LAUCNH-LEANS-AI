"""
Keyword extraction utility for processing idea text.
"""
import re
from typing import List, Set
from collections import Counter


class KeywordExtractor:
    """Utility class for extracting keywords from idea text."""
    
    # Common stop words to filter out
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'would', 'could', 'should', 'can',
        'this', 'these', 'they', 'them', 'their', 'there', 'where', 'when',
        'what', 'who', 'why', 'how', 'i', 'you', 'we', 'my', 'your', 'our',
        'me', 'us', 'him', 'her', 'his', 'hers', 'ours', 'yours', 'theirs'
    }
    
    # Business-related keywords that should be prioritized
    BUSINESS_KEYWORDS = {
        'saas', 'software', 'platform', 'service', 'app', 'application',
        'tool', 'solution', 'system', 'product', 'business', 'startup',
        'company', 'enterprise', 'customer', 'user', 'client', 'market',
        'industry', 'technology', 'digital', 'online', 'web', 'mobile',
        'automation', 'analytics', 'data', 'ai', 'artificial', 'intelligence',
        'machine', 'learning', 'cloud', 'api', 'integration', 'dashboard'
    }
    
    @classmethod
    def extract_keywords(cls, idea_text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract relevant keywords from idea text.
        
        Args:
            idea_text: The original idea text to process
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of extracted keywords, prioritized by relevance
        """
        if not idea_text or not idea_text.strip():
            return []
        
        # Clean and normalize text
        cleaned_text = cls._clean_text(idea_text)
        
        # Extract words
        words = cls._extract_words(cleaned_text)
        
        # Filter and score words
        scored_words = cls._score_words(words)
        
        # Return top keywords
        return [word for word, _ in scored_words[:max_keywords]]
    
    @classmethod
    def _clean_text(cls, text: str) -> str:
        """Clean and normalize the input text."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces and hyphens
        text = re.sub(r'[^\w\s\-]', ' ', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @classmethod
    def _extract_words(cls, text: str) -> List[str]:
        """Extract individual words from cleaned text."""
        # Split on spaces and hyphens
        words = re.split(r'[\s\-]+', text)
        
        # Filter out empty strings and single characters
        words = [word for word in words if len(word) > 1]
        
        return words
    
    @classmethod
    def _score_words(cls, words: List[str]) -> List[tuple]:
        """Score words by relevance and frequency."""
        # Count word frequency
        word_counts = Counter(words)
        
        # Score each unique word
        scored_words = []
        for word, count in word_counts.items():
            # Skip stop words
            if word in cls.STOP_WORDS:
                continue
            
            # Base score is frequency
            score = count
            
            # Boost business-related keywords
            if word in cls.BUSINESS_KEYWORDS:
                score *= 2
            
            # Boost longer words (more specific)
            if len(word) > 6:
                score *= 1.5
            
            scored_words.append((word, score))
        
        # Sort by score (descending)
        scored_words.sort(key=lambda x: x[1], reverse=True)
        
        return scored_words