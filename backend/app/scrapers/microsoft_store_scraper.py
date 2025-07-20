"""
Microsoft Store scraper using Patchright headless browser for Windows app data extraction.
"""
import asyncio
import logging
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote_plus

from patchright.async_api import Page

from .base_scraper import BaseScraper, ScrapingResult, ScrapingStatus, CompetitorData, FeedbackData
from ..services.headless_browser_service import get_browser_service


logger = logging.getLogger(__name__)


class MicrosoftStoreScraper(BaseScraper):
    """Scraper for Microsoft Store using Patchright headless browser to extract Windows app data."""
    
    def __init__(self):
        """Initialize the Microsoft Store scraper with Patchright browser automation."""
        super().__init__("Microsoft Store")
        self.base_url = "https://apps.microsoft.com"
        self.search_url = "https://apps.microsoft.com/search"
        self.max_results = 20
        self.timeout = 30
        self.max_retries = 3
        self.delay_between_requests = (2, 6)  # Random delay range in seconds
        
        # Stealth configuration for Microsoft Store
        self.stealth_config = {
            'enable_human_delays': True,
            'enable_mouse_movements': True,
            'enable_scroll_simulation': True,
            'enable_typing_delays': True,
            'min_delay_ms': 600,
            'max_delay_ms': 2400,
            'typing_speed_wpm': random.randint(40, 70),
        }
        
        # User agents optimized for Microsoft Store
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        ]
        
        # Viewport sizes
        self.viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
        ]
    
    def validate_config(self) -> bool:
        """
        Validate that the Microsoft Store scraper is properly configured.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            if not self.user_agents or len(self.user_agents) == 0:
                logger.error("No user agents configured for Microsoft Store scraper")
                return False
            
            if not self.base_url or not self.base_url.startswith('http'):
                logger.error("Invalid base URL for Microsoft Store scraper")
                return False
            
            if self.timeout <= 0 or self.max_retries <= 0:
                logger.error("Invalid timeout or retry settings for Microsoft Store scraper")
                return False
            
            logger.info("Microsoft Store scraper configuration is valid")
            return True
            
        except Exception as e:
            logger.error(f"Microsoft Store scraper configuration validation failed: {str(e)}")
            return False
    
    async def scrape(self, keywords: List[str], idea_text: str) -> ScrapingResult:
        """
        Scrape Microsoft Store using Patchright headless browser for Windows app data.
        
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
                "browser_sessions_used": 0,
                "source": self.source_name,
                "scraping_method": "browser"
            }
            
            # Generate search queries based on keywords and idea text
            search_queries = self._generate_search_queries(keywords, idea_text)
            metadata["search_queries"] = search_queries
            
            # Get browser service
            browser_service = await get_browser_service()
            
            # Execute searches for each query
            for query in search_queries[:3]:  # Limit to top 3 queries
                try:
                    # Use browser service with stealth configuration
                    search_results = await browser_service.scrape_url(
                        url=self._build_search_url(query),
                        scraper_function=lambda page: self._scrape_search_page(page, query),
                        max_retries=self.max_retries,
                        stealth_config=self._get_dynamic_stealth_config()
                    )
                    
                    metadata["browser_sessions_used"] += 1
                    
                    # Extract app information from search results
                    query_competitors = await self._extract_app_competitors(search_results, browser_service)
                    competitors.extend(query_competitors)
                    
                    # Extract reviews and feedback
                    query_feedback = await self._extract_app_feedback(search_results, browser_service)
                    feedback.extend(query_feedback)
                    
                    metadata["successful_queries"] += 1
                    metadata["keywords_searched"].append(query)
                    metadata["apps_found"] += len(query_competitors)
                    metadata["reviews_extracted"] += len(query_feedback)
                    
                    # Human-like delay between requests
                    delay = random.uniform(*self.delay_between_requests)
                    logger.info(f"Waiting {delay:.1f} seconds before next search...")
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    logger.warning(f"Failed to execute Microsoft Store search for query '{query}': {str(e)}")
                    metadata["failed_queries"] += 1
                    
                    # Exponential backoff on failures
                    backoff_delay = min(15, 2 ** metadata["failed_queries"])
                    await asyncio.sleep(backoff_delay)
                    continue
            
            # Remove duplicate competitors
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
            
            logger.info(f"Microsoft Store scraping completed: {len(unique_competitors)} apps, "
                       f"{len(unique_feedback)} reviews, "
                       f"{metadata['successful_queries']}/{len(search_queries)} successful queries")
            
            return ScrapingResult(
                status=status,
                competitors=unique_competitors[:10],  # Limit to top 10 apps
                feedback=unique_feedback[:15],  # Limit to top 15 reviews
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Microsoft Store scraping failed: {str(e)}")
            return ScrapingResult(
                status=ScrapingStatus.FAILED,
                competitors=[],
                feedback=[],
                error_message=str(e),
                metadata=metadata
            )
    
    def _build_search_url(self, query: str) -> str:
        """Build Microsoft Store search URL."""
        encoded_query = quote_plus(query)
        return f"{self.search_url}?query={encoded_query}"
    
    def _get_dynamic_stealth_config(self) -> Dict[str, Any]:
        """Get dynamic stealth configuration with randomization."""
        config = self.stealth_config.copy()
        config['user_agent'] = random.choice(self.user_agents)
        config['viewport'] = random.choice(self.viewports)
        config['typing_speed_wpm'] = random.randint(40, 70)
        config['min_delay_ms'] = random.randint(400, 900)
        config['max_delay_ms'] = random.randint(1600, 3200)
        return config
    
    async def _scrape_search_page(self, page: Page, query: str) -> Dict[str, Any]:
        """Scrape Microsoft Store search page."""
        results = {
            "query": query,
            "apps": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Wait for page to load
            await page.wait_for_load_state('networkidle', timeout=30000)
            
            # Simulate human reading behavior
            await self._simulate_human_behavior(page)
            
            # Extract app results
            await self._extract_app_results(page, results)
            
            logger.info(f"Successfully scraped Microsoft Store search page for query: {query}")
            logger.info(f"Found {len(results['apps'])} apps")
            
            return results
            
        except Exception as e:
            logger.error(f"Error scraping Microsoft Store search page for query '{query}': {str(e)}")
            raise
    
    async def _simulate_human_behavior(self, page: Page) -> None:
        """Simulate human behavior on the page."""
        # Random delay to simulate reading
        reading_delay = random.uniform(1.0, 3.2)
        await asyncio.sleep(reading_delay)
        
        # Simulate scrolling
        try:
            for _ in range(random.randint(2, 4)):
                scroll_distance = random.randint(350, 750)
                await page.mouse.wheel(0, scroll_distance)
                await asyncio.sleep(random.uniform(0.5, 1.3))
        except Exception:
            pass
    
    async def _extract_app_results(self, page: Page, results: Dict[str, Any]) -> None:
        """Extract app results from search page."""
        # Microsoft Store result selectors
        app_selectors = [
            'div[data-testid="product-card"]',  # Main app card
            'div.ProductCard',  # Alternative card
            'article[role="listitem"]',  # List item
            'div.ms-List-cell',  # List cell
        ]
        
        for selector in app_selectors:
            try:
                app_elements = await page.query_selector_all(selector)
                if app_elements:
                    logger.info(f"Found {len(app_elements)} apps with selector: {selector}")
                    
                    for element in app_elements[:self.max_results]:
                        try:
                            app_data = await self._extract_single_app(element)
                            if app_data and app_data.get('name'):
                                results['apps'].append(app_data)
                        except Exception as e:
                            logger.debug(f"Failed to extract single app: {str(e)}")
                            continue
                    
                    if results['apps']:
                        break
                        
            except Exception as e:
                logger.debug(f"Failed to query selector {selector}: {str(e)}")
                continue
        
        logger.info(f"Extracted {len(results['apps'])} app results")
    
    async def _extract_single_app(self, element) -> Optional[Dict[str, Any]]:
        """Extract data from a single app element."""
        try:
            # App name
            name_selectors = [
                'h3[data-testid="product-title"]',
                'h3.ProductTitle',
                'h3 a',
                'h3',
                'div[data-testid="product-title"]'
            ]
            
            name = None
            for selector in name_selectors:
                try:
                    name_element = await element.query_selector(selector)
                    if name_element:
                        name = await name_element.text_content()
                        if name and name.strip():
                            break
                except Exception:
                    continue
            
            # App link
            link_selectors = [
                'a[href*="/detail/"]',
                'a[data-testid="product-link"]',
                'h3 a',
                'a[href*="/store/apps/"]'
            ]
            
            app_url = None
            for selector in link_selectors:
                try:
                    link_element = await element.query_selector(selector)
                    if link_element:
                        href = await link_element.get_attribute('href')
                        if href:
                            if href.startswith('/'):
                                app_url = f"{self.base_url}{href}"
                            else:
                                app_url = href
                            break
                except Exception:
                    continue
            
            # Developer
            developer_selectors = [
                'div[data-testid="product-publisher"]',
                'div.ProductPublisher',
                'p.ProductPublisher',
                'span.ProductPublisher'
            ]
            
            developer = None
            for selector in developer_selectors:
                try:
                    dev_element = await element.query_selector(selector)
                    if dev_element:
                        developer = await dev_element.text_content()
                        if developer and developer.strip():
                            break
                except Exception:
                    continue
            
            # Rating
            rating_selectors = [
                'div[data-testid="product-rating"]',
                'div.ProductRating',
                'span[aria-label*="star"]',
                'div[aria-label*="star"]'
            ]
            
            rating = None
            for selector in rating_selectors:
                try:
                    rating_element = await element.query_selector(selector)
                    if rating_element:
                        # Try to get rating from aria-label
                        aria_label = await rating_element.get_attribute('aria-label')
                        if aria_label:
                            import re
                            rating_match = re.search(r'(\d+\.?\d*)', aria_label)
                            if rating_match:
                                rating = float(rating_match.group(1))
                                break
                        
                        # Try to get rating from text content
                        rating_text = await rating_element.text_content()
                        if rating_text:
                            import re
                            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                            if rating_match:
                                rating = float(rating_match.group(1))
                                break
                except Exception:
                    continue
            
            # Category
            category_selectors = [
                'div[data-testid="product-category"]',
                'div.ProductCategory',
                'span.ProductCategory'
            ]
            
            category = None
            for selector in category_selectors:
                try:
                    cat_element = await element.query_selector(selector)
                    if cat_element:
                        category = await cat_element.text_content()
                        if category and category.strip():
                            break
                except Exception:
                    continue
            
            # Price
            price_selectors = [
                'div[data-testid="product-price"]',
                'div.ProductPrice',
                'span.ProductPrice',
                'button[aria-label*="Free"]',
                'button[aria-label*="Get"]'
            ]
            
            price = None
            for selector in price_selectors:
                try:
                    price_element = await element.query_selector(selector)
                    if price_element:
                        if 'button' in selector:
                            aria_label = await price_element.get_attribute('aria-label')
                            if aria_label and ('Free' in aria_label or 'Get' in aria_label):
                                price = 'Free'
                                break
                        else:
                            price = await price_element.text_content()
                            if price and price.strip():
                                break
                except Exception:
                    continue
            
            if name:
                return {
                    'name': name.strip(),
                    'developer': developer.strip() if developer else None,
                    'rating': rating,
                    'category': category.strip() if category else None,
                    'price': price.strip() if price else None,
                    'app_url': app_url
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting single app: {str(e)}")
            return None
    
    async def _extract_app_competitors(self, search_results: Dict[str, Any], browser_service) -> List[CompetitorData]:
        """Extract competitor data from app search results."""
        competitors = []
        
        for app in search_results.get('apps', []):
            try:
                # Get additional app details if we have the app URL
                app_details = None
                if app.get('app_url'):
                    try:
                        app_details = await browser_service.scrape_url(
                            url=app['app_url'],
                            scraper_function=self._scrape_app_details_page,
                            max_retries=2,
                            stealth_config=self._get_dynamic_stealth_config()
                        )
                        await asyncio.sleep(random.uniform(1, 3))  # Delay between app detail requests
                    except Exception as e:
                        logger.debug(f"Failed to get app details for {app.get('name')}: {str(e)}")
                
                # Determine pricing model
                pricing_model = 'Free'
                if app.get('price'):
                    if app['price'].lower() == 'free' or 'free' in app['price'].lower():
                        pricing_model = 'Free'
                    else:
                        pricing_model = f'Paid - {app["price"]}'
                
                # Create competitor data
                competitor = CompetitorData(
                    name=app['name'],
                    description=app_details.get('description') if app_details else None,
                    website=app_details.get('website') if app_details else None,
                    estimated_users=None,  # Not available from Microsoft Store
                    estimated_revenue=None,  # Not available from Microsoft Store
                    pricing_model=pricing_model,
                    source=self.source_name,
                    source_url=app.get('app_url'),
                    confidence_score=0.8,  # High confidence for Microsoft Store data
                    launch_date=app_details.get('release_date') if app_details else None,
                    founder_ceo=app.get('developer'),
                    review_count=app_details.get('review_count') if app_details else None,
                    average_rating=app.get('rating')
                )
                
                competitors.append(competitor)
                
            except Exception as e:
                logger.debug(f"Failed to create competitor data for app: {str(e)}")
                continue
        
        return competitors
    
    async def _extract_app_feedback(self, search_results: Dict[str, Any], browser_service) -> List[FeedbackData]:
        """Extract feedback data from app reviews."""
        feedback = []
        
        # For each app, try to get some reviews
        for app in search_results.get('apps', [])[:5]:  # Limit to first 5 apps
            if app.get('app_url'):
                try:
                    reviews = await browser_service.scrape_url(
                        url=app['app_url'],
                        scraper_function=self._scrape_app_reviews,
                        max_retries=2,
                        stealth_config=self._get_dynamic_stealth_config()
                    )
                    
                    for review in reviews[:3]:  # Limit to 3 reviews per app
                        feedback_item = FeedbackData(
                            text=review.get('text', ''),
                            sentiment=review.get('sentiment'),
                            sentiment_score=review.get('sentiment_score'),
                            source=self.source_name,
                            source_url=app['app_url'],
                            author_info={'app_name': app['name']}
                        )
                        feedback.append(feedback_item)
                    
                    await asyncio.sleep(random.uniform(1, 2))  # Delay between review requests
                    
                except Exception as e:
                    logger.debug(f"Failed to get reviews for {app.get('name')}: {str(e)}")
                    continue
        
        return feedback
    
    async def _scrape_app_details_page(self, page: Page) -> Dict[str, Any]:
        """Scrape app details page for additional information."""
        details = {}
        
        try:
            await page.wait_for_load_state('networkidle', timeout=20000)
            
            # Description
            desc_selectors = [
                'div[data-testid="product-description"]',
                'div.ProductDescription',
                'section.ProductDescription p',
                'div.ms-Stack p'
            ]
            
            for selector in desc_selectors:
                try:
                    desc_element = await page.query_selector(selector)
                    if desc_element:
                        details['description'] = await desc_element.text_content()
                        break
                except Exception:
                    continue
            
            # Review count
            review_selectors = [
                'span[data-testid="review-count"]',
                'div.ReviewCount',
                'span:has-text("reviews")',
                'div:has-text("reviews")'
            ]
            
            for selector in review_selectors:
                try:
                    review_element = await page.query_selector(selector)
                    if review_element:
                        review_text = await review_element.text_content()
                        if review_text:
                            # Extract number from text like "1,234 reviews"
                            import re
                            review_match = re.search(r'([\d,]+)', review_text.replace(',', ''))
                            if review_match:
                                details['review_count'] = int(review_match.group(1))
                                break
                except Exception:
                    continue
            
            # Developer website
            website_selectors = [
                'a[href^="http"]:has-text("Website")',
                'a[href^="http"]:has-text("Developer")',
                'a[data-testid="developer-website"]'
            ]
            
            for selector in website_selectors:
                try:
                    website_element = await page.query_selector(selector)
                    if website_element:
                        details['website'] = await website_element.get_attribute('href')
                        break
                except Exception:
                    continue
            
            # Release date
            date_selectors = [
                'div:has-text("Released")',
                'span:has-text("Released")',
                'div[data-testid="release-date"]'
            ]
            
            for selector in date_selectors:
                try:
                    date_element = await page.query_selector(selector)
                    if date_element:
                        date_text = await date_element.text_content()
                        if date_text and 'Released' in date_text:
                            details['release_date'] = date_text.replace('Released', '').strip()
                            break
                except Exception:
                    continue
            
        except Exception as e:
            logger.debug(f"Error scraping app details: {str(e)}")
        
        return details
    
    async def _scrape_app_reviews(self, page: Page) -> List[Dict[str, Any]]:
        """Scrape app reviews from the details page."""
        reviews = []
        
        try:
            await page.wait_for_load_state('networkidle', timeout=20000)
            
            # Scroll to reviews section
            try:
                reviews_section = await page.query_selector('section[data-testid="reviews"]')
                if not reviews_section:
                    reviews_section = await page.query_selector('div.ReviewsSection')
                
                if reviews_section:
                    await reviews_section.scroll_into_view_if_needed()
                    await asyncio.sleep(1)
            except Exception:
                pass
            
            # Review selectors
            review_selectors = [
                'div[data-testid="review-item"]',
                'div.ReviewItem',
                'article.ReviewItem'
            ]
            
            for selector in review_selectors:
                try:
                    review_elements = await page.query_selector_all(selector)
                    if review_elements:
                        for element in review_elements[:5]:  # Limit to 5 reviews
                            try:
                                # Try different text selectors
                                text_selectors = [
                                    'div[data-testid="review-text"]',
                                    'div.ReviewText',
                                    'p.ReviewText',
                                    'div.ms-Stack p'
                                ]
                                
                                review_text = None
                                for text_selector in text_selectors:
                                    try:
                                        text_element = await element.query_selector(text_selector)
                                        if text_element:
                                            review_text = await text_element.text_content()
                                            if review_text and len(review_text.strip()) > 10:
                                                break
                                    except Exception:
                                        continue
                                
                                if review_text:
                                    reviews.append({
                                        'text': review_text.strip(),
                                        'sentiment': None,  # Will be analyzed later
                                        'sentiment_score': None
                                    })
                            except Exception:
                                continue
                        
                        if reviews:
                            break
                            
                except Exception:
                    continue
        
        except Exception as e:
            logger.debug(f"Error scraping app reviews: {str(e)}")
        
        return reviews
    
    def _generate_search_queries(self, keywords: List[str], idea_text: str) -> List[str]:
        """Generate search queries for Microsoft Store."""
        queries = []
        
        # Basic keyword searches
        for keyword in keywords[:3]:
            queries.append(keyword)
        
        # Category-based searches
        app_categories = ['productivity', 'business', 'utilities', 'lifestyle', 'social']
        for keyword in keywords[:2]:
            for category in app_categories[:2]:
                queries.append(f"{keyword} {category}")
        
        # Competitor searches
        competitor_terms = ['alternative', 'similar', 'like', 'competitor']
        for keyword in keywords[:2]:
            for term in competitor_terms[:2]:
                queries.append(f"{keyword} {term}")
        
        return queries[:8]  # Limit total queries
    
    def _deduplicate_competitors(self, competitors: List[CompetitorData]) -> List[CompetitorData]:
        """Remove duplicate competitors based on name."""
        seen = set()
        unique_competitors = []
        
        for competitor in competitors:
            # Create identifier based on name
            identifier = competitor.name.lower().strip()
            if identifier not in seen:
                seen.add(identifier)
                unique_competitors.append(competitor)
        
        return unique_competitors
    
    def _deduplicate_feedback(self, feedback: List[FeedbackData]) -> List[FeedbackData]:
        """Remove duplicate feedback based on text."""
        seen = set()
        unique_feedback = []
        
        for item in feedback:
            # Create identifier based on first 50 characters of text
            identifier = item.text[:50].lower().strip()
            if identifier not in seen and len(identifier) > 10:
                seen.add(identifier)
                unique_feedback.append(item)
        
        return unique_feedback