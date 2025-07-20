"""
Google Play Store scraper using google-play-scraper library for reliable Android app data extraction.
"""
import asyncio
import logging
import random
from typing import List, Dict, Any, Optional
from datetime import datetime

from google_play_scraper import search, app, reviews, Sort, exceptions

from .base_scraper import BaseScraper, ScrapingResult, ScrapingStatus, CompetitorData, FeedbackData
from ..utils.data_cleaner import DataCleaner
from ..services.sentiment_analysis_service import SentimentAnalysisService


logger = logging.getLogger(__name__)


class GooglePlayStoreScraper(BaseScraper):
    """Scraper for Google Play Store using google-play-scraper library for reliable Android app data extraction."""
    
    def __init__(self):
        """Initialize the Google Play Store scraper with google-play-scraper library."""
        super().__init__("Google Play Store")
        self.max_results_per_query = 20  # Results per search query
        self.max_queries = 3  # Maximum search queries to execute
        self.max_reviews_per_app = 5  # Maximum reviews to fetch per app
        self.delay_between_requests = (1, 3)  # Shorter delays since no browser automation
        self.supported_languages = ['en']  # Supported languages for search
        self.supported_countries = ['us']  # Supported countries for search
        self.sentiment_analyzer = SentimentAnalysisService()
        self.max_comments_per_app = 10  # Increased to capture more pain points
    
    def validate_config(self) -> bool:
        """
        Validate that the Google Play Store scraper is properly configured.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            if self.max_results_per_query <= 0:
                logger.error("Invalid max_results_per_query for Google Play Store scraper")
                return False
            
            if self.max_queries <= 0:
                logger.error("Invalid max_queries for Google Play Store scraper")
                return False
            
            if not self.supported_languages:
                logger.error("No supported languages configured for Google Play Store scraper")
                return False
            
            if not self.supported_countries:
                logger.error("No supported countries configured for Google Play Store scraper")
                return False
            
            logger.info("Google Play Store scraper configuration is valid")
            return True
            
        except Exception as e:
            logger.error(f"Google Play Store scraper configuration validation failed: {str(e)}")
            return False
    
    async def scrape(self, keywords: List[str], idea_text: str) -> ScrapingResult:
        """
        Scrape Google Play Store using google-play-scraper library for Android app data.
        
        Args:
            keywords: List of extracted keywords from the idea
            idea_text: Original idea text for context
            
        Returns:
            ScrapingResult containing competitor app data and reviews
        """
        try:
            # Store keywords for relevance checking
            self.search_keywords = [kw.lower() for kw in keywords]
            
            competitors = []
            feedback = []
            metadata = {
                "keywords_searched": [],
                "search_queries": [],
                "successful_queries": 0,
                "failed_queries": 0,
                "apps_found": 0,
                "reviews_extracted": 0,
                "api_calls_made": 0,
                "source": self.source_name,
                "scraping_method": "google-play-scraper-api"
            }
            
            # Generate search queries based on keywords and idea text
            search_queries = self._generate_search_queries(keywords, idea_text)
            metadata["search_queries"] = search_queries
            
            # Execute searches using google-play-scraper library
            for query in search_queries[:self.max_queries]:
                try:
                    logger.info(f"Searching Google Play Store for: {query}")
                    
                    # Search for apps using the google-play-scraper library
                    search_results = await self._search_apps(query)
                    metadata["api_calls_made"] += 1
                    
                    if search_results:
                        # Extract competitor data from search results
                        query_competitors = await self._extract_competitors_from_search(search_results)
                        competitors.extend(query_competitors)
                        
                        # Extract reviews for top apps (limit to top 3 to avoid rate limiting)
                        query_feedback = await self._extract_reviews_from_apps(search_results[:3])
                        feedback.extend(query_feedback)
                        
                        metadata["successful_queries"] += 1
                        metadata["keywords_searched"].append(query)
                        metadata["apps_found"] += len(query_competitors)
                        metadata["reviews_extracted"] += len(query_feedback)
                        
                        logger.info(f"Found {len(query_competitors)} apps and {len(query_feedback)} reviews for query: {query}")
                    else:
                        logger.warning(f"No results found for query: {query}")
                    
                    # Short delay between requests to respect rate limits
                    delay = random.uniform(*self.delay_between_requests)
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    logger.warning(f"Failed to search for query '{query}': {str(e)}")
                    metadata["failed_queries"] += 1
                    continue
            
            # Remove duplicate competitors and feedback
            unique_competitors = self._deduplicate_competitors(competitors)
            unique_feedback = self._deduplicate_feedback(feedback)
            
            # Initialize comments and sentiment_summary for all competitors
            for competitor in unique_competitors:
                await self._add_comments_to_competitor(competitor, [])
            
            # Extract comments and sentiment analysis for top competitors
            for competitor in unique_competitors[:5]:  # Only get comments for top 5
                try:
                    # Extract reviews as comments with sentiment analysis
                    competitor_comments = await self._extract_reviews_with_sentiment(competitor)
                    
                    # Update with actual comments and sentiment summary
                    await self._add_comments_to_competitor(competitor, competitor_comments)
                    
                    await asyncio.sleep(0.5)  # Small delay between requests
                except Exception as e:
                    logger.warning(f"Failed to extract comments for {competitor.name}: {str(e)}")
                    continue
            
            # Determine scraping status
            if metadata["successful_queries"] > 0:
                status = ScrapingStatus.SUCCESS if len(unique_competitors) > 0 else ScrapingStatus.PARTIAL_SUCCESS
            else:
                status = ScrapingStatus.FAILED
            
            # Update metadata with final stats
            metadata.update({
                "total_competitors": len(unique_competitors),
                "total_feedback": len(unique_feedback),
                "success_rate": metadata["successful_queries"] / len(search_queries) if search_queries else 0
            })
            
            logger.info(f"Google Play Store scraping completed: {len(unique_competitors)} apps, "
                       f"{len(unique_feedback)} reviews, "
                       f"{metadata['successful_queries']}/{len(search_queries)} successful queries")
            
            return ScrapingResult(
                status=status,
                competitors=unique_competitors[:15],  # Limit to top 15 apps
                feedback=unique_feedback[:20],  # Limit to top 20 reviews
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Google Play Store scraping failed: {str(e)}")
            return ScrapingResult(
                status=ScrapingStatus.FAILED,
                competitors=[],
                feedback=[],
                error_message=str(e),
                metadata=metadata or {}
            )
    
    async def _search_apps(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for apps using google-play-scraper library.
        
        Args:
            query: Search query string
            
        Returns:
            List of app data dictionaries
        """
        try:
            # Use asyncio to run the synchronous search function
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: search(
                    query,
                    lang=self.supported_languages[0],
                    country=self.supported_countries[0],
                    n_hits=self.max_results_per_query
                )
            )
            
            logger.info(f"Found {len(results)} apps for query: {query}")
            return results
            
        except exceptions.NotFoundError:
            logger.warning(f"No apps found for query: {query}")
            return []
        except Exception as e:
            logger.error(f"Error searching for apps with query '{query}': {str(e)}")
            return []
    
    async def _get_app_details(self, app_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed app information using google-play-scraper library.
        
        Args:
            app_id: Google Play Store app ID
            
        Returns:
            App details dictionary or None if failed
        """
        try:
            loop = asyncio.get_event_loop()
            details = await loop.run_in_executor(
                None,
                lambda: app(
                    app_id,
                    lang=self.supported_languages[0],
                    country=self.supported_countries[0]
                )
            )
            
            return details
            
        except exceptions.NotFoundError:
            logger.warning(f"App not found: {app_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting app details for {app_id}: {str(e)}")
            return None
    
    async def _get_app_reviews(self, app_id: str) -> List[Dict[str, Any]]:
        """
        Get app reviews using google-play-scraper library, prioritizing negative reviews for pain points.
        
        Args:
            app_id: Google Play Store app ID
            
        Returns:
            List of review dictionaries prioritized by negative sentiment
        """
        all_reviews = []
        
        try:
            loop = asyncio.get_event_loop()
            
            # Get most relevant reviews first
            relevant_results = await loop.run_in_executor(
                None,
                lambda: reviews(
                    app_id,
                    lang=self.supported_languages[0],
                    country=self.supported_countries[0],
                    sort=Sort.MOST_RELEVANT,
                    count=self.max_reviews_per_app // 2
                )
            )
            
            if relevant_results and len(relevant_results) > 0:
                all_reviews.extend(relevant_results[0])
            
            # Also get newest reviews to catch recent pain points
            await asyncio.sleep(0.5)  # Rate limiting
            newest_results = await loop.run_in_executor(
                None,
                lambda: reviews(
                    app_id,
                    lang=self.supported_languages[0],
                    country=self.supported_countries[0],
                    sort=Sort.NEWEST,
                    count=self.max_reviews_per_app // 2
                )
            )
            
            if newest_results and len(newest_results) > 0:
                all_reviews.extend(newest_results[0])
            
            # Remove duplicates based on review content
            unique_reviews = []
            seen_content = set()
            
            for review in all_reviews:
                content_key = review.get('content', '')[:50].lower().strip()
                if content_key not in seen_content and len(content_key) > 10:
                    unique_reviews.append(review)
                    seen_content.add(content_key)
            
            # Sort reviews to prioritize negative ones (pain points)
            # Lower scores (1-2 stars) come first, then higher scores
            sorted_reviews = sorted(unique_reviews, key=lambda x: (
                x.get('score', 3),  # Lower scores first
                -x.get('thumbsUpCount', 0)  # Then by helpfulness
            ))
            
            final_reviews = sorted_reviews[:self.max_reviews_per_app]
            
            logger.info(f"Found {len(final_reviews)} prioritized reviews for app: {app_id}")
            return final_reviews
            
        except exceptions.NotFoundError:
            logger.warning(f"No reviews found for app: {app_id}")
            return []
        except Exception as e:
            logger.error(f"Error getting reviews for app {app_id}: {str(e)}")
            return []
    
    async def _extract_competitors_from_search(self, search_results: List[Dict[str, Any]]) -> List[CompetitorData]:
        """
        Extract competitor data from search results with relevance filtering.
        
        Args:
            search_results: List of app data from search
            
        Returns:
            List of relevant CompetitorData objects
        """
        competitors = []
        
        for app_data in search_results:
            try:
                # Check relevance before processing
                if not self._is_app_relevant(app_data):
                    logger.debug(f"Skipping irrelevant app: {app_data.get('title', 'Unknown')}")
                    continue
                
                # Create competitor data primarily from search results to avoid too many API calls
                # Only get detailed info for top apps to respect rate limits
                app_details = None
                if len(competitors) < 5:  # Only get details for top 5 apps
                    try:
                        app_details = await self._get_app_details(app_data['appId'])
                        await asyncio.sleep(0.5)  # Rate limiting delay
                    except Exception as e:
                        logger.debug(f"Failed to get app details for {app_data['appId']}: {str(e)}")
                
                # Double-check relevance with detailed description if available
                if app_details and not self._is_app_relevant_detailed(app_data, app_details):
                    logger.debug(f"Skipping app after detailed check: {app_data.get('title', 'Unknown')}")
                    continue
                
                # Create competitor data using available information
                raw_description = app_details.get('description') if app_details else app_data.get('summary')
                competitor = CompetitorData(
                    name=DataCleaner.clean_html_text(app_data.get('title', 'Unknown App')),
                    description=DataCleaner.clean_html_text(raw_description),
                    website=app_details.get('developerWebsite') if app_details else None,
                    estimated_users=self._format_installs(app_details.get('installs') if app_details else None),
                    estimated_revenue=None,  # Not available from Play Store API
                    pricing_model=self._determine_pricing_model(app_details if app_details else app_data),
                    source=self.source_name,
                    source_url=f"https://play.google.com/store/apps/details?id={app_data['appId']}",
                    confidence_score=0.9 if app_details else 0.8,  # Higher confidence with detailed data
                    launch_date=app_details.get('released') if app_details else None,
                    founder_ceo=DataCleaner.clean_html_text(app_data.get('developer')),
                    review_count=app_details.get('reviews') if app_details else None,
                    average_rating=app_data.get('score'),
                    comments=[],  # Initialize empty comments
                    sentiment_summary=None  # Will be set later
                )
                
                competitors.append(competitor)
                
            except Exception as e:
                logger.debug(f"Failed to create competitor data for app: {str(e)}")
                continue
        
        return competitors
    
    async def _extract_reviews_from_apps(self, app_list: List[Dict[str, Any]]) -> List[FeedbackData]:
        """
        Extract reviews from a list of apps.
        
        Args:
            app_list: List of app data dictionaries
            
        Returns:
            List of FeedbackData objects
        """
        feedback = []
        
        for app_data in app_list:
            try:
                app_id = app_data['appId']
                app_name = app_data.get('title', 'Unknown App')
                
                # Get reviews for this app
                app_reviews = await self._get_app_reviews(app_id)
                
                for review in app_reviews:
                    feedback_item = FeedbackData(
                        text=DataCleaner.clean_html_text(review.get('content', '')),
                        sentiment=None,  # Will be analyzed later
                        sentiment_score=review.get('score'),  # Use review score as sentiment indicator
                        source=self.source_name,
                        source_url=f"https://play.google.com/store/apps/details?id={app_id}",
                        author_info={
                            'app_name': DataCleaner.clean_html_text(app_name),
                            'app_id': app_id,
                            'reviewer': DataCleaner.clean_html_text(review.get('userName')),
                            'review_date': review.get('at'),
                            'thumbs_up': review.get('thumbsUpCount', 0)
                        }
                    )
                    feedback.append(feedback_item)
                
                # Short delay between review requests
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.debug(f"Failed to extract reviews for app: {str(e)}")
                continue
        
        return feedback
    
    async def _extract_reviews_with_sentiment(self, competitor: CompetitorData) -> List[Dict[str, Any]]:
        """
        Extract reviews with sentiment analysis for a Google Play Store app.
        
        Args:
            competitor: CompetitorData object with source_url
            
        Returns:
            List of review dictionaries with sentiment analysis
        """
        comments = []
        
        if not competitor.source_url:
            return comments
        
        try:
            # Extract app ID from source URL
            app_id = competitor.source_url.split('id=')[1].split('&')[0] if 'id=' in competitor.source_url else None
            if not app_id:
                return comments
            
            # Get reviews for this app
            app_reviews = await self._get_app_reviews(app_id)
            
            # Process and analyze sentiment for top reviews
            for i, review in enumerate(app_reviews[:self.max_comments_per_app]):
                try:
                    review_text = DataCleaner.clean_html_text(review.get('content', ''))
                    if not review_text or len(review_text.strip()) < 10:
                        continue
                    
                    # Analyze sentiment
                    sentiment_result = self.sentiment_analyzer.analyze_sentiment(review_text)
                    
                    comment_with_sentiment = {
                        'text': review_text,
                        'author': DataCleaner.clean_html_text(review.get('userName', 'Anonymous')),
                        'sentiment': {
                            'label': sentiment_result.label.value,
                            'score': sentiment_result.score,
                            'confidence': sentiment_result.confidence
                        },
                        'position': i + 1,
                        'rating': review.get('score'),  # Google Play Store specific
                        'thumbs_up': review.get('thumbsUpCount', 0)  # Google Play Store specific
                    }
                    
                    comments.append(comment_with_sentiment)
                    
                except Exception as e:
                    logger.debug(f"Failed to process review: {str(e)}")
                    continue
            
            logger.info(f"Extracted {len(comments)} reviews with sentiment for {competitor.name}")
            
        except Exception as e:
            logger.debug(f"Failed to extract reviews with sentiment for {competitor.name}: {str(e)}")
        
        return comments
    
    async def _add_comments_to_competitor(self, competitor: CompetitorData, comments: List[Dict[str, Any]]) -> None:
        """
        Add comments and sentiment summary to competitor data, prioritizing pain points.
        
        Args:
            competitor: CompetitorData object to enhance
            comments: List of comments with sentiment analysis
        """
        # Categorize comments by sentiment - prioritize negative (pain points)
        negative_comments = []
        neutral_comments = []
        positive_comments = []
        
        for comment in comments:
            sentiment_label = comment.get('sentiment', {}).get('label', 'neutral')
            # Also consider low ratings as negative sentiment indicators
            rating = comment.get('rating', 3)
            
            if sentiment_label == 'negative' or (rating and rating <= 2):
                negative_comments.append(comment)
            elif sentiment_label == 'positive' or (rating and rating >= 4):
                positive_comments.append(comment)
            else:
                neutral_comments.append(comment)
        
        # Sort negative comments by confidence and rating (lower ratings = higher priority pain points)
        negative_comments.sort(key=lambda x: (
            x.get('sentiment', {}).get('confidence', 0),
            -(x.get('rating', 3))  # Lower rating = higher priority
        ), reverse=True)
        
        # Prioritize comments: negative first (pain points), then neutral, then positive
        prioritized_comments = negative_comments + neutral_comments + positive_comments
        
        # Always set comments field with prioritized order
        competitor.comments = prioritized_comments if prioritized_comments else []
        
        if not comments:
            # Set empty sentiment summary if no comments
            competitor.sentiment_summary = {
                'total_comments': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'positive_percentage': 0.0,
                'negative_percentage': 0.0,
                'neutral_percentage': 0.0,
                'average_sentiment_score': 0.0,
                'overall_sentiment': 'neutral',
                'pain_points': [],
                'pain_point_categories': {},
                'positive_feedback': [],
                'neutral_feedback': []
            }
            return
        
        # Calculate sentiment summary with categorized feedback
        sentiment_labels = [comment['sentiment']['label'] for comment in comments]
        sentiment_scores = [comment['sentiment']['score'] for comment in comments]
        
        positive_count = sentiment_labels.count('positive')
        negative_count = sentiment_labels.count('negative')
        neutral_count = sentiment_labels.count('neutral')
        
        average_sentiment_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        # Extract key pain points from negative comments
        pain_points = []
        for comment in negative_comments[:5]:  # Top 5 pain points
            pain_points.append({
                'text': comment['text'][:200] + '...' if len(comment['text']) > 200 else comment['text'],
                'author': comment.get('author', 'Anonymous'),
                'rating': comment.get('rating'),
                'confidence': comment.get('sentiment', {}).get('confidence', 0),
                'thumbs_up': comment.get('thumbs_up', 0)
            })
        
        # Categorize pain points by theme
        pain_point_categories = self._categorize_pain_points(negative_comments)
        
        # Extract positive feedback highlights
        positive_feedback = []
        for comment in positive_comments[:2]:  # Top 2 positive highlights
            positive_feedback.append({
                'text': comment['text'][:200] + '...' if len(comment['text']) > 200 else comment['text'],
                'author': comment.get('author', 'Anonymous'),
                'rating': comment.get('rating'),
                'confidence': comment.get('sentiment', {}).get('confidence', 0),
                'thumbs_up': comment.get('thumbs_up', 0)
            })
        
        # Extract neutral feedback
        neutral_feedback = []
        for comment in neutral_comments[:2]:  # Top 2 neutral comments
            neutral_feedback.append({
                'text': comment['text'][:200] + '...' if len(comment['text']) > 200 else comment['text'],
                'author': comment.get('author', 'Anonymous'),
                'rating': comment.get('rating'),
                'thumbs_up': comment.get('thumbs_up', 0)
            })
        
        competitor.sentiment_summary = {
            'total_comments': len(comments),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'positive_percentage': round((positive_count / len(comments)) * 100, 1),
            'negative_percentage': round((negative_count / len(comments)) * 100, 1),
            'neutral_percentage': round((neutral_count / len(comments)) * 100, 1),
            'average_sentiment_score': round(average_sentiment_score, 3),
            'overall_sentiment': self._determine_overall_sentiment(average_sentiment_score),
            'pain_points': pain_points,  # Prioritized pain points
            'pain_point_categories': pain_point_categories,  # Categorized pain points
            'positive_feedback': positive_feedback,
            'neutral_feedback': neutral_feedback
        }
        
        logger.info(f"Added {len(comments)} reviews to {competitor.name} - Pain points: {len(pain_points)}, Positive: {len(positive_feedback)}")
    
    def _determine_overall_sentiment(self, average_score: float) -> str:
        """
        Determine overall sentiment based on average score.
        
        Args:
            average_score: Average sentiment score
            
        Returns:
            Overall sentiment label
        """
        if average_score > 0.1:
            return 'positive'
        elif average_score < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def _categorize_pain_points(self, negative_comments: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Categorize pain points from negative comments into common themes.
        
        Args:
            negative_comments: List of negative comments
            
        Returns:
            Dictionary of categorized pain points
        """
        categories = {
            'usability': [],
            'performance': [],
            'features': [],
            'pricing': [],
            'support': [],
            'bugs': [],
            'other': []
        }
        
        # Keywords for categorization
        category_keywords = {
            'usability': ['confusing', 'difficult', 'hard to use', 'complicated', 'interface', 'ui', 'ux', 'navigation'],
            'performance': ['slow', 'crash', 'freeze', 'lag', 'loading', 'speed', 'performance', 'battery'],
            'features': ['missing', 'lack', 'need', 'want', 'feature', 'functionality', 'option'],
            'pricing': ['expensive', 'price', 'cost', 'money', 'subscription', 'payment', 'billing'],
            'support': ['support', 'help', 'customer service', 'response', 'contact'],
            'bugs': ['bug', 'error', 'broken', 'issue', 'problem', 'glitch', 'not working']
        }
        
        for comment in negative_comments:
            text = comment.get('text', '').lower()
            categorized = False
            
            for category, keywords in category_keywords.items():
                if any(keyword in text for keyword in keywords):
                    categories[category].append(comment.get('text', '')[:150])
                    categorized = True
                    break
            
            if not categorized:
                categories['other'].append(comment.get('text', '')[:150])
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    
    def _generate_search_queries(self, keywords: List[str], idea_text: str) -> List[str]:
        """
        Generate focused search queries for Google Play Store.
        
        Args:
            keywords: List of keywords from the idea
            idea_text: Original idea text
            
        Returns:
            List of focused search query strings
        """
        queries = []
        
        # Combine keywords to create more specific searches
        if len(keywords) >= 2:
            # Primary search: combine main keywords
            primary_query = " ".join(keywords[:2])
            queries.append(primary_query)
            
            # Secondary searches: each keyword with "app"
            for keyword in keywords[:2]:
                if len(keyword) > 2:
                    queries.append(f"{keyword} app")
        else:
            # Single keyword searches
            for keyword in keywords[:2]:
                if len(keyword) > 2:
                    queries.append(keyword)
                    queries.append(f"{keyword} app")
        
        # Add category-specific searches only if relevant
        main_keyword = keywords[0].lower() if keywords else ""
        
        # Define category mappings for better targeting
        category_mappings = {
            'fitness': ['fitness', 'workout', 'exercise', 'health'],
            'productivity': ['productivity', 'task', 'todo', 'work'],
            'business': ['business', 'finance', 'accounting', 'crm'],
            'education': ['education', 'learning', 'study', 'school'],
            'entertainment': ['game', 'music', 'video', 'entertainment'],
            'social': ['social', 'chat', 'messaging', 'dating'],
            'shopping': ['shopping', 'ecommerce', 'store', 'marketplace']
        }
        
        # Only add category searches if the main keyword matches a category
        for category, related_terms in category_mappings.items():
            if any(term in main_keyword for term in related_terms):
                if len(keywords) >= 2:
                    queries.append(f"{keywords[1]} {category}")
                break
        
        # Remove duplicates and limit
        unique_queries = list(dict.fromkeys(queries))  # Preserves order
        return unique_queries[:4]  # Limit to 4 focused queries
    
    def _format_installs(self, installs: Optional[str]) -> Optional[str]:
        """
        Format install count for display.
        
        Args:
            installs: Install count string from Play Store
            
        Returns:
            Formatted install count or None
        """
        if not installs:
            return None
        
        # Convert to more readable format
        if isinstance(installs, str):
            return installs
        elif isinstance(installs, int):
            if installs >= 1000000:
                return f"{installs // 1000000}M+"
            elif installs >= 1000:
                return f"{installs // 1000}K+"
            else:
                return str(installs)
        
        return str(installs)
    
    def _determine_pricing_model(self, app_data: Dict[str, Any]) -> str:
        """
        Determine the pricing model of an app.
        
        Args:
            app_data: App data dictionary
            
        Returns:
            Pricing model string
        """
        if app_data.get('free', True):
            # Check if it has in-app purchases
            if app_data.get('offersIAP', False):
                return 'Freemium'
            else:
                return 'Free'
        else:
            price = app_data.get('price')
            if price:
                return f'Paid ({price})'
            else:
                return 'Paid'
    
    def _deduplicate_competitors(self, competitors: List[CompetitorData]) -> List[CompetitorData]:
        """
        Remove duplicate competitors based on name.
        
        Args:
            competitors: List of CompetitorData objects
            
        Returns:
            List of unique CompetitorData objects
        """
        seen = set()
        unique_competitors = []
        
        for competitor in competitors:
            identifier = competitor.name.lower().strip()
            if identifier not in seen and len(identifier) > 1:
                seen.add(identifier)
                unique_competitors.append(competitor)
        
        return unique_competitors
    
    def _deduplicate_feedback(self, feedback: List[FeedbackData]) -> List[FeedbackData]:
        """
        Remove duplicate feedback based on text content.
        
        Args:
            feedback: List of FeedbackData objects
            
        Returns:
            List of unique FeedbackData objects
        """
        seen = set()
        unique_feedback = []
        
        for item in feedback:
            # Create identifier based on first 50 characters of text
            identifier = item.text[:50].lower().strip()
            if identifier not in seen and len(identifier) > 10:
                seen.add(identifier)
                unique_feedback.append(item)
        
        return unique_feedback
    
    def _is_app_relevant(self, app_data: Dict[str, Any]) -> bool:
        """
        Check if an app is relevant to the search query based on basic criteria.
        
        Args:
            app_data: App data from search results
            
        Returns:
            True if app appears relevant, False otherwise
        """
        app_name = app_data.get('title', '').lower()
        app_summary = app_data.get('summary', '').lower()
        developer = app_data.get('developer', '').lower()
        
        # Skip generic system apps and major platforms
        generic_apps = [
            'gmail', 'google messages', 'instagram', 'snapchat', 'whatsapp', 
            'messenger', 'telegram', 'discord', 'tiktok', 'youtube', 'netflix',
            'google maps', 'google photos', 'contacts', 'phone', 'chrome',
            'facebook', 'twitter', 'linkedin', 'pinterest'
        ]
        
        # Skip if it's a generic app unless it's specifically relevant
        for generic in generic_apps:
            if generic in app_name and not self._has_relevant_keywords(app_name + ' ' + app_summary):
                return False
        
        # Skip Google/Meta system apps unless specifically relevant
        system_developers = ['google llc', 'meta platforms', 'facebook']
        if any(dev in developer for dev in system_developers):
            if not self._has_relevant_keywords(app_name + ' ' + app_summary):
                return False
        
        return True
    
    def _is_app_relevant_detailed(self, app_data: Dict[str, Any], app_details: Dict[str, Any]) -> bool:
        """
        Perform detailed relevance check using full app description.
        
        Args:
            app_data: Basic app data from search
            app_details: Detailed app data
            
        Returns:
            True if app is relevant, False otherwise
        """
        full_description = app_details.get('description', '').lower()
        app_name = app_data.get('title', '').lower()
        
        # Combine all text for analysis
        full_text = f"{app_name} {full_description}"
        
        return self._has_relevant_keywords(full_text)
    
    def _has_relevant_keywords(self, text: str) -> bool:
        """
        Check if text contains keywords relevant to the search query.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if text contains relevant keywords
        """
        if not hasattr(self, 'search_keywords') or not self.search_keywords:
            return True  # If no keywords set, allow all
        
        text_lower = text.lower()
        
        # Check for direct keyword matches
        direct_matches = sum(1 for keyword in self.search_keywords if keyword in text_lower)
        if direct_matches > 0:
            return True
        
        # Define category-specific related terms
        category_terms = {
            'fitness': [
                'fitness', 'workout', 'exercise', 'gym', 'health', 'training',
                'muscle', 'cardio', 'yoga', 'running', 'weight', 'diet',
                'nutrition', 'calories', 'steps', 'activity', 'sport', 'bodybuilding',
                'strength', 'endurance', 'pilates', 'crossfit', 'marathon', 'cycling'
            ],
            'productivity': [
                'productivity', 'task', 'todo', 'project', 'organize', 'planning',
                'schedule', 'calendar', 'note', 'reminder', 'workflow', 'efficiency',
                'time management', 'gtd', 'kanban', 'scrum', 'agile'
            ],
            'business': [
                'business', 'finance', 'accounting', 'invoice', 'sales', 'crm',
                'marketing', 'analytics', 'revenue', 'customer', 'lead', 'profit',
                'enterprise', 'commerce', 'trading', 'investment', 'startup'
            ],
            'education': [
                'education', 'learning', 'study', 'school', 'course', 'lesson',
                'tutorial', 'training', 'skill', 'knowledge', 'academic', 'student'
            ],
            'social': [
                'social', 'chat', 'messaging', 'communication', 'network', 'community',
                'friends', 'dating', 'relationship', 'connect', 'share'
            ],
            'entertainment': [
                'game', 'gaming', 'entertainment', 'fun', 'play', 'music', 'video',
                'movie', 'streaming', 'media', 'content'
            ]
        }
        
        # Check if any search keyword matches a category and if text contains related terms
        for search_keyword in self.search_keywords:
            for category, terms in category_terms.items():
                if search_keyword in terms:
                    # If search keyword is in this category, check for related terms
                    related_matches = sum(1 for term in terms if term in text_lower)
                    if related_matches > 0:
                        return True
        
        # Check for app-specific terms if "app" is in search keywords
        if 'app' in self.search_keywords:
            app_terms = ['application', 'mobile', 'android', 'smartphone', 'device']
            app_matches = sum(1 for term in app_terms if term in text_lower)
            if app_matches > 0:
                return True
        
        return False