"""
Browser manager for navigating websites using Playwright
"""
import logging
import random
import time
import os
import asyncio
from typing import Dict, List, Any, Optional
from playwright.async_api import async_playwright, Browser, Page, Response
from fake_useragent import UserAgent
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class BrowserManager:
    """Browser manager for automated website navigation"""
    
    def __init__(self, use_proxies: bool = False, headless: bool = True):
        """
        Initialize browser manager
        
        Args:
            use_proxies: Whether to use proxy rotation
            headless: Whether to run browser in headless mode
        """
        self.use_proxies = use_proxies
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.user_agent = UserAgent()
        self.current_proxy = None
        self.downloads_dir = os.path.join(os.getcwd(), "downloads")
        
        # Create downloads directory if it doesn't exist
        os.makedirs(self.downloads_dir, exist_ok=True)
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
    
    async def init_browser(self) -> Page:
        """
        Initialize browser and return page
        
        Returns:
            Playwright page object
        """
        try:
            self.playwright = await async_playwright().start()
            
            # Generate a random user agent
            user_agent_string = self.user_agent.random
            
            # Configure browser options
            browser_args = []
            
            # Add proxy if needed
            if self.use_proxies and self.current_proxy:
                proxy_url = f"{self.current_proxy['protocol']}://{self.current_proxy['ip']}:{self.current_proxy['port']}"
                logger.info(f"Using proxy: {proxy_url}")
                browser_args.append(f"--proxy-server={proxy_url}")
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )
            
            # Create context with custom user-agent
            self.context = await self.browser.new_context(
                user_agent=user_agent_string,
                viewport={'width': 1366, 'height': 768},
                accept_downloads=True
            )
            
            # Add event listeners for debugging
            self.context.on("request", self._on_request)
            self.context.on("response", self._on_response)
            
            # Create new page
            self.page = await self.context.new_page()
            
            logger.info(f"Browser initialized with user agent: {user_agent_string}")
            return self.page
            
        except Exception as e:
            logger.error(f"Error initializing browser: {e}")
            if self.playwright:
                await self.playwright.stop()
            
            # Re-raise exception to be handled by caller
            raise
    
    def _on_request(self, request):
        """Handle request events for debugging"""
        logger.debug(f"Request: {request.method} {request.url}")
    
    def _on_response(self, response):
        """Handle response events for debugging"""
        logger.debug(f"Response: {response.status} {response.url}")
    
    async def navigate(self, url: str, wait_for_load: bool = True) -> Dict[str, Any]:
        """
        Navigate to a specific URL
        
        Args:
            url: URL to navigate to
            wait_for_load: Whether to wait for page load
            
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
            if not self.page:
                await self.init_browser()
                
            # Add random delay to simulate human behavior
            delay = random.uniform(3, 10)
            logger.debug(f"Adding random delay of {delay:.2f} seconds")
            await asyncio.sleep(delay)
            
            # Navigate to URL
            logger.info(f"Navigating to {url}")
            response = await self.page.goto(url, wait_until='domcontentloaded' if wait_for_load else 'commit')
            
            # Wait a bit more for JavaScript execution
            if wait_for_load:
                await asyncio.sleep(2)
                
            result['status'] = response.status
            result['url'] = self.page.url
            result['content'] = await self.page.content()
            result['success'] = response.ok
            
            logger.info(f"Navigation completed: {url} (Status: {response.status})")
            
            return result
            
        except Exception as e:
            logger.error(f"Navigation error for {url}: {e}")
            result['status'] = 500
            result['content'] = f"Error: {str(e)}"
            return result
    
    async def get_links(self, selector: str = 'a[href]') -> List[str]:
        """
        Extract links from the current page
        
        Args:
            selector: CSS selector for links
            
        Returns:
            List of URLs
        """
        links = []
        try:
            if not self.page:
                logger.error("Browser not initialized")
                return links
                
            # Get all href attributes from elements matching the selector
            hrefs = await self.page.eval_on_selector_all(
                selector,
                "elements => elements.map(el => el.href)"
            )
            
            for href in hrefs:
                if href and href.startswith('http'):
                    links.append(href)
                    
            logger.debug(f"Extracted {len(links)} links from page")
            return links
            
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return links
    
    async def download_file(self, url: str) -> Optional[bytes]:
        """
        Download a file from a URL
        
        Args:
            url: URL of the file to download
            
        Returns:
            File content as bytes or None if download failed
        """
        try:
            if not self.context:
                await self.init_browser()
                
            # Create a special page just for download
            download_page = await self.context.new_page()
            
            # Start download and wait for download to start
            download_task = asyncio.create_task(
                self.context.wait_for_event("download")
            )
            
            # Navigate to download URL
            await download_page.goto(url)
            
            # Wait for download to start
            download = await download_task
            
            # Save to a temporary path
            temp_path = await download.path()
            
            # Read file content
            with open(temp_path, 'rb') as f:
                file_content = f.read()
            
            # Close the special page
            await download_page.close()
            
            logger.info(f"Downloaded file from {url} ({len(file_content)} bytes)")
            return file_content
            
        except Exception as e:
            logger.error(f"Error downloading file from {url}: {e}")
            return None
        
    async def take_screenshot(self, path: str) -> bool:
        """
        Take a screenshot of the current page
        
        Args:
            path: Path to save screenshot
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.page:
                logger.error("Browser not initialized")
                return False
                
            await self.page.screenshot(path=path)
            logger.debug(f"Screenshot saved to {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return False
    
    async def close(self) -> None:
        """Close browser and release resources"""
        try:
            if self.page:
                await self.page.close()
                
            if self.context:
                await self.context.close()
                
            if self.browser:
                await self.browser.close()
                
            if self.playwright:
                await self.playwright.stop()
                
            logger.info("Browser resources closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing browser: {e}")