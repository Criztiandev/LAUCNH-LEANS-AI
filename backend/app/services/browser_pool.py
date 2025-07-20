"""
Browser pool management for headless browser automation with Patchright.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import random
from contextlib import asynccontextmanager

from patchright.async_api import async_playwright, Browser, BrowserContext, Page


logger = logging.getLogger(__name__)


class BrowserStatus(Enum):
    """Status of browser instance."""
    AVAILABLE = "available"
    IN_USE = "in_use"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


@dataclass
class BrowserInstance:
    """Represents a browser instance in the pool."""
    id: str
    browser: Browser
    status: BrowserStatus = BrowserStatus.AVAILABLE
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: datetime = field(default_factory=datetime.utcnow)
    request_count: int = 0
    failure_count: int = 0
    contexts: List[BrowserContext] = field(default_factory=list)


@dataclass
class BrowserPoolConfig:
    """Configuration for browser pool."""
    min_browsers: int = 3
    max_browsers: int = 5
    max_requests_per_browser: int = 10
    max_browser_age_minutes: int = 30
    max_failure_count: int = 3
    context_timeout_seconds: int = 30
    page_timeout_seconds: int = 30


class BrowserPool:
    """Manages a pool of headless browser instances for concurrent scraping."""
    
    def __init__(self, config: Optional[BrowserPoolConfig] = None):
        """Initialize the browser pool."""
        self.config = config or BrowserPoolConfig()
        self.browsers: Dict[str, BrowserInstance] = {}
        self.playwright = None
        self._lock = asyncio.Lock()
        self._initialized = False
        self._cleanup_task = None
        
    async def initialize(self) -> None:
        """Initialize the browser pool."""
        if self._initialized:
            return
            
        async with self._lock:
            if self._initialized:
                return
                
            try:
                self.playwright = await async_playwright().start()
                logger.info("Playwright initialized")
                
                # Create initial browser instances
                for i in range(self.config.min_browsers):
                    await self._create_browser_instance()
                
                # Start cleanup task
                self._cleanup_task = asyncio.create_task(self._cleanup_loop())
                
                self._initialized = True
                logger.info(f"Browser pool initialized with {len(self.browsers)} browsers")
                
            except Exception as e:
                logger.error(f"Failed to initialize browser pool: {str(e)}")
                raise
    
    async def shutdown(self) -> None:
        """Shutdown the browser pool and cleanup resources."""
        if not self._initialized:
            return
            
        async with self._lock:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Close all browsers
            for browser_instance in list(self.browsers.values()):
                await self._close_browser_instance(browser_instance.id)
            
            if self.playwright:
                await self.playwright.stop()
                
            self._initialized = False
            logger.info("Browser pool shutdown complete")
    
    @asynccontextmanager
    async def get_browser_context(self, stealth_config: Optional[Dict[str, Any]] = None):
        """
        Get a browser context for scraping operations.
        
        Args:
            stealth_config: Optional stealth configuration
            
        Yields:
            BrowserContext: A browser context ready for use
        """
        if not self._initialized:
            await self.initialize()
        
        browser_instance = await self._acquire_browser()
        context = None
        
        try:
            context = await self._create_context(browser_instance, stealth_config)
            yield context
            
        except Exception as e:
            logger.error(f"Error in browser context: {str(e)}")
            browser_instance.failure_count += 1
            raise
            
        finally:
            if context:
                try:
                    await context.close()
                except Exception as e:
                    logger.warning(f"Error closing context: {str(e)}")
            
            await self._release_browser(browser_instance)
    
    async def _acquire_browser(self) -> BrowserInstance:
        """Acquire an available browser instance."""
        async with self._lock:
            # Find available browser
            for browser_instance in self.browsers.values():
                if (browser_instance.status == BrowserStatus.AVAILABLE and 
                    browser_instance.failure_count < self.config.max_failure_count):
                    browser_instance.status = BrowserStatus.IN_USE
                    browser_instance.last_used = datetime.utcnow()
                    browser_instance.request_count += 1
                    return browser_instance
            
            # Create new browser if under max limit
            if len(self.browsers) < self.config.max_browsers:
                browser_instance = await self._create_browser_instance()
                browser_instance.status = BrowserStatus.IN_USE
                browser_instance.last_used = datetime.utcnow()
                browser_instance.request_count += 1
                return browser_instance
            
            # Wait for available browser (simple retry)
            await asyncio.sleep(1)
            return await self._acquire_browser()
    
    async def _release_browser(self, browser_instance: BrowserInstance) -> None:
        """Release a browser instance back to the pool."""
        async with self._lock:
            if browser_instance.id in self.browsers:
                # Check if browser needs maintenance
                if (browser_instance.request_count >= self.config.max_requests_per_browser or
                    browser_instance.failure_count >= self.config.max_failure_count):
                    await self._close_browser_instance(browser_instance.id)
                    # Create replacement if needed
                    if len(self.browsers) < self.config.min_browsers:
                        await self._create_browser_instance()
                else:
                    browser_instance.status = BrowserStatus.AVAILABLE
    
    async def _create_browser_instance(self) -> BrowserInstance:
        """Create a new browser instance."""
        try:
            browser_id = f"browser_{len(self.browsers)}_{int(datetime.utcnow().timestamp())}"
            
            # Launch browser with stealth settings
            browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                ]
            )
            
            browser_instance = BrowserInstance(
                id=browser_id,
                browser=browser
            )
            
            self.browsers[browser_id] = browser_instance
            logger.info(f"Created browser instance: {browser_id}")
            
            return browser_instance
            
        except Exception as e:
            logger.error(f"Failed to create browser instance: {str(e)}")
            raise
    
    async def _create_context(
        self, 
        browser_instance: BrowserInstance, 
        stealth_config: Optional[Dict[str, Any]] = None
    ) -> BrowserContext:
        """Create a browser context with stealth configuration."""
        stealth_config = stealth_config or {}
        
        # Random viewport size
        viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864},
        ]
        viewport = random.choice(viewports)
        
        # Random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        user_agent = stealth_config.get('user_agent', random.choice(user_agents))
        
        context = await browser_instance.browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # New York
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        # Add to tracking
        browser_instance.contexts.append(context)
        
        return context
    
    async def _close_browser_instance(self, browser_id: str) -> None:
        """Close and remove a browser instance."""
        if browser_id in self.browsers:
            browser_instance = self.browsers[browser_id]
            try:
                # Close all contexts
                for context in browser_instance.contexts:
                    try:
                        await context.close()
                    except Exception as e:
                        logger.warning(f"Error closing context: {str(e)}")
                
                # Close browser
                await browser_instance.browser.close()
                logger.info(f"Closed browser instance: {browser_id}")
                
            except Exception as e:
                logger.error(f"Error closing browser {browser_id}: {str(e)}")
            
            finally:
                del self.browsers[browser_id]
    
    async def _cleanup_loop(self) -> None:
        """Background task to cleanup old browsers."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._cleanup_old_browsers()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
    
    async def _cleanup_old_browsers(self) -> None:
        """Clean up old or failed browser instances."""
        async with self._lock:
            current_time = datetime.utcnow()
            browsers_to_close = []
            
            for browser_id, browser_instance in self.browsers.items():
                # Check if browser is too old
                age = current_time - browser_instance.created_at
                if age > timedelta(minutes=self.config.max_browser_age_minutes):
                    browsers_to_close.append(browser_id)
                    continue
                
                # Check if browser has too many failures
                if browser_instance.failure_count >= self.config.max_failure_count:
                    browsers_to_close.append(browser_id)
                    continue
                
                # Check if browser has handled too many requests
                if browser_instance.request_count >= self.config.max_requests_per_browser:
                    browsers_to_close.append(browser_id)
                    continue
            
            # Close old browsers
            for browser_id in browsers_to_close:
                if self.browsers[browser_id].status == BrowserStatus.AVAILABLE:
                    await self._close_browser_instance(browser_id)
            
            # Ensure minimum browsers
            while len(self.browsers) < self.config.min_browsers:
                await self._create_browser_instance()
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get current pool statistics."""
        stats = {
            'total_browsers': len(self.browsers),
            'available_browsers': 0,
            'in_use_browsers': 0,
            'failed_browsers': 0,
            'maintenance_browsers': 0,
            'total_requests': 0,
            'total_failures': 0,
        }
        
        for browser_instance in self.browsers.values():
            stats['total_requests'] += browser_instance.request_count
            stats['total_failures'] += browser_instance.failure_count
            
            if browser_instance.status == BrowserStatus.AVAILABLE:
                stats['available_browsers'] += 1
            elif browser_instance.status == BrowserStatus.IN_USE:
                stats['in_use_browsers'] += 1
            elif browser_instance.status == BrowserStatus.FAILED:
                stats['failed_browsers'] += 1
            elif browser_instance.status == BrowserStatus.MAINTENANCE:
                stats['maintenance_browsers'] += 1
        
        return stats