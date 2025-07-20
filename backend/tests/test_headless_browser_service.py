"""
Unit tests for headless browser service.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.headless_browser_service import HeadlessBrowserService, get_browser_service, shutdown_browser_service
from app.services.browser_pool import BrowserPoolConfig
from app.services.stealth_manager import StealthConfig
from app.services.session_manager import SessionConfig


@pytest.fixture
def browser_service():
    """Create a test browser service."""
    pool_config = BrowserPoolConfig(min_browsers=1, max_browsers=2)
    stealth_config = StealthConfig(enable_human_delays=False)  # Disable for faster tests
    session_config = SessionConfig(cleanup_interval_seconds=60)  # Longer for tests
    
    return HeadlessBrowserService(pool_config, stealth_config, session_config)


@pytest.fixture
def mock_page():
    """Create a mock page."""
    page = AsyncMock()
    page.goto = AsyncMock()
    page.content = AsyncMock(return_value="<html><body>Test content</body></html>")
    page.text_content = AsyncMock(return_value="Test content")
    page.evaluate = AsyncMock(return_value="Mozilla/5.0")
    page.url = "https://example.com"
    return page


@pytest.fixture
async def mock_browser_components():
    """Mock all browser service components."""
    with patch('app.services.headless_browser_service.BrowserPool') as mock_pool_class, \
         patch('app.services.headless_browser_service.StealthManager') as mock_stealth_class, \
         patch('app.services.headless_browser_service.SessionManager') as mock_session_class:
        
        # Mock browser pool
        mock_pool = AsyncMock()
        mock_pool.initialize = AsyncMock()
        mock_pool.shutdown = AsyncMock()
        mock_pool.get_browser_context = AsyncMock()
        mock_pool_class.return_value = mock_pool
        
        # Mock stealth manager
        mock_stealth = AsyncMock()
        mock_stealth.wait_for_page_load = AsyncMock(return_value=True)
        mock_stealth_class.return_value = mock_stealth
        
        # Mock session manager
        mock_session = AsyncMock()
        mock_session.start = AsyncMock()
        mock_session.stop = AsyncMock()
        mock_session.create_session = AsyncMock()
        mock_session.get_page = AsyncMock()
        mock_session_class.return_value = mock_session
        
        yield {
            'pool': mock_pool,
            'stealth': mock_stealth,
            'session': mock_session
        }


@pytest.mark.asyncio
async def test_browser_service_initialization(browser_service, mock_browser_components):
    """Test browser service initialization."""
    await browser_service.initialize()
    
    assert browser_service._initialized is True
    assert mock_browser_components['pool'].initialize.called
    assert mock_browser_components['session'].start.called


@pytest.mark.asyncio
async def test_browser_service_double_initialization(browser_service, mock_browser_components):
    """Test that double initialization doesn't cause issues."""
    await browser_service.initialize()
    await browser_service.initialize()  # Should not cause issues
    
    assert browser_service._initialized is True
    # Should only initialize once
    assert mock_browser_components['pool'].initialize.call_count == 1


@pytest.mark.asyncio
async def test_browser_service_shutdown(browser_service, mock_browser_components):
    """Test browser service shutdown."""
    await browser_service.initialize()
    await browser_service.shutdown()
    
    assert browser_service._initialized is False
    assert mock_browser_components['session'].stop.called
    assert mock_browser_components['pool'].shutdown.called


@pytest.mark.asyncio
async def test_browser_service_shutdown_not_initialized(browser_service, mock_browser_components):
    """Test shutdown when not initialized."""
    await browser_service.shutdown()
    
    # Should not call shutdown methods if not initialized
    assert not mock_browser_components['session'].stop.called
    assert not mock_browser_components['pool'].shutdown.called


