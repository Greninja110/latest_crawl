"""
AI Processor for communicating with Hugging Face AI model API endpoints
"""
import logging
import os
import json
import requests
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import asyncio

from config.settings import HF_API_ENDPOINTS

logger = logging.getLogger(__name__)

class AIProcessor:
    """Interface with the Hugging Face AI model endpoints"""
    
    def __init__(self):
        """Initialize the AI processor"""
        self.api_endpoints = HF_API_ENDPOINTS
        self.session = None
    
    async def _get_session(self):
        """Get or create an aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def classify_content(self, content: str) -> Dict[str, Any]:
        """
        Classify content type using AI
        
        Args:
            content: Text content to classify
            
        Returns:
            Classification result
        """
        try:
            endpoint = self.api_endpoints.get("classify_document")
            if not endpoint:
                logger.error("Document classification endpoint not configured")
                return {}
            
            # Truncate content to avoid excessive request size
            truncated_content = content[:10000]
            
            # Send request to the AI endpoint
            response = requests.post(
                endpoint,
                json={"text": truncated_content},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("classification", {})
            else:
                logger.warning(f"Classification API returned error: {response.status_code}, {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error classifying content: {e}")
            return {}
    
    def extract_entities(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from content
        
        Args:
            content: Text content to process
            
        Returns:
            List of extracted entities
        """
        try:
            endpoint = self.api_endpoints.get("extract_entities")
            if not endpoint:
                logger.error("Entity extraction endpoint not configured")
                return []
            
            # Truncate content to avoid excessive request size
            truncated_content = content[:10000]
            
            # Send request to the AI endpoint
            response = requests.post(
                endpoint,
                json={"text": truncated_content},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("entities", [])
            else:
                logger.warning(f"Entity extraction API returned error: {response.status_code}, {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    def answer_question(self, context: str, question: str) -> Dict[str, Any]:
        """
        Get answer to a question based on context
        
        Args:
            context: Text context for the question
            question: Question to answer
            
        Returns:
            Answer data
        """
        try:
            endpoint = self.api_endpoints.get("answer_question")
            if not endpoint:
                logger.error("Question answering endpoint not configured")
                return {}
            
            # Truncate context to avoid excessive request size
            truncated_context = context[:15000]
            
            # Send request to the AI endpoint
            response = requests.post(
                endpoint,
                json={"context": truncated_context, "question": question},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("result", {})
            else:
                logger.warning(f"Question answering API returned error: {response.status_code}, {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {}
    
    def process_image_ocr(self, image_path: str) -> Dict[str, Any]:
        """
        Process image with OCR
        
        Args:
            image_path: Path to image file
            
        Returns:
            OCR results
        """
        try:
            endpoint = self.api_endpoints.get("extract_ocr")
            if not endpoint:
                logger.error("OCR endpoint not configured")
                return {}
            
            # Create file payload
            with open(image_path, "rb") as img_file:
                files = {"file": (os.path.basename(image_path), img_file)}
                
                # Send request to the AI endpoint
                response = requests.post(
                    endpoint,
                    files=files,
                    timeout=60
                )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("result", {})
            else:
                logger.warning(f"OCR API returned error: {response.status_code}, {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error processing image with OCR: {e}")
            return {}
    
    def detect_tables_in_image(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Detect tables in an image
        
        Args:
            image_path: Path to image file
            
        Returns:
            Detected tables
        """
        try:
            endpoint = self.api_endpoints.get("detect_tables")
            if not endpoint:
                logger.error("Table detection endpoint not configured")
                return []
            
            # Create file payload
            with open(image_path, "rb") as img_file:
                files = {"file": (os.path.basename(image_path), img_file)}
                
                # Send request to the AI endpoint
                response = requests.post(
                    endpoint,
                    files=files,
                    timeout=60
                )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("tables", [])
            else:
                logger.warning(f"Table detection API returned error: {response.status_code}, {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error detecting tables in image: {e}")
            return []
    
    def process_image_chart(self, image_path: str) -> Dict[str, Any]:
        """
        Process chart image
        
        Args:
            image_path: Path to image file
            
        Returns:
            Chart analysis results
        """
        try:
            endpoint = self.api_endpoints.get("analyze_chart")
            if not endpoint:
                logger.error("Chart analysis endpoint not configured")
                return {}
            
            # Create file payload
            with open(image_path, "rb") as img_file:
                files = {"file": (os.path.basename(image_path), img_file)}
                
                # Send request to the AI endpoint
                response = requests.post(
                    endpoint,
                    files=files,
                    timeout=60
                )
            
            if response.status_code == 200:
                result = response.json()
                chart_data = {}
                
                # Merge chart_type and chart_data
                if "chart_type" in result:
                    chart_data.update(result["chart_type"])
                if "chart_data" in result:
                    chart_data.update(result["chart_data"])
                
                return chart_data
            else:
                logger.warning(f"Chart analysis API returned error: {response.status_code}, {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error processing chart image: {e}")
            return {}
    
    async def process_admission_content(self, text: str, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process admission content with AI assistance
        
        Args:
            text: Extracted text content
            tables: Extracted tables
            
        Returns:
            Enhanced admission data
        """
        try:
            # Create specific questions to ask the AI based on the content
            questions = [
                {"question": "What are the application deadlines mentioned?", "field": "application_deadlines"},
                {"question": "What courses are offered?", "field": "courses_offered"},
                {"question": "How many total seats are available and what is the category-wise distribution?", "field": "seats_available"},
                {"question": "What is the fee structure?", "field": "fee_structure"},
                {"question": "Is hostel facility available for boys and girls?", "field": "hostel_facilities"},
                {"question": "What are the eligibility criteria and entrance exams required?", "field": "eligibility_criteria"}
            ]
            
            results = {}
            
            # Create context by combining text and table data
            context = text + "\n\n"
            for i, table in enumerate(tables):
                if "raw_text" in table:
                    context += f"Table {i+1}:\n{table['raw_text']}\n\n"
            
            # Use asyncio to ask multiple questions concurrently
            session = await self._get_session()
            endpoint = self.api_endpoints.get("answer_question")
            
            if not endpoint:
                logger.error("Question answering endpoint not configured")
                return {}
            
            async def ask_question(question, field):
                try:
                    async with session.post(
                        endpoint,
                        json={"context": context[:15000], "question": question},
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            answer = result.get("result", {}).get("answer", "")
                            return field, answer
                        else:
                            logger.warning(f"Question answering API returned error: {response.status}, {await response.text()}")
                            return field, ""
                except Exception as e:
                    logger.error(f"Error asking question: {e}")
                    return field, ""
            
            # Ask all questions concurrently
            tasks = [ask_question(q["question"], q["field"]) for q in questions]
            responses = await asyncio.gather(*tasks)
            
            # Process responses
            for field, answer in responses:
                if answer:
                    results[field] = answer
            
            # Add confidence score
            results["confidence_score"] = 0.85
            
            return results
        except Exception as e:
            logger.error(f"Error processing admission content with AI: {e}")
            return {}
    
    async def process_placement_content(self, text: str, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process placement content with AI assistance
        
        Args:
            text: Extracted text content
            tables: Extracted tables
            
        Returns:
            Enhanced placement data
        """
        try:
            # Create specific questions to ask the AI based on the content
            questions = [
                {"question": "What are the placement statistics including average package, highest package and placement percentage?", "field": "statistics"},
                {"question": "Which companies recruited from this college?", "field": "recruiters"},
                {"question": "What are the historical placement records for previous years?", "field": "historical_data"},
                {"question": "How many students went for higher studies, abroad studies or founded startups?", "field": "alternative_paths"},
                {"question": "What internship opportunities are available?", "field": "internships"},
                {"question": "What are the different recruitment types (on-campus, off-campus, pool campus)?", "field": "recruitment_types"}
            ]
            
            results = {}
            
            # Create context by combining text and table data
            context = text + "\n\n"
            for i, table in enumerate(tables):
                if "raw_text" in table:
                    context += f"Table {i+1}:\n{table['raw_text']}\n\n"
            
            # Use asyncio to ask multiple questions concurrently
            session = await self._get_session()
            endpoint = self.api_endpoints.get("answer_question")
            
            if not endpoint:
                logger.error("Question answering endpoint not configured")
                return {}
            
            async def ask_question(question, field):
                try:
                    async with session.post(
                        endpoint,
                        json={"context": context[:15000], "question": question},
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            answer = result.get("result", {}).get("answer", "")
                            return field, answer
                        else:
                            logger.warning(f"Question answering API returned error: {response.status}, {await response.text()}")
                            return field, ""
                except Exception as e:
                    logger.error(f"Error asking question: {e}")
                    return field, ""
            
            # Ask all questions concurrently
            tasks = [ask_question(q["question"], q["field"]) for q in questions]
            responses = await asyncio.gather(*tasks)
            
            # Process responses
            for field, answer in responses:
                if answer:
                    results[field] = answer
            
            # Add confidence score
            results["confidence_score"] = 0.85
            
            return results
        except Exception as e:
            logger.error(f"Error processing placement content with AI: {e}")
            return {}
    
    async def process_table(self, table_html: str, table_id: str, college_name: str) -> Dict[str, Any]:
        """
        Process a table with AI
        
        Args:
            table_html: HTML of the table
            table_id: ID of the table in storage
            college_name: Name of the college
            
        Returns:
            Processed table data
        """
        try:
            # First, determine what kind of information this table contains
            classification = self.classify_content(table_html)
            
            # Default is a general table
            table_type = classification.get("class", "general") if classification else "general"
            
            processed_data = {
                "college_name": college_name,
                "raw_data_id": table_id,
                "table_type": table_type,
                "structured_data": {},
                "processing_date": datetime.now(),
                "confidence_score": classification.get("confidence", 0.6) if classification else 0.6
            }
            
            # Based on the table type, ask specific questions
            questions = []
            
            if table_type == "admission":
                questions = [
                    {"question": "What courses are listed in this table?", "field": "courses"},
                    {"question": "What are the seat numbers or capacity mentioned in this table?", "field": "seats"},
                    {"question": "What fees are mentioned in this table?", "field": "fees"},
                    {"question": "Are there any important dates mentioned?", "field": "dates"}
                ]
            elif table_type == "placement":
                questions = [
                    {"question": "What placement statistics are shown in this table?", "field": "statistics"},
                    {"question": "Which companies or recruiters are listed?", "field": "companies"},
                    {"question": "Is this showing historical placement data for different years?", "field": "historical"}
                ]
            
            # Context for question answering
            context = f"Table from {college_name} website:\n{table_html}"
            
            # Use asyncio to ask multiple questions concurrently
            session = await self._get_session()
            endpoint = self.api_endpoints.get("answer_question")
            
            if not endpoint:
                logger.error("Question answering endpoint not configured")
                return processed_data
            
            async def ask_question(question, field):
                try:
                    async with session.post(
                        endpoint,
                        json={"context": context[:15000], "question": question},
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            answer = result.get("result", {}).get("answer", "")
                            return field, answer
                        else:
                            logger.warning(f"Question answering API returned error: {response.status}, {await response.text()}")
                            return field, ""
                except Exception as e:
                    logger.error(f"Error asking question: {e}")
                    return field, ""
            
            # Ask all questions concurrently
            tasks = [ask_question(q["question"], q["field"]) for q in questions]
            responses = await asyncio.gather(*tasks)
            
            # Process responses
            for field, answer in responses:
                if answer:
                    processed_data["structured_data"][field] = answer
            
            return processed_data
        except Exception as e:
            logger.error(f"Error processing table: {e}")
            return {
                "college_name": college_name,
                "raw_data_id": table_id,
                "table_type": "unknown",
                "structured_data": {},
                "processing_date": datetime.now(),
                "confidence_score": 0.3,
                "error": str(e)
            }
    
    async def process_pdf(self, pdf_path: str, pdf_id: str, college_name: str) -> Dict[str, Any]:
        """
        Process a PDF document with AI
        
        Args:
            pdf_path: Path to the PDF file
            pdf_id: ID of the PDF in storage
            college_name: Name of the college
            
        Returns:
            Processed PDF data
        """
        try:
            # For PDFs, we'd ideally extract the text first (implemented in PDFExtractor)
            # Here we'll simulate that we already have extracted text
            # In a real implementation, this would call the PDFExtractor first
            
            # For demo purposes, we'll simulate PDF text extraction and classification
            with open(pdf_path, 'rb') as f:
                # Get first 100KB to simulate text extraction
                simulated_text = f"PDF content from {college_name} with ID {pdf_id}"
            
            # Classify the content
            classification = self.classify_content(simulated_text)
            
            # Default is a general document
            document_type = classification.get("class", "general") if classification else "general"
            
            processed_data = {
                "college_name": college_name,
                "raw_data_id": pdf_id,
                "document_type": document_type,
                "extracted_data": {},
                "processing_date": datetime.now(),
                "confidence_score": classification.get("confidence", 0.6) if classification else 0.6
            }
            
            # Based on document type, ask specific questions
            questions = []
            
            if document_type == "admission":
                questions = [
                    {"question": "What are the application deadlines mentioned?", "field": "application_deadlines"},
                    {"question": "What courses are offered?", "field": "courses_offered"},
                    {"question": "What is the fee structure?", "field": "fee_structure"},
                    {"question": "What is the admission process?", "field": "admission_process"}
                ]
            elif document_type == "placement":
                questions = [
                    {"question": "What are the placement statistics?", "field": "placement_statistics"},
                    {"question": "Which companies have recruited?", "field": "recruiters"},
                    {"question": "What is the placement process?", "field": "placement_process"}
                ]
            
            # Simulate asking questions about the PDF content
            for q in questions:
                # In a real implementation, we would use the AI endpoints
                processed_data["extracted_data"][q["field"]] = f"Simulated AI answer for {q['question']}"
            
            return processed_data
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return {
                "college_name": college_name,
                "raw_data_id": pdf_id,
                "document_type": "unknown",
                "extracted_data": {},
                "processing_date": datetime.now(),
                "confidence_score": 0.3,
                "error": str(e)
            }
    
    async def process_image(self, image_path: str, image_id: str, college_name: str) -> Dict[str, Any]:
        """
        Process an image with AI
        
        Args:
            image_path: Path to the image file
            image_id: ID of the image in storage
            college_name: Name of the college
            
        Returns:
            Processed image data
        """
        try:
            # Run OCR on the image
            ocr_result = self.process_image_ocr(image_path)
            
            # Check if it's a chart
            chart_result = self.process_image_chart(image_path)
            
            # Detect tables in the image
            table_result = self.detect_tables_in_image(image_path)
            
            # Default image type based on results
            image_type = "photo"  # Default
            if chart_result and chart_result.get("chart_type", "unknown") != "unknown":
                image_type = "chart"
            elif table_result and len(table_result) > 0:
                image_type = "table"
            elif ocr_result and ocr_result.get("full_text", ""):
                words = ocr_result.get("full_text", "").split()
                if len(words) > 30:
                    image_type = "text"
            
            processed_data = {
                "college_name": college_name,
                "raw_data_id": image_id,
                "image_type": image_type,
                "extracted_data": {
                    "ocr_text": ocr_result.get("full_text", "") if ocr_result else "",
                    "chart_data": chart_result if chart_result else {},
                    "table_data": table_result if table_result else []
                },
                "processing_date": datetime.now(),
                "confidence_score": 0.7
            }
            
            return processed_data
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return {
                "college_name": college_name,
                "raw_data_id": image_id,
                "image_type": "unknown",
                "extracted_data": {},
                "processing_date": datetime.now(),
                "confidence_score": 0.3,
                "error": str(e)
            }