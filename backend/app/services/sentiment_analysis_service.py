"""
Enhanced sentiment analysis service using TextBlob and VADER.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)


class SentimentLabel(Enum):
    """Sentiment classification labels."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    label: SentimentLabel
    score: float  # Normalized score between -1 (very negative) and 1 (very positive)
    confidence: float  # Confidence score between 0 and 1
    textblob_polarity: float
    textblob_subjectivity: float
    vader_compound: float
    vader_positive: float
    vader_negative: float
    vader_neutral: float


class SentimentAnalysisService:
    """Enhanced sentiment analysis service combining TextBlob and VADER."""
    
    def __init__(self):
        """Initialize the sentiment analysis service."""
        self.vader_analyzer = SentimentIntensityAnalyzer()
        
        # Thresholds for sentiment classification
        self.positive_threshold = 0.1
        self.negative_threshold = -0.1
        
        # Confidence calculation weights
        self.textblob_weight = 0.4
        self.vader_weight = 0.6
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of given text using both TextBlob and VADER.
        
        Args:
            text: Text to analyze
            
        Returns:
            SentimentResult with comprehensive analysis
        """
        if not text or not isinstance(text, str):
            return self._create_neutral_result()
        
        # Clean and prepare text
        cleaned_text = self._preprocess_text(text)
        
        try:
            # TextBlob analysis
            blob = TextBlob(cleaned_text)
            textblob_polarity = blob.sentiment.polarity
            textblob_subjectivity = blob.sentiment.subjectivity
            
            # VADER analysis
            vader_scores = self.vader_analyzer.polarity_scores(cleaned_text)
            vader_compound = vader_scores['compound']
            vader_positive = vader_scores['pos']
            vader_negative = vader_scores['neg']
            vader_neutral = vader_scores['neu']
            
            # Calculate combined score
            combined_score = self._calculate_combined_score(
                textblob_polarity, vader_compound
            )
            
            # Determine sentiment label
            sentiment_label = self._classify_sentiment(combined_score)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(
                textblob_polarity, textblob_subjectivity,
                vader_compound, vader_positive, vader_negative, vader_neutral
            )
            
            return SentimentResult(
                label=sentiment_label,
                score=combined_score,
                confidence=confidence,
                textblob_polarity=textblob_polarity,
                textblob_subjectivity=textblob_subjectivity,
                vader_compound=vader_compound,
                vader_positive=vader_positive,
                vader_negative=vader_negative,
                vader_neutral=vader_neutral
            )
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return self._create_neutral_result()
    
    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """
        Analyze sentiment for a batch of texts.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of SentimentResult objects
        """
        results = []
        for text in texts:
            result = self.analyze_sentiment(text)
            results.append(result)
        return results
    
    def get_sentiment_summary(self, results: List[SentimentResult]) -> Dict[str, Any]:
        """
        Generate summary statistics for a batch of sentiment results.
        
        Args:
            results: List of SentimentResult objects
            
        Returns:
            Dictionary with summary statistics
        """
        if not results:
            return {
                'total_count': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'positive_percentage': 0.0,
                'negative_percentage': 0.0,
                'neutral_percentage': 0.0,
                'average_score': 0.0,
                'average_confidence': 0.0
            }
        
        positive_count = sum(1 for r in results if r.label == SentimentLabel.POSITIVE)
        negative_count = sum(1 for r in results if r.label == SentimentLabel.NEGATIVE)
        neutral_count = sum(1 for r in results if r.label == SentimentLabel.NEUTRAL)
        total_count = len(results)
        
        average_score = sum(r.score for r in results) / total_count
        average_confidence = sum(r.confidence for r in results) / total_count
        
        return {
            'total_count': total_count,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'positive_percentage': (positive_count / total_count) * 100,
            'negative_percentage': (negative_count / total_count) * 100,
            'neutral_percentage': (neutral_count / total_count) * 100,
            'average_score': round(average_score, 3),
            'average_confidence': round(average_confidence, 3)
        }
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for sentiment analysis.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Limit text length for performance (keep first 1000 characters)
        if len(text) > 1000:
            text = text[:1000]
        
        return text.strip()
    
    def _calculate_combined_score(self, textblob_polarity: float, vader_compound: float) -> float:
        """
        Calculate combined sentiment score from TextBlob and VADER.
        
        Args:
            textblob_polarity: TextBlob polarity score (-1 to 1)
            vader_compound: VADER compound score (-1 to 1)
            
        Returns:
            Combined score (-1 to 1)
        """
        # Weighted average of both scores
        combined = (self.textblob_weight * textblob_polarity + 
                   self.vader_weight * vader_compound)
        
        # Ensure score is within bounds
        return max(-1.0, min(1.0, combined))
    
    def _classify_sentiment(self, score: float) -> SentimentLabel:
        """
        Classify sentiment based on combined score.
        
        Args:
            score: Combined sentiment score
            
        Returns:
            SentimentLabel classification
        """
        if score > self.positive_threshold:
            return SentimentLabel.POSITIVE
        elif score < self.negative_threshold:
            return SentimentLabel.NEGATIVE
        else:
            return SentimentLabel.NEUTRAL
    
    def _calculate_confidence(
        self, 
        textblob_polarity: float, 
        textblob_subjectivity: float,
        vader_compound: float,
        vader_positive: float,
        vader_negative: float,
        vader_neutral: float
    ) -> float:
        """
        Calculate confidence score for sentiment prediction.
        
        Args:
            textblob_polarity: TextBlob polarity score
            textblob_subjectivity: TextBlob subjectivity score
            vader_compound: VADER compound score
            vader_positive: VADER positive score
            vader_negative: VADER negative score
            vader_neutral: VADER neutral score
            
        Returns:
            Confidence score between 0 and 1
        """
        # Agreement between TextBlob and VADER increases confidence
        agreement = 1.0 - abs(textblob_polarity - vader_compound) / 2.0
        
        # Higher absolute scores indicate more confident predictions
        textblob_strength = abs(textblob_polarity)
        vader_strength = abs(vader_compound)
        
        # Subjectivity affects confidence (more subjective = less confident for factual analysis)
        subjectivity_factor = 1.0 - (textblob_subjectivity * 0.3)
        
        # VADER score distribution (more extreme distributions = higher confidence)
        vader_max_score = max(vader_positive, vader_negative, vader_neutral)
        vader_distribution_confidence = vader_max_score
        
        # Combine all factors
        confidence = (
            agreement * 0.4 +
            textblob_strength * 0.2 +
            vader_strength * 0.2 +
            subjectivity_factor * 0.1 +
            vader_distribution_confidence * 0.1
        )
        
        # Ensure confidence is within bounds
        return max(0.0, min(1.0, confidence))
    
    def _create_neutral_result(self) -> SentimentResult:
        """Create a neutral sentiment result for error cases."""
        return SentimentResult(
            label=SentimentLabel.NEUTRAL,
            score=0.0,
            confidence=0.0,
            textblob_polarity=0.0,
            textblob_subjectivity=0.0,
            vader_compound=0.0,
            vader_positive=0.0,
            vader_negative=0.0,
            vader_neutral=1.0
        )