@pytest.mark.asyncio
async def test_get_page_context_manager(browser_service, mock_browser_components, mock_page):
    """Test getting a page through context manager."""
    # Setup mocks
    mock_context = AsyncMock()
    mock_session = AsyncMock()
    
    mock_browser_components['pool'].get_browser_context.return_value.__aenter__ = AsyncMock(return_value=mock_context)
    mock_browser_components['pool'].get_browser_context.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].create_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_browser_components['session'].create_session.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].get_page.return_value.__aenter__ = AsyncMock(return_value=mock_page)
    mock_browser_components['session'].get_page.return_value.__aexit__ = AsyncMock(return_value=None)
    
    async with browser_service.get_page() as page:
        assert page == mock_page
    
    assert mock_browser_components['pool'].get_browser_context.called
    assert mock_browser_components['session'].create_session.called
    assert mock_browser_components['session'].get_page.called


@pytest.mark.asyncio
async def test_get_page_auto_initialize(browser_service, mock_browser_components, mock_page):
    """Test that get_page auto-initializes the service."""
    # Setup mocks
    mock_context = AsyncMock()
    mock_session = AsyncMock()
    
    mock_browser_components['pool'].get_browser_context.return_value.__aenter__ = AsyncMock(return_value=mock_context)
    mock_browser_components['pool'].get_browser_context.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].create_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_browser_components['session'].create_session.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].get_page.return_value.__aenter__ = AsyncMock(return_value=mock_page)
    mock_browser_components['session'].get_page.return_value.__aexit__ = AsyncMock(return_value=None)
    
    # Service not initialized yet
    assert not browser_service._initialized
    
    async with browser_service.get_page() as page:
        assert page == mock_page
    
    # Should have auto-initialized
    assert browser_service._initialized
    assert mock_browser_components['pool'].initialize.called


@pytest.mark.asyncio
async def test_scrape_url_success(browser_service, mock_browser_components, mock_page):
    """Test successful URL scraping."""
    # Setup mocks
    mock_context = AsyncMock()
    mock_session = AsyncMock()
    
    mock_browser_components['pool'].get_browser_context.return_value.__aenter__ = AsyncMock(return_value=mock_context)
    mock_browser_components['pool'].get_browser_context.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].create_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_browser_components['session'].create_session.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].get_page.return_value.__aenter__ = AsyncMock(return_value=mock_page)
    mock_browser_components['session'].get_page.return_value.__aexit__ = AsyncMock(return_value=None)
    
    # Mock scraper function
    async def mock_scraper(page):
        return {"title": "Test Page", "content": "Test content"}
    
    result = await browser_service.scrape_url("https://example.com", mock_scraper)
    
    assert result == {"title": "Test Page", "content": "Test content"}
    assert mock_page.goto.called
    assert mock_browser_components['stealth'].wait_for_page_load.called


@pytest.mark.asyncio
async def test_scrape_url_bot_detection(browser_service, mock_browser_components, mock_page):
    """Test URL scraping with bot detection."""
    # Setup mocks
    mock_context = AsyncMock()
    mock_session = AsyncMock()
    
    mock_browser_components['pool'].get_browser_context.return_value.__aenter__ = AsyncMock(return_value=mock_context)
    mock_browser_components['pool'].get_browser_context.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].create_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_browser_components['session'].create_session.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].get_page.return_value.__aenter__ = AsyncMock(return_value=mock_page)
    mock_browser_components['session'].get_page.return_value.__aexit__ = AsyncMock(return_value=None)
    
    # Mock bot detection
    mock_browser_components['stealth'].wait_for_page_load.return_value = False
    
    async def mock_scraper(page):
        return {"title": "Test Page"}
    
    with pytest.raises(RuntimeError, match="Bot detection or CAPTCHA detected"):
        await browser_service.scrape_url("https://example.com", mock_scraper)


