"""
Simple integration test for browser infrastructure.
"""
import asyncio
import logging
from app.services.headless_browser_service import HeadlessBrowserService
from app.services.browser_pool import BrowserPoolConfig
from app.services.stealth_manager import StealthConfig
from app.services.session_manager import SessionConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_browser_infrastructure():
    """Test the browser infrastructure with a simple example."""
    
    # Create service with minimal configuration
    pool_config = BrowserPoolConfig(
        min_browsers=1,
        max_browsers=2,
        max_requests_per_browser=5
    )
    
    stealth_config = StealthConfig(
        enable_human_delays=True,
        min_delay_ms=100,
        max_delay_ms=500
    )
    
    session_config = SessionConfig(
        max_session_duration_minutes=5,
        max_requests_per_session=10
    )
    
    service = HeadlessBrowserService(pool_config, stealth_config, session_config)
    
    try:
        logger.info("Initializing browser service...")
        await service.initialize()
        logger.info("Browser service initialized successfully")
        
        # Test basic page scraping
        async def simple_scraper(page):
            """Simple scraper function."""
            title = await page.title()
            url = page.url
            
            # Test JavaScript execution
            user_agent = await page.evaluate("() => navigator.userAgent")
            
            return {
                'title': title,
                'url': url,
                'user_agent': user_agent,
                'success': True
            }
        
        logger.info("Testing basic page scraping...")
        result = await service.scrape_url(
            "https://www.google.com",
            simple_scraper,
            max_retries=2
        )
        
        logger.info(f"Scraping result: {result}")
        
        # Test service statistics
        stats = service.get_service_stats()
        logger.info(f"Service stats: {stats}")
        
        # Test browser automation test suite
        logger.info("Running browser automation test suite...")
        test_results = await service.test_browser_automation()
        
        successful_tests = [t for t in test_results['tests'] if t.get('success', False)]
        logger.info(f"Test suite results: {len(successful_tests)}/{len(test_results['tests'])} tests passed")
        
        for test in test_results['tests']:
            status = "PASSED" if test.get('success', False) else "FAILED"
            logger.info(f"  {test['name']}: {status}")
            if not test.get('success', False) and 'error' in test:
                logger.info(f"    Error: {test['error']}")
        
        logger.info("Browser infrastructure test completed successfully!")
        
    except Exception as e:
        logger.error(f"Browser infrastructure test failed: {str(e)}")
        raise
    
    finally:
        logger.info("Shutting down browser service...")
        await service.shutdown()
        logger.info("Browser service shutdown complete")


if __name__ == "__main__":
    asyncio.run(test_browser_infrastructure())