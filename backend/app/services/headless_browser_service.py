"""
Headless browser service for managing browser pool and scraping operations.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from contextlib import asynccontextmanager

from patchright.async_api import Page

from .browser_pool import BrowserPool, BrowserPoolConfig
from .stealth_manager import StealthManager, StealthConfig
from .session_manager import SessionManager, SessionConfig


logger = logging.getLogger(__name__)


class HeadlessBrowserService:
    """Main service for headless browser automation with stealth capabilities."""
    
    def __init__(
        self,
        pool_config: Optional[BrowserPoolConfig] = None,
        stealth_config: Optional[StealthConfig] = None,
        session_config: Optional[SessionConfig] = None
    ):
        """Initialize the headless browser service."""
        self.pool_config = pool_config or BrowserPoolConfig()
        self.stealth_config = stealth_config or StealthConfig()
        self.session_config = session_config or SessionConfig()
        
        self.browser_pool = BrowserPool(self.pool_config)
        self.stealth_manager = StealthManager(self.stealth_config)
        self.session_manager = SessionManager(self.session_config, self.stealth_manager)
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the browser service."""
        if self._initialized:
            return
        
        try:
            await self.browser_pool.initialize()
            await self.session_manager.start()
            self._initialized = True
            logger.info("Headless browser service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize browser service: {str(e)}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the browser service."""
        if not self._initialized:
            return
        
        try:
            await self.session_manager.stop()
            await self.browser_pool.shutdown()
            self._initialized = False
            logger.info("Headless browser service shutdown")
        except Exception as e:
            logger.error(f"Error during browser service shutdown: {str(e)}")
    
    @asynccontextmanager
    async def get_page(self, stealth_config: Optional[Dict[str, Any]] = None):
        """
        Get a page for scraping with full stealth and session management.
        
        Args:
            stealth_config: Optional stealth configuration override
            
        Yields:
            Page: A page ready for scraping
        """
        if not self._initialized:
            await self.initialize()
        
        # Get browser context from pool
        async with self.browser_pool.get_browser_context(stealth_config) as context:
            # Create managed session
            async with self.session_manager.create_session(context, stealth_config) as session:
                # Get page from session
                async with self.session_manager.get_page(session) as page:
                    yield page
    
    async def scrape_url(
        self,
        url: str,
        scraper_function: Callable[[Page], Any],
        max_retries: int = 3,
        stealth_config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Scrape a URL with automatic retry and error handling.
        
        Args:
            url: URL to scrape
            scraper_function: Function that takes a Page and returns scraped data
            max_retries: Maximum number of retry attempts
            stealth_config: Optional stealth configuration
            
        Returns:
            Result from scraper_function
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                async with self.get_page(stealth_config) as page:
                    # Navigate to URL
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    
                    # Wait for page to load and check for bot detection
                    if not await self.stealth_manager.wait_for_page_load(page):
                        raise RuntimeError("Bot detection or CAPTCHA detected")
                    
                    # Run scraper function
                    result = await scraper_function(page)
                    
                    logger.info(f"Successfully scraped {url} on attempt {attempt + 1}")
                    return result
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"Scraping attempt {attempt + 1} failed for {url}: {str(e)}")
                
                if attempt < max_retries:
                    # Wait before retry with exponential backoff
                    wait_time = (2 ** attempt) + (0.5 * attempt)
                    await asyncio.sleep(wait_time)
                    logger.info(f"Retrying {url} in {wait_time} seconds...")
        
        logger.error(f"All scraping attempts failed for {url}")
        raise last_exception
    
    async def scrape_multiple_urls(
        self,
        urls: List[str],
        scraper_function: Callable[[Page, str], Any],
        max_concurrent: int = 3,
        max_retries: int = 3,
        stealth_config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs concurrently.
        
        Args:
            urls: List of URLs to scrape
            scraper_function: Function that takes a Page and URL and returns scraped data
            max_concurrent: Maximum concurrent scraping operations
            max_retries: Maximum number of retry attempts per URL
            stealth_config: Optional stealth configuration
            
        Returns:
            List of results with URL and data/error information
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_single_url(url: str) -> Dict[str, Any]:
            async with semaphore:
                try:
                    result = await self.scrape_url(
                        url,
                        lambda page: scraper_function(page, url),
                        max_retries,
                        stealth_config
                    )
                    return {
                        'url': url,
                        'success': True,
                        'data': result,
                        'error': None
                    }
                except Exception as e:
                    return {
                        'url': url,
                        'success': False,
                        'data': None,
                        'error': str(e)
                    }
        
        # Create tasks for all URLs
        tasks = [scrape_single_url(url) for url in urls]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    'url': 'unknown',
                    'success': False,
                    'data': None,
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def test_browser_automation(self, test_url: str = "https://httpbin.org/user-agent") -> Dict[str, Any]:
        """
        Test browser automation with anti-bot scenarios.
        
        Args:
            test_url: URL to test with
            
        Returns:
            Test results
        """
        test_results = {
            'test_url': test_url,
            'timestamp': datetime.utcnow().isoformat(),
            'tests': []
        }
        
        # Test 1: Basic page loading
        try:
            async with self.get_page() as page:
                await page.goto(test_url, wait_until='networkidle')
                content = await page.content()
                
                test_results['tests'].append({
                    'name': 'basic_page_loading',
                    'success': True,
                    'content_length': len(content),
                    'url': page.url
                })
        except Exception as e:
            test_results['tests'].append({
                'name': 'basic_page_loading',
                'success': False,
                'error': str(e)
            })
        
        # Test 2: User agent detection
        try:
            async with self.get_page() as page:
                await page.goto("https://httpbin.org/user-agent")
                content = await page.text_content('body')
                
                test_results['tests'].append({
                    'name': 'user_agent_test',
                    'success': True,
                    'user_agent_detected': 'Chrome' in content if content else False,
                    'content': content
                })
        except Exception as e:
            test_results['tests'].append({
                'name': 'user_agent_test',
                'success': False,
                'error': str(e)
            })
        
        # Test 3: JavaScript execution
        try:
            async with self.get_page() as page:
                await page.goto("https://httpbin.org/")
                js_result = await page.evaluate("() => navigator.userAgent")
                
                test_results['tests'].append({
                    'name': 'javascript_execution',
                    'success': True,
                    'js_user_agent': js_result
                })
        except Exception as e:
            test_results['tests'].append({
                'name': 'javascript_execution',
                'success': False,
                'error': str(e)
            })
        
        # Test 4: Stealth measures
        try:
            async with self.get_page() as page:
                await page.goto("https://httpbin.org/")
                
                # Check webdriver property
                webdriver_undefined = await page.evaluate("() => typeof navigator.webdriver === 'undefined'")
                
                # Check plugins
                plugins_length = await page.evaluate("() => navigator.plugins.length")
                
                test_results['tests'].append({
                    'name': 'stealth_measures',
                    'success': True,
                    'webdriver_undefined': webdriver_undefined,
                    'plugins_count': plugins_length
                })
        except Exception as e:
            test_results['tests'].append({
                'name': 'stealth_measures',
                'success': False,
                'error': str(e)
            })
        
        return test_results
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics."""
        return {
            'initialized': self._initialized,
            'timestamp': datetime.utcnow().isoformat(),
            'browser_pool': self.browser_pool.get_pool_stats(),
            'session_manager': self.session_manager.get_session_stats(),
            'config': {
                'pool_config': {
                    'min_browsers': self.pool_config.min_browsers,
                    'max_browsers': self.pool_config.max_browsers,
                    'max_requests_per_browser': self.pool_config.max_requests_per_browser,
                    'max_browser_age_minutes': self.pool_config.max_browser_age_minutes,
                },
                'stealth_config': {
                    'enable_human_delays': self.stealth_config.enable_human_delays,
                    'enable_mouse_movements': self.stealth_config.enable_mouse_movements,
                    'enable_scroll_simulation': self.stealth_config.enable_scroll_simulation,
                    'typing_speed_wpm': self.stealth_config.typing_speed_wpm,
                },
                'session_config': {
                    'max_session_duration_minutes': self.session_config.max_session_duration_minutes,
                    'max_idle_time_minutes': self.session_config.max_idle_time_minutes,
                    'max_requests_per_session': self.session_config.max_requests_per_session,
                }
            }
        }


# Global service instance
_browser_service: Optional[HeadlessBrowserService] = None


async def get_browser_service() -> HeadlessBrowserService:
    """Get the global browser service instance."""
    global _browser_service
    
    if _browser_service is None:
        _browser_service = HeadlessBrowserService()
        await _browser_service.initialize()
    
    return _browser_service


async def shutdown_browser_service() -> None:
    """Shutdown the global browser service instance."""
    global _browser_service
    
    if _browser_service is not None:
        await _browser_service.shutdown()
        _browser_service = None