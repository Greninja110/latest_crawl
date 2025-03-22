"""
Base extractor for handling different types of content
"""
import logging
import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseExtractor:
    """Base class for all content extractors"""
    
    def __init__(self, ai_processor=None):
        """
        Initialize the base extractor
        
        Args:
            ai_processor: AI processor for content understanding
        """
        self.ai_processor = ai_processor
    
    def extract_text(self, html: str) -> str:
        """
        Extract clean text from HTML content
        
        Args:
            html: HTML content
            
        Returns:
            Extracted text
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
            
            # Get text with better formatting
            paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
            content_text = "\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            if not content_text:
                content_text = soup.get_text(separator='\n', strip=True)
            
            return content_text
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    def extract_tables(self, html: str) -> List[Dict[str, Any]]:
        """
        Extract tables from HTML content
        
        Args:
            html: HTML content
            
        Returns:
            List of tables as dictionaries
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            tables = []
            
            for table in soup.find_all('table'):
                table_data = []
                
                # Extract headers
                headers = []
                header_row = table.find('thead')
                if header_row:
                    th_tags = header_row.find_all('th')
                    if th_tags:
                        headers = [th.get_text(strip=True) for th in th_tags]
                
                # If no thead, check first tr for headers
                if not headers:
                    first_row = table.find('tr')
                    if first_row:
                        th_tags = first_row.find_all('th')
                        if th_tags:
                            headers = [th.get_text(strip=True) for th in th_tags]
                        else:
                            # Use first row td elements as headers if no th found
                            td_tags = first_row.find_all('td')
                            if td_tags:
                                headers = [td.get_text(strip=True) for td in td_tags]
                
                # Process rows
                rows = []
                for row in table.find_all('tr')[1:] if headers else table.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        row_data = [cell.get_text(strip=True) for cell in cells]
                        rows.append(row_data)
                
                # Create structured table data
                if headers and rows:
                    # Standardize structure with rows as dictionaries
                    structured_rows = []
                    for row in rows:
                        # Handle case where row has fewer cells than headers
                        row_dict = {}
                        for i, value in enumerate(row):
                            if i < len(headers):
                                row_dict[headers[i]] = value
                            else:
                                # Extra values without headers
                                row_dict[f"column_{i+1}"] = value
                        
                        structured_rows.append(row_dict)
                    
                    tables.append({
                        "headers": headers,
                        "rows": structured_rows,
                        "raw_rows": rows
                    })
                elif rows:
                    # No headers, just use rows as-is
                    tables.append({
                        "headers": [],
                        "rows": [],
                        "raw_rows": rows
                    })
            
            return tables
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            return []
    
    def extract_links(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """
        Extract links from HTML content
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List of links with text and URL
        """
        try:
            from urllib.parse import urljoin
            
            soup = BeautifulSoup(html, 'html.parser')
            links = []
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag.get('href')
                if not href:
                    continue
                
                # Skip JavaScript links and anchors
                if href.startswith('javascript:') or href == '#':
                    continue
                
                # Resolve relative URL
                full_url = urljoin(base_url, href)
                
                # Extract text
                text = a_tag.get_text(strip=True)
                
                links.append({
                    "text": text,
                    "url": full_url
                })
            
            return links
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []
    
    def extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract dates from text content
        
        Args:
            text: Text content
            
        Returns:
            List of extracted dates
        """
        try:
            # Define common date patterns
            date_patterns = [
                # DD/MM/YYYY or MM/DD/YYYY
                r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})',
                # Month DD, YYYY
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})',
                # DD Month YYYY
                r'(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December),?\s+(\d{4})',
                # Short month forms
                r'(\d{1,2})[/.-](Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[/.-](\d{2,4})',
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})'
            ]
            
            found_dates = []
            
            for pattern in date_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    context = self._get_context(text, match.start(), 100)
                    found_dates.append({
                        "date_str": match.group(0),
                        "match_groups": match.groups(),
                        "position": match.start(),
                        "context": context
                    })
            
            return found_dates
        except Exception as e:
            logger.error(f"Error extracting dates: {e}")
            return []
    
    def extract_numbers(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract numbers with context from text
        
        Args:
            text: Text content
            
        Returns:
            List of extracted numbers with context
        """
        try:
            # Define patterns for numbers with context
            patterns = [
                # Currency amounts
                r'(?:Rs\.?|INR|₹)\s*(\d+(?:,\d+)*(?:\.\d+)?)',
                # Percentages
                r'(\d+(?:\.\d+)?)%',
                # Numbers with commas
                r'(\d+(?:,\d+)+)',
                # Decimal numbers
                r'(\d+\.\d+)',
                # Large numbers
                r'(\d{4,})'
            ]
            
            found_numbers = []
            
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    value = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    # Remove commas for numeric conversion
                    numeric_value = value.replace(',', '')
                    
                    try:
                        converted_value = float(numeric_value)
                    except:
                        converted_value = None
                    
                    context = self._get_context(text, match.start(), 100)
                    
                    found_numbers.append({
                        "match": match.group(0),
                        "value": value,
                        "numeric_value": converted_value,
                        "position": match.start(),
                        "context": context
                    })
            
            return found_numbers
        except Exception as e:
            logger.error(f"Error extracting numbers: {e}")
            return []
    
    def _get_context(self, text: str, position: int, context_size: int = 100) -> str:
        """
        Get context around a position in text
        
        Args:
            text: Full text
            position: Position to get context around
            context_size: Size of context on each side
            
        Returns:
            Context text
        """
        start = max(0, position - context_size)
        end = min(len(text), position + context_size)
        
        # Try to find sentence or paragraph boundaries
        context = text[start:end]
        
        # Add ellipsis if we're cutting text
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text) else ""
        
        return f"{prefix}{context}{suffix}"