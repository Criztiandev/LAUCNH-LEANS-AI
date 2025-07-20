"""
Data cleaning and deduplication utilities for scraped data.
"""
import re
from typing import List, Dict, Any, Set
from urllib.parse import urlparse
from ..scrapers.base_scraper import CompetitorData, FeedbackData


class DataCleaner:
    """Utility class for cleaning and deduplicating scraped data."""
    
    @classmethod
    def clean_competitors(cls, competitors: List[CompetitorData]) -> List[CompetitorData]:
        """
        Clean and deduplicate competitor data.
        
        Args:
            competitors: List of competitor data to clean
            
        Returns:
            Cleaned and deduplicated list of competitors
        """
        if not competitors:
            return []
        
        # Clean individual competitor data
        cleaned_competitors = []
        for competitor in competitors:
            cleaned = cls._clean_competitor(competitor)
            if cleaned:
                cleaned_competitors.append(cleaned)
        
        # Deduplicate competitors
        deduplicated = cls._deduplicate_competitors(cleaned_competitors)
        
        return deduplicated
    
    @classmethod
    def clean_feedback(cls, feedback_list: List[FeedbackData]) -> List[FeedbackData]:
        """
        Clean and deduplicate feedback data.
        
        Args:
            feedback_list: List of feedback data to clean
            
        Returns:
            Cleaned and deduplicated list of feedback
        """
        if not feedback_list:
            return []
        
        # Clean individual feedback data
        cleaned_feedback = []
        for feedback in feedback_list:
            cleaned = cls._clean_feedback(feedback)
            if cleaned:
                cleaned_feedback.append(cleaned)
        
        # Deduplicate feedback
        deduplicated = cls._deduplicate_feedback(cleaned_feedback)
        
        return deduplicated
    
    @classmethod
    def _clean_competitor(cls, competitor: CompetitorData) -> CompetitorData:
        """Clean individual competitor data."""
        # Clean name
        name = cls._clean_text(competitor.name) if competitor.name else ""
        if not name or len(name) < 2:
            return None
        
        # Clean description
        description = cls._clean_text(competitor.description) if competitor.description else None
        if description and len(description) < 10:
            description = None
        
        # Clean and validate website URL
        website = cls._clean_url(competitor.website) if competitor.website else None
        
        # Clean revenue string
        revenue = cls._clean_revenue(competitor.estimated_revenue) if competitor.estimated_revenue else None
        
        # Clean pricing model
        pricing = cls._clean_text(competitor.pricing_model) if competitor.pricing_model else None
        
        # Validate confidence score
        confidence = max(0.0, min(1.0, competitor.confidence_score or 0.0))
        
        return CompetitorData(
            name=name,
            description=description,
            website=website,
            estimated_users=competitor.estimated_users,
            estimated_revenue=revenue,
            pricing_model=pricing,
            source=competitor.source,
            source_url=competitor.source_url,
            confidence_score=confidence
        )
    
    @classmethod
    def _clean_feedback(cls, feedback: FeedbackData) -> FeedbackData:
        """Clean individual feedback data."""
        # Clean feedback text
        text = cls._clean_text(feedback.text) if feedback.text else ""
        if not text or len(text) < 5:
            return None
        
        # Validate sentiment
        sentiment = feedback.sentiment
        if sentiment and sentiment.lower() not in ['positive', 'negative', 'neutral']:
            sentiment = None
        
        # Validate sentiment score
        sentiment_score = feedback.sentiment_score
        if sentiment_score is not None:
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
        
        return FeedbackData(
            text=text,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            source=feedback.source,
            source_url=feedback.source_url,
            author_info=feedback.author_info
        )
    
    @classmethod
    def _deduplicate_competitors(cls, competitors: List[CompetitorData]) -> List[CompetitorData]:
        """Remove duplicate competitors based on name and website similarity."""
        if not competitors:
            return []
        
        unique_competitors = []
        seen_names = set()
        seen_websites = set()
        
        for competitor in competitors:
            # Create normalized identifiers
            name_key = cls._normalize_for_comparison(competitor.name)
            website_key = cls._normalize_url_for_comparison(competitor.website) if competitor.website else None
            
            # Check for duplicates
            is_duplicate = False
            
            # Check name similarity
            if name_key in seen_names:
                is_duplicate = True
            
            # Check website similarity
            if website_key and website_key in seen_websites:
                is_duplicate = True
            
            if not is_duplicate:
                unique_competitors.append(competitor)
                seen_names.add(name_key)
                if website_key:
                    seen_websites.add(website_key)
        
        return unique_competitors
    
    @classmethod
    def _deduplicate_feedback(cls, feedback_list: List[FeedbackData]) -> List[FeedbackData]:
        """Remove duplicate feedback based on text similarity."""
        if not feedback_list:
            return []
        
        unique_feedback = []
        seen_texts = set()
        
        for feedback in feedback_list:
            # Create normalized text for comparison
            text_key = cls._normalize_for_comparison(feedback.text)
            
            # Skip if we've seen similar text
            if text_key not in seen_texts:
                unique_feedback.append(feedback)
                seen_texts.add(text_key)
        
        return unique_feedback
    
    @classmethod
    def _clean_text(cls, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        return text
    
    @classmethod
    def _clean_url(cls, url: str) -> str:
        """Clean and validate URL."""
        if not url:
            return None
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            parsed = urlparse(url)
            # Check if netloc exists and contains at least one dot (basic domain validation)
            if parsed.netloc and '.' in parsed.netloc and len(parsed.netloc.split('.')) >= 2:
                # Additional check: netloc should not be just "invalid-url" or similar
                parts = parsed.netloc.split('.')
                if all(len(part) > 0 for part in parts) and len(parts[-1]) >= 2:
                    return url
        except Exception:
            pass
        
        return None
    
    @classmethod
    def _clean_revenue(cls, revenue: str) -> str:
        """Clean revenue string."""
        if not revenue:
            return None
        
        # Remove extra whitespace and normalize
        revenue = re.sub(r'\s+', ' ', revenue.strip())
        
        # Keep only if it contains numbers or common revenue indicators
        if re.search(r'[\d$€£¥]|million|billion|thousand|k|m|b', revenue.lower()):
            return revenue
        
        return None
    
    @classmethod
    def _normalize_for_comparison(cls, text: str) -> str:
        """Normalize text for similarity comparison."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation and extra spaces
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    @classmethod
    def _normalize_url_for_comparison(cls, url: str) -> str:
        """Normalize URL for similarity comparison."""
        if not url:
            return ""
        
        try:
            parsed = urlparse(url.lower())
            # Use domain name for comparison
            return parsed.netloc.replace('www.', '')
        except Exception:
            return url.lower()