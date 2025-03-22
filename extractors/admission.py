"""
Specialized extractor for admission-related content
"""
import logging
import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime

from extractors.base import BaseExtractor

logger = logging.getLogger(__name__)

class AdmissionExtractor(BaseExtractor):
    """Specialized extractor for admission-related information"""
    
    def __init__(self, ai_processor=None):
        """Initialize admission extractor"""
        super().__init__(ai_processor)
        
        # Keywords for specific admission data points
        self.admission_keywords = {
            "dates_deadlines": [
                "application deadline", "last date", "admission date", "important dates", 
                "admission schedule", "last date to apply", "registration deadline"
            ],
            "courses": [
                "courses offered", "available courses", "programs", "specializations",
                "branches", "disciplines", "degrees", "courses available"
            ],
            "capacity": [
                "total seats", "seat matrix", "intake", "capacity", "available seats", 
                "reservation", "category", "quota", "vacant"
            ],
            "financial": [
                "fee structure", "fees", "tuition", "scholarship", "payment schedule",
                "fee payment", "waiver", "financial aid", "loan"
            ],
            "facilities": [
                "hostel facility", "hostel availability", "accomodation", "boys hostel", 
                "girls hostel", "amenities", "infrastructure", "campus facility"
            ],
            "eligibility": [
                "eligibility criteria", "minimum marks", "cut-off", "entrance exam",
                "qualifying exam", "admission criteria", "required percentage", "jee", "gate"
            ]
        }
    
    def extract_admission_data(self, content: str, college_name: str) -> Dict[str, Any]:
        """
        Extract admission-related information from content
        
        Args:
            content: HTML or text content
            college_name: Name of the college
            
        Returns:
            Dictionary with extracted admission data
        """
        # Extract basic text if HTML provided
        if "<html" in content or "<body" in content:
            text_content = self.extract_text(content)
            tables = self.extract_tables(content)
        else:
            text_content = content
            tables = []
        
        # Initialize result object
        admission_data = {
            "college_name": college_name,
            "last_updated": datetime.now(),
            "admission_data": {
                "application_deadlines": self._extract_application_deadlines(text_content, tables),
                "courses_offered": self._extract_courses(text_content, tables),
                "seats_available": self._extract_seats(text_content, tables),
                "fee_structure": self._extract_fees(text_content, tables),
                "hostel_facilities": self._extract_hostel_info(text_content, tables),
                "eligibility_criteria": self._extract_eligibility(text_content, tables)
            },
            "confidence_score": 0.7,  # Default confidence
            "processing_date": datetime.now()
        }
        
        # If AI processor is available, use it for enhanced extraction
        if self.ai_processor:
            try:
                enhanced_data = self.ai_processor.process_admission_content(text_content, tables)
                if enhanced_data:
                    # Merge AI-extracted data with rule-based extraction
                    for key, value in enhanced_data.items():
                        if value and key in admission_data["admission_data"]:
                            admission_data["admission_data"][key] = value
                    
                    # Update confidence score
                    admission_data["confidence_score"] = enhanced_data.get("confidence_score", 0.8)
            except Exception as e:
                logger.error(f"Error in AI processing of admission content: {e}")
        
        return admission_data
    
    def _extract_application_deadlines(self, text: str, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract application deadlines
        
        Args:
            text: Text content
            tables: Extracted tables
            
        Returns:
            List of deadline information
        """
        deadlines = []
        
        # Extract dates from text
        dates = self.extract_dates(text)
        
        for date in dates:
            context = date["context"].lower()
            
            # Check if context contains deadline-related keywords
            is_deadline = any(keyword in context for keyword in self.admission_keywords["dates_deadlines"])
            
            if is_deadline:
                deadline_info = {
                    "date_str": date["date_str"],
                    "context": date["context"],
                    "event_type": self._determine_deadline_type(context)
                }
                
                # Try to parse standardized date if possible
                try:
                    # Add parsing logic if needed
                    pass
                except:
                    pass
                
                deadlines.append(deadline_info)
        
        # Extract deadlines from tables
        for table in tables:
            headers = [h.lower() for h in table.get("headers", [])]
            
            # Check if this table might contain deadline information
            has_date_header = any("date" in h for h in headers)
            has_deadline_header = any(any(kw in h for kw in self.admission_keywords["dates_deadlines"]) for h in headers)
            
            if has_date_header or has_deadline_header:
                date_col = None
                event_col = None
                
                # Find the date and event columns
                for i, header in enumerate(headers):
                    if "date" in header:
                        date_col = i
                    if any(kw in header for kw in ["event", "activity", "particular", "detail"]):
                        event_col = i
                
                if date_col is not None:
                    for row in table.get("raw_rows", []):
                        if len(row) > date_col:
                            date_str = row[date_col]
                            event_type = "application"
                            
                            # Try to determine event type
                            if event_col is not None and len(row) > event_col:
                                event_text = row[event_col].lower()
                                event_type = self._determine_deadline_type(event_text)
                            
                            deadlines.append({
                                "date_str": date_str,
                                "context": " - ".join(row),
                                "event_type": event_type
                            })
        
        return deadlines
    
    def _determine_deadline_type(self, context: str) -> str:
        """
        Determine the type of deadline from context
        
        Args:
            context: Context text
            
        Returns:
            Type of deadline
        """
        context = context.lower()
        
        if any(term in context for term in ["application", "apply", "registration", "register", "form"]):
            return "application"
        elif any(term in context for term in ["entrance", "exam", "test"]):
            return "entrance_exam"
        elif any(term in context for term in ["result", "declaration", "announce", "publication"]):
            return "result_declaration"
        elif any(term in context for term in ["interview", "counselling", "counseling", "selection"]):
            return "interview_counselling"
        elif any(term in context for term in ["fee", "payment", "deposit"]):
            return "fee_payment"
        elif any(term in context for term in ["class", "start", "commencement", "begin"]):
            return "class_commencement"
        else:
            return "other"
    
    def _extract_courses(self, text: str, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract courses offered
        
        Args:
            text: Text content
            tables: Extracted tables
            
        Returns:
            List of course information
        """
        courses = []
        
        # Look for courses in tables
        for table in tables:
            headers = [h.lower() for h in table.get("headers", [])]
            
            # Check if table might contain course information
            has_course_header = any(any(kw in h for kw in ["course", "program", "degree", "branch", "discipline"]) for h in headers)
            
            if has_course_header:
                course_col = None
                duration_col = None
                seats_col = None
                fee_col = None
                
                # Find relevant columns
                for i, header in enumerate(headers):
                    if any(kw in header for kw in ["course", "program", "degree", "branch"]):
                        course_col = i
                    elif any(kw in header for kw in ["duration", "years", "period"]):
                        duration_col = i
                    elif any(kw in header for kw in ["seats", "intake", "capacity"]):
                        seats_col = i
                    elif any(kw in header for kw in ["fee", "fees", "tuition"]):
                        fee_col = i
                
                if course_col is not None:
                    for row in table.get("raw_rows", []):
                        if len(row) > course_col and row[course_col]:
                            course_info = {
                                "name": row[course_col]
                            }
                            
                            # Add duration if available
                            if duration_col is not None and len(row) > duration_col:
                                course_info["duration"] = row[duration_col]
                            
                            # Add seats if available
                            if seats_col is not None and len(row) > seats_col:
                                course_info["seats"] = row[seats_col]
                            
                            # Add fee if available
                            if fee_col is not None and len(row) > fee_col:
                                course_info["fee"] = row[fee_col]
                            
                            courses.append(course_info)
        
        # If no courses found in tables, try to extract from text
        if not courses:
            # Look for course lists in text
            course_sections = []
            
            # Try to find sections with course information
            for keyword in self.admission_keywords["courses"]:
                pattern = rf"(?:{keyword})[:\s]+((?:.+?(?:\n|$)){{1,10}})"
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    section = match.group(1)
                    course_sections.append(section)
            
            # Extract individual courses from sections
            for section in course_sections:
                # Split by common separators and line breaks
                course_candidates = re.split(r'[,;\n•\-]', section)
                
                for candidate in course_candidates:
                    candidate = candidate.strip()
                    if len(candidate) > 3 and not candidate.isdigit():  # Basic validation
                        courses.append({"name": candidate})
        
        return courses
    
    def _extract_seats(self, text: str, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract seat availability information
        
        Args:
            text: Text content
            tables: Extracted tables
            
        Returns:
            Dictionary with seat information
        """
        seat_info = {
            "total": None,
            "category_wise": {}
        }
        
        # Extract total seats from text
        total_patterns = [
            r"total(?:\s+number\s+of)?\s+seats\s*(?:is|are|:)?\s*(\d+)",
            r"total\s+intake\s*(?:is|:)?\s*(\d+)",
            r"(?:college|institute)\s+(?:has|with)\s*(\d+)\s+seats"
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    seat_info["total"] = int(match.group(1))
                    break
                except:
                    pass
        
        # Look for category-wise distribution in tables
        for table in tables:
            headers = [h.lower() for h in table.get("headers", [])]
            
            # Check if table might contain seat reservation information
            category_headers = ["category", "reservation", "quota"]
            has_category_header = any(any(kw in h for kw in category_headers) for h in headers)
            
            if has_category_header:
                category_col = None
                seats_col = None
                
                # Find relevant columns
                for i, header in enumerate(headers):
                    if any(kw in header for kw in category_headers):
                        category_col = i
                    elif any(kw in header for kw in ["seats", "number", "capacity", "count"]):
                        seats_col = i
                
                if category_col is not None and seats_col is not None:
                    for row in table.get("raw_rows", []):
                        if len(row) > max(category_col, seats_col):
                            category = row[category_col]
                            seats = row[seats_col]
                            
                            # Try to convert seats to integer
                            try:
                                seats_value = int(seats)
                                seat_info["category_wise"][category] = seats_value
                            except:
                                seat_info["category_wise"][category] = seats
        
        # If total is still None, try to sum up category-wise values
        if seat_info["total"] is None and seat_info["category_wise"]:
            try:
                numeric_values = [v for v in seat_info["category_wise"].values() if isinstance(v, (int, float))]
                if numeric_values:
                    seat_info["total"] = sum(numeric_values)
            except:
                pass
        
        return seat_info
    
    def _extract_fees(self, text: str, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract fee information
        
        Args:
            text: Text content
            tables: Extracted tables
            
        Returns:
            Dictionary with fee information
        """
        fee_info = {
            "course_wise": {},
            "payment_schedule": None
        }
        
        # Look for fee information in tables
        for table in tables:
            headers = [h.lower() for h in table.get("headers", [])]
            
            # Check if table might contain fee information
            fee_headers = ["fee", "fees", "tuition", "amount"]
            has_fee_header = any(any(kw in h for kw in fee_headers) for h in headers)
            
            if has_fee_header:
                course_col = None
                fee_col = None
                
                # Find relevant columns
                for i, header in enumerate(headers):
                    if any(kw in header for kw in ["course", "program", "branch", "degree"]):
                        course_col = i
                    elif any(kw in header for kw in fee_headers):
                        fee_col = i
                
                if fee_col is not None:
                    for row in table.get("raw_rows", []):
                        if len(row) > fee_col:
                            # Get fee value and try to convert to number
                            fee_value = row[fee_col]
                            try:
                                # Remove currency symbols and commas
                                cleaned_fee = re.sub(r'[^\d.]', '', fee_value)
                                numeric_fee = float(cleaned_fee)
                            except:
                                numeric_fee = fee_value
                            
                            if course_col is not None and len(row) > course_col:
                                # Course-wise fee
                                course_name = row[course_col]
                                fee_info["course_wise"][course_name] = numeric_fee
                            else:
                                # Single fee or unnamed course
                                row_text = " ".join(row)
                                if "hostel" in row_text.lower():
                                    fee_info["hostel_fee"] = numeric_fee
                                elif "first" in row_text.lower() or "1st" in row_text.lower():
                                    fee_info["first_year"] = numeric_fee
                                else:
                                    fee_info["general_fee"] = numeric_fee
        
        # Extract payment schedule information
        schedule_patterns = [
            r"payment\s+schedule[:\s]+((?:.+?(?:\n|$)){1,10})",
            r"fee\s+payment\s+schedule[:\s]+((?:.+?(?:\n|$)){1,10})",
            r"installment(?:\s+details)?[:\s]+((?:.+?(?:\n|$)){1,10})"
        ]
        
        for pattern in schedule_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fee_info["payment_schedule"] = match.group(1).strip()
                break
        
        return fee_info
    
    def _extract_hostel_info(self, text: str, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract hostel facility information
        
        Args:
            text: Text content
            tables: Extracted tables
            
        Returns:
            Dictionary with hostel information
        """
        hostel_info = {
            "boys_hostel": None,
            "girls_hostel": None,
            "hostel_fee": None
        }
        
        # Check for presence of hostels
        boys_patterns = [
            r"boys\s+hostel\s+(?:is\s+)?(available|not available)",
            r"hostel\s+(?:facilities\s+)for\s+boys\s+(?:is\s+)?(available|not available)",
            r"(separate|dedicated)\s+hostel\s+for\s+boys"
        ]
        
        girls_patterns = [
            r"girls\s+hostel\s+(?:is\s+)?(available|not available)",
            r"hostel\s+(?:facilities\s+)for\s+girls\s+(?:is\s+)?(available|not available)",
            r"(separate|dedicated)\s+hostel\s+for\s+girls"
        ]
        
        # Check boys hostel
        for pattern in boys_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.group(1).lower() in ["available", "separate", "dedicated"]:
                    hostel_info["boys_hostel"] = True
                else:
                    hostel_info["boys_hostel"] = False
                break
        
        # Check girls hostel
        for pattern in girls_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.group(1).lower() in ["available", "separate", "dedicated"]:
                    hostel_info["girls_hostel"] = True
                else:
                    hostel_info["girls_hostel"] = False
                break
        
        # If not found in patterns, look for simple mentions
        if hostel_info["boys_hostel"] is None:
            if re.search(r"boys\s+hostel", text, re.IGNORECASE):
                hostel_info["boys_hostel"] = True
        
        if hostel_info["girls_hostel"] is None:
            if re.search(r"girls\s+hostel", text, re.IGNORECASE):
                hostel_info["girls_hostel"] = True
        
        # Look for hostel fee
        fee_patterns = [
            r"hostel\s+fee[s]?\s*(?:is|:)?\s*(?:Rs\.?|INR|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)",
            r"hostel\s+charges[:\s]*(?:Rs\.?|INR|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)"
        ]
        
        for pattern in fee_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # Remove commas for numeric conversion
                    numeric_value = match.group(1).replace(',', '')
                    hostel_info["hostel_fee"] = float(numeric_value)
                    break
                except:
                    hostel_info["hostel_fee"] = match.group(1)
                    break
        
        return hostel_info
    
    def _extract_eligibility(self, text: str, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract eligibility criteria
        
        Args:
            text: Text content
            tables: Extracted tables
            
        Returns:
            Dictionary with eligibility information
        """
        eligibility_info = {
            "academic_requirements": None,
            "entrance_exams": [],
            "cutoff_scores": {}
        }
        
        # Extract academic requirements section
        requirement_patterns = [
            r"eligibility\s+criteria[:\s]+((?:.+?(?:\n|$)){1,15})",
            r"academic\s+requirements[:\s]+((?:.+?(?:\n|$)){1,15})",
            r"minimum\s+qualification[:\s]+((?:.+?(?:\n|$)){1,15})"
        ]
        
        for pattern in requirement_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                eligibility_info["academic_requirements"] = match.group(1).strip()
                break
        
        # Extract entrance exam information
        exam_patterns = [
            r"entrance\s+exam[s]?[:\s]+((?:.+?(?:\n|$)){1,5})",
            r"qualifying\s+exam[s]?[:\s]+((?:.+?(?:\n|$)){1,5})"
        ]
        
        # Common entrance exams to look for
        common_exams = [
            "JEE Main", "JEE Advanced", "GATE", "CAT", "MAT", "NEET",
            "GMAT", "GRE", "CMAT", "XAT", "CLAT", "NATA", "BITSAT"
        ]
        
        # Look for mentions of common exams
        for exam in common_exams:
            if re.search(rf"\b{re.escape(exam)}\b", text, re.IGNORECASE):
                eligibility_info["entrance_exams"].append(exam)
        
        # Extract specific cutoff scores
        for exam in eligibility_info["entrance_exams"]:
            cutoff_patterns = [
                rf"{re.escape(exam)}(?:\s+cut[\-\s]off|\s+score|\s+rank)(?:\s+is|\s*:)?\s*(\d+(?:\.\d+)?)",
                rf"minimum\s+{re.escape(exam)}\s+(?:score|rank|percentile)(?:\s+is|\s*:)?\s*(\d+(?:\.\d+)?)"
            ]
            
            for pattern in cutoff_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        eligibility_info["cutoff_scores"][exam] = float(match.group(1))
                    except:
                        eligibility_info["cutoff_scores"][exam] = match.group(1)
                    break
        
        # Look for minimum percentage requirements
        percentage_patterns = [
            r"minimum\s+(?:percentage|marks)(?:\s+required)?\s*(?:is|:)?\s*(\d+(?:\.\d+)?)\s*%",
            r"(?:candidate|student)s?\s+must\s+have\s+(?:secured|obtained|scored)(?:\s+a\s+minimum\s+of)?\s*(\d+(?:\.\d+)?)\s*%"
        ]
        
        for pattern in percentage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    eligibility_info["cutoff_scores"]["12th_percentage"] = float(match.group(1))
                except:
                    eligibility_info["cutoff_scores"]["12th_percentage"] = match.group(1)
                break
        
        return eligibility_info