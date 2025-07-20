"""
Google search scraper using Patchright headless browser for extracting competitor information and market trends.
"""
import asyncio
import logging
import os
import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import random
from urllib.parse import quote_plus, urlparse

from patchright.async_api import Page

from .base_scraper import BaseScraper, ScrapingResult, ScrapingStatus, CompetitorData, FeedbackData
from ..services.headless_browser_service import get_browser_service


logger = logging.getLogger(__name__)


class GoogleScraper(BaseScraper):
    """Scraper for Google search using Patchright headless browser to extract competitor information and market trends."""
    
    def __init__(self):
        """Initialize the Google scraper with Patchright browser automation."""
        super().__init__("Google")
        self.base_url = "https://www.google.com/search"
        self.num_results = 10
        self.timeout = 30
        self.max_retries = 3
        self.delay_between_requests = (2, 8)  # Random delay range in seconds
        
        # Advanced stealth configuration
        self.stealth_config = {
            'enable_human_delays': True,
            'enable_mouse_movements': True,
            'enable_scroll_simulation': True,
            'enable_typing_delays': True,
            'min_delay_ms': 500,
            'max_delay_ms': 3000,
            'typing_speed_wpm': random.randint(35, 65),
        }
        
        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
        ]
        
        # Viewport sizes for randomization
        self.viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864},
            {'width': 1280, 'height': 720},
            {'width': 1600, 'height': 900},
        ]
    
    def validate_config(self) -> bool:
        """
        Validate that the Google scraper is properly configured.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Check if we have valid user agents
            if not self.user_agents or len(self.user_agents) == 0:
                logger.error("No user agents configured for Google scraper")
                return False
            
            # Check if base URL is valid
            if not self.base_url or not self.base_url.startswith('http'):
                logger.error("Invalid base URL for Google scraper")
                return False
            
            # Check timeout and retry settings
            if self.timeout <= 0 or self.max_retries <= 0:
                logger.error("Invalid timeout or retry settings for Google scraper")
                return False
            
            # Check stealth configuration
            if not self.stealth_config or not isinstance(self.stealth_config, dict):
                logger.error("Invalid stealth configuration for Google scraper")
                return False
            
            # Check viewports
            if not self.viewports or len(self.viewports) == 0:
                logger.error("No viewports configured for Google scraper")
                return False
            
            # All checks passed
            logger.info("Google scraper configuration is valid")
            return True
            
        except Exception as e:
            logger.error(f"Google scraper configuration validation failed: {str(e)}")
            return False
    
    async def scrape(self, keywords: List[str], idea_text: str) -> ScrapingResult:
        """
        Scrape Google search using Patchright headless browser for competitor information and market trends.
        
        Args:
            keywords: List of extracted keywords from the idea
            idea_text: Original idea text for context
            
        Returns:
            ScrapingResult containing competitor data and market trends
        """
        try:
            competitors = []
            feedback = []
            metadata = {
                "keywords_searched": [],
                "search_queries": [],
                "successful_queries": 0,
                "failed_queries": 0,
                "captcha_detected": 0,
                "bot_detection_detected": 0,
                "browser_sessions_used": 0,
                "source": self.source_name,
                "scraping_method": "browser"
            }
            
            # Generate search queries based on keywords and idea text
            search_queries = self._generate_search_queries(keywords, idea_text)
            metadata["search_queries"] = search_queries
            
            # Get browser service
            browser_service = await get_browser_service()
            
            # Execute searches for each query with intelligent retry
            for query in search_queries[:5]:  # Limit to top 5 queries to avoid rate limiting
                try:
                    # Use browser service with stealth configuration
                    search_results = await browser_service.scrape_url(
                        url=self._build_search_url(query),
                        scraper_function=lambda page: self._scrape_search_page(page, query),
                        max_retries=self.max_retries,
                        stealth_config=self._get_dynamic_stealth_config()
                    )
                    
                    metadata["browser_sessions_used"] += 1
                    
                    # Extract competitor information
                    query_competitors = self._extract_competitors(search_results, query)
                    competitors.extend(query_competitors)
                    
                    # Extract market feedback and trends
                    query_feedback = self._extract_feedback(search_results, query)
                    feedback.extend(query_feedback)
                    
                    # Extract search volume trends if available
                    trends_data = self._extract_search_trends(search_results, query)
                    if trends_data:
                        metadata[f"trends_{query}"] = trends_data
                    
                    metadata["successful_queries"] += 1
                    metadata["keywords_searched"].append(query)
                    
                    # Human-like delay between requests
                    delay = random.uniform(*self.delay_between_requests)
                    logger.info(f"Waiting {delay:.1f} seconds before next search...")
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if 'captcha' in error_msg:
                        metadata["captcha_detected"] += 1
                        logger.warning(f"CAPTCHA detected for query '{query}': {str(e)}")
                    elif 'bot detection' in error_msg or 'blocked' in error_msg:
                        metadata["bot_detection_detected"] += 1
                        logger.warning(f"Bot detection triggered for query '{query}': {str(e)}")
                    else:
                        logger.warning(f"Failed to execute Google search for query '{query}': {str(e)}")
                    
                    metadata["failed_queries"] += 1
                    
                    # Exponential backoff on failures
                    backoff_delay = min(30, 2 ** metadata["failed_queries"])
                    await asyncio.sleep(backoff_delay)
                    continue
            
            # Remove duplicate competitors based on name and website
            unique_competitors = self._deduplicate_competitors(competitors)
            
            # Remove duplicate feedback
            unique_feedback = self._deduplicate_feedback(feedback)
            
            # Determine scraping status
            if metadata["successful_queries"] > 0:
                if len(unique_competitors) > 0:
                    status = ScrapingStatus.SUCCESS
                elif metadata["captcha_detected"] > 0 or metadata["bot_detection_detected"] > 0:
                    status = ScrapingStatus.PARTIAL_SUCCESS
                else:
                    status = ScrapingStatus.PARTIAL_SUCCESS
            else:
                status = ScrapingStatus.FAILED
            
            # Update metadata with final stats
            metadata.update({
                "total_competitors": len(unique_competitors),
                "total_feedback": len(unique_feedback),
                "success_rate": metadata["successful_queries"] / len(search_queries) if search_queries else 0,
                "anti_bot_encounters": metadata["captcha_detected"] + metadata["bot_detection_detected"]
            })
            
            logger.info(f"Google scraping completed: {len(unique_competitors)} competitors, "
                       f"{len(unique_feedback)} feedback items, "
                       f"{metadata['successful_queries']}/{len(search_queries)} successful queries")
            
            return ScrapingResult(
                status=status,
                competitors=unique_competitors[:15],  # Limit to top 15 competitors
                feedback=unique_feedback[:20],  # Limit to top 20 feedback items
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Google scraping failed: {str(e)}")
            return ScrapingResult(
                status=ScrapingStatus.FAILED,
                competitors=[],
                feedback=[],
                error_message=str(e),
                metadata=metadata
            )
    
    def _build_search_url(self, query: str) -> str:
        """
        Build Google search URL with query parameters.
        
        Args:
            query: Search query string
            
        Returns:
            Complete Google search URL
        """
        encoded_query = quote_plus(query)
        return f"{self.base_url}?q={encoded_query}&num={self.num_results}&hl=en&gl=us"
    
    def _get_dynamic_stealth_config(self) -> Dict[str, Any]:
        """
        Get dynamic stealth configuration with randomization.
        
        Returns:
            Stealth configuration dictionary
        """
        config = self.stealth_config.copy()
        
        # Randomize user agent
        config['user_agent'] = random.choice(self.user_agents)
        
        # Randomize viewport
        config['viewport'] = random.choice(self.viewports)
        
        # Randomize typing speed
        config['typing_speed_wpm'] = random.randint(35, 65)
        
        # Randomize delays
        config['min_delay_ms'] = random.randint(300, 800)
        config['max_delay_ms'] = random.randint(1500, 4000)
        
        return config
    
    async def _scrape_search_page(self, page: Page, query: str) -> Dict[str, Any]:
        """
        Scrape Google search page using Patchright with human-like behavior.
        
        Args:
            page: Patchright page object
            query: Search query
            
        Returns:
            Dictionary containing scraped search results
        """
        results = {
            "query": query,
            "organic_results": [],
            "featured_snippet": None,
            "knowledge_panel": None,
            "related_searches": [],
            "search_volume_data": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Wait for page to load completely
            await page.wait_for_load_state('networkidle', timeout=30000)
            
            # Check for CAPTCHA or bot detection
            if await self._detect_captcha_or_bot_detection(page):
                raise RuntimeError("CAPTCHA or bot detection encountered")
            
            # Simulate human reading behavior
            await self._simulate_human_reading(page)
            
            # Extract organic search results with dynamic selectors
            await self._extract_organic_results(page, results)
            
            # Extract featured snippet if present
            await self._extract_featured_snippet(page, results)
            
            # Extract knowledge panel if present
            await self._extract_knowledge_panel(page, results)
            
            # Extract related searches
            await self._extract_related_searches(page, results)
            
            # Extract search volume trends if available
            await self._extract_search_volume_trends(page, results)
            
            # Simulate human scrolling behavior
            await self._simulate_human_scrolling(page)
            
            logger.info(f"Successfully scraped Google search page for query: {query}")
            logger.info(f"Found {len(results['organic_results'])} organic results")
            
            return results
            
        except Exception as e:
            logger.error(f"Error scraping Google search page for query '{query}': {str(e)}")
            raise
    
    async def _detect_captcha_or_bot_detection(self, page: Page) -> bool:
        """
        Detect CAPTCHA or bot detection on the page.
        
        Args:
            page: Patchright page object
            
        Returns:
            True if CAPTCHA or bot detection is detected
        """
        # Check for CAPTCHA elements
        captcha_selectors = [
            '[class*="captcha"]',
            '[id*="captcha"]',
            '[class*="recaptcha"]',
            '[id*="recaptcha"]',
            'iframe[src*="recaptcha"]',
            '.g-recaptcha',
            '#recaptcha',
            '[data-sitekey]',
        ]
        
        for selector in captcha_selectors:
            try:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    logger.warning(f"CAPTCHA detected with selector: {selector}")
                    return True
            except Exception:
                continue
        
        # Check for bot detection text
        try:
            page_text = await page.text_content('body')
            if page_text:
                page_text_lower = page_text.lower()
                bot_detection_phrases = [
                    'unusual traffic',
                    'automated queries',
                    'verify you are human',
                    'prove you are not a robot',
                    'security check',
                    'suspicious activity',
                    'blocked',
                    'access denied',
                    'rate limit',
                    'too many requests'
                ]
                
                for phrase in bot_detection_phrases:
                    if phrase in page_text_lower:
                        logger.warning(f"Bot detection detected with phrase: {phrase}")
                        return True
        except Exception:
            pass
        
        return False
    
    async def _simulate_human_reading(self, page: Page) -> None:
        """
        Simulate human reading behavior with random delays.
        
        Args:
            page: Patchright page object
        """
        # Random delay to simulate reading the page
        reading_delay = random.uniform(1.5, 4.0)
        await asyncio.sleep(reading_delay)
        
        # Simulate mouse movement
        try:
            viewport = await page.viewport_size()
            if viewport:
                # Move mouse to random positions
                for _ in range(random.randint(2, 5)):
                    x = random.randint(100, viewport['width'] - 100)
                    y = random.randint(100, viewport['height'] - 100)
                    await page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
        except Exception:
            pass
    
    async def _simulate_human_scrolling(self, page: Page) -> None:
        """
        Simulate human scrolling behavior.
        
        Args:
            page: Patchright page object
        """
        try:
            # Scroll down in small increments
            for _ in range(random.randint(2, 5)):
                scroll_distance = random.randint(200, 500)
                await page.mouse.wheel(0, scroll_distance)
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Sometimes scroll back up
            if random.random() < 0.3:
                scroll_distance = random.randint(100, 300)
                await page.mouse.wheel(0, -scroll_distance)
                await asyncio.sleep(random.uniform(0.3, 0.8))
        except Exception:
            pass
    
    async def _extract_organic_results(self, page: Page, results: Dict[str, Any]) -> None:
        """
        Extract organic search results using dynamic selectors.
        
        Args:
            page: Patchright page object
            results: Results dictionary to populate
        """
        # Modern Google search result selectors (updated for 2024)
        result_selectors = [
            'div.MjjYud',  # Main result container
            'div.g',       # Classic result container
            'div.tF2Cxc',  # Alternative result container
            'div.yuRUbf',  # Link container
            'div.kvH3mc',  # Another variant
            'div.hlcw0c',  # Mobile variant
        ]
        
        for selector in result_selectors:
            try:
                result_elements = await page.query_selector_all(selector)
                if result_elements:
                    logger.info(f"Found {len(result_elements)} results with selector: {selector}")
                    
                    for element in result_elements:
                        try:
                            result_data = await self._extract_single_result(element)
                            if result_data and result_data.get('title') and result_data.get('link'):
                                # Skip Google-specific links
                                link = result_data['link']
                                if not link.startswith('/') and 'google.com' not in link:
                                    results['organic_results'].append(result_data)
                        except Exception as e:
                            logger.debug(f"Failed to extract single result: {str(e)}")
                            continue
                    
                    # If we found results, break
                    if results['organic_results']:
                        break
                        
            except Exception as e:
                logger.debug(f"Failed to query selector {selector}: {str(e)}")
                continue
        
        logger.info(f"Extracted {len(results['organic_results'])} organic results")
    
    async def _extract_single_result(self, element) -> Optional[Dict[str, Any]]:
        """
        Extract data from a single search result element.
        
        Args:
            element: Page element containing the search result
            
        Returns:
            Dictionary with result data or None
        """
        try:
            # Try multiple title selectors
            title_selectors = [
                'h3',
                'h3.LC20lb',
                'h3.DKV0Md',
                '[role="heading"]',
                'a h3',
                'h3.zBAuLc',
                'h3.DFN0Dc',
                '.DKV0Md',
                '.LC20lb'
            ]
            
            title = None
            for selector in title_selectors:
                try:
                    title_element = await element.query_selector(selector)
                    if title_element:
                        title = await title_element.text_content()
                        if title and title.strip():
                            break
                except Exception:
                    continue
            
            # Try multiple link selectors
            link_selectors = [
                'a[href]',
                'a.cz3goc',
                'div.yuRUbf a',
                'div.Z26q7c a',
                'div.kvH3mc a',
                'h3 a',
                'a[href^="http"]'
            ]
            
            link = None
            for selector in link_selectors:
                try:
                    link_element = await element.query_selector(selector)
                    if link_element:
                        link = await link_element.get_attribute('href')
                        if link and link.startswith('http'):
                            break
                except Exception:
                    continue
            
            # Try multiple snippet selectors
            snippet_selectors = [
                'div.VwiC3b',
                'span.aCOpRe',
                'div.s3v9rd',
                'div.lEBKkf',
                'div.yXK7lf',
                'div.Z26q7c div.VwiC3b',
                'div.kvH3mc div.VwiC3b',
                'div.HiHjCd',
                'div.BNeawe.s3v9rd.AP7Wnd',
                '.VwiC3b',
                '.s3v9rd'
            ]
            
            snippet = ""
            for selector in snippet_selectors:
                try:
                    snippet_element = await element.query_selector(selector)
                    if snippet_element:
                        snippet = await snippet_element.text_content()
                        if snippet and snippet.strip():
                            break
                except Exception:
                    continue
            
            if title and link:
                return {
                    'title': title.strip(),
                    'link': link,
                    'snippet': snippet.strip() if snippet else ""
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting single result: {str(e)}")
            return None
    
    async def _extract_featured_snippet(self, page: Page, results: Dict[str, Any]) -> None:
        """
        Extract featured snippet if present.
        
        Args:
            page: Patchright page object
            results: Results dictionary to populate
        """
        featured_selectors = [
            'div.c2xzTb',
            'div.IZ6rdc',
            'div.xpdopen',
            'div.kp-wholepage',
            'div.ifM9O',
            '.c2xzTb',
            '.IZ6rdc'
        ]
        
        for selector in featured_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    snippet_text = await element.text_content()
                    if snippet_text and snippet_text.strip():
                        results['featured_snippet'] = snippet_text.strip()
                        logger.debug(f"Extracted featured snippet with selector: {selector}")
                        break
            except Exception:
                continue
    
    async def _extract_knowledge_panel(self, page: Page, results: Dict[str, Any]) -> None:
        """
        Extract knowledge panel information if present.
        
        Args:
            page: Patchright page object
            results: Results dictionary to populate
        """
        knowledge_selectors = [
            'div.kp-wholepage',
            'div.knowledge-panel',
            'div.kp-header',
            '.kp-wholepage',
            '.knowledge-panel'
        ]
        
        for selector in knowledge_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    panel_text = await element.text_content()
                    if panel_text and panel_text.strip():
                        results['knowledge_panel'] = panel_text.strip()
                        logger.debug(f"Extracted knowledge panel with selector: {selector}")
                        break
            except Exception:
                continue
    
    async def _extract_related_searches(self, page: Page, results: Dict[str, Any]) -> None:
        """
        Extract related searches if present.
        
        Args:
            page: Patchright page object
            results: Results dictionary to populate
        """
        related_selectors = [
            'div.AJLUJb > div > a',
            'div.brs_col a',
            'div.s75CSd',
            'div.card-section a',
            '.AJLUJb a',
            '.brs_col a'
        ]
        
        for selector in related_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    for element in elements:
                        try:
                            text = await element.text_content()
                            if text and text.strip():
                                results['related_searches'].append(text.strip())
                        except Exception:
                            continue
                    
                    if results['related_searches']:
                        logger.debug(f"Extracted {len(results['related_searches'])} related searches")
                        break
            except Exception:
                continue
    
    async def _extract_search_volume_trends(self, page: Page, results: Dict[str, Any]) -> None:
        """
        Extract search volume trends and related keyword data if available.
        
        Args:
            page: Patchright page object
            results: Results dictionary to populate
        """
        try:
            # Look for Google Trends data or search volume indicators
            trends_selectors = [
                'div[data-trends]',
                '.trends-widget',
                '.search-volume',
                '[data-search-volume]'
            ]
            
            for selector in trends_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        trends_data = await element.text_content()
                        if trends_data and trends_data.strip():
                            results['search_volume_data'] = trends_data.strip()
                            logger.debug(f"Extracted search volume data with selector: {selector}")
                            break
                except Exception:
                    continue
            
            # Extract related keywords from autocomplete or suggestions
            suggestion_selectors = [
                '.sbqs_c',
                '.suggestions',
                '.autocomplete'
            ]
            
            related_keywords = []
            for selector in suggestion_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        try:
                            text = await element.text_content()
                            if text and text.strip():
                                related_keywords.append(text.strip())
                        except Exception:
                            continue
                except Exception:
                    continue
            
            if related_keywords:
                results['related_keywords'] = related_keywords[:10]  # Limit to top 10
                
        except Exception as e:
            logger.debug(f"Error extracting search volume trends: {str(e)}")
    
    def _generate_search_queries(self, keywords: List[str], idea_text: str) -> List[str]:
        """
        Generate search queries based on keywords and idea text.
        
        Args:
            keywords: List of keywords extracted from the idea
            idea_text: Original idea text
            
        Returns:
            List of search queries
        """
        # Extract main product category/type from idea text
        product_type = self._extract_product_type(idea_text, keywords)
        
        # Generate search queries
        queries = []
        
        # Add basic keyword searches - avoid redundancy like "software software"
        for keyword in keywords[:3]:  # Use top 3 keywords
            # Check if keyword already contains "software" or "tool"
            if "software" not in keyword.lower():
                queries.append(f"{keyword} software")
            if "tool" not in keyword.lower():
                queries.append(f"{keyword} tool")
            # Add the keyword by itself for broader results
            queries.append(keyword)
        
        # Add competitor-focused queries
        if product_type:
            queries.append(f"best {product_type} software")
            queries.append(f"top {product_type} tools")
            queries.append(f"{product_type} software alternatives")
            queries.append(f"{product_type} competitors")
            queries.append(f"{product_type} companies")
        
        # Add specific competitor research queries
        for keyword in keywords[:2]:  # Use top 2 keywords
            if "software" not in keyword.lower():
                queries.append(f"alternatives to {keyword} software")
                queries.append(f"{keyword} software competitors")
            else:
                queries.append(f"alternatives to {keyword}")
                queries.append(f"{keyword} competitors")
            
        # Add market trend queries
        queries.append(f"{' '.join(keywords[:2])} market trends")
        queries.append(f"{' '.join(keywords[:2])} industry statistics")
        
        # Remove duplicates and return
        return list(dict.fromkeys(queries))
    
    def _extract_product_type(self, idea_text: str, keywords: List[str]) -> Optional[str]:
        """
        Extract the main product type/category from the idea text.
        
        Args:
            idea_text: Original idea text
            keywords: Extracted keywords
            
        Returns:
            Product type string or None if not found
        """
        # Common SaaS product type patterns
        patterns = [
            r'([\w\s]+) (software|platform|tool|solution|app|application)',
            r'([\w\s]+) for ([\w\s]+)',
            r'([\w\s]+) to (manage|track|monitor|analyze|automate) ([\w\s]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, idea_text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    # Return the most relevant part of the match, cleaned up
                    result = matches[0][0].strip().lower()
                    # Remove leading articles
                    result = re.sub(r'^(a|an|the)\s+', '', result)
                    return result
                result = matches[0].strip().lower()
                # Remove leading articles
                result = re.sub(r'^(a|an|the)\s+', '', result)
                return result
        
        # Fallback to first keyword if no pattern matches
        return keywords[0] if keywords else None
    

    

    
    def _extract_search_trends(self, search_results: Dict[str, Any], query: str) -> Optional[Dict[str, Any]]:
        """
        Extract search volume trends and related keyword data for market intelligence.
        
        Args:
            search_results: Parsed search results
            query: Original search query
            
        Returns:
            Dictionary with trends data or None
        """
        trends_data = {}
        
        # Extract search volume data if available
        if search_results.get('search_volume_data'):
            trends_data['search_volume'] = search_results['search_volume_data']
        
        # Extract related keywords
        if search_results.get('related_keywords'):
            trends_data['related_keywords'] = search_results['related_keywords']
        
        # Extract related searches as trend indicators
        if search_results.get('related_searches'):
            trends_data['related_searches'] = search_results['related_searches'][:5]
        
        # Analyze result titles for market trends
        if search_results.get('organic_results'):
            trend_keywords = []
            for result in search_results['organic_results'][:10]:
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                combined_text = f"{title} {snippet}"
                
                # Look for trend indicators
                trend_indicators = [
                    'trending', 'popular', 'growing', 'emerging', 'rising',
                    'best', 'top', 'leading', 'market leader', 'industry standard',
                    '2024', '2023', 'new', 'latest', 'updated'
                ]
                
                for indicator in trend_indicators:
                    if indicator in combined_text:
                        trend_keywords.append(indicator)
            
            if trend_keywords:
                trends_data['trend_indicators'] = list(set(trend_keywords))
        
        return trends_data if trends_data else None
    
    def _extract_competitors(self, search_results: Dict[str, Any], query: str) -> List[CompetitorData]:
        """
        Extract competitor information from search results.
        
        Args:
            search_results: Parsed search results
            query: Original search query
            
        Returns:
            List of CompetitorData objects
        """
        competitors = []
        
        # Process organic results
        for result in search_results.get("organic_results", []):
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            link = result.get("link", "")
            
            # Skip if no title or link
            if not title or not link:
                continue
                
            # Check if result appears to be a competitor
            if self._is_likely_competitor(title, snippet, query):
                # Extract company/product name
                company_name = self._extract_company_name(title, link)
                
                if company_name:
                    # Estimate users based on domain authority and position
                    estimated_users = self._estimate_users(link, title)
                    
                    # Estimate revenue based on estimated users
                    estimated_revenue = self._estimate_revenue(estimated_users)
                    
                    # Create competitor data
                    competitor = CompetitorData(
                        name=company_name,
                        description=snippet[:200] if snippet else "",
                        website=link,
                        source=self.source_name,
                        source_url=link,
                        confidence_score=self._calculate_competitor_confidence(title, snippet, query),
                        estimated_users=estimated_users,
                        estimated_revenue=estimated_revenue,
                        pricing_model=self._extract_pricing_model(snippet)
                    )
                    
                    # Add scraping method metadata
                    if not hasattr(competitor, 'metadata'):
                        competitor.metadata = {}
                    competitor.metadata['scraping_method'] = 'browser'
                    
                    # Try to extract additional information
                    self._enrich_competitor_data(competitor, title, snippet)
                    
                    competitors.append(competitor)
        
        return competitors
        
    def _estimate_users(self, website: str, title: str) -> Optional[int]:
        """
        Estimate user count based on domain and title keywords.
        
        Args:
            website: Website URL
            title: Result title
            
        Returns:
            Estimated user count or None
        """
        # Base estimate on domain authority indicators
        base_estimate = 1000  # Default base estimate
        
        # Check for well-known domains
        domain = urlparse(website).netloc.lower()
        
        # Major players get higher estimates
        if any(big_domain in domain for big_domain in ['salesforce', 'hubspot', 'zoho', 'microsoft']):
            return random.randint(500000, 2000000)
        
        # Medium-sized players
        if any(mid_domain in domain for mid_domain in ['pipedrive', 'freshworks', 'zendesk', 'monday']):
            return random.randint(100000, 500000)
        
        # Adjust based on title keywords
        title_lower = title.lower()
        
        # Look for indicators of popularity
        if any(indicator in title_lower for indicator in ['leading', 'top', 'best', '#1']):
            base_estimate *= 5
        
        # Look for scale indicators
        if any(indicator in title_lower for indicator in ['enterprise', 'global']):
            base_estimate *= 3
        elif any(indicator in title_lower for indicator in ['small business', 'startup']):
            base_estimate *= 0.5
            
        # Add some randomness
        return int(base_estimate * random.uniform(0.8, 1.2))
        
    def _estimate_revenue(self, estimated_users: Optional[int]) -> Optional[str]:
        """
        Estimate revenue based on user count.
        
        Args:
            estimated_users: Estimated user count
            
        Returns:
            Revenue estimate string or None
        """
        if not estimated_users:
            return None
            
        if estimated_users > 500000:
            return "$100M+ ARR"
        elif estimated_users > 100000:
            return "$50M+ ARR"
        elif estimated_users > 50000:
            return "$10M+ ARR"
        elif estimated_users > 10000:
            return "$1M+ ARR"
        elif estimated_users > 5000:
            return "$500K+ ARR"
        elif estimated_users > 1000:
            return "$100K+ ARR"
        else:
            return "Early stage"
            
    def _enrich_competitor_data(self, competitor: CompetitorData, title: str, snippet: str) -> None:
        """
        Enrich competitor data with additional information.
        
        Args:
            competitor: CompetitorData object to enrich
            title: Result title
            snippet: Result snippet
        """
        combined_text = f"{title} {snippet}".lower()
        
        # Try to extract launch date
        date_patterns = [
            r'founded in (\d{4})',
            r'since (\d{4})',
            r'established in (\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, combined_text)
            if match:
                competitor.launch_date = match.group(1)
                break
                
        # Try to extract founder/CEO
        founder_patterns = [
            r'founded by ([A-Z][a-z]+ [A-Z][a-z]+)',
            r'CEO ([A-Z][a-z]+ [A-Z][a-z]+)'
        ]
        
        for pattern in founder_patterns:
            match = re.search(pattern, combined_text)
            if match:
                competitor.founder_ceo = match.group(1)
                break
                
        # Try to extract ratings
        rating_patterns = [
            r'(\d+\.?\d*)/5',
            r'(\d+\.?\d*) out of 5',
            r'(\d+\.?\d*) stars'
        ]
        
        for pattern in rating_patterns:
            match = re.search(pattern, combined_text)
            if match:
                try:
                    competitor.average_rating = float(match.group(1))
                    break
                except:
                    pass
                    
        # Try to extract review count
        review_patterns = [
            r'(\d+,?\d*) reviews',
            r'(\d+,?\d*) ratings'
        ]
        
        for pattern in review_patterns:
            match = re.search(pattern, combined_text)
            if match:
                try:
                    review_count = match.group(1).replace(',', '')
                    competitor.review_count = int(review_count)
                    break
                except:
                    pass
    
    def _is_likely_competitor(self, title: str, snippet: str, query: str) -> bool:
        """
        Determine if a search result is likely to be a competitor.
        
        Args:
            title: Result title
            snippet: Result snippet
            query: Original search query
            
        Returns:
            True if likely a competitor, False otherwise
        """
        # For debugging
        logger.debug(f"Checking if result is competitor: {title}")
        
        # If title or snippet is empty, it's not a competitor
        if not title or not snippet:
            return False
            
        combined_text = f"{title.lower()} {snippet.lower()}"
        query_lower = query.lower()
        
        # Strong non-competitor indicators that should exclude results
        strong_non_competitor_indicators = [
            "what is", "definition", "guide", "tutorial", "how to",
            "wikipedia", "blog post", "article", "news", "forum",
            "reddit", "quora", "stack overflow", "github", "youtube",
            "facebook", "twitter", "instagram", "linkedin", "pinterest",
            "tiktok", "dictionary", "glossary", "faq", "help center"
        ]
        
        # Check for strong exclusion indicators first
        has_strong_exclusion = any(indicator in combined_text for indicator in strong_non_competitor_indicators)
        if has_strong_exclusion:
            logger.debug(f"Excluded due to strong non-competitor indicator: {title}")
            return False
        
        # Check for competitor indicators
        competitor_indicators = [
            "software", "platform", "tool", "solution", "app", "saas",
            "service", "product", "suite", "system", "crm", "customer relationship",
            "management", "business", "enterprise", "cloud", "api", "dashboard",
            "analytics", "automation", "integration", "workflow", "pipeline"
        ]
        
        # Check if title contains competitor indicators
        has_competitor_indicator = any(indicator in combined_text for indicator in competitor_indicators)
        
        # Check if query is competitor-focused
        is_competitor_query = any(pattern in query_lower for pattern in [
            "alternative", "competitor", "vs", "versus", "comparison", "best", "top"
        ])
        
        # Check for company/product name patterns
        has_product_pattern = bool(re.search(r'[A-Z][a-z]+(?:CRM|HQ|App|\.io|\.com|\.ai)', title))
        
        # Check for pricing mentions which often indicate products
        has_pricing_mention = any(term in combined_text for term in [
            "pricing", "subscription", "monthly", "annually", "free trial",
            "premium", "basic plan", "enterprise plan", "per user", "per month"
        ])
        
        # If the query explicitly mentions a product category, be more lenient
        product_category_mentioned = any(category in query_lower for category in [
            "crm", "software", "tool", "platform", "solution", "app"
        ])
        
        # Check for company name patterns (capitalized words)
        has_company_name = bool(re.search(r'\b[A-Z][a-z]+\b', title))
        
        # Check for domain name in title
        has_domain = bool(re.search(r'\b[a-zA-Z0-9]+\.[a-z]{2,}\b', title))
        
        # For CRM-specific queries, be more lenient
        is_crm_query = "crm" in query_lower
        
        # Combine all signals - require stronger evidence for competitor classification
        is_competitor = (
            (has_competitor_indicator and has_company_name) or
            is_competitor_query or
            has_product_pattern or
            has_pricing_mention or
            (product_category_mentioned and has_company_name and has_competitor_indicator) or
            (has_domain and has_competitor_indicator and has_company_name) or
            (is_crm_query and has_company_name and has_competitor_indicator)
        )
        
        # Log the decision
        if is_competitor:
            logger.debug(f"Identified as competitor: {title}")
        else:
            logger.debug(f"Not identified as competitor: {title}")
        
        return is_competitor
    
    def _extract_company_name(self, title: str, url: str) -> Optional[str]:
        """
        Extract company or product name from title and URL.
        
        Args:
            title: Result title
            url: Result URL
            
        Returns:
            Company/product name or None if not found
        """
        # Try to extract from title first - expanded patterns
        title_patterns = [
            r'^([A-Z][a-zA-Z0-9]+(?:\s[A-Z][a-zA-Z0-9]+)?)(?:\s*[-|:]\s*.+)?$',  # "ProductName - description" or "Product Name - description"
            r'^([A-Z][a-zA-Z0-9]+(?:\s[A-Z][a-zA-Z0-9]+)?)(?:\s*\|\s*.+)?$',     # "ProductName | description" or "Product Name | description"
            r'^([A-Z][a-zA-Z0-9]+(?:\.\w+)?)(?:\s*[-|:]\s*.+)?$',                # "Product.io - description"
            r'^([A-Z][a-zA-Z0-9]+(?:CRM|HQ|App|\.io|\.com|\.ai))(?:\s*.+)?$',    # "ProductCRM" or "Product.io"
            r'^([A-Z][a-zA-Z0-9]+\s(?:CRM|Software|Platform|Tool|App))(?:\s*.+)?$', # "Product CRM" or "Product Software"
        ]
        
        for pattern in title_patterns:
            match = re.match(pattern, title)
            if match:
                return match.group(1).strip()
        
        # Try to extract from domain
        try:
            domain = urlparse(url).netloc
            
            # Remove www. prefix
            domain = re.sub(r'^www\.', '', domain)
            
            # Handle special cases first
            if domain.lower() == "monday.com":
                return "Monday"
            elif domain.lower() == "asana.com":
                return "Asana"
            elif domain.lower() in ["salesforce.com", "salesforce.org"]:
                return "Salesforce"
            elif domain.lower() == "hubspot.com":
                return "HubSpot"
            elif domain.lower() == "zoho.com":
                return "Zoho"
            elif domain.lower() == "pipedrive.com":
                return "Pipedrive"
            elif domain.lower() == "freshworks.com":
                return "Freshworks"
            
            # Remove common TLDs
            domain = re.sub(r'\.(com|org|net|io|co|app|ai)$', '', domain)
            
            # Handle subdomains
            domain_parts = domain.split('.')
            if len(domain_parts) > 1:
                # Use the most significant part (usually the second-to-last)
                domain = domain_parts[-2]
            else:
                domain = domain_parts[0]
            
            # Convert to title case for better readability
            if domain and len(domain) >= 2:
                # Handle camelCase or kebab-case domains
                if '-' in domain:
                    parts = domain.split('-')
                    return ' '.join(part.title() for part in parts)
                # Add space before capital letters in camelCase
                domain_with_spaces = re.sub(r'([a-z])([A-Z])', r'\1 \2', domain)
                return domain_with_spaces.title()
        except:
            pass
        
        # Try to find a product name pattern in the title
        product_pattern = re.search(r'([A-Z][a-zA-Z0-9]+(?:CRM|HQ|App|\.io|\.com|\.ai))', title)
        if product_pattern:
            return product_pattern.group(1)
        
        # If all else fails, use the first 2-3 words of the title
        words = title.split()
        if words:
            # Skip common prefixes like "Best" or "Top"
            if words[0].lower() in ["best", "top", "leading", "popular", "free", "affordable"]:
                words = words[1:]
            return ' '.join(words[:min(3, len(words))])
        
        return None
    
    def _calculate_competitor_confidence(self, title: str, snippet: str, query: str) -> float:
        """
        Calculate confidence score for competitor identification.
        
        Args:
            title: Result title
            snippet: Result snippet
            query: Original search query
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        combined_text = f"{title.lower()} {snippet.lower()}"
        base_score = 0.5
        
        # Adjust based on competitor indicators in text
        strong_indicators = [
            "alternative to", "competitor to", "similar to",
            "vs", "versus", "comparison", "pricing", "features"
        ]
        
        # Check for strong indicators
        for indicator in strong_indicators:
            if indicator in combined_text:
                base_score += 0.1
        
        # Adjust based on query type
        if "alternative" in query.lower() or "competitor" in query.lower():
            base_score += 0.2
        elif "best" in query.lower() or "top" in query.lower():
            base_score += 0.15
        
        # Cap at 0.95 to account for uncertainty
        return min(0.95, base_score)
    
    def _extract_pricing_model(self, snippet: str) -> Optional[str]:
        """
        Extract pricing model information from snippet.
        
        Args:
            snippet: Result snippet
            
        Returns:
            Pricing model string or None if not found
        """
        snippet_lower = snippet.lower()
        
        # Check for pricing indicators
        if "free" in snippet_lower and ("premium" in snippet_lower or "paid" in snippet_lower):
            return "Freemium"
        elif "subscription" in snippet_lower:
            return "Subscription"
        elif "one-time" in snippet_lower or "one time" in snippet_lower:
            return "One-time purchase"
        elif "free" in snippet_lower:
            return "Free"
        elif "trial" in snippet_lower:
            return "Free trial"
        
        return None
    
    def _extract_feedback(self, search_results: Dict[str, Any], query: str) -> List[FeedbackData]:
        """
        Extract market feedback from search results.
        
        Args:
            search_results: Parsed search results
            query: Original search query
            
        Returns:
            List of FeedbackData objects
        """
        feedback = []
        
        # Extract feedback from featured snippet
        featured_snippet = search_results.get("featured_snippet")
        if featured_snippet:
            sentiment, sentiment_score = self._analyze_sentiment(featured_snippet)
            
            feedback_data = FeedbackData(
                text=featured_snippet[:500],  # Limit text length
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                source=self.source_name,
                source_url=f"https://www.google.com/search?q={quote_plus(query)}",
                author_info={
                    "type": "featured_snippet",
                    "query": query
                }
            )
            
            feedback.append(feedback_data)
        
        # Extract feedback from organic results that contain reviews or opinions
        for result in search_results.get("organic_results", []):
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            link = result.get("link", "")
            
            # Skip if no snippet
            if not snippet:
                continue
                
            # Check if snippet contains feedback indicators
            if self._contains_feedback_indicators(title, snippet):
                sentiment, sentiment_score = self._analyze_sentiment(snippet)
                
                feedback_data = FeedbackData(
                    text=snippet[:500],  # Limit text length
                    sentiment=sentiment,
                    sentiment_score=sentiment_score,
                    source=self.source_name,
                    source_url=link,
                    author_info={
                        "type": "search_result",
                        "title": title,
                        "query": query
                    }
                )
                
                feedback.append(feedback_data)
        
        return feedback
    
    def _contains_feedback_indicators(self, title: str, snippet: str) -> bool:
        """
        Check if text contains feedback indicators.
        
        Args:
            title: Result title
            snippet: Result snippet
            
        Returns:
            True if contains feedback indicators, False otherwise
        """
        combined_text = f"{title.lower()} {snippet.lower()}"
        
        feedback_indicators = [
            "review", "opinion", "experience", "testimonial",
            "rating", "star", "recommend", "feedback", "thought",
            "pros and cons", "advantage", "disadvantage",
            "like", "dislike", "love", "hate"
        ]
        
        return any(indicator in combined_text for indicator in feedback_indicators)
    
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
    
    def _deduplicate_competitors(self, competitors: List[CompetitorData]) -> List[CompetitorData]:
        """
        Remove duplicate competitors based on name.
        
        Args:
            competitors: List of CompetitorData objects
            
        Returns:
            List of unique CompetitorData objects
        """
        unique_competitors = {}
        
        for competitor in competitors:
            name_lower = competitor.name.lower()
            
            if name_lower not in unique_competitors:
                unique_competitors[name_lower] = competitor
            else:
                # If duplicate, keep the one with higher confidence score
                if competitor.confidence_score > unique_competitors[name_lower].confidence_score:
                    unique_competitors[name_lower] = competitor
        
        return list(unique_competitors.values())
    
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