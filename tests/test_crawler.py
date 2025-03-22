"""
Basic tests for the crawler components
"""
import os
import asyncio
import unittest
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.browser import BrowserManager
from crawler.crawler import CollegeCrawler
from extractors.base import BaseExtractor
from extractors.admission import AdmissionExtractor
from extractors.placement import PlacementExtractor

class TestBrowserManager(unittest.TestCase):
    """Tests for the BrowserManager class"""
    
    def setUp(self):
        """Set up test case"""
        self.browser_manager = None
    
    async def test_init_browser(self):
        """Test browser initialization"""
        self.browser_manager = BrowserManager()
        page = await self.browser_manager.init_browser()
        self.assertIsNotNone(page)
    
    async def test_navigate(self):
        """Test navigation to a URL"""
        self.browser_manager = BrowserManager()
        await self.browser_manager.init_browser()
        result = await self.browser_manager.navigate("https://www.example.com")
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 200)
        self.assertIn("<html", result['content'])
    
    async def tearDown(self):
        """Clean up after test"""
        if self.browser_manager:
            await self.browser_manager.close()

class TestBaseExtractor(unittest.TestCase):
    """Tests for the BaseExtractor class"""
    
    def setUp(self):
        """Set up test case"""
        self.extractor = BaseExtractor()
        
        # Sample HTML for testing
        self.sample_html = """
        <html>
            <body>
                <h1>Test Page</h1>
                <p>This is a test paragraph.</p>
                <table>
                    <tr><th>Header 1</th><th>Header 2</th></tr>
                    <tr><td>Cell 1</td><td>Cell 2</td></tr>
                    <tr><td>Cell 3</td><td>Cell 4</td></tr>
                </table>
                <a href="https://www.example.com">Example Link</a>
            </body>
        </html>
        """
    
    def test_extract_text(self):
        """Test text extraction"""
        text = self.extractor.extract_text(self.sample_html)
        self.assertIn("Test Page", text)
        self.assertIn("This is a test paragraph", text)
    
    def test_extract_tables(self):
        """Test table extraction"""
        tables = self.extractor.extract_tables(self.sample_html)
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0]['headers'], ['Header 1', 'Header 2'])
        self.assertEqual(len(tables[0]['rows']), 2)
    
    def test_extract_links(self):
        """Test link extraction"""
        links = self.extractor.extract_links(self.sample_html, "https://test.com")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]['url'], "https://www.example.com")
        self.assertEqual(links[0]['text'], "Example Link")

# Define test runner
def run_async_test(test_case):
    """Run async test case"""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_case())

if __name__ == "__main__":
    unittest.main()