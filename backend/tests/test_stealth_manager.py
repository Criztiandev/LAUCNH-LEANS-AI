"""
Unit tests for stealth manager and anti-detection measures.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.stealth_manager import StealthManager, StealthConfig


@pytest.fixture
def stealth_config():
    """Create a test stealth configuration."""
    return StealthConfig(
        enable_human_delays=True,
        enable_mouse_movements=True,
        enable_scroll_simulation=True,
        enable_typing_delays=True,
        min_delay_ms=50,
        max_delay_ms=200,
        mouse_movement_steps=5,
        scroll_pause_probability=0.5,
        typing_speed_wpm=60
    )


@pytest.fixture
def mock_page():
    """Create a mock page object."""
    page = AsyncMock()
    page.add_init_script = AsyncMock()
    page.set_extra_http_headers = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.keyboard = AsyncMock()
    page.mouse = AsyncMock()
    page.evaluate = AsyncMock()
    page.query_selector = AsyncMock()
    page.text_content = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.url = "https://example.com"
    return page


@pytest.mark.asyncio
async def test_stealth_manager_initialization(stealth_config):
    """Test stealth manager initialization."""
    manager = StealthManager(stealth_config)
    
    assert manager.config == stealth_config
    assert len(manager._user_agents) > 0
    assert len(manager._viewports) > 0


def test_get_random_user_agent(stealth_config):
    """Test random user agent generation."""
    manager = StealthManager(stealth_config)
    
    user_agent = manager.get_random_user_agent()
    
    assert isinstance(user_agent, str)
    assert len(user_agent) > 0
    assert 'Mozilla' in user_agent


def test_get_random_viewport(stealth_config):
    """Test random viewport generation."""
    manager = StealthManager(stealth_config)
    
    viewport = manager.get_random_viewport()
    
    assert isinstance(viewport, dict)
    assert 'width' in viewport
    assert 'height' in viewport
    assert viewport['width'] > 0
    assert viewport['height'] > 0


@pytest.mark.asyncio
async def test_setup_page_stealth(stealth_config, mock_page):
    """Test page stealth setup."""
    manager = StealthManager(stealth_config)
    
    await manager.setup_page_stealth(mock_page)
    
    # Verify init script was added
    assert mock_page.add_init_script.called
    init_script = mock_page.add_init_script.call_args[0][0]
    assert 'navigator.webdriver' in init_script
    assert 'navigator.plugins' in init_script
    
    # Verify headers were set
    assert mock_page.set_extra_http_headers.called
    headers = mock_page.set_extra_http_headers.call_args[0][0]
    assert 'Accept-Language' in headers
    assert 'User-Agent' not in headers  # Should not override user agent here


@pytest.mark.asyncio
async def test_human_delay(stealth_config):
    """Test human-like delay functionality."""
    manager = StealthManager(stealth_config)
    
    import time
    start_time = time.time()
    await manager.human_delay(100, 200)
    end_time = time.time()
    
    # Should have delayed between 0.1 and 0.2 seconds
    delay_time = end_time - start_time
    assert 0.05 <= delay_time <= 0.25  # Allow some tolerance


@pytest.mark.asyncio
async def test_human_delay_disabled(stealth_config, mock_page):
    """Test human delay when disabled."""
    stealth_config.enable_human_delays = False
    manager = StealthManager(stealth_config)
    
    import time
    start_time = time.time()
    await manager.human_delay(1000, 2000)  # Long delay
    end_time = time.time()
    
    # Should not have delayed significantly
    delay_time = end_time - start_time
    assert delay_time < 0.1


@pytest.mark.asyncio
async def test_human_type(stealth_config, mock_page):
    """Test human-like typing."""
    manager = StealthManager(stealth_config)
    
    # Mock element
    mock_element = AsyncMock()
    mock_page.wait_for_selector.return_value = mock_element
    
    test_text = "Hello World"
    await manager.human_type(mock_page, "#input", test_text)
    
    # Verify element interaction
    assert mock_element.click.called
    assert mock_page.keyboard.press.called
    assert mock_page.keyboard.type.call_count == len(test_text)


@pytest.mark.asyncio
async def test_human_type_disabled(stealth_config, mock_page):
    """Test human typing when disabled."""
    stealth_config.enable_typing_delays = False
    manager = StealthManager(stealth_config)
    
    # Mock element
    mock_element = AsyncMock()
    mock_page.wait_for_selector.return_value = mock_element
    
    test_text = "Hello World"
    await manager.human_type(mock_page, "#input", test_text)
    
    # Should use fill instead of individual typing
    assert mock_element.fill.called
    assert mock_element.fill.call_args[0][0] == test_text


@pytest.mark.asyncio
async def test_human_click(stealth_config, mock_page):
    """Test human-like clicking."""
    manager = StealthManager(stealth_config)
    
    # Mock element with bounding box
    mock_element = AsyncMock()
    mock_element.bounding_box.return_value = {
        'x': 100, 'y': 200, 'width': 50, 'height': 30
    }
    mock_page.wait_for_selector.return_value = mock_element
    mock_page.evaluate.return_value = {'x': 0, 'y': 0}
    
    await manager.human_click(mock_page, "#button")
    
    # Verify click sequence
    assert mock_element.click.called
    if stealth_config.enable_mouse_movements:
        assert mock_page.mouse.move.called


@pytest.mark.asyncio
async def test_human_scroll(stealth_config, mock_page):
    """Test human-like scrolling."""
    manager = StealthManager(stealth_config)
    
    await manager.human_scroll(mock_page, 'down', 300)
    
    # Verify mouse wheel was used
    assert mock_page.mouse.wheel.called
    
    # Check that multiple wheel events were triggered (steps)
    assert mock_page.mouse.wheel.call_count > 1


@pytest.mark.asyncio
async def test_human_scroll_disabled(stealth_config, mock_page):
    """Test human scrolling when disabled."""
    stealth_config.enable_scroll_simulation = False
    manager = StealthManager(stealth_config)
    
    await manager.human_scroll(mock_page, 'down', 300)
    
    # Should not have scrolled
    assert not mock_page.mouse.wheel.called


@pytest.mark.asyncio
async def test_detect_captcha_positive(stealth_config, mock_page):
    """Test CAPTCHA detection - positive case."""
    manager = StealthManager(stealth_config)
    
    # Mock CAPTCHA element
    mock_captcha_element = AsyncMock()
    mock_captcha_element.is_visible.return_value = True
    mock_page.query_selector.return_value = mock_captcha_element
    
    result = await manager.detect_captcha(mock_page)
    
    assert result is True


@pytest.mark.asyncio
async def test_detect_captcha_text_based(stealth_config, mock_page):
    """Test CAPTCHA detection based on text content."""
    manager = StealthManager(stealth_config)
    
    # Mock no visible elements but CAPTCHA text
    mock_page.query_selector.return_value = None
    mock_page.text_content.return_value = "Please verify you are human"
    
    result = await manager.detect_captcha(mock_page)
    
    assert result is True


@pytest.mark.asyncio
async def test_detect_captcha_negative(stealth_config, mock_page):
    """Test CAPTCHA detection - negative case."""
    manager = StealthManager(stealth_config)
    
    # Mock no CAPTCHA elements or text
    mock_page.query_selector.return_value = None
    mock_page.text_content.return_value = "Welcome to our website"
    
    result = await manager.detect_captcha(mock_page)
    
    assert result is False


@pytest.mark.asyncio
async def test_detect_bot_detection_positive(stealth_config, mock_page):
    """Test bot detection - positive case."""
    manager = StealthManager(stealth_config)
    
    mock_page.text_content.return_value = "Access denied due to suspicious activity"
    
    result = await manager.detect_bot_detection(mock_page)
    
    assert result is True


@pytest.mark.asyncio
async def test_detect_bot_detection_url_based(stealth_config, mock_page):
    """Test bot detection based on URL."""
    manager = StealthManager(stealth_config)
    
    mock_page.url = "https://cloudflare.com/security-check"
    mock_page.text_content.return_value = "Normal content"
    
    result = await manager.detect_bot_detection(mock_page)
    
    assert result is True


@pytest.mark.asyncio
async def test_detect_bot_detection_negative(stealth_config, mock_page):
    """Test bot detection - negative case."""
    manager = StealthManager(stealth_config)
    
    mock_page.text_content.return_value = "Welcome to our website"
    
    result = await manager.detect_bot_detection(mock_page)
    
    assert result is False


@pytest.mark.asyncio
async def test_wait_for_page_load_success(stealth_config, mock_page):
    """Test successful page load waiting."""
    manager = StealthManager(stealth_config)
    
    # Mock successful load
    mock_page.wait_for_load_state = AsyncMock()
    mock_page.text_content.return_value = "Normal page content"
    
    result = await manager.wait_for_page_load(mock_page)
    
    assert result is True
    assert mock_page.wait_for_load_state.called


@pytest.mark.asyncio
async def test_wait_for_page_load_bot_detection(stealth_config, mock_page):
    """Test page load waiting with bot detection."""
    manager = StealthManager(stealth_config)
    
    # Mock bot detection
    mock_page.wait_for_load_state = AsyncMock()
    mock_page.text_content.return_value = "Access denied"
    
    result = await manager.wait_for_page_load(mock_page)
    
    assert result is False


@pytest.mark.asyncio
async def test_wait_for_page_load_captcha(stealth_config, mock_page):
    """Test page load waiting with CAPTCHA."""
    manager = StealthManager(stealth_config)
    
    # Mock CAPTCHA
    mock_page.wait_for_load_state = AsyncMock()
    mock_page.text_content.return_value = "Please verify you are human"
    mock_captcha_element = AsyncMock()
    mock_captcha_element.is_visible.return_value = True
    mock_page.query_selector.return_value = mock_captcha_element
    
    result = await manager.wait_for_page_load(mock_page)
    
    assert result is False


@pytest.mark.asyncio
async def test_wait_for_page_load_timeout(stealth_config, mock_page):
    """Test page load waiting with timeout."""
    manager = StealthManager(stealth_config)
    
    # Mock timeout
    mock_page.wait_for_load_state.side_effect = asyncio.TimeoutError()
    
    result = await manager.wait_for_page_load(mock_page, timeout=1000)
    
    assert result is False


def test_get_stealth_config(stealth_config):
    """Test stealth configuration retrieval."""
    manager = StealthManager(stealth_config)
    
    config = manager.get_stealth_config()
    
    assert isinstance(config, dict)
    assert 'user_agent' in config
    assert 'viewport' in config
    assert 'enable_human_delays' in config
    assert config['enable_human_delays'] == stealth_config.enable_human_delays


@pytest.mark.asyncio
async def test_move_mouse_human_like(stealth_config, mock_page):
    """Test human-like mouse movement."""
    manager = StealthManager(stealth_config)
    
    await manager._move_mouse_human_like(mock_page, 0, 0, 100, 100)
    
    # Should have made multiple mouse moves
    assert mock_page.mouse.move.call_count == stealth_config.mouse_movement_steps + 1


@pytest.mark.asyncio
async def test_setup_page_stealth_error_handling(stealth_config, mock_page):
    """Test error handling in page stealth setup."""
    manager = StealthManager(stealth_config)
    
    # Mock error in init script
    mock_page.add_init_script.side_effect = Exception("Init script failed")
    
    # Should not raise exception, just log warning
    await manager.setup_page_stealth(mock_page)
    
    # Headers should still be attempted
    assert mock_page.set_extra_http_headers.called