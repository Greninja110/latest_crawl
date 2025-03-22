"""
Helper utilities for the crawler system
"""
import logging
import os
import re
import hashlib
import random
import time
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

def setup_logging(log_level: str, log_file: str = None) -> None:
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level (INFO, DEBUG, etc.)
        log_file: Optional log file path
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if log file specified
    if log_file:
        try:
            # Create directory for log file if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            logger.error(f"Error setting up log file: {e}")

def generate_filename(url: str, prefix: str = "", suffix: str = "") -> str:
    """
    Generate a filename from a URL
    
    Args:
        url: URL to generate filename from
        prefix: Optional prefix for the filename
        suffix: Optional suffix for the filename
        
    Returns:
        Generated filename
    """
    # Parse URL to get the path
    parsed_url = urlparse(url)
    path = parsed_url.path
    
    # Get the last part of the path as the base filename
    base_name = os.path.basename(path)
    
    # If the basename is empty, use the netloc (domain)
    if not base_name:
        base_name = parsed_url.netloc.replace(".", "_")
    
    # Remove invalid characters
    base_name = re.sub(r'[\\/*?:"<>|]', "_", base_name)
    
    # If still no valid name, create a hash
    if not base_name or base_name.isspace():
        base_name = hashlib.md5(url.encode()).hexdigest()[:12]
    
    # Add prefix and suffix
    final_name = prefix
    if prefix and not prefix.endswith("_"):
        final_name += "_"
    
    final_name += base_name
    
    if suffix:
        if not suffix.startswith("_"):
            final_name += "_"
        final_name += suffix
    
    return final_name

def get_file_extension(url: str, default: str = "html") -> str:
    """
    Get file extension from URL
    
    Args:
        url: URL to get extension from
        default: Default extension if none found
        
    Returns:
        File extension
    """
    path = urlparse(url).path
    ext = os.path.splitext(path)[1]
    
    if ext:
        # Remove dot and return lowercase extension
        return ext[1:].lower()
    else:
        return default

def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid
    
    Args:
        url: URL to check
        
    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def clean_text(text: str) -> str:
    """
    Clean and normalize text
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Replace multiple whitespace with single space
    cleaned = re.sub(r'\s+', ' ', text)
    
    # Remove non-printable characters
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', cleaned)
    
    # Trim whitespace
    cleaned = cleaned.strip()
    
    return cleaned

def extract_numbers(text: str) -> List[float]:
    """
    Extract numbers from text
    
    Args:
        text: Text to extract numbers from
        
    Returns:
        List of extracted numbers
    """
    pattern = r'[-+]?\d*\.\d+|\d+'
    matches = re.findall(pattern, text)
    
    numbers = []
    for match in matches:
        try:
            num = float(match)
            numbers.append(num)
        except:
            pass
    
    return numbers

def get_domain(url: str) -> str:
    """
    Extract domain from URL
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain name
    """
    try:
        return urlparse(url).netloc
    except:
        return ""

def is_same_domain(url1: str, url2: str) -> bool:
    """
    Check if two URLs have the same domain
    
    Args:
        url1: First URL
        url2: Second URL
        
    Returns:
        True if same domain, False otherwise
    """
    return get_domain(url1) == get_domain(url2)

def is_relative_to_domain(base_domain: str, url: str) -> bool:
    """
    Check if URL is relative to the given base domain
    
    Args:
        base_domain: Base domain to check against
        url: URL to check
        
    Returns:
        True if URL is relative to the domain, False otherwise
    """
    url_domain = get_domain(url)
    
    # If the URL has no domain, it's relative
    if not url_domain:
        return True
    
    # Otherwise, check if domains match
    return url_domain == base_domain or url_domain.endswith("." + base_domain)

def url_to_filename(url: str, extension: str = "html") -> str:
    """
    Convert URL to a safe filename
    
    Args:
        url: URL to convert
        extension: File extension to use
        
    Returns:
        Safe filename
    """
    # Remove protocol and query parameters
    url_parts = urlparse(url)
    clean_url = url_parts.netloc + url_parts.path
    
    # Replace invalid characters
    clean_url = re.sub(r'[\\/*?:"<>|]', "_", clean_url)
    
    # Replace dots and slashes
    clean_url = clean_url.replace(".", "_").replace("/", "_")
    
    # If filename is too long, hash part of it
    if len(clean_url) > 100:
        hash_part = hashlib.md5(url.encode()).hexdigest()[:10]
        clean_url = clean_url[:90] + "_" + hash_part
    
    # Add extension if specified
    if extension:
        if not extension.startswith("."):
            extension = "." + extension
        clean_url += extension
    
    return clean_url

def format_datetime(dt: datetime = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime to string
    
    Args:
        dt: Datetime to format (uses current time if None)
        format_str: Format string
        
    Returns:
        Formatted datetime string
    """
    if dt is None:
        dt = datetime.now()
    
    return dt.strftime(format_str)

