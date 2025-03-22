"""
Configuration settings for the college website crawler
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Hugging Face API Endpoints
HF_API_BASE_URL = "https://greninja253-web-crawl.hf.space"
HF_API_ENDPOINTS = {
    "extract_entities": f"{HF_API_BASE_URL}/extract/entities",
    "classify_document": f"{HF_API_BASE_URL}/classify/document",
    "answer_question": f"{HF_API_BASE_URL}/answer/question",
    "extract_ocr": f"{HF_API_BASE_URL}/extract/ocr",
    "detect_tables": f"{HF_API_BASE_URL}/detect/tables",
    "analyze_chart": f"{HF_API_BASE_URL}/analyze/chart",
    "process_batch": f"{HF_API_BASE_URL}/process/batch"
}

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "college_data")
MONGODB_RAW_COLLECTION = "raw_data"
MONGODB_PROCESSED_COLLECTION = "processed_data"

# Crawler Settings
MAX_PAGES_PER_COLLEGE = 50
MAX_DEPTH = 3
TIMEOUT = 30  # seconds
HEADLESS = True  # Run browser in headless mode

# Request Settings
REQUEST_TIMEOUT = 15  # seconds
MAX_RETRIES = 3
USER_AGENT_ROTATION = True

# Delay Settings (for anti-crawling measures)
MIN_DELAY = 3  # seconds
MAX_DELAY = 10  # seconds
RANDOM_DELAY = True

# Proxy Settings
USE_PROXIES = False
PROXY_ROTATION_FREQUENCY = 10  # Rotate after every 10 requests

# Log Settings
LOG_LEVEL = "INFO"
LOG_FILE = "crawler.log"

# Target Keywords
ADMISSION_KEYWORDS = [
    "admission", "admissions", "enroll", "apply", "application",
    "courses", "eligibility", "qualification", "fees", "hostel",
    "deadline", "dates", "seats", "capacity", "reservation"
]

PLACEMENT_KEYWORDS = [
    "placement", "placements", "career", "careers", "recruit",
    "recruitment", "jobs", "salary", "package", "companies", 
    "hiring", "internship", "internships", "company", "placed"
]

# File types to extract
ALLOWED_FILE_TYPES = [
    "pdf", "doc", "docx", "xls", "xlsx", "csv",
    "jpg", "jpeg", "png", "gif"
]

# Domain restrict to prevent crawler from going to external sites
DOMAIN_RESTRICT = True

# Content type classification
CONTENT_TYPES = {
    "text": ["text/html", "text/plain"],
    "pdf": ["application/pdf"],
    "doc": ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    "image": ["image/jpeg", "image/png", "image/gif", "image/webp"],
    "excel": ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
}