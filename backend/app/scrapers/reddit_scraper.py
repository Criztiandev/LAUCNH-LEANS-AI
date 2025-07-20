"""
Reddit scraper for extracting user feedback and discussions related to SaaS ideas.
"""
import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
import re
from datetime import datetime, timedelta

import praw
from praw.exceptions import PRAWException

from .base_scraper import BaseScraper, ScrapingResult, ScrapingStatus, CompetitorData, FeedbackData


logger = logging.getLogger(__name__)


class RedditScraper(BaseScraper):
    """Scraper for Reddit to extract user feedback and discussions."""
    
    def __init__(self):
        """Initialize the Reddit scraper."""
        super().__init__("Reddit")
        self.reddit = None
        self.relevant_subreddits = [
            'SaaS',
            'startups',
            'Entrepreneur',
            'smallbusiness',
            'webdev',
            'programming',
            'technology',
            'business',
            'ProductManagement',
            'marketing',
            'freelance',
            'digitalnomad',
            'solopreneur',
            'IMadeThis',
            'sideproject'
        ]
        self.max_posts_per_subreddit = 10
        self.max_comments_per_post = 5
    
    def validate_config(self) -> bool:
        """
        Validate that Reddit API credentials are properly configured.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        required_vars = [
            'REDDIT_CLIENT_ID',
            'REDDIT_CLIENT_SECRET',
            'REDDIT_USER_AGENT'
        ]
        
        for var in required_vars:
            if not os.getenv(var):
                logger.error(f"Missing required environment variable: {var}")
                return False
        
        try:
            self._initialize_reddit()
            # Test the connection
            self.reddit.user.me()
            return True
        except Exception as e:
            logger.error(f"Reddit API validation failed: {str(e)}")
            return False
    
    def _initialize_reddit(self) -> None:
        """Initialize the Reddit API client."""
        if not self.reddit:
            self.reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent=os.getenv('REDDIT_USER_AGENT', 'SaaS-Validator-Bot/1.0'),
                read_only=True
            )
    
    async def scrape(self, keywords: List[str], idea_text: str) -> ScrapingResult:
        """
        Scrape Reddit for user feedback and discussions based on keywords.
        
        Args:
            keywords: List of extracted keywords from the idea
            idea_text: Original idea text for context
            
        Returns:
            ScrapingResult containing feedback data and potential competitors
        """
        try:
            if not self.validate_config():
                return ScrapingResult(
                    status=ScrapingStatus.FAILED,
                    competitors=[],
                    feedback=[],
                    error_message="Reddit API configuration is invalid"
                )
            
            self._initialize_reddit()
            
            competitors = []
            feedback = []
            
            # Search for discussions in relevant subreddits
            for keyword in keywords[:5]:  # Limit to top 5 keywords
                try:
                    keyword_feedback = await self._search_keyword_discussions(keyword, idea_text)
                    feedback.extend(keyword_feedback)
                    
                    # Add delay to respect rate limits
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"Failed to search Reddit for keyword '{keyword}': {str(e)}")
                    continue
            
            # Remove duplicate feedback based on text similarity
            unique_feedback = self._deduplicate_feedback(feedback)
            
            # Limit results to avoid overwhelming the system
            final_feedback = unique_feedback[:50]
            
            # Try to extract competitor mentions from discussions
            competitors = self._extract_competitor_mentions(final_feedback, keywords)
            
            status = ScrapingStatus.SUCCESS if final_feedback else ScrapingStatus.FAILED
            
            return ScrapingResult(
                status=status,
                competitors=competitors,
                feedback=final_feedback,
                metadata={
                    "keywords_searched": keywords[:5],
                    "subreddits_searched": self.relevant_subreddits,
                    "total_feedback": len(final_feedback),
                    "total_competitors": len(competitors),
                    "source": self.source_name
                }
            )
            
        except Exception as e:
            logger.error(f"Reddit scraping failed: {str(e)}")
            return ScrapingResult(
                status=ScrapingStatus.FAILED,
                competitors=[],
                feedback=[],
                error_message=str(e)
            )
    
    async def _search_keyword_discussions(self, keyword: str, idea_text: str) -> List[FeedbackData]:
        """
        Search for discussions related to a keyword across relevant subreddits.
        
        Args:
            keyword: Search keyword
            idea_text: Original idea text for context
            
        Returns:
            List of FeedbackData objects
        """
        feedback = []
        
        for subreddit_name in self.relevant_subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search for posts containing the keyword
                search_results = subreddit.search(
                    keyword,
                    sort='relevance',
                    time_filter='year',
                    limit=self.max_posts_per_subreddit
                )
                
                for post in search_results:
                    try:
                        # Extract feedback from post title and body
                        post_feedback = self._extract_post_feedback(post, keyword)
                        if post_feedback:
                            feedback.extend(post_feedback)
                        
                        # Extract feedback from top comments
                        comment_feedback = self._extract_comment_feedback(post, keyword)
                        if comment_feedback:
                            feedback.extend(comment_feedback)
                        
                        # Add small delay between posts
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        logger.warning(f"Failed to process post {post.id}: {str(e)}")
                        continue
                
                # Add delay between subreddits
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.warning(f"Failed to search subreddit {subreddit_name}: {str(e)}")
                continue
        
        return feedback
    
    def _extract_post_feedback(self, post, keyword: str) -> List[FeedbackData]:
        """
        Extract feedback from a Reddit post.
        
        Args:
            post: Reddit post object
            keyword: Search keyword for context
            
        Returns:
            List of FeedbackData objects
        """
        feedback = []
        
        try:
            # Combine title and selftext for analysis
            post_text = f"{post.title} {post.selftext}".strip()
            
            if len(post_text) < 20:  # Skip very short posts
                return feedback
            
            # Basic sentiment analysis based on keywords
            sentiment, sentiment_score = self._analyze_sentiment(post_text)
            
            # Create feedback data
            feedback_data = FeedbackData(
                text=post_text[:500],  # Limit text length
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                source=self.source_name,
                source_url=f"https://reddit.com{post.permalink}",
                author_info={
                    "username": str(post.author) if post.author else "deleted",
                    "subreddit": str(post.subreddit),
                    "score": post.score,
                    "created_utc": post.created_utc,
                    "num_comments": post.num_comments
                }
            )
            
            feedback.append(feedback_data)
            
        except Exception as e:
            logger.warning(f"Failed to extract post feedback: {str(e)}")
        
        return feedback
    
    def _extract_comment_feedback(self, post, keyword: str) -> List[FeedbackData]:
        """
        Extract feedback from Reddit post comments.
        
        Args:
            post: Reddit post object
            keyword: Search keyword for context
            
        Returns:
            List of FeedbackData objects
        """
        feedback = []
        
        try:
            # Get top comments
            post.comments.replace_more(limit=0)  # Remove "more comments" objects
            top_comments = post.comments[:self.max_comments_per_post]
            
            for comment in top_comments:
                try:
                    if hasattr(comment, 'body') and len(comment.body) > 20:
                        # Basic sentiment analysis
                        sentiment, sentiment_score = self._analyze_sentiment(comment.body)
                        
                        feedback_data = FeedbackData(
                            text=comment.body[:500],  # Limit text length
                            sentiment=sentiment,
                            sentiment_score=sentiment_score,
                            source=self.source_name,
                            source_url=f"https://reddit.com{post.permalink}",
                            author_info={
                                "username": str(comment.author) if comment.author else "deleted",
                                "subreddit": str(post.subreddit),
                                "score": comment.score,
                                "created_utc": comment.created_utc,
                                "is_comment": True,
                                "parent_post_title": post.title
                            }
                        )
                        
                        feedback.append(feedback_data)
                        
                except Exception as e:
                    logger.warning(f"Failed to extract comment feedback: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Failed to extract comments: {str(e)}")
        
        return feedback
    
    def _analyze_sentiment(self, text: str) -> tuple[str, float]:
        """
        Basic sentiment analysis using keyword matching.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (sentiment, sentiment_score)
        """
        text_lower = text.lower()
        
        # Positive indicators
        positive_words = [
            'great', 'awesome', 'excellent', 'amazing', 'fantastic', 'wonderful',
            'love', 'like', 'good', 'best', 'perfect', 'helpful', 'useful',
            'recommend', 'impressed', 'satisfied', 'happy', 'pleased'
        ]
        
        # Negative indicators
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'worst',
            'useless', 'broken', 'frustrated', 'disappointed', 'annoying',
            'problem', 'issue', 'bug', 'error', 'fail', 'sucks', 'waste'
        ]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            sentiment_score = min(0.8, 0.3 + (positive_count * 0.1))
        elif negative_count > positive_count:
            sentiment = "negative"
            sentiment_score = max(-0.8, -0.3 - (negative_count * 0.1))
        else:
            sentiment = "neutral"
            sentiment_score = 0.0
        
        return sentiment, sentiment_score
    
    def _deduplicate_feedback(self, feedback: List[FeedbackData]) -> List[FeedbackData]:
        """
        Remove duplicate feedback based on text similarity.
        
        Args:
            feedback: List of FeedbackData objects
            
        Returns:
            List of unique FeedbackData objects
        """
        unique_feedback = []
        seen_texts = set()
        
        for item in feedback:
            # Create a normalized version for comparison
            normalized_text = re.sub(r'\s+', ' ', item.text.lower().strip())
            
            # Skip if we've seen very similar text
            if normalized_text not in seen_texts:
                seen_texts.add(normalized_text)
                unique_feedback.append(item)
        
        return unique_feedback
    
    def _extract_competitor_mentions(self, feedback: List[FeedbackData], keywords: List[str]) -> List[CompetitorData]:
        """
        Extract potential competitor mentions from feedback discussions.
        
        Args:
            feedback: List of feedback data
            keywords: Original keywords for context
            
        Returns:
            List of CompetitorData objects
        """
        competitors = []
        competitor_mentions = {}
        
        # Common patterns for competitor mentions
        patterns = [
            r'I use ([A-Z][a-zA-Z0-9]{2,15})(?:\s|,|\.|\s+for)',
            r'try ([A-Z][a-zA-Z0-9]{2,15})(?:\s|,|\.)',
            r'check out ([A-Z][a-zA-Z0-9]{2,15})(?:\s|,|\.)',
            r'recommend ([A-Z][a-zA-Z0-9]{2,15})(?:\s|,|\.)',
            r'([A-Z][a-zA-Z0-9]{2,15}) is (great|good|awesome|excellent)',
            r'([A-Z][a-zA-Z0-9]{2,15}) works (well|great|perfectly)'
        ]
        
        for feedback_item in feedback:
            for pattern in patterns:
                matches = re.findall(pattern, feedback_item.text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        competitor_name = match[0].strip()
                    else:
                        competitor_name = match.strip()
                    
                    # Filter out common words and short names
                    if (len(competitor_name) > 3 and 
                        competitor_name.lower() not in ['this', 'that', 'they', 'them', 'here', 'there']):
                        
                        if competitor_name not in competitor_mentions:
                            competitor_mentions[competitor_name] = {
                                'count': 0,
                                'sentiment_scores': [],
                                'sources': []
                            }
                        
                        competitor_mentions[competitor_name]['count'] += 1
                        competitor_mentions[competitor_name]['sentiment_scores'].append(
                            feedback_item.sentiment_score or 0.0
                        )
                        competitor_mentions[competitor_name]['sources'].append(
                            feedback_item.source_url
                        )
        
        # Convert mentions to competitor data
        for name, data in competitor_mentions.items():
            if data['count'] >= 2:  # Only include if mentioned multiple times
                avg_sentiment = sum(data['sentiment_scores']) / len(data['sentiment_scores'])
                
                competitor = CompetitorData(
                    name=name,
                    description=f"Mentioned {data['count']} times in Reddit discussions",
                    source=self.source_name,
                    source_url=data['sources'][0] if data['sources'] else None,
                    confidence_score=min(0.8, 0.3 + (data['count'] * 0.1)),
                    estimated_users=None,
                    estimated_revenue=None,
                    pricing_model=None
                )
                
                competitors.append(competitor)
        
        return competitors[:5]  # Limit to top 5 competitor mentions