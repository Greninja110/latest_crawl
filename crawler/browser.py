"""
Simplified browser implementation using requests instead of Playwright
"""
import logging
import random
import time
from typing import Dict, List, Any, Optional
import requests
from fake_useragent import UserAgent
from urllib.parse import urljoin
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class SimpleBrowser:
    """Simple browser-like interface using requests"""
    
    def __init__(self, use_proxies: bool = False):
        """
        Initialize simple browser
        
        Args:
            use_proxies: Whether to use proxy rotation (not implemented in simplified version)
        """
        self.session = requests.Session()
        self.user_agent = UserAgent()
        
        # Set initial user agent
        self.session.headers.update({
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        })
        
        logger.info(f"Initialized SimpleBrowser with user agent: {self.session.headers['User-Agent']}")
    
    async def navigate(self, url: str, wait_for_load: bool = True) -> Dict[str, Any]:
        """
        Navigate to a specific URL (async compatible interface)
        
        Args:
            url: URL to navigate to
            wait_for_load: Whether to wait for page load (ignored in simplified version)
            
        Returns:
            Dict with page info
        """
        result = {
            'success': False,
            'url': url,
            'content': '',
            'status': 0
        }
        
        try:
            # Add random delay to simulate human behavior
            delay = random.uniform(3, 10)
            logger.debug(f"Adding random delay of {delay:.2f} seconds")
            time.sleep(delay)
            
            # Rotate user agent
            self.session.headers.update({'User-Agent': self.user_agent.random})
            
            # Make the request
            response = self.session.get(url, timeout=30)
            
            result['status'] = response.status_code
            result['url'] = response.url
            result['content'] = response.text
            result['success'] = response.ok
            
            logger.info(f"Navigated to {url} (Status: {response.status_code})")
            
            return result
            
        except Exception as e:
            logger.error(f"Navigation error for {url}: {e}")
            return result
    
    async def get_links(self, selector: str = 'a[href]') -> List[str]:
        """
        Extract links from the current page (requires navigate to be called first)
        
        Args:
            selector: CSS selector for links
            
        Returns:
            List of URLs
        """
        links = []
        if not hasattr(self, 'current_content'):
            return links
        
        try:
            soup = BeautifulSoup(self.current_content, 'html.parser')
            for a in soup.select(selector):
                href = a.get('href')
                if href:
                    links.append(href)
            return links
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []
    
    async def download_file(self, url: str) -> Optional[bytes]:
        """
        Download a file from a URL
        
        Args:
            url: URL of the file to download
            
        Returns:
            File content as bytes or None if download failed
        """
        try:
            response = self.session.get(url, stream=True, timeout=30)
            if response.ok:
                return response.content
            return None
        except Exception as e:
            logger.error(f"Error downloading file from {url}: {e}")
            return None
    
    async def close(self) -> None:
        """Close session and release resources"""
        try:
            if hasattr(self, 'session'):
                self.session.close()
            logger.info("Browser session closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser session: {e}")