def extract_date_from_string(date_str: str) -> Optional[datetime]:
    """
    Extract date from string
    
    Args:
        date_str: String containing date
        
    Returns:
        Extracted datetime or None if not found
    """
    # Common date formats to try
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d.%m.%Y",
        "%m.%d.%Y",
        "%B %d, %Y",
        "%d %B, %Y",
        "%d %b %Y",
        "%b %d, %Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            pass
    
    return None

def human_readable_size(size_bytes: int) -> str:
    """
    Convert size in bytes to human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human readable size string
    """
    if size_bytes == 0:
        return "0B"
    
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = 0
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.2f} {size_name[i]}"

def load_json_file(file_path: str) -> Any:
    """
    Load JSON data from file
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Loaded JSON data or None if error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return None

def save_json_file(data: Any, file_path: str) -> bool:
    """
    Save data to JSON file
    
    Args:
        data: Data to save
        file_path: Path to save to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        return False

def extract_email(text: str) -> List[str]:
    """
    Extract email addresses from text
    
    Args:
        text: Text to extract from
        
    Returns:
        List of extracted email addresses
    """
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(pattern, text)

def extract_phone(text: str) -> List[str]:
    """
    Extract phone numbers from text
    
    Args:
        text: Text to extract from
        
    Returns:
        List of extracted phone numbers
    """
    # Pattern for Indian phone numbers
    pattern = r'(?:\+91|0)?[6-9]\d{9}'
    return re.findall(pattern, text)

def random_wait(min_seconds: float = 3.0, max_seconds: float = 10.0) -> None:
    """
    Wait for a random amount of time
    
    Args:
        min_seconds: Minimum wait time in seconds
        max_seconds: Maximum wait time in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"Waiting for {delay:.2f} seconds")
    time.sleep(delay)

def get_content_type(url: str) -> Optional[str]:
    """
    Get content type of a URL
    
    Args:
        url: URL to check
        
    Returns:
        Content type string or None if error
    """
    try:
        # Send HEAD request to avoid downloading the full content
        response = requests.head(url, timeout=10)
        return response.headers.get('Content-Type')
    except Exception as e:
        logger.debug(f"Error getting content type for {url}: {e}")
        return None

def normalize_url(url: str, base_url: str = None) -> str:
    """
    Normalize a URL
    
    Args:
        url: URL to normalize
        base_url: Base URL for resolving relative URLs
        
    Returns:
        Normalized URL
    """
    # Remove fragments
    url = url.split('#')[0]
    
    # Resolve relative URLs
    if base_url and not bool(urlparse(url).netloc):
        url = urljoin(base_url, url)
    
    # Canonical form
    parsed = urlparse(url)
    
    # Convert scheme and netloc to lowercase
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    
    # Rebuild URL
    return f"{scheme}://{netloc}{parsed.path}{parsed.params}"

def setup_logging(log_level: str, log_file: str = None) -> None:
    """
    Setup logging configuration with enhanced formatting and file output
    
    Args:
        log_level: Logging level (INFO, DEBUG, etc.)
        log_file: Optional log file path
    """
    import logging
    import os
    import sys
    from datetime import datetime
    
    try:
        import colorlog
        has_colorlog = True
    except ImportError:
        has_colorlog = False
    
    # Convert string level to numeric
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    # Create logs directory if it doesn't exist and log_file is specified
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Add timestamp to log filename if not present
        if not any(c in log_file for c in ['%', '{']):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename, ext = os.path.splitext(log_file)
            log_file = f"{filename}_{timestamp}{ext}"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Define log format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Configure console handler with colors if available
    if has_colorlog:
        # Color mapping
        color_formatter = colorlog.ColoredFormatter(
            '%(log_color)s' + log_format,
            datefmt=date_format,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(color_formatter)
    else:
        formatter = logging.Formatter(log_format, datefmt=date_format)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
    
    root_logger.addHandler(console_handler)
    
    # Configure file handler if log file is specified
    if log_file:
        try:
            file_formatter = logging.Formatter(log_format, datefmt=date_format)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
            
            # Log the file location at startup
            root_logger.info(f"Log file created at: {os.path.abspath(log_file)}")
        except Exception as e:
            root_logger.error(f"Failed to create log file: {e}")
    
    # Log initial message
    root_logger.info(f"Logging initialized at {log_level} level")
    
    # Create custom logger for VS Code debug output
    vs_logger = logging.getLogger('vscode')
    vs_handler = logging.StreamHandler(sys.stdout)
    vs_handler.setFormatter(logging.Formatter('%(levelname)s [VS]: %(message)s'))
    vs_logger.addHandler(vs_handler)
    vs_logger.setLevel(numeric_level)
    
    # Add logging to uncaught exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Let KeyboardInterrupt pass through
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        root_logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception