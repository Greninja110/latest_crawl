"""
PDF extractor for processing PDF documents
"""
import logging
import re
import os
import fitz  # PyMuPDF
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup
import tempfile

from extractors.base import BaseExtractor

logger = logging.getLogger(__name__)

class PDFExtractor(BaseExtractor):
    """Extractor for PDF documents"""
    
    def __init__(self, ai_processor=None):
        """Initialize PDF extractor"""
        super().__init__(ai_processor)
    
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text and structured content from PDF
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dict with extracted content
        """
        try:
            result = {
                "success": True,
                "text": "",
                "tables": [],
                "images": [],
                "metadata": {},
                "pages": 0
            }
            
            # Open the PDF
            doc = fitz.open(pdf_path)
            result["pages"] = len(doc)
            
            # Extract metadata
            metadata = doc.metadata
            if metadata:
                result["metadata"] = {
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", ""),
                    "subject": metadata.get("subject", ""),
                    "keywords": metadata.get("keywords", ""),
                    "creator": metadata.get("creator", ""),
                    "producer": metadata.get("producer", ""),
                    "creation_date": metadata.get("creationDate", ""),
                    "modification_date": metadata.get("modDate", "")
                }
            
            # Extract text and tables from all pages
            full_text = ""
            for page_num, page in enumerate(doc):
                # Extract text
                page_text = page.get_text()
                full_text += page_text + "\n\n"
                
                # Extract tables
                tables = self._extract_tables_from_page(page)
                if tables:
                    for i, table in enumerate(tables):
                        table["page"] = page_num + 1
                        table["table_id"] = f"page{page_num+1}_table{i+1}"
                        result["tables"].append(table)
                
                # Extract images
                images = self._extract_images_from_page(page, pdf_path, page_num)
                result["images"].extend(images)
            
            result["text"] = full_text
            
            return result
        except Exception as e:
            logger.error(f"Error extracting content from PDF {pdf_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "tables": [],
                "images": [],
                "metadata": {},
                "pages": 0
            }
    
    def _extract_tables_from_page(self, page: fitz.Page) -> List[Dict[str, Any]]:
        """
        Extract tables from a PDF page
        
        Args:
            page: PDF page object
            
        Returns:
            List of extracted tables
        """
        tables = []
        
        try:
            # Get blocks that might represent tables
            blocks = page.get_text("dict")["blocks"]
            
            # Identify potential table blocks
            for block in blocks:
                if block["type"] == 0:  # Text block
                    lines = block.get("lines", [])
                    
                    # Check if this might be a table
                    if self._is_potential_table(lines):
                        table_data = self._process_table_lines(lines)
                        if table_data and table_data["rows"]:
                            tables.append(table_data)
            
            return tables
        except Exception as e:
            logger.error(f"Error extracting tables from page: {e}")
            return []
    
    def _is_potential_table(self, lines: List[Dict[str, Any]]) -> bool:
        """
        Check if a set of lines potentially represents a table
        
        Args:
            lines: List of line objects from PDF
            
        Returns:
            Boolean indicating if this might be a table
        """
        if len(lines) < 2:
            return False
        
        # Check if lines are aligned in columns
        x_positions = []
        
        # Collect span positions from the first few lines
        for i, line in enumerate(lines[:min(5, len(lines))]):
            line_positions = []
            for span in line.get("spans", []):
                line_positions.append(span["origin"][0])
            x_positions.append(line_positions)
        
        # If we have consistent column positions across lines, it might be a table
        if len(x_positions) >= 2:
            # Check for consistency in the number of spans
            span_counts = [len(positions) for positions in x_positions]
            if len(set(span_counts)) == 1 and span_counts[0] > 1:
                return True
                
            # Check for alignment of positions
            for i in range(1, len(x_positions)):
                # Allow for some variation in position
                matching = sum(1 for pos1, pos2 in zip(x_positions[0], x_positions[i]) 
                              if abs(pos1 - pos2) < 5)
                if matching / len(x_positions[0]) >= 0.7:  # 70% match threshold
                    return True
        
        return False
    
    def _process_table_lines(self, lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process lines that represent a table
        
        Args:
            lines: List of line objects from PDF
            
        Returns:
            Structured table data
        """
        if not lines:
            return None
        
        table_data = {
            "headers": [],
            "rows": [],
            "raw_text": ""
        }
        
        # Collect all spans and their positions
        all_spans = []
        for line in lines:
            line_spans = []
            for span in line.get("spans", []):
                line_spans.append({
                    "text": span.get("text", "").strip(),
                    "x": span["origin"][0],
                    "y": span["origin"][1],
                    "font": span.get("font", ""),
                    "size": span.get("size", 0),
                    "bold": span.get("flags", 0) & 2 > 0  # Check if bold flag is set
                })
            if line_spans:
                all_spans.append(line_spans)
        
        if not all_spans:
            return None
        
        # Try to identify headers (first row or bold text)
        headers = []
        header_row_idx = 0
        
        # Check if first row has bold text or different font size
        if len(all_spans) > 1:
            first_row = all_spans[0]
            second_row = all_spans[1]
            
            # Check if first row has bold text
            is_header = any(span["bold"] for span in first_row)
            
            # Or check if first row has different font size
            if not is_header and first_row and second_row:
                first_sizes = [span["size"] for span in first_row]
                second_sizes = [span["size"] for span in second_row]
                
                avg_first = sum(first_sizes) / len(first_sizes)
                avg_second = sum(second_sizes) / len(second_sizes)
                
                is_header = abs(avg_first - avg_second) > 1  # More than 1pt difference
            
            if is_header:
                headers = [span["text"] for span in first_row]
                header_row_idx = 1  # Skip the header row when processing data rows
        
        # If no headers identified, use empty strings
        if not headers and all_spans:
            headers = [""] * len(all_spans[0])
        
        # Process data rows
        rows = []
        for row_idx in range(header_row_idx, len(all_spans)):
            row = all_spans[row_idx]
            row_values = [span["text"] for span in row]
            
            # Skip empty rows
            if not any(val.strip() for val in row_values):
                continue
                
            rows.append(row_values)
        
        # Assemble raw text
        raw_lines = []
        for spans in all_spans:
            raw_lines.append(" | ".join(span["text"] for span in spans))
        raw_text = "\n".join(raw_lines)
        
        table_data["headers"] = headers
        table_data["rows"] = rows
        table_data["raw_text"] = raw_text
        
        return table_data
    
    def _extract_images_from_page(self, page: fitz.Page, pdf_path: str, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract images from a PDF page
        
        Args:
            page: PDF page object
            pdf_path: Path to the PDF file (for generating image filenames)
            page_num: Page number
            
        Returns:
            List of extracted image information
        """
        images = []
        
        try:
            # Get image list
            img_list = page.get_images(full=True)
            
            for img_idx, img in enumerate(img_list):
                # Get image properties
                xref = img[0]
                
                try:
                    # Extract image
                    base_image = page.parent.extract_image(xref)
                    
                    if base_image:
                        # Create a temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{base_image['ext']}") as temp_file:
                            temp_file.write(base_image["image"])
                            temp_path = temp_file.name
                        
                        # Get image dimensions
                        width = base_image.get("width", 0)
                        height = base_image.get("height", 0)
                        
                        images.append({
                            "page": page_num + 1,
                            "image_id": f"page{page_num+1}_img{img_idx+1}",
                            "path": temp_path,
                            "width": width,
                            "height": height,
                            "format": base_image["ext"]
                        })
                except Exception as img_err:
                    logger.warning(f"Error extracting image from PDF {pdf_path} page {page_num+1}: {img_err}")
            
            return images
        except Exception as e:
            logger.error(f"Error extracting images from page {page_num+1} of PDF {pdf_path}: {e}")
            return []
    
    def classify_pdf_content(self, text: str) -> str:
        """
        Classify the content type of a PDF document
        
        Args:
            text: Extracted text from PDF
            
        Returns:
            Classification ('admission', 'placement', 'general')
        """
        # Use AI processor if available
        if self.ai_processor:
            try:
                classification = self.ai_processor.classify_content(text)
                if classification and classification.get('confidence', 0) > 0.6:
                    return classification['class']
            except Exception as e:
                logger.warning(f"AI classification failed: {e}")
        
        # Fallback to keyword counting
        text_lower = text.lower()
        
        # Count admission keywords
        admission_count = sum(1 for kw in [
            "admission", "apply", "eligibility", "entrance", "application form",
            "counselling", "selection", "seat", "course", "fee", "hostel"
        ] if kw in text_lower)
        
        # Count placement keywords
        placement_count = sum(1 for kw in [
            "placement", "recruiter", "company", "salary", "package", "career",
            "internship", "training", "industry", "job", "employed", "hire"
        ] if kw in text_lower)
        
        if admission_count > placement_count:
            return "admission"
        elif placement_count > admission_count:
            return "placement"
        else:
            return "general"
    
    def extract_text_with_formatting(self, pdf_path: str) -> str:
        """
        Extract text with basic formatting (paragraphs, bullets) from PDF
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text with some formatting preserved
        """
        try:
            doc = fitz.open(pdf_path)
            formatted_text = ""
            
            for page in doc:
                # Get blocks
                blocks = page.get_text("dict")["blocks"]
                
                for block in blocks:
                    if block["type"] == 0:  # Text block
                        block_text = ""
                        
                        for line in block.get("lines", []):
                            line_text = ""
                            for span in line.get("spans", []):
                                line_text += span["text"]
                            
                            if line_text.strip():
                                block_text += line_text + " "
                        
                        block_text = block_text.strip()
                        if block_text:
                            # Check if this is likely a bullet point
                            if block_text.startswith("•") or block_text.startswith("-") or re.match(r"^\d+\.", block_text):
                                formatted_text += block_text + "\n"
                            else:
                                formatted_text += block_text + "\n\n"
            
            return formatted_text
        except Exception as e:
            logger.error(f"Error extracting formatted text from PDF {pdf_path}: {e}")
            return ""
    
    def cleanup_temp_files(self, extracted_data: Dict[str, Any]) -> None:
        """
        Clean up temporary image files
        
        Args:
            extracted_data: Extracted data containing image paths
        """
        for image in extracted_data.get("images", []):
            try:
                if "path" in image and os.path.exists(image["path"]):
                    os.unlink(image["path"])
            except Exception as e:
                logger.warning(f"Error cleaning up temporary file {image.get('path')}: {e}")