"""
Image extractor for processing image files using OCR and chart recognition
"""
import logging
import os
import requests
import tempfile
from typing import Dict, List, Any, Optional
import json

from extractors.base import BaseExtractor

logger = logging.getLogger(__name__)

class ImageExtractor(BaseExtractor):
    """Extractor for image content using the AI API endpoints"""
    
    def __init__(self, ai_processor=None):
        """Initialize image extractor"""
        super().__init__(ai_processor)
    
    def extract_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text and visual elements from image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict with extracted content
        """
        try:
            result = {
                "success": True,
                "text": "",
                "tables": [],
                "is_chart": False,
                "chart_data": None,
                "elements": []
            }
            
            # Use AI processor to extract text via OCR
            if self.ai_processor:
                ocr_result = self.ai_processor.process_image_ocr(image_path)
                if ocr_result:
                    result["text"] = ocr_result.get("full_text", "")
                    result["elements"] = ocr_result.get("items", [])
                
                # Check if image is a chart
                chart_result = self.ai_processor.process_image_chart(image_path)
                if chart_result:
                    result["is_chart"] = True
                    result["chart_data"] = chart_result
                    
                # Check for tables in the image
                table_result = self.ai_processor.detect_tables_in_image(image_path)
                if table_result:
                    result["tables"] = table_result
            
            return result
        except Exception as e:
            logger.error(f"Error extracting content from image {image_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "tables": [],
                "is_chart": False,
                "chart_data": None,
                "elements": []
            }
    
    def classify_image_content(self, image_path: str, extracted_text: str = None) -> str:
        """
        Classify the content type of an image
        
        Args:
            image_path: Path to the image file
            extracted_text: OCR text (if already extracted)
            
        Returns:
            Classification ('chart', 'table', 'text', 'logo', 'photo')
        """
        # Try to classify using AI processor
        if self.ai_processor:
            try:
                # Check if it's a chart
                chart_result = self.ai_processor.process_image_chart(image_path)
                if chart_result and chart_result.get("chart_type", "unknown") != "unknown":
                    return "chart"
                
                # Check if it contains tables
                table_result = self.ai_processor.detect_tables_in_image(image_path)
                if table_result and len(table_result) > 0:
                    return "table"
                
                # If not a chart or table, check text density
                text = extracted_text
                if not text:
                    ocr_result = self.ai_processor.process_image_ocr(image_path)
                    if ocr_result:
                        text = ocr_result.get("full_text", "")
                
                if text:
                    # If there's substantial text, classify as text image
                    words = text.split()
                    if len(words) > 30:
                        return "text"
                
                # Basic guess based on file characteristics
                # In a production system, you'd use more sophisticated image classification
                return "photo"  # Default to photo
                
            except Exception as e:
                logger.warning(f"Error classifying image content: {e}")
                return "unknown"
        else:
            return "unknown"
    
    def extract_data_from_chart(self, image_path: str) -> Dict[str, Any]:
        """
        Extract data from a chart image
        
        Args:
            image_path: Path to the chart image
            
        Returns:
            Dict with extracted chart data
        """
        if self.ai_processor:
            try:
                chart_result = self.ai_processor.process_image_chart(image_path)
                return chart_result
            except Exception as e:
                logger.error(f"Error extracting data from chart {image_path}: {e}")
        
        return {
            "chart_type": "unknown",
            "data": {}
        }
    
    def extract_data_from_table_image(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Extract data from a table in an image
        
        Args:
            image_path: Path to the image with table
            
        Returns:
            List of extracted tables
        """
        if self.ai_processor:
            try:
                # Detect tables in the image
                tables = self.ai_processor.detect_tables_in_image(image_path)
                
                # If tables found, extract text for each table region
                if tables:
                    extracted_tables = []
                    
                    # Process each table
                    for i, table in enumerate(tables):
                        table_info = {
                            "table_id": f"table_{i+1}",
                            "x": table.get("x", 0),
                            "y": table.get("y", 0),
                            "width": table.get("width", 0),
                            "height": table.get("height", 0),
                            "content": {}
                        }
                        
                        # Extract text for this table region
                        # In a full implementation, you'd crop the image to the table region
                        # and run OCR specifically on that region for better results
                        table_info["content"] = {"raw_text": f"Table {i+1} content"}
                        
                        extracted_tables.append(table_info)
                    
                    return extracted_tables
                
                return []
            except Exception as e:
                logger.error(f"Error extracting data from table image {image_path}: {e}")
        
        return []