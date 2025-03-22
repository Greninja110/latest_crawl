"""
Main crawler engine for navigating and extracting data from college websites
"""
import logging
import asyncio
import re
import os
import time
import json
from typing import Dict, List, Set, Any, Tuple, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime
import hashlib
import requests
from bs4 import BeautifulSoup

from config.settings import (
    MAX_PAGES_PER_COLLEGE, 
    MAX_DEPTH, 
    DOMAIN_RESTRICT,
    ADMISSION_KEYWORDS,
    PLACEMENT_KEYWORDS,
    ALLOWED_FILE_TYPES
)
from config.targets import TARGET_COLLEGES, CUSTOM_URL_PATTERNS, PAGE_CONTENT_INDICATORS
from crawler.browser import BrowserManager
from storage.mongodb import MongoDBConnector
from processors.ai_processor import AIProcessor

logger = logging.getLogger(__name__)

class CollegeCrawler:
    """Main crawler engine for college websites"""
    
    def __init__(self, use_browser: bool = True, use_proxies: bool = False):
        """
        Initialize the crawler
        
        Args:
            use_browser: Whether to use browser automation (Playwright)
            use_proxies: Whether to use proxy rotation
        """
        self.use_browser = use_browser
        self.use_proxies = use_proxies
        self.browser_manager = None
        self.db = MongoDBConnector()
        self.ai_processor = AIProcessor()
        
        # Track visited URLs to avoid duplicates
        self.visited_urls = set()
        self.queued_urls = set()
        
        # Store file download paths
        self.downloads_dir = "downloads"
        os.makedirs(self.downloads_dir, exist_ok=True)
        
    async def init_browser(self) -> None:
        """Initialize browser if needed"""
        if self.use_browser and not self.browser_manager:
            self.browser_manager = BrowserManager(use_proxies=self.use_proxies)
            await self.browser_manager.init_browser()
    
    async def crawl_college(self, college: Dict[str, Any]) -> None:
        """
        Crawl a specific college website
        
        Args:
            college: College dictionary with 'name', 'base_url', etc.
        """
        logger.info(f"Starting crawl for: {college['name']}")
        college_name = college['name']
        base_url = college['base_url']
        domain = college.get('domain') or urlparse(base_url).netloc
        
        # Reset tracking for this college
        self.visited_urls = set()
        self.queued_urls = set()
        
        # Initialize browser if using it
        if self.use_browser:
            await self.init_browser()
        
        # Start with the base URL
        await self.process_url(base_url, college_name, domain, page_type="general", depth=0)
        
        # Process specific admission and placement paths
        for path in college.get('admission_paths', []):
            url = urljoin(base_url, path)
            if url not in self.queued_urls:
                self.queued_urls.add(url)
                await self.process_url(url, college_name, domain, page_type="admission", depth=0)
                
        for path in college.get('placement_paths', []):
            url = urljoin(base_url, path)
            if url not in self.queued_urls:
                self.queued_urls.add(url)
                await self.process_url(url, college_name, domain, page_type="placement", depth=0)
        
        # Process the URL queue
        while self.queued_urls and len(self.visited_urls) < MAX_PAGES_PER_COLLEGE:
            url = self.queued_urls.pop()
            if url not in self.visited_urls:
                await self.process_url(url, college_name, domain, depth=1)
                
        logger.info(f"Finished crawling: {college['name']} - Visited {len(self.visited_urls)} pages")
    
    async def process_url(
        self, 
        url: str, 
        college_name: str, 
        domain: str, 
        page_type: str = None, 
        depth: int = 0
    ) -> None:
        """
        Process a single URL
        
        Args:
            url: URL to process
            college_name: Name of the college
            domain: College domain for restricting crawl
            page_type: Type of page ('admission', 'placement', 'general')
            depth: Current depth in crawl
        """
        # Skip if we've already visited or if we've reached max pages
        if url in self.visited_urls or len(self.visited_urls) >= MAX_PAGES_PER_COLLEGE:
            return
            
        # Mark as visited
        self.visited_urls.add(url)
        
        logger.info(f"Processing URL: {url} (type: {page_type}, depth: {depth})")
        
        # Determine if we should use browser or direct requests
        page_data = None
        if self.use_browser and self.browser_manager:
            page_data = await self.browser_manager.navigate(url)
        else:
            page_data = self._fetch_with_requests(url)
        
        if not page_data or not page_data['success']:
            logger.warning(f"Failed to fetch {url}")
            return
            
        # Analyze content to determine page type if not provided
        if not page_type:
            page_type = self._determine_page_type(page_data['content'])
        
        # Store raw data in MongoDB
        raw_data = {
            "college_name": college_name,
            "url": url,
            "page_type": page_type,
            "content_type": "text/html",
            "raw_content": self._extract_main_content(page_data['content']),
            "raw_html": page_data['content'],
            "extraction_date": datetime.now(),
            "metadata": {
                "http_status": page_data['status'],
                "crawler_session": self._generate_session_id(),
                "depth": depth
            }
        }
        
        raw_id = self.db.insert_raw_data(raw_data)
        logger.debug(f"Saved raw data with ID: {raw_id}")
        
        # Extract and process any embedded data
        await self._process_embedded_content(page_data['content'], url, college_name, raw_id)
        
        # If we haven't reached max depth, extract and queue links
        if depth < MAX_DEPTH:
            links = self._extract_links(page_data['content'], url)
            
            # Filter links
            filtered_links = self._filter_links(links, domain, page_type)
            
            # Queue filtered links
            for link, link_type in filtered_links:
                if link not in self.visited_urls and link not in self.queued_urls:
                    self.queued_urls.add(link)
                    # If the link type is specific (admission/placement), use it
                    processed_type = link_type if link_type in ("admission", "placement") else page_type
                    logger.debug(f"Queued: {link} (type: {processed_type})")
    
    def _fetch_with_requests(self, url: str) -> Dict[str, Any]:
        """
        Fetch a URL using requests library
        
        Args:
            url: URL to fetch
            
        Returns:
            Dict with page data
        """
        result = {
            'success': False,
            'url': url,
            'content': '',
            'status': 0
        }
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            result['status'] = response.status_code
            result['url'] = response.url
            
            if response.status_code == 200:
                result['content'] = response.text
                result['success'] = True
                
            return result
        except Exception as e:
            logger.error(f"Error fetching {url} with requests: {e}")
            return result
    
    def _determine_page_type(self, content: str) -> str:
        """
        Determine the type of page based on content
        
        Args:
            content: HTML content of the page
            
        Returns:
            Page type ('admission', 'placement', or 'general')
        """
        # Use AI processor for more accurate classification
        try:
            classification = self.ai_processor.classify_content(content)
            if classification and classification.get('confidence', 0) > 0.6:
                return classification['class']
        except Exception as e:
            logger.warning(f"AI classification failed: {e}")
        
        # Fallback to keyword matching
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text().lower()
        
        # Check for specific page indicators
        admission_indicators = [ind.lower() for ind in PAGE_CONTENT_INDICATORS['admission']]
        placement_indicators = [ind.lower() for ind in PAGE_CONTENT_INDICATORS['placement']]
        
        admission_count = sum(1 for ind in admission_indicators if ind in text)
        placement_count = sum(1 for ind in placement_indicators if ind in text)
        
        # Count keyword occurrences
        admission_keyword_count = sum(1 for keyword in ADMISSION_KEYWORDS if keyword.lower() in text)
        placement_keyword_count = sum(1 for keyword in PLACEMENT_KEYWORDS if keyword.lower() in text)
        
        # Determine type based on frequency
        if admission_count > placement_count or admission_keyword_count > placement_keyword_count:
            return "admission"
        elif placement_count > admission_count or placement_keyword_count > admission_keyword_count:
            return "placement"
        else:
            return "general"
    
    def _extract_main_content(self, html: str) -> str:
        """
        Extract the main content text from HTML
        
        Args:
            html: HTML content
            
        Returns:
            Extracted main content text
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
            
            # Try to find main content area
            main_content = None
            
            # Try common content containers
            content_selectors = [
                "main", "article", "#content", ".content", "#main-content", 
                ".main-content", "#main", ".main", ".page-content", "#page-content"
            ]
            
            for selector in content_selectors:
                content = soup.select(selector)
                if content:
                    main_content = content[0]
                    break
            
            # If no main content found, use body
            if not main_content:
                main_content = soup.body
            
            if not main_content:
                return soup.get_text(separator='\n', strip=True)
            
            # Get text with better formatting
            paragraphs = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
            content_text = "\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            if not content_text:
                content_text = main_content.get_text(separator='\n', strip=True)
            
            return content_text
        except Exception as e:
            logger.error(f"Error extracting main content: {e}")
            # Fallback to simple text extraction
            try:
                soup = BeautifulSoup(html, 'html.parser')
                return soup.get_text(separator='\n', strip=True)
            except:
                return ""
    
    async def _process_embedded_content(
        self, 
        html: str, 
        base_url: str, 
        college_name: str, 
        parent_id: str
    ) -> None:
        """
        Extract and process embedded content like tables, images, PDFs
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            college_name: Name of the college
            parent_id: ID of the parent raw data document
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Process tables
        tables = soup.find_all('table')
        for i, table in enumerate(tables):
            try:
                # Convert table to HTML string
                table_html = str(table)
                
                # Save table as raw data
                table_data = {
                    "college_name": college_name,
                    "url": base_url,
                    "page_type": "table",
                    "content_type": "text/html",
                    "raw_content": table.get_text(separator='\n', strip=True),
                    "raw_html": table_html,
                    "extraction_date": datetime.now(),
                    "metadata": {
                        "parent_id": parent_id,
                        "table_index": i,
                        "crawler_session": self._generate_session_id()
                    }
                }
                
                table_id = self.db.insert_raw_data(table_data)
                logger.debug(f"Saved table with ID: {table_id}")
                
                # Process table with AI
                await self.ai_processor.process_table(table_html, table_id, college_name)
                
            except Exception as e:
                logger.error(f"Error processing table: {e}")
        
        # Process images that might contain charts or data
        data_images = []
        
        # Look for images in specific contexts that suggest they contain data
        chart_indicators = ['chart', 'graph', 'data', 'statistics', 'placement', 'admission']
        
        # Find image tags
        for img in soup.find_all('img'):
            # Skip small icons and logos
            if img.get('width') and int(img.get('width')) < 200:
                continue
            if img.get('height') and int(img.get('height')) < 200:
                continue
                
            # Check if the image is likely a chart or data image
            is_data_image = False
            
            # Check image alt, title, or class
            for attr in ['alt', 'title', 'class']:
                if img.get(attr):
                    for indicator in chart_indicators:
                        if indicator.lower() in img.get(attr).lower():
                            is_data_image = True
                            break
            
            # Check parent elements for context
            parent = img.parent
            for _ in range(3):  # Check up to 3 levels up
                if parent and parent.name:
                    parent_text = parent.get_text().lower()
                    for indicator in chart_indicators:
                        if indicator in parent_text:
                            is_data_image = True
                            break
                    
                    # Move up to the next parent
                    parent = parent.parent
                else:
                    break
            
            if is_data_image:
                src = img.get('src')
                if src:
                    # Resolve relative URLs
                    full_url = urljoin(base_url, src)
                    data_images.append(full_url)
        
        # Process each data image
        for img_url in data_images:
            try:
                # Download the image
                img_content = await self._download_file(img_url)
                if not img_content:
                    continue
                
                # Store image raw data
                img_data = {
                    "college_name": college_name,
                    "url": img_url,
                    "page_type": "image",
                    "content_type": "image",
                    "raw_content": "",
                    "raw_html": "",
                    "extraction_date": datetime.now(),
                    "metadata": {
                        "parent_id": parent_id,
                        "content_length": len(img_content),
                        "crawler_session": self._generate_session_id()
                    }
                }
                
                img_id = self.db.insert_raw_data(img_data)
                logger.debug(f"Saved image with ID: {img_id}")
                
                # Save image to disk
                img_path = os.path.join(self.downloads_dir, f"{img_id}.jpg")
                with open(img_path, 'wb') as f:
                    f.write(img_content)
                
                # Process image with AI
                await self.ai_processor.process_image(img_path, img_id, college_name)
                
            except Exception as e:
                logger.error(f"Error processing image {img_url}: {e}")
        
        # Process linked files (PDFs, etc.)
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if not href:
                continue
                
            # Resolve relative URL
            full_url = urljoin(base_url, href)
            
            # Check if it's a file we want to download
            file_ext = os.path.splitext(full_url.lower())[1].lstrip('.')
            if file_ext in ALLOWED_FILE_TYPES:
                try:
                    # Download the file
                    file_content = await self._download_file(full_url)
                    if not file_content:
                        continue
                    
                    # Determine content type
                    content_type = "application/octet-stream"
                    if file_ext == "pdf":
                        content_type = "application/pdf"
                    elif file_ext in ["doc", "docx"]:
                        content_type = "application/msword"
                    elif file_ext in ["xls", "xlsx"]:
                        content_type = "application/vnd.ms-excel"
                    elif file_ext in ["jpg", "jpeg", "png", "gif"]:
                        content_type = f"image/{file_ext}"
                        
                    # Store file metadata in MongoDB
                    file_data = {
                        "college_name": college_name,
                        "url": full_url,
                        "page_type": file_ext,
                        "content_type": content_type,
                        "raw_content": "",
                        "raw_html": "",
                        "extraction_date": datetime.now(),
                        "metadata": {
                            "parent_id": parent_id,
                            "content_length": len(file_content),
                            "file_extension": file_ext,
                            "crawler_session": self._generate_session_id()
                        }
                    }
                    
                    file_id = self.db.insert_raw_data(file_data)
                    logger.debug(f"Saved file {full_url} with ID: {file_id}")
                    
                    # Save file to disk
                    file_path = os.path.join(self.downloads_dir, f"{file_id}.{file_ext}")
                    with open(file_path, 'wb') as f:
                        f.write(file_content)
                    
                    # Process file with appropriate AI processor
                    if file_ext == "pdf":
                        await self.ai_processor.process_pdf(file_path, file_id, college_name)
                    elif file_ext in ["jpg", "jpeg", "png", "gif"]:
                        await self.ai_processor.process_image(file_path, file_id, college_name)
                    
                except Exception as e:
                    logger.error(f"Error processing file {full_url}: {e}")
    
    async def _download_file(self, url: str) -> Optional[bytes]:
        """
        Download a file from a URL
        
        Args:
            url: URL of the file to download
            
        Returns:
            File content as bytes or None if download failed
        """
        try:
            if self.use_browser and self.browser_manager:
                return await self.browser_manager.download_file(url)
            else:
                response = requests.get(url, timeout=15, stream=True)
                if response.status_code == 200:
                    return response.content
                return None
        except Exception as e:
            logger.error(f"Error downloading file {url}: {e}")
            return None
    
    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract links from HTML content
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List of extracted URLs
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            links = []
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag.get('href')
                if not href:
                    continue
                    
                # Skip JavaScript links and anchors
                if href.startswith('javascript:') or href.startswith('#'):
                    continue
                    
                # Resolve relative URL
                full_url = urljoin(base_url, href)
                
                # Skip mail links
                if full_url.startswith('mailto:'):
                    continue
                    
                links.append(full_url)
                
            return links
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []
    
    def _filter_links(
        self, 
        links: List[str], 
        domain: str, 
        current_page_type: str
    ) -> List[Tuple[str, str]]:
        """
        Filter and categorize links
        
        Args:
            links: List of URLs to filter
            domain: Domain for restricting crawl
            current_page_type: Type of the current page
            
        Returns:
            List of tuples (URL, page_type)
        """
        filtered_links = []
        
        for url in links:
            # Parse URL
            parsed = urlparse(url)
            
            # Skip external links if domain restriction is enabled
            if DOMAIN_RESTRICT and domain not in parsed.netloc:
                continue
                
            # Skip non-http(s) links
            if not parsed.scheme.startswith('http'):
                continue
                
            # Skip common file types we don't want to crawl (but will download separately)
            skip_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png', '.gif']
            if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
                continue
            
            # Determine page type based on URL patterns
            page_type = current_page_type
            
            # Check admission patterns
            for pattern in CUSTOM_URL_PATTERNS['admission_patterns']:
                if re.search(pattern, parsed.path.lower()):
                    page_type = "admission"
                    break
                    
            # Check placement patterns
            for pattern in CUSTOM_URL_PATTERNS['placement_patterns']:
                if re.search(pattern, parsed.path.lower()):
                    page_type = "placement"
                    break
            
            filtered_links.append((url, page_type))
            
        return filtered_links
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID for tracking crawl sessions"""
        return hashlib.md5(f"{time.time()}".encode()).hexdigest()
    
    async def close(self) -> None:
        """Close resources"""
        if self.browser_manager:
            await self.browser_manager.close()
        
        if self.db:
            self.db.close()
            
        logger.info("Crawler resources closed")