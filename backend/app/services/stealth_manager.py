"""
Stealth manager for anti-detection measures and human behavior simulation.
"""
import asyncio
import random
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from patchright.async_api import Page, BrowserContext


logger = logging.getLogger(__name__)


@dataclass
class StealthConfig:
    """Configuration for stealth measures."""
    enable_human_delays: bool = True
    enable_mouse_movements: bool = True
    enable_scroll_simulation: bool = True
    enable_typing_delays: bool = True
    min_delay_ms: int = 100
    max_delay_ms: int = 2000
    mouse_movement_steps: int = 10
    scroll_pause_probability: float = 0.3
    typing_speed_wpm: int = 45  # Words per minute


class StealthManager:
    """Manages anti-detection measures and human behavior simulation."""
    
    def __init__(self, config: Optional[StealthConfig] = None):
        """Initialize the stealth manager."""
        self.config = config or StealthConfig()
        self._user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
        ]
        
        self._viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864},
            {'width': 1280, 'height': 720},
            {'width': 1600, 'height': 900},
        ]
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent string."""
        return random.choice(self._user_agents)
    
    def get_random_viewport(self) -> Dict[str, int]:
        """Get a random viewport size."""
        return random.choice(self._viewports)
    
    async def setup_page_stealth(self, page: Page) -> None:
        """Setup stealth measures for a page."""
        try:
            # Override navigator properties to avoid detection
            await page.add_init_script("""
                // Override webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Override plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Override chrome runtime
                if (!window.chrome) {
                    window.chrome = {};
                }
                if (!window.chrome.runtime) {
                    window.chrome.runtime = {};
                }
                
                // Override screen properties
                Object.defineProperty(screen, 'colorDepth', {
                    get: () => 24,
                });
                
                // Override timezone
                Date.prototype.getTimezoneOffset = function() {
                    return -300; // EST timezone
                };
            """)
            
            # Set extra headers
            await page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            })
            
            logger.debug("Page stealth setup completed")
            
        except Exception as e:
            logger.warning(f"Error setting up page stealth: {str(e)}")
    
    async def human_delay(self, min_ms: Optional[int] = None, max_ms: Optional[int] = None) -> None:
        """Add human-like delay."""
        if not self.config.enable_human_delays:
            return
        
        min_delay = min_ms or self.config.min_delay_ms
        max_delay = max_ms or self.config.max_delay_ms
        
        delay = random.randint(min_delay, max_delay) / 1000.0
        await asyncio.sleep(delay)
    
    async def human_type(self, page: Page, selector: str, text: str) -> None:
        """Type text with human-like delays."""
        element = await page.wait_for_selector(selector)
        
        if not self.config.enable_typing_delays:
            await element.fill(text)
            return
        
        # Clear existing text
        await element.click()
        await page.keyboard.press('Control+a')
        
        # Calculate typing delay based on WPM
        chars_per_second = (self.config.typing_speed_wpm * 5) / 60  # 5 chars per word average
        base_delay = 1000 / chars_per_second  # milliseconds per character
        
        for char in text:
            # Add randomness to typing speed
            delay = base_delay + random.uniform(-50, 100)
            await asyncio.sleep(delay / 1000.0)
            await page.keyboard.type(char)
        
        # Random pause after typing
        await self.human_delay(200, 800)
    
    async def human_click(self, page: Page, selector: str) -> None:
        """Click with human-like behavior."""
        element = await page.wait_for_selector(selector)
        
        if self.config.enable_mouse_movements:
            # Get element position
            box = await element.bounding_box()
            if box:
                # Move mouse to element with steps
                current_pos = await page.evaluate('() => ({ x: 0, y: 0 })')
                target_x = box['x'] + box['width'] / 2
                target_y = box['y'] + box['height'] / 2
                
                await self._move_mouse_human_like(page, current_pos['x'], current_pos['y'], target_x, target_y)
        
        # Random delay before click
        await self.human_delay(100, 500)
        
        # Click
        await element.click()
        
        # Random delay after click
        await self.human_delay(200, 800)
    
    async def human_scroll(self, page: Page, direction: str = 'down', distance: int = 300) -> None:
        """Scroll with human-like behavior."""
        if not self.config.enable_scroll_simulation:
            return
        
        scroll_steps = random.randint(3, 8)
        step_distance = distance // scroll_steps
        
        for i in range(scroll_steps):
            if direction == 'down':
                await page.mouse.wheel(0, step_distance)
            else:
                await page.mouse.wheel(0, -step_distance)
            
            # Random pause during scrolling
            if random.random() < self.config.scroll_pause_probability:
                await self.human_delay(200, 1000)
            else:
                await self.human_delay(50, 200)
    
    async def _move_mouse_human_like(self, page: Page, start_x: float, start_y: float, end_x: float, end_y: float) -> None:
        """Move mouse in human-like curved path."""
        steps = self.config.mouse_movement_steps
        
        for i in range(steps + 1):
            progress = i / steps
            
            # Add some curve to the movement
            curve_offset = 20 * random.uniform(-1, 1) * (progress * (1 - progress))
            
            x = start_x + (end_x - start_x) * progress + curve_offset
            y = start_y + (end_y - start_y) * progress + curve_offset
            
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.01, 0.05))
    
    async def detect_captcha(self, page: Page) -> bool:
        """Detect if a CAPTCHA is present on the page."""
        captcha_selectors = [
            '[class*="captcha"]',
            '[id*="captcha"]',
            '[class*="recaptcha"]',
            '[id*="recaptcha"]',
            'iframe[src*="recaptcha"]',
            'iframe[src*="captcha"]',
            '[class*="challenge"]',
            '[id*="challenge"]',
            '.g-recaptcha',
            '#recaptcha',
            '[data-sitekey]',
        ]
        
        for selector in captcha_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    is_visible = await element.is_visible()
                    if is_visible:
                        logger.warning(f"CAPTCHA detected with selector: {selector}")
                        return True
            except Exception:
                continue
        
        # Check for common CAPTCHA text
        captcha_texts = [
            'verify you are human',
            'prove you are not a robot',
            'complete the captcha',
            'security check',
            'verify your identity',
            'i\'m not a robot',
        ]
        
        try:
            page_text = await page.text_content('body')
            if page_text:
                page_text_lower = page_text.lower()
                for text in captcha_texts:
                    if text in page_text_lower:
                        logger.warning(f"CAPTCHA detected with text: {text}")
                        return True
        except Exception:
            pass
        
        return False
    
    async def detect_bot_detection(self, page: Page) -> bool:
        """Detect if bot detection is active."""
        bot_detection_indicators = [
            'access denied',
            'blocked',
            'suspicious activity',
            'automated requests',
            'rate limit',
            'too many requests',
            'cloudflare',
            'checking your browser',
            'please wait',
            'security check',
        ]
        
        try:
            page_text = await page.text_content('body')
            if page_text:
                page_text_lower = page_text.lower()
                for indicator in bot_detection_indicators:
                    if indicator in page_text_lower:
                        logger.warning(f"Bot detection detected: {indicator}")
                        return True
        except Exception:
            pass
        
        # Check for common bot detection redirects
        current_url = page.url
        bot_detection_urls = [
            'cloudflare.com',
            'distilnetworks.com',
            'perimeterx.com',
            'datadome.co',
        ]
        
        for url_part in bot_detection_urls:
            if url_part in current_url:
                logger.warning(f"Bot detection redirect detected: {url_part}")
                return True
        
        return False
    
    async def wait_for_page_load(self, page: Page, timeout: int = 30000) -> bool:
        """Wait for page to fully load with human-like behavior."""
        try:
            # Wait for network to be idle
            await page.wait_for_load_state('networkidle', timeout=timeout)
            
            # Random delay to simulate reading
            await self.human_delay(1000, 3000)
            
            # Check for bot detection
            if await self.detect_bot_detection(page):
                return False
            
            # Check for CAPTCHA
            if await self.detect_captcha(page):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error waiting for page load: {str(e)}")
            return False
    
    def get_stealth_config(self) -> Dict[str, Any]:
        """Get current stealth configuration."""
        return {
            'user_agent': self.get_random_user_agent(),
            'viewport': self.get_random_viewport(),
            'enable_human_delays': self.config.enable_human_delays,
            'enable_mouse_movements': self.config.enable_mouse_movements,
            'enable_scroll_simulation': self.config.enable_scroll_simulation,
            'enable_typing_delays': self.config.enable_typing_delays,
        }