"""
Specialized extractor for placement and internship data
"""
import logging
import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime

from extractors.base import BaseExtractor

logger = logging.getLogger(__name__)

class PlacementExtractor(BaseExtractor):
    """Specialized extractor for placement and internship information"""
    
    def __init__(self, ai_processor=None):
        """Initialize placement extractor"""
        super().__init__(ai_processor)
        
        # Keywords for specific placement data points
        self.placement_keywords = {
            "statistics": [
                "average package", "highest package", "lowest package", "median salary",
                "placement statistics", "average salary", "mean package", "placement record"
            ],
            "companies": [
                "recruiting companies", "top recruiters", "companies visited", "participating companies",
                "recruitment partners", "hiring partners", "campus recruiters", "top companies"
            ],
            "placement_percentage": [
                "placement percentage", "students placed", "placement rate", "placed students",
                "placement ratio", "placement record", "eligible students"
            ],
            "internships": [
                "internship", "summer training", "industrial training", "summer internship",
                "winter internship", "internship offers", "industrial exposure"
            ],
            "recruiters": [
                "recruiters", "hiring companies", "companies visited", "industry partners",
                "recruitment drive", "placement drive", "campus placement"
            ],
            "sectors": [
                "industry sectors", "sector wise", "domain wise", "industry segments",
                "verticals", "industries", "fields", "streams"
            ]
        }
    
    def extract_placement_data(self, content: str, college_name: str) -> Dict[str, Any]:
        """
        Extract placement-related information from content
        
        Args:
            content: HTML or text content
            college_name: Name of the college
            
        Returns:
            Dictionary with extracted placement data
        """
        # Extract basic text if HTML provided
        if "<html" in content or "<body" in content:
            text_content = self.extract_text(content)
            tables = self.extract_tables(content)
        else:
            text_content = content
            tables = []
        
        # Initialize result object
        placement_data = {
            "college_name": college_name,
            "last_updated": datetime.now(),
            "placement_data": {
                "statistics": self._extract_placement_statistics(text_content, tables),
                "recruiters": self._extract_recruiters(text_content, tables),
                "historical_data": self._extract_historical_data(text_content, tables),
                "alternative_paths": self._extract_alternative_paths(text_content, tables),
                "internships": self._extract_internships(text_content, tables),
                "recruitment_types": self._extract_recruitment_types(text_content)
            },
            "confidence_score": 0.7,  # Default confidence
            "processing_date": datetime.now()
        }
        
        # If AI processor is available, use it for enhanced extraction
        if self.ai_processor:
            try:
                enhanced_data = self.ai_processor.process_placement_content(text_content, tables)
                if enhanced_data:
                    # Merge AI-extracted data with rule-based extraction
                    for key, value in enhanced_data.items():
                        if value and key in placement_data["placement_data"]:
                            placement_data["placement_data"][key] = value
                    
                    # Update confidence score
                    placement_data["confidence_score"] = enhanced_data.get("confidence_score", 0.8)
            except Exception as e:
                logger.error(f"Error in AI processing of placement content: {e}")
        
        return placement_data
    
    def _extract_placement_statistics(self, text: str, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract placement statistics
        
        Args:
            text: Text content
            tables: Extracted tables
            
        Returns:
            Dictionary with placement statistics
        """
        statistics = {
            "avg_package": None,
            "highest_package": None,
            "median_package": None,
            "students_placed_count": None,
            "total_students": None,
            "placement_percentage": None
        }
        
        # Define patterns for various statistics
        patterns = {
            "avg_package": [
                r"average\s+(?:package|salary|ctc)(?:\s+is|\s*:)?\s*(?:Rs\.?|INR|₹)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs)?",
                r"average\s+(?:package|salary|ctc)(?:\s+of|\s*:)?\s*(?:Rs\.?|INR|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)"
            ],
            "highest_package": [
                r"highest\s+(?:package|salary|ctc)(?:\s+is|\s*:)?\s*(?:Rs\.?|INR|₹)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs)?",
                r"highest\s+(?:package|salary|ctc)(?:\s+of|\s*:)?\s*(?:Rs\.?|INR|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)",
                r"maximum\s+(?:package|salary|ctc)(?:\s+is|\s*:)?\s*(?:Rs\.?|INR|₹)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs)?"
            ],
            "median_package": [
                r"median\s+(?:package|salary|ctc)(?:\s+is|\s*:)?\s*(?:Rs\.?|INR|₹)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs)?",
                r"median\s+(?:package|salary|ctc)(?:\s+of|\s*:)?\s*(?:Rs\.?|INR|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)"
            ],
            "students_placed_count": [
                r"(\d+)\s+students\s+(?:were\s+)?placed",
                r"number\s+of\s+students\s+placed(?:\s+is|\s*:)?\s*(\d+)",
                r"placed\s+(\d+)\s+students"
            ],
            "total_students": [
                r"total\s+(?:number\s+of\s+)?students(?:\s+is|\s*:)?\s*(\d+)",
                r"(\d+)\s+students\s+were\s+eligible",
                r"batch\s+(?:strength|size)(?:\s+of|\s+is|\s*:)?\s*(\d+)"
            ],
            "placement_percentage": [
                r"placement\s+percentage(?:\s+is|\s*:)?\s*(\d+(?:\.\d+)?)\s*%",
                r"(\d+(?:\.\d+)?)\s*%\s+(?:students\s+)?(?:were\s+)?placed",
                r"placement\s+rate(?:\s+is|\s*:)?\s*(\d+(?:\.\d+)?)\s*%"
            ]
        }
        
        # Extract statistics from text
        for stat, stat_patterns in patterns.items():
            for pattern in stat_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        # Remove commas and convert to float
                        value = match.group(1).replace(',', '')
                        
                        # Special handling for packages in lakhs
                        is_lakh = "lakh" in pattern.lower() or "lac" in pattern.lower()
                        
                        if is_lakh:
                            # Convert to lakhs if pattern mentions lakhs
                            statistics[stat] = float(value)
                        else:
                            # Determine if the value is in lakhs based on magnitude
                            # Values less than 100 are likely in lakhs already
                            float_value = float(value)
                            if float_value < 100:
                                statistics[stat] = float_value
                            else:
                                # Convert to lakhs if the value is large (assuming in thousands)
                                statistics[stat] = float_value / 100000
                        
                        break
                    except:
                        statistics[stat] = match.group(1)
                        break
        
        # Look for statistics in tables
        for table in tables:
            headers = [h.lower() if h else "" for h in table.get("headers", [])]
            
            # Check if table might contain placement statistics
            has_stat_header = any(any(kw in h for kw in ["package", "salary", "ctc", "placed", "recruitment"]) for h in headers if h)
            
            if has_stat_header:
                # Extract from single row tables (summary tables)
                if len(table.get("raw_rows", [])) <= 3:
                    for row in table.get("raw_rows", []):
                        row_text = " ".join(row).lower()
                        
                        # Look for statistics in row text
                        for stat, stat_patterns in patterns.items():
                            if statistics[stat] is None:  # Only update if not already found
                                for pattern in stat_patterns:
                                    match = re.search(pattern, row_text, re.IGNORECASE)
                                    if match:
                                        try:
                                            value = match.group(1).replace(',', '')
                                            statistics[stat] = float(value)
                                        except:
                                            statistics[stat] = match.group(1)
                                        break
        
        # Calculate placement percentage if we have the necessary data but it's not directly found
        if statistics["placement_percentage"] is None and statistics["students_placed_count"] and statistics["total_students"]:
            try:
                placement_percentage = (float(statistics["students_placed_count"]) / float(statistics["total_students"])) * 100
                statistics["placement_percentage"] = round(placement_percentage, 2)
            except:
                pass
        
        return statistics
    
    def _extract_recruiters(self, text: str, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract recruiter information
        
        Args:
            text: Text content
            tables: Extracted tables
            
        Returns:
            Dictionary with recruiter information
        """
        recruiters_info = {
            "top_companies": [],
            "total_companies_visited": None
        }
        
        # Look for mentions of total companies
        total_patterns = [
            r"(\d+)\s+companies\s+(?:visited|participated|recruited)",
            r"total\s+(?:number\s+of\s+)?companies(?:\s+visited)?(?:\s+is|\s*:)?\s*(\d+)",
            r"(?:visited|participated|recruited)(?:\s+by)?\s+(\d+)\s+companies"
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    recruiters_info["total_companies_visited"] = int(match.group(1))
                    break
                except:
                    recruiters_info["total_companies_visited"] = match.group(1)
                    break
        
        # Extract company names from text
        company_section_patterns = [
            r"(?:top|major|prominent)\s+recruiters(?:\s+include)?[:\s]+(.+?)(?:\n\n|\.\s+[A-Z])",
            r"(?:top|major|prominent)\s+companies(?:\s+include)?[:\s]+(.+?)(?:\n\n|\.\s+[A-Z])",
            r"our\s+recruiters(?:\s+include)?[:\s]+(.+?)(?:\n\n|\.\s+[A-Z])"
        ]
        
        for pattern in company_section_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                companies_text = match.group(1)
                # Split by common separators
                company_candidates = re.split(r'[,;/\n•]', companies_text)
                
                for candidate in company_candidates:
                    candidate = candidate.strip()
                    if len(candidate) > 2 and not candidate.isdigit():  # Basic validation
                        # Exclude common noise phrases
                        noise_phrases = ["companies", "include", "etc", "and", "more", "others"]
                        if not any(phrase == candidate.lower() for phrase in noise_phrases):
                            recruiters_info["top_companies"].append(candidate)
        
        # Extract from tables
        for table in tables:
            headers = [h.lower() if h else "" for h in table.get("headers", [])]
            
            # Check if table might contain company information
            company_keywords = ["company", "recruiter", "organization", "firm"]
            has_company_col = any(any(kw in h for kw in company_keywords) for h in headers if h)
            
            if has_company_col:
                company_col = None
                
                # Find company column
                for i, header in enumerate(headers):
                    if header and any(kw in header for kw in company_keywords):
                        company_col = i
                        break
                
                if company_col is not None:
                    for row in table.get("raw_rows", []):
                        if len(row) > company_col and row[company_col]:
                            company = row[company_col].strip()
                            if len(company) > 2 and not company.isdigit():
                                recruiters_info["top_companies"].append(company)
        
        # Deduplicate companies
        if recruiters_info["top_companies"]:
            recruiters_info["top_companies"] = list(dict.fromkeys(recruiters_info["top_companies"]))
        
        return recruiters_info
    
    def _extract_historical_data(self, text: str, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract historical placement data
        
        Args:
            text: Text content
            tables: Extracted tables
            
        Returns:
            Dictionary with historical data
        """
        historical_data = {
            "year_wise": {}
        }
        
        # Look for historical data in tables
        for table in tables:
            headers = [h.lower() if h else "" for h in table.get("headers", [])]
            
            # Check if table might contain year-wise data
            year_keywords = ["year", "session", "batch", "academic year"]
            stat_keywords = ["package", "placed", "salary", "ctc", "recruitment"]
            
            has_year_col = any(any(kw in h for kw in year_keywords) for h in headers if h)
            has_stat_col = any(any(kw in h for kw in stat_keywords) for h in headers if h)
            
            if has_year_col and has_stat_col:
                year_col = None
                package_col = None
                percentage_col = None
                
                # Find relevant columns
                for i, header in enumerate(headers):
                    if not header:
                        continue
                    if any(kw in header for kw in year_keywords):
                        year_col = i
                    elif "package" in header or "salary" in header or "ctc" in header:
                        package_col = i
                    elif "percentage" in header or "%" in header:
                        percentage_col = i
                
                if year_col is not None:
                    for row in table.get("raw_rows", []):
                        if len(row) <= year_col:
                            continue
                            
                        year_value = row[year_col].strip()
                        
                        # Look for years in various formats
                        year_match = re.search(r'(20\d\d)(?:[^0-9]|$)', year_value)
                        if not year_match:
                            year_match = re.search(r'(\d\d)[^0-9](\d\d)', year_value)
                        
                        if year_match:
                            year = year_match.group(1)
                            year_data = {}
                            
                            # Extract package
                            if package_col is not None and len(row) > package_col:
                                package_value = row[package_col]
                                try:
                                    # Remove non-numeric characters
                                    cleaned_package = re.sub(r'[^\d.]', '', package_value)
                                    if cleaned_package:
                                        year_data["avg_package"] = float(cleaned_package)
                                except:
                                    year_data["avg_package"] = package_value
                            
                            # Extract placement percentage
                            if percentage_col is not None and len(row) > percentage_col:
                                percentage_value = row[percentage_col]
                                try:
                                    # Remove % and other non-numeric characters
                                    cleaned_percentage = re.sub(r'[^0-9.]', '', percentage_value)
                                    if cleaned_percentage:
                                        year_data["placed"] = f"{float(cleaned_percentage)}%"
                                except:
                                    year_data["placed"] = percentage_value
                            
                            if year_data:
                                historical_data["year_wise"][year] = year_data
        
        return historical_data
    
    def _extract_alternative_paths(self, text: str, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract information about alternative career paths
        
        Args:
            text: Text content
            tables: Extracted tables
            
        Returns:
            Dictionary with alternative path information
        """
        alternative_paths = {
            "higher_studies": None,
            "abroad_studies": None,
            "startups_founded": None
        }
        
        # Define patterns for various alternative paths
        patterns = {
            "higher_studies": [
                r"(\d+(?:\.\d+)?)\s*%\s+(?:students\s+)?(?:went\s+for|opted\s+for|pursuing)\s+higher\s+studies",
                r"higher\s+studies\s*(?::|\s+-)?\s*(\d+(?:\.\d+)?)\s*%",
                r"(\d+)\s+students\s+(?:went\s+for|opted\s+for|pursuing)\s+higher\s+studies"
            ],
            "abroad_studies": [
                r"(\d+(?:\.\d+)?)\s*%\s+(?:students\s+)?(?:went|studying)\s+abroad",
                r"(?:study|studies)\s+abroad\s*(?::|\s+-)?\s*(\d+(?:\.\d+)?)\s*%",
                r"(\d+)\s+students\s+(?:went|studying)\s+abroad"
            ],
            "startups_founded": [
                r"(\d+(?:\.\d+)?)\s*%\s+(?:students\s+)?founded\s+(?:their\s+own\s+)?(?:startups|companies|ventures)",
                r"(?:startups|ventures|entrepreneurship)\s*(?::|\s+-)?\s*(\d+(?:\.\d+)?)\s*%",
                r"(\d+)\s+students\s+founded\s+(?:their\s+own\s+)?(?:startups|companies|ventures)"
            ]
        }
        
        # Extract information from text
        for path, path_patterns in patterns.items():
            for pattern in path_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        value = float(match.group(1))
                        # If the value is greater than 100, it's likely a count, not percentage
                        if value > 100 and "%" not in pattern:
                            alternative_paths[path] = int(value)
                        else:
                            alternative_paths[path] = value
                        break
                    except:
                        alternative_paths[path] = match.group(1)
                        break
        
        # Look for data in tables
        for table in tables:
            headers = [h.lower() if h else "" for h in table.get("headers", [])]
            
            # Check if table might contain alternative path data
            alt_path_keywords = ["higher studies", "abroad", "startups", "entrepreneurship"]
            has_alt_path_col = any(any(kw in h for kw in alt_path_keywords) for h in headers if h)
            
            if has_alt_path_col:
                for i, header in enumerate(headers):
                    if not header:
                        continue
                        
                    path_key = None
                    if "higher studies" in header:
                        path_key = "higher_studies"
                    elif "abroad" in header:
                        path_key = "abroad_studies"
                    elif "startup" in header or "entrepreneur" in header:
                        path_key = "startups_founded"
                    
                    if path_key and alternative_paths[path_key] is None:
                        # Extract value from corresponding cells
                        for row in table.get("raw_rows", []):
                            if len(row) > i:
                                value = row[i]
                                try:
                                    if "%" in value:
                                        # Extract percentage
                                        num_value = re.sub(r'[^0-9.]', '', value)
                                        if num_value:
                                            alternative_paths[path_key] = float(num_value)
                                    else:
                                        # Try to convert to number
                                        num_value = re.sub(r'[^0-9.]', '', value)
                                        if num_value:
                                            num_value = float(num_value)
                                            alternative_paths[path_key] = int(num_value) if num_value.is_integer() else num_value
                                except:
                                    if value and not value.isspace():
                                        alternative_paths[path_key] = value
                                break
        
        return alternative_paths
    
    def _extract_internships(self, text: str, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract internship information
        
        Args:
            text: Text content
            tables: Extracted tables
            
        Returns:
            Dictionary with internship information
        """
        internship_info = {
            "count": None,
            "companies": [],
            "percentage": None
        }
        
        # Extract internship count
        count_patterns = [
            r"(\d+)\s+(?:students\s+)?(?:received|got|were\s+offered)\s+internship",
            r"(?:offered|provided)\s+(\d+)\s+internships",
            r"number\s+of\s+internships(?:\s+is|\s*:)?\s*(\d+)"
        ]
        
        for pattern in count_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    internship_info["count"] = int(match.group(1))
                    break
                except:
                    internship_info["count"] = match.group(1)
                    break
        
        # Extract internship percentage
        percentage_patterns = [
            r"(\d+(?:\.\d+)?)\s*%\s+(?:students\s+)?(?:received|got|were\s+offered)\s+internship",
            r"internship\s+percentage(?:\s+is|\s*:)?\s*(\d+(?:\.\d+)?)\s*%"
        ]
        
        for pattern in percentage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    internship_info["percentage"] = float(match.group(1))
                    break
                except:
                    internship_info["percentage"] = match.group(1)
                    break
        
        # Extract internship companies
        company_section_patterns = [
            r"internship\s+(?:companies|providers|recruiters)(?:\s+include)?[:\s]+(.+?)(?:\n\n|\.\s+[A-Z])",
            r"companies\s+(?:offering|providing)\s+internships?(?:\s+include)?[:\s]+(.+?)(?:\n\n|\.\s+[A-Z])"
        ]
        
        for pattern in company_section_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                companies_text = match.group(1)
                # Split by common separators
                company_candidates = re.split(r'[,;/\n•]', companies_text)
                
                for candidate in company_candidates:
                    candidate = candidate.strip()
                    if len(candidate) > 2 and not candidate.isdigit():
                        # Exclude common noise phrases
                        noise_phrases = ["companies", "include", "etc", "and", "more", "others"]
                        if not any(phrase == candidate.lower() for phrase in noise_phrases):
                            internship_info["companies"].append(candidate)
        
        # Look for internship data in tables
        for table in tables:
            headers = [h.lower() if h else "" for h in table.get("headers", [])]
            
            # Check if table might contain internship data
            internship_keywords = ["internship", "summer training", "industrial training"]
            company_keywords = ["company", "organization", "provider"]
            
            has_internship_header = any(any(kw in h for kw in internship_keywords) for h in headers if h)
            
            if has_internship_header:
                # If it's a company listing table
                company_col = None
                for i, header in enumerate(headers):
                    if header and any(kw in header for kw in company_keywords):
                        company_col = i
                        break
                
                if company_col is not None:
                    for row in table.get("raw_rows", []):
                        if len(row) > company_col and row[company_col]:
                            company = row[company_col].strip()
                            if len(company) > 2 and not company.isdigit():
                                internship_info["companies"].append(company)
        
        # Deduplicate companies
        if internship_info["companies"]:
            internship_info["companies"] = list(dict.fromkeys(internship_info["companies"]))
        
        return internship_info
    
    def _extract_recruitment_types(self, text: str) -> Dict[str, Any]:
        """
        Extract information about types of recruitment
        
        Args:
            text: Text content
            
        Returns:
            Dictionary with recruitment types information
        """
        recruitment_types = {
            "on_campus": None,
            "off_campus": None,
            "pool_campus": None
        }
        
        # Define patterns for various recruitment types
        patterns = {
            "on_campus": [
                r"(\d+(?:\.\d+)?)\s*%\s+(?:of\s+)?(?:students\s+)?(?:placed|recruited)\s+through\s+on[\s-]campus",
                r"on[\s-]campus\s+placement(?:\s+percentage)?(?:\s+is|\s*:)?\s*(\d+(?:\.\d+)?)\s*%",
                r"(\d+)\s+students\s+(?:placed|recruited)\s+through\s+on[\s-]campus"
            ],
            "off_campus": [
                r"(\d+(?:\.\d+)?)\s*%\s+(?:of\s+)?(?:students\s+)?(?:placed|recruited)\s+through\s+off[\s-]campus",
                r"off[\s-]campus\s+placement(?:\s+percentage)?(?:\s+is|\s*:)?\s*(\d+(?:\.\d+)?)\s*%",
                r"(\d+)\s+students\s+(?:placed|recruited)\s+through\s+off[\s-]campus"
            ],
            "pool_campus": [
                r"(\d+(?:\.\d+)?)\s*%\s+(?:of\s+)?(?:students\s+)?(?:placed|recruited)\s+through\s+pool[\s-]campus",
                r"pool[\s-]campus\s+placement(?:\s+percentage)?(?:\s+is|\s*:)?\s*(\d+(?:\.\d+)?)\s*%",
                r"(\d+)\s+students\s+(?:placed|recruited)\s+through\s+pool[\s-]campus"
            ]
        }
        
        # Extract information from text
        for recruitment_type, type_patterns in patterns.items():
            for pattern in type_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        value = float(match.group(1))
                        # If the value is greater than 100, it's likely a count, not percentage
                        if value > 100 and "%" not in pattern:
                            recruitment_types[recruitment_type] = int(value)
                        else:
                            recruitment_types[recruitment_type] = value
                        break
                    except:
                        recruitment_types[recruitment_type] = match.group(1)
                        break
        
        return recruitment_types