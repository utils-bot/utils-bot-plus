"""
Screenshot service utilities for capturing web pages
"""

import asyncio
import io
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import aiohttp
from PIL import Image

from core.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)


class ScreenshotService:
    """Service for capturing website screenshots."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_key = settings.screenshot_api_key
        self.service_url = settings.screenshot_service_url or "https://screenshot-api.render.com"
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL format and security."""
        try:
            parsed = urlparse(url)
            
            # Check for valid scheme
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check for valid domain
            if not parsed.netloc:
                return False
            
            # Prevent local/private IPs (basic check)
            if parsed.hostname:
                if parsed.hostname.startswith('127.') or parsed.hostname == 'localhost':
                    return False
                if parsed.hostname.startswith('192.168.') or parsed.hostname.startswith('10.'):
                    return False
            
            return True
        except Exception:
            return False
    
    async def capture_screenshot(
        self, 
        url: str, 
        width: int = 1920, 
        height: int = 1080,
        full_page: bool = False,
        wait_time: int = 2
    ) -> Optional[bytes]:
        """
        Capture a screenshot of a web page.
        
        Args:
            url: The URL to capture
            width: Viewport width
            height: Viewport height
            full_page: Whether to capture full page or just viewport
            wait_time: Seconds to wait before capturing
        
        Returns:
            Screenshot image data as bytes, or None if failed
        """
        if not self._validate_url(url):
            logger.warning(f"Invalid URL for screenshot: {url}")
            return None
        
        if not self.session:
            logger.error("Screenshot service not initialized")
            return None
        
        try:
            # Use screenshotone.com API if available
            if self.api_key and self.service_url:
                return await self._capture_with_api(url, width, height, full_page, wait_time)
            else:
                # Fallback to basic HTTP request (for simple cases)
                return await self._capture_basic(url)
                
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None
    
    async def _capture_with_api(
        self, 
        url: str, 
        width: int, 
        height: int, 
        full_page: bool, 
        wait_time: int
    ) -> Optional[bytes]:
        """Capture screenshot using external API service."""
        params = {
            'url': url,
            'viewport_width': width,
            'viewport_height': height,
            'format': 'png',
            'full_page': full_page,
            'delay': wait_time,
            'block_ads': True,
            'block_cookie_banners': True,
            'cache': True,
            'cache_ttl': 3600  # 1 hour cache
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'UtilsBot+/1.0'
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        try:
            async with self.session.get(
                self.service_url, 
                params=params, 
                headers=headers,
                timeout=timeout
            ) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logger.error(f"Screenshot API error: {response.status}")
                    return None
        except asyncio.TimeoutError:
            logger.error("Screenshot API timeout")
            return None
        except Exception as e:
            logger.error(f"Screenshot API request failed: {e}")
            return None
    
    async def _capture_basic(self, url: str) -> Optional[bytes]:
        """Basic fallback method - just fetch the page content."""
        # This is a very basic fallback - you might want to implement
        # a headless browser solution here (like playwright or selenium)
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    # For this basic version, we'll just return a placeholder
                    # In a real implementation, you'd use a headless browser
                    return await self._create_placeholder_image(url)
                return None
        except Exception as e:
            logger.error(f"Basic screenshot capture failed: {e}")
            return None
    
    async def _create_placeholder_image(self, url: str) -> bytes:
        """Create a placeholder image with URL text."""
        # Create a simple image with text
        img = Image.new('RGB', (800, 600), color='white')
        
        # In a real implementation, you'd add the URL text to the image
        # For now, just return a blank image
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    async def get_page_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get basic page information (title, description, etc.)."""
        if not self._validate_url(url):
            return None
        
        if not self.session:
            return None
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._extract_page_info(html, url)
                return None
        except Exception as e:
            logger.error(f"Failed to get page info: {e}")
            return None
    
    def _extract_page_info(self, html: str, url: str) -> Dict[str, Any]:
        """Extract basic information from HTML content."""
        import re
        
        info = {'url': url}
        
        # Extract title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        if title_match:
            info['title'] = title_match.group(1).strip()
        
        # Extract meta description
        desc_match = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', 
            html, 
            re.IGNORECASE
        )
        if desc_match:
            info['description'] = desc_match.group(1).strip()
        
        # Extract Open Graph data
        og_title = re.search(
            r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', 
            html, 
            re.IGNORECASE
        )
        if og_title:
            info['og_title'] = og_title.group(1).strip()
        
        og_desc = re.search(
            r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', 
            html, 
            re.IGNORECASE
        )
        if og_desc:
            info['og_description'] = og_desc.group(1).strip()
        
        return info


# Global instance for easy access
screenshot_service = ScreenshotService()