@pytest.mark.asyncio
async def test_scrape_url_with_retries(browser_service, mock_browser_components, mock_page):
    """Test URL scraping with retries."""
    # Setup mocks
    mock_context = AsyncMock()
    mock_session = AsyncMock()
    
    mock_browser_components['pool'].get_browser_context.return_value.__aenter__ = AsyncMock(return_value=mock_context)
    mock_browser_components['pool'].get_browser_context.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].create_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_browser_components['session'].create_session.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].get_page.return_value.__aenter__ = AsyncMock(return_value=mock_page)
    mock_browser_components['session'].get_page.return_value.__aexit__ = AsyncMock(return_value=None)
    
    # Mock scraper function that fails first time
    call_count = 0
    async def mock_scraper(page):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("First attempt failed")
        return {"title": "Success on retry"}
    
    result = await browser_service.scrape_url("https://example.com", mock_scraper, max_retries=2)
    
    assert result == {"title": "Success on retry"}
    assert call_count == 2


@pytest.mark.asyncio
async def test_scrape_url_max_retries_exceeded(browser_service, mock_browser_components, mock_page):
    """Test URL scraping when max retries are exceeded."""
    # Setup mocks
    mock_context = AsyncMock()
    mock_session = AsyncMock()
    
    mock_browser_components['pool'].get_browser_context.return_value.__aenter__ = AsyncMock(return_value=mock_context)
    mock_browser_components['pool'].get_browser_context.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].create_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_browser_components['session'].create_session.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].get_page.return_value.__aenter__ = AsyncMock(return_value=mock_page)
    mock_browser_components['session'].get_page.return_value.__aexit__ = AsyncMock(return_value=None)
    
    # Mock scraper function that always fails
    async def mock_scraper(page):
        raise Exception("Always fails")
    
    with pytest.raises(Exception, match="Always fails"):
        await browser_service.scrape_url("https://example.com", mock_scraper, max_retries=1)


@pytest.mark.asyncio
async def test_scrape_multiple_urls(browser_service, mock_browser_components, mock_page):
    """Test scraping multiple URLs concurrently."""
    # Setup mocks
    mock_context = AsyncMock()
    mock_session = AsyncMock()
    
    mock_browser_components['pool'].get_browser_context.return_value.__aenter__ = AsyncMock(return_value=mock_context)
    mock_browser_components['pool'].get_browser_context.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].create_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_browser_components['session'].create_session.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].get_page.return_value.__aenter__ = AsyncMock(return_value=mock_page)
    mock_browser_components['session'].get_page.return_value.__aexit__ = AsyncMock(return_value=None)
    
    urls = ["https://example1.com", "https://example2.com"]
    
    async def mock_scraper(page, url):
        return {"url": url, "title": f"Title for {url}"}
    
    results = await browser_service.scrape_multiple_urls(urls, mock_scraper, max_concurrent=2)
    
    assert len(results) == 2
    for result in results:
        assert result['success'] is True
        assert 'data' in result
        assert result['error'] is None


@pytest.mark.asyncio
async def test_scrape_multiple_urls_with_failures(browser_service, mock_browser_components, mock_page):
    """Test scraping multiple URLs with some failures."""
    # Setup mocks
    mock_context = AsyncMock()
    mock_session = AsyncMock()
    
    mock_browser_components['pool'].get_browser_context.return_value.__aenter__ = AsyncMock(return_value=mock_context)
    mock_browser_components['pool'].get_browser_context.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].create_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_browser_components['session'].create_session.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].get_page.return_value.__aenter__ = AsyncMock(return_value=mock_page)
    mock_browser_components['session'].get_page.return_value.__aexit__ = AsyncMock(return_value=None)
    
    urls = ["https://example1.com", "https://example2.com"]
    
    async def mock_scraper(page, url):
        if "example1" in url:
            raise Exception("Failed to scrape example1")
        return {"url": url, "title": f"Title for {url}"}
    
    results = await browser_service.scrape_multiple_urls(urls, mock_scraper, max_concurrent=2)
    
    assert len(results) == 2
    
    # First URL should have failed
    failed_result = next(r for r in results if "example1" in r['url'])
    assert failed_result['success'] is False
    assert failed_result['error'] is not None
    
    # Second URL should have succeeded
    success_result = next(r for r in results if "example2" in r['url'])
    assert success_result['success'] is True
    assert success_result['data'] is not None


