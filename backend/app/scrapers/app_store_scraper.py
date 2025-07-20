"""
iOS App Store scraper using app-store-web-scraper library for reliable iOS app data extraction.
"""
import asyncio
import logging
import random
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from app_store_web_scraper import AppStoreSession, AppStoreEntry
except ImportError:
    # Fallback if library structure is different
    try:
        import app_store_web_scraper as asws
        AppStoreSession = getattr(asws, 'AppStoreSession', None)
        AppStoreEntry = getattr(asws, 'AppStoreEntry', None)
    except:
        AppStoreSession = None
        AppStoreEntry = None

from .base_scraper import BaseScraper, ScrapingResult, ScrapingStatus, CompetitorData, FeedbackData
from ..utils.data_cleaner import DataCleaner


logger = logging.getLogger(__name__)


class AppStoreScraper(BaseScraper):
    """Scraper for iOS App Store using app-store-web-scraper library for reliable iOS app data extraction."""
    
    def __init__(self):
        """Initialize the iOS App Store scraper with app-store-web-scraper library."""
        super().__init__("iOS App Store")
        self.max_results_per_query = 20
        self.max_queries = 3
        self.max_reviews_per_app = 5
        self.delay_between_requests = (1, 3)
        self.supported_countries = ['us', 'gb', 'ca']
        
        if AppStoreSession:
            self.session = AppStoreSession()
        else:
            self.session = None
            logger.warning("AppStoreSession not available, falling back to iTunes API")
    
    def validate_config(self) -> bool:
        """Validate that the iOS App Store scraper is properly configured."""
        try:
            if self.max_results_per_query <= 0:
                logger.error("Invalid max_results_per_query for iOS App Store scraper")
                return False
            
            if self.max_queries <= 0:
                logger.error("Invalid max_queries for iOS App Store scraper")
                return False
            
            if not self.supported_countries:
                logger.error("No supported countries configured for iOS App Store scraper")
                return False
            
            logger.info("iOS App Store scraper configuration is valid")
            return True
            
        except Exception as e:
            logger.error(f"iOS App Store scraper configuration validation failed: {str(e)}")
            return False
    
    async def scrape(self, keywords: List[str], idea_text: str) -> ScrapingResult:
        """Scrape iOS App Store using app-store-scraper library for iOS app data."""
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
                "scraping_method": "app-store-scraper-api"
            }
            
            search_queries = self._generate_search_queries(keywords, idea_text)
            metadata["search_queries"] = search_queries
            
            for query in search_queries[:self.max_queries]:
                try:
                    logger.info(f"Searching iOS App Store for: {query}")
                    
                    search_results = await self._search_apps(query)
                    metadata["api_calls_made"] += 1
                    
                    if search_results:
                        query_competitors = await self._extract_competitors_from_search(search_results)
                        competitors.extend(query_competitors)
                        
                        query_feedback = await self._extract_reviews_from_apps(search_results[:3])
                        feedback.extend(query_feedback)
                        
                        metadata["successful_queries"] += 1
                        metadata["keywords_searched"].append(query)
                        metadata["apps_found"] += len(query_competitors)
                        metadata["reviews_extracted"] += len(query_feedback)
                        
                        logger.info(f"Found {len(query_competitors)} apps and {len(query_feedback)} reviews for query: {query}")
                    else:
                        logger.warning(f"No results found for query: {query}")
                        metadata["failed_queries"] += 1
                    
                    delay = random.uniform(*self.delay_between_requests)
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    logger.warning(f"Failed to search for query '{query}': {str(e)}")
                    metadata["failed_queries"] += 1
                    continue
            
            unique_competitors = self._deduplicate_competitors(competitors)
            unique_feedback = self._deduplicate_feedback(feedback)
            
            if metadata["successful_queries"] > 0:
                status = ScrapingStatus.SUCCESS if len(unique_competitors) > 0 else ScrapingStatus.PARTIAL_SUCCESS
            else:
                status = ScrapingStatus.FAILED
            
            metadata.update({
                "total_competitors": len(unique_competitors),
                "total_feedback": len(unique_feedback),
                "success_rate": metadata["successful_queries"] / len(search_queries) if search_queries else 0
            })
            
            logger.info(f"iOS App Store scraping completed: {len(unique_competitors)} apps, "
                       f"{len(unique_feedback)} reviews, "
                       f"{metadata['successful_queries']}/{len(search_queries)} successful queries")
            
            return ScrapingResult(
                status=status,
                competitors=unique_competitors[:15],
                feedback=unique_feedback[:20],
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"iOS App Store scraping failed: {str(e)}")
            return ScrapingResult(
                status=ScrapingStatus.FAILED,
                competitors=[],
                feedback=[],
                error_message=str(e),
                metadata=metadata or {}
            )
    
    async def _search_apps(self, query: str) -> List[Dict[str, Any]]:
        """Search for apps using app-store-web-scraper library or iTunes Search API fallback."""
        try:
            if self.session and hasattr(self.session, 'search'):
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    None,
                    lambda: self.session.search(query, limit=self.max_results_per_query)
                )
                logger.info(f"Found {len(results)} iOS apps for query: {query}")
                return results
            else:
                return await self._search_apps_itunes_api(query)
            
        except Exception as e:
            logger.error(f"Error searching for iOS apps with query '{query}': {str(e)}")
            try:
                return await self._search_apps_itunes_api(query)
            except Exception as fallback_error:
                logger.error(f"Fallback search also failed: {str(fallback_error)}")
                return []
    
    async def _search_apps_itunes_api(self, query: str) -> List[Dict[str, Any]]:
        """Fallback search using iTunes Search API."""
        import aiohttp
        
        try:
            params = {
                'term': query,
                'media': 'software',
                'entity': 'software',
                'country': 'us',
                'limit': self.max_results_per_query
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin'
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get('https://itunes.apple.com/search', params=params) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'application/json' in content_type:
                            data = await response.json()
                            results = data.get('results', [])
                            
                            converted_results = []
                            for item in results:
                                converted_results.append({
                                    'id': item.get('trackId'),
                                    'name': item.get('trackName'),
                                    'title': item.get('trackName'),
                                    'developer': item.get('artistName'),
                                    'artist_name': item.get('artistName'),
                                    'description': item.get('description', ''),
                                    'rating': item.get('averageUserRating'),
                                    'average_rating': item.get('averageUserRating'),
                                    'rating_count': item.get('userRatingCount'),
                                    'price': item.get('price', 0),
                                    'formatted_price': item.get('formattedPrice', 'Free'),
                                    'url': item.get('trackViewUrl'),
                                    'app_url': item.get('trackViewUrl'),
                                    'release_date': item.get('releaseDate'),
                                    'developer_url': item.get('sellerUrl')
                                })
                            
                            logger.info(f"Found {len(converted_results)} iOS apps for query: {query} (iTunes API)")
                            return converted_results
                        else:
                            logger.warning(f"iTunes API returned non-JSON content: {content_type}")
                            return []
                    else:
                        logger.error(f"iTunes Search API returned status {response.status} for query: {query}")
                        return []
            
        except Exception as e:
            logger.error(f"Error with iTunes Search API for query '{query}': {str(e)}")
            return []
    
    async def _get_app_details(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed app information using app-store-web-scraper library or AppStoreEntry."""
        try:
            if AppStoreEntry:
                loop = asyncio.get_event_loop()
                app_entry = await loop.run_in_executor(
                    None,
                    lambda: AppStoreEntry(app_id)
                )
                
                details = {
                    'description': getattr(app_entry, 'description', ''),
                    'developer_website': getattr(app_entry, 'developer_website', None),
                    'release_date': getattr(app_entry, 'release_date', None),
                    'review_count': getattr(app_entry, 'review_count', None),
                    'rating': getattr(app_entry, 'rating', None),
                    'price': getattr(app_entry, 'price', 0),
                    'in_app_purchases': getattr(app_entry, 'offers_in_app_purchases', False)
                }
                
                return details
            else:
                return await self._get_app_details_itunes_api(app_id)
            
        except Exception as e:
            logger.error(f"Error getting iOS app details for {app_id}: {str(e)}")
            try:
                return await self._get_app_details_itunes_api(app_id)
            except Exception as fallback_error:
                logger.error(f"Fallback app details also failed: {str(fallback_error)}")
                return None
    
    async def _get_app_details_itunes_api(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Fallback method to get app details using iTunes Lookup API."""
        import aiohttp
        
        try:
            params = {
                'id': app_id,
                'country': 'us'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get('https://itunes.apple.com/lookup', params=params) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'application/json' in content_type:
                            data = await response.json()
                            results = data.get('results', [])
                            if results:
                                item = results[0]
                                return {
                                    'description': item.get('description', ''),
                                    'developer_website': item.get('sellerUrl'),
                                    'release_date': item.get('releaseDate'),
                                    'review_count': item.get('userRatingCount'),
                                    'rating': item.get('averageUserRating'),
                                    'price': item.get('price', 0),
                                    'in_app_purchases': 'iosUniversal' in item.get('features', [])
                                }
                    else:
                        logger.error(f"iTunes Lookup API returned status {response.status} for app ID: {app_id}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error with iTunes Lookup API for app {app_id}: {str(e)}")
            return None
    
    async def _get_app_reviews(self, app_id: str) -> List[Dict[str, Any]]:
        """Get app reviews using app-store-web-scraper library."""
        try:
            if AppStoreEntry:
                loop = asyncio.get_event_loop()
                app_entry = await loop.run_in_executor(
                    None,
                    lambda: AppStoreEntry(app_id)
                )
                
                reviews_data = await loop.run_in_executor(
                    None,
                    lambda: app_entry.reviews(limit=self.max_reviews_per_app)
                )
                
                reviews = []
                for review in reviews_data:
                    reviews.append({
                        'content': getattr(review, 'content', ''),
                        'review': getattr(review, 'content', ''),
                        'rating': getattr(review, 'rating', None),
                        'author': getattr(review, 'author', ''),
                        'user_name': getattr(review, 'author', ''),
                        'date': getattr(review, 'date', None),
                        'title': getattr(review, 'title', '')
                    })
                
                logger.info(f"Found {len(reviews)} reviews for iOS app: {app_id}")
                return reviews
            else:
                logger.warning(f"Cannot get reviews for app {app_id} - AppStoreEntry not available")
                return []
            
        except Exception as e:
            logger.error(f"Error getting reviews for iOS app {app_id}: {str(e)}")
            return []
    
    async def _extract_competitors_from_search(self, search_results: List[Dict[str, Any]]) -> List[CompetitorData]:
        """Extract competitor data from app-store-web-scraper results."""
        competitors = []
        
        logger.info(f"Extracting competitors from {len(search_results)} search results")
        
        for i, app_data in enumerate(search_results):
            try:
                if not app_data:
                    logger.debug(f"Skipping empty app data at index {i}")
                    continue
                
                app_name = app_data.get('name') or app_data.get('title')
                logger.info(f"Processing app {i+1}: {app_name}")
                
                if not app_name or app_name.strip() == '':
                    logger.debug(f"Skipping app with invalid name: {app_data}")
                    continue
                
                competitor = CompetitorData(
                    name=DataCleaner.clean_html_text(app_name),
                    description=DataCleaner.clean_html_text(app_data.get('description', '')),
                    website=app_data.get('developer_url'),
                    estimated_users=None,
                    estimated_revenue=None,
                    pricing_model=self._determine_pricing_model(app_data),
                    source=self.source_name,
                    source_url=app_data.get('url') or app_data.get('app_url', ''),
                    confidence_score=0.8,
                    launch_date=app_data.get('release_date'),
                    founder_ceo=DataCleaner.clean_html_text(app_data.get('developer') or app_data.get('artist_name')),
                    review_count=app_data.get('rating_count'),
                    average_rating=app_data.get('rating') or app_data.get('average_rating')
                )
                
                logger.info(f"Created competitor: {competitor.name}")
                competitors.append(competitor)
                
            except Exception as e:
                logger.error(f"Failed to create competitor data for iOS app at index {i}: {str(e)}")
                logger.debug(f"App data that failed: {app_data}")
                continue
        
        logger.info(f"Successfully created {len(competitors)} competitors")
        return competitors
    
    async def _extract_reviews_from_apps(self, app_list: List[Dict[str, Any]]) -> List[FeedbackData]:
        """Extract reviews from a list of apps using app-store-web-scraper."""
        feedback = []
        
        for app_data in app_list:
            try:
                app_id = app_data.get('id') or app_data.get('app_id')
                app_name = app_data.get('name') or app_data.get('title', 'Unknown App')
                
                if not app_id:
                    continue
                
                app_reviews = await self._get_app_reviews(str(app_id))
                
                for review in app_reviews:
                    feedback_item = FeedbackData(
                        text=DataCleaner.clean_html_text(review.get('review') or review.get('content', '')),
                        sentiment=None,
                        sentiment_score=review.get('rating'),
                        source=self.source_name,
                        source_url=app_data.get('url') or app_data.get('app_url', ''),
                        author_info={
                            'app_name': DataCleaner.clean_html_text(app_name),
                            'app_id': str(app_id),
                            'reviewer': DataCleaner.clean_html_text(review.get('user_name') or review.get('author')),
                            'review_date': review.get('date'),
                            'review_title': DataCleaner.clean_html_text(review.get('title')),
                            'rating': review.get('rating')
                        }
                    )
                    feedback.append(feedback_item)
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.debug(f"Failed to extract reviews for iOS app: {str(e)}")
                continue
        
        return feedback
    
    def _generate_search_queries(self, keywords: List[str], idea_text: str) -> List[str]:
        """Generate search queries for iOS App Store."""
        queries = []
        
        for keyword in keywords[:3]:
            if len(keyword) > 2:
                queries.append(keyword)
        
        categories = ['productivity', 'business', 'utilities', 'lifestyle', 'health', 'fitness']
        for keyword in keywords[:2]:
            for category in categories[:2]:
                if keyword.lower() != category:
                    queries.append(f"{keyword} {category}")
        
        for keyword in keywords[:2]:
            queries.append(f"{keyword} app")
            queries.append(f"{keyword} iOS")
        
        unique_queries = list(dict.fromkeys(queries))
        return unique_queries[:6]
    
    def _determine_pricing_model(self, app_data: Dict[str, Any]) -> str:
        """Determine the pricing model of an app from app-store-web-scraper data."""
        price = app_data.get('price', 0)
        formatted_price = app_data.get('formatted_price', 'Free')
        
        if price == 0 or price == '0' or formatted_price == 'Free' or formatted_price == '$0.00':
            has_iap = app_data.get('in_app_purchases', False) or app_data.get('offers_in_app_purchases', False)
            if has_iap:
                return 'Freemium'
            else:
                return 'Free'
        else:
            return f'Paid ({formatted_price})'
    
    def _deduplicate_competitors(self, competitors: List[CompetitorData]) -> List[CompetitorData]:
        """Remove duplicate competitors based on name."""
        seen = set()
        unique_competitors = []
        
        for competitor in competitors:
            if competitor and competitor.name:
                identifier = competitor.name.lower().strip()
                if identifier not in seen and len(identifier) > 1:
                    seen.add(identifier)
                    unique_competitors.append(competitor)
        
        return unique_competitors
    
    def _deduplicate_feedback(self, feedback: List[FeedbackData]) -> List[FeedbackData]:
        """Remove duplicate feedback based on text content."""
        seen = set()
        unique_feedback = []
        
        for item in feedback:
            if item and item.text:
                identifier = item.text[:50].lower().strip()
                if identifier not in seen and len(identifier) > 10:
                    seen.add(identifier)
                    unique_feedback.append(item)
        
        return unique_feedback