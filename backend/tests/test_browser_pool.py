"""
Unit tests for browser pool management.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.services.browser_pool import BrowserPool, BrowserPoolConfig, BrowserInstance, BrowserStatus


@pytest.fixture
def pool_config():
    """Create a test browser pool configuration."""
    return BrowserPoolConfig(
        min_browsers=2,
        max_browsers=3,
        max_requests_per_browser=5,
        max_browser_age_minutes=1,  # Short for testing
        max_failure_count=2,
        context_timeout_seconds=10,
        page_timeout_seconds=10
    )


@pytest.fixture
async def mock_playwright():
    """Create a mock playwright instance."""
    with patch('app.services.browser_pool.async_playwright') as mock_playwright:
        mock_playwright_instance = AsyncMock()
        mock_playwright.return_value.start = AsyncMock(return_value=mock_playwright_instance)
        
        # Mock chromium browser
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock()
        mock_browser.close = AsyncMock()
        
        mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright_instance.stop = AsyncMock()
        
        yield mock_playwright_instance


@pytest.mark.asyncio
async def test_browser_pool_initialization(pool_config, mock_playwright):
    """Test browser pool initialization."""
    pool = BrowserPool(pool_config)
    
    await pool.initialize()
    
    assert pool._initialized is True
    assert len(pool.browsers) == pool_config.min_browsers
    assert mock_playwright.chromium.launch.call_count == pool_config.min_browsers
    
    await pool.shutdown()


@pytest.mark.asyncio
async def test_browser_pool_context_acquisition(pool_config, mock_playwright):
    """Test browser context acquisition."""
    pool = BrowserPool(pool_config)
    await pool.initialize()
    
    # Mock context
    mock_context = AsyncMock()
    mock_browser = list(pool.browsers.values())[0].browser
    mock_browser.new_context.return_value = mock_context
    
    async with pool.get_browser_context() as context:
        assert context == mock_context
        assert mock_browser.new_context.called
    
    assert mock_context.close.called
    await pool.shutdown()


@pytest.mark.asyncio
async def test_browser_pool_concurrent_contexts(pool_config, mock_playwright):
    """Test concurrent browser context usage."""
    pool = BrowserPool(pool_config)
    await pool.initialize()
    
    # Mock contexts
    contexts = []
    for browser_instance in pool.browsers.values():
        mock_context = AsyncMock()
        browser_instance.browser.new_context.return_value = mock_context
        contexts.append(mock_context)
    
    async def use_context():
        async with pool.get_browser_context() as context:
            await asyncio.sleep(0.1)  # Simulate work
            return context
    
    # Use all browsers concurrently
    tasks = [use_context() for _ in range(pool_config.min_browsers)]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == pool_config.min_browsers
    
    # All contexts should be closed
    for context in contexts:
        assert context.close.called
    
    await pool.shutdown()


@pytest.mark.asyncio
async def test_browser_pool_scaling(pool_config, mock_playwright):
    """Test browser pool scaling up to max browsers."""
    pool = BrowserPool(pool_config)
    await pool.initialize()
    
    initial_browser_count = len(pool.browsers)
    
    # Mock contexts for new browsers
    def create_mock_browser():
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=AsyncMock())
        mock_browser.close = AsyncMock()
        return mock_browser
    
    mock_playwright.chromium.launch.side_effect = create_mock_browser
    
    async def use_context():
        async with pool.get_browser_context():
            await asyncio.sleep(0.2)  # Hold context longer
    
    # Create more concurrent requests than initial browsers
    tasks = [use_context() for _ in range(pool_config.max_browsers + 1)]
    await asyncio.gather(*tasks)
    
    # Should have scaled up but not exceed max
    assert len(pool.browsers) <= pool_config.max_browsers
    
    await pool.shutdown()


@pytest.mark.asyncio
async def test_browser_instance_failure_handling(pool_config, mock_playwright):
    """Test browser instance failure handling."""
    pool = BrowserPool(pool_config)
    await pool.initialize()
    
    # Get a browser instance and simulate failures
    browser_instance = list(pool.browsers.values())[0]
    browser_instance.failure_count = pool_config.max_failure_count
    
    # Mock context creation failure
    browser_instance.browser.new_context.side_effect = Exception("Context creation failed")
    
    with pytest.raises(Exception, match="Context creation failed"):
        async with pool.get_browser_context():
            pass
    
    await pool.shutdown()


@pytest.mark.asyncio
async def test_browser_pool_cleanup(pool_config, mock_playwright):
    """Test browser pool cleanup of old browsers."""
    pool = BrowserPool(pool_config)
    await pool.initialize()
    
    # Make browsers old
    for browser_instance in pool.browsers.values():
        browser_instance.created_at = datetime.utcnow() - timedelta(minutes=pool_config.max_browser_age_minutes + 1)
        browser_instance.status = BrowserStatus.AVAILABLE
    
    # Trigger cleanup
    await pool._cleanup_old_browsers()
    
    # Should have recreated minimum browsers
    assert len(pool.browsers) == pool_config.min_browsers
    
    await pool.shutdown()


@pytest.mark.asyncio
async def test_browser_pool_request_limit(pool_config, mock_playwright):
    """Test browser replacement after request limit."""
    pool = BrowserPool(pool_config)
    await pool.initialize()
    
    # Get a browser and max out its requests
    browser_instance = list(pool.browsers.values())[0]
    browser_instance.request_count = pool_config.max_requests_per_browser
    
    # Mock new browser creation
    new_mock_browser = AsyncMock()
    new_mock_browser.new_context = AsyncMock(return_value=AsyncMock())
    new_mock_browser.close = AsyncMock()
    mock_playwright.chromium.launch.return_value = new_mock_browser
    
    # Use the browser - should trigger replacement
    async with pool.get_browser_context():
        pass
    
    # Browser should have been replaced
    assert browser_instance.browser.close.called
    
    await pool.shutdown()


@pytest.mark.asyncio
async def test_browser_pool_stats(pool_config, mock_playwright):
    """Test browser pool statistics."""
    pool = BrowserPool(pool_config)
    await pool.initialize()
    
    stats = pool.get_pool_stats()
    
    assert stats['total_browsers'] == pool_config.min_browsers
    assert stats['available_browsers'] == pool_config.min_browsers
    assert stats['in_use_browsers'] == 0
    assert stats['failed_browsers'] == 0
    assert 'total_requests' in stats
    assert 'total_failures' in stats
    
    await pool.shutdown()


@pytest.mark.asyncio
async def test_browser_pool_shutdown(pool_config, mock_playwright):
    """Test browser pool shutdown."""
    pool = BrowserPool(pool_config)
    await pool.initialize()
    
    # Store references to browsers for verification
    browsers = [instance.browser for instance in pool.browsers.values()]
    
    await pool.shutdown()
    
    # All browsers should be closed
    for browser in browsers:
        assert browser.close.called
    
    assert pool._initialized is False
    assert len(pool.browsers) == 0
    assert mock_playwright.stop.called


@pytest.mark.asyncio
async def test_browser_pool_context_stealth_config(pool_config, mock_playwright):
    """Test browser context creation with stealth configuration."""
    pool = BrowserPool(pool_config)
    await pool.initialize()
    
    stealth_config = {
        'user_agent': 'Custom User Agent',
        'viewport': {'width': 1280, 'height': 720}
    }
    
    mock_context = AsyncMock()
    mock_browser = list(pool.browsers.values())[0].browser
    mock_browser.new_context.return_value = mock_context
    
    async with pool.get_browser_context(stealth_config) as context:
        assert context == mock_context
    
    # Verify context was created with proper configuration
    call_args = mock_browser.new_context.call_args
    assert call_args is not None
    assert 'user_agent' in call_args.kwargs
    assert 'viewport' in call_args.kwargs
    
    await pool.shutdown()


@pytest.mark.asyncio
async def test_browser_pool_double_initialization(pool_config, mock_playwright):
    """Test that double initialization doesn't cause issues."""
    pool = BrowserPool(pool_config)
    
    await pool.initialize()
    initial_browser_count = len(pool.browsers)
    
    # Initialize again
    await pool.initialize()
    
    # Should not create additional browsers
    assert len(pool.browsers) == initial_browser_count
    assert pool._initialized is True
    
    await pool.shutdown()


@pytest.mark.asyncio
async def test_browser_pool_error_during_initialization(pool_config):
    """Test error handling during browser pool initialization."""
    with patch('app.services.browser_pool.async_playwright') as mock_playwright:
        mock_playwright.return_value.start.side_effect = Exception("Playwright start failed")
        
        pool = BrowserPool(pool_config)
        
        with pytest.raises(Exception, match="Playwright start failed"):
            await pool.initialize()
        
        assert pool._initialized is False