@pytest.mark.asyncio
async def test_test_browser_automation(browser_service, mock_browser_components, mock_page):
    """Test browser automation testing functionality."""
    # Setup mocks
    mock_context = AsyncMock()
    mock_session = AsyncMock()
    
    mock_browser_components['pool'].get_browser_context.return_value.__aenter__ = AsyncMock(return_value=mock_context)
    mock_browser_components['pool'].get_browser_context.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].create_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_browser_components['session'].create_session.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_browser_components['session'].get_page.return_value.__aenter__ = AsyncMock(return_value=mock_page)
    mock_browser_components['session'].get_page.return_value.__aexit__ = AsyncMock(return_value=None)
    
    # Mock page responses
    mock_page.content.return_value = "<html><body>Test</body></html>"
    mock_page.text_content.return_value = "User-Agent: Mozilla/5.0 Chrome"
    mock_page.evaluate.side_effect = [
        "Mozilla/5.0 Chrome",  # navigator.userAgent
        True,  # webdriver undefined
        5  # plugins length
    ]
    
    result = await browser_service.test_browser_automation()
    
    assert 'test_url' in result
    assert 'timestamp' in result
    assert 'tests' in result
    assert len(result['tests']) == 4  # 4 test cases
    
    # Check that all tests ran
    test_names = [test['name'] for test in result['tests']]
    expected_tests = ['basic_page_loading', 'user_agent_test', 'javascript_execution', 'stealth_measures']
    for expected_test in expected_tests:
        assert expected_test in test_names


def test_get_service_stats(browser_service, mock_browser_components):
    """Test service statistics retrieval."""
    # Mock stats from components
    mock_browser_components['pool'].get_pool_stats.return_value = {
        'total_browsers': 2,
        'available_browsers': 1
    }
    mock_browser_components['session'].get_session_stats.return_value = {
        'total_sessions': 1,
        'active_sessions': 1
    }
    
    stats = browser_service.get_service_stats()
    
    assert 'initialized' in stats
    assert 'timestamp' in stats
    assert 'browser_pool' in stats
    assert 'session_manager' in stats
    assert 'config' in stats
    
    assert stats['browser_pool']['total_browsers'] == 2
    assert stats['session_manager']['total_sessions'] == 1


@pytest.mark.asyncio
async def test_global_browser_service():
    """Test global browser service functions."""
    with patch('app.services.headless_browser_service.HeadlessBrowserService') as mock_service_class:
        mock_service = AsyncMock()
        mock_service.initialize = AsyncMock()
        mock_service.shutdown = AsyncMock()
        mock_service_class.return_value = mock_service
        
        # Get service (should create and initialize)
        service1 = await get_browser_service()
        assert service1 == mock_service
        assert mock_service.initialize.called
        
        # Get service again (should return same instance)
        service2 = await get_browser_service()
        assert service2 == service1
        assert mock_service.initialize.call_count == 1  # Should not initialize again
        
        # Shutdown service
        await shutdown_browser_service()
        assert mock_service.shutdown.called


@pytest.mark.asyncio
async def test_initialization_error_handling(browser_service, mock_browser_components):
    """Test error handling during initialization."""
    mock_browser_components['pool'].initialize.side_effect = Exception("Pool init failed")
    
    with pytest.raises(Exception, match="Pool init failed"):
        await browser_service.initialize()
    
    assert not browser_service._initialized


@pytest.mark.asyncio
async def test_shutdown_error_handling(browser_service, mock_browser_components):
    """Test error handling during shutdown."""
    await browser_service.initialize()
    
    mock_browser_components['session'].stop.side_effect = Exception("Session stop failed")
    
    # Should handle error gracefully
    await browser_service.shutdown()
    
    assert not browser_service._initialized