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
        Get app reviews using google-play-scraper library.
        
        Args:
            app_id: Google Play Store app ID
            
        Returns:
            List of review dictionaries
        """
        try:
            loop = asyncio.get_event_loop()
            review_results = await loop.run_in_executor(
                None,
                lambda: reviews(
                    app_id,
                    lang=self.supported_languages[0],
                    country=self.supported_countries[0],
                    sort=Sort.MOST_RELEVANT,
                    count=self.max_reviews_per_app
                )
            )
            
            # Extract reviews from the result tuple
            review_list = review_results[0] if review_results and len(review_results) > 0 else []
            
            logger.info(f"Found {len(review_list)} reviews for app: {app_id}")
            return review_list
            
        except exceptions.NotFoundError:
            logger.warning(f"No reviews found for app: {app_id}")
            return []
        except Exception as e:
            logger.error(f"Error getting reviews for app {app_id}: {str(e)}")
            return []
    
    async def _extract_competitors_from_search(self, search_results: List[Dict[str, Any]]) -> List[CompetitorData]:
        """
        Extract competitor data from search results.
        
        Args:
            search_results: List of app data from search
            
        Returns:
            List of CompetitorData objects
        """
        competitors = []
        
        for app_data in search_results:
            try:
                # Create competitor data primarily from search results to avoid too many API calls
                # Only get detailed info for top apps to respect rate limits
                app_details = None
                if len(competitors) < 5:  # Only get details for top 5 apps
                    try:
                        app_details = await self._get_app_details(app_data['appId'])
                        await asyncio.sleep(0.5)  # Rate limiting delay
                    except Exception as e:
                        logger.debug(f"Failed to get app details for {app_data['appId']}: {str(e)}")
                
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
                    average_rating=app_data.get('score')
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
    
    def _generate_search_queries(self, keywords: List[str], idea_text: str) -> List[str]:
        """
        Generate search queries for Google Play Store.
        
        Args:
            keywords: List of keywords from the idea
            idea_text: Original idea text
            
        Returns:
            List of search query strings
        """
        queries = []
        
        # Use top keywords directly
        for keyword in keywords[:3]:
            if len(keyword) > 2:  # Skip very short keywords
                queries.append(keyword)
        
        # Add category-based searches
        categories = ['productivity', 'business', 'tools', 'lifestyle', 'health', 'fitness']
        for keyword in keywords[:2]:
            for category in categories[:2]:
                if keyword.lower() != category:
                    queries.append(f"{keyword} {category}")
        
        # Add app-specific searches
        for keyword in keywords[:2]:
            queries.append(f"{keyword} app")
            queries.append(f"{keyword} mobile")
        
        # Remove duplicates and limit
        unique_queries = list(dict.fromkeys(queries))  # Preserves order
        return unique_queries[:6]  # Limit to 6 queries
    
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