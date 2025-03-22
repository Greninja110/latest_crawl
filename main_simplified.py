"""
Simplified main script for the college website data extraction system
"""
import os
import sys
import logging
import asyncio
import argparse
from datetime import datetime
import traceback
from typing import Dict, List, Any, Optional

from config.settings import LOG_LEVEL, LOG_FILE
from config.targets import TARGET_COLLEGES
from crawler.simplified_crawler import SimplifiedCrawler
from utils.helpers import setup_logging, format_datetime

logger = logging.getLogger(__name__)

async def crawl_college(college: Dict[str, Any]) -> None:
    """
    Crawl a specific college
    
    Args:
        college: College dictionary with name, URL, etc.
    """
    crawler = SimplifiedCrawler()
    
    try:
        logger.info(f"Starting crawl for {college['name']}")
        start_time = datetime.now()
        
        # Crawl the college
        await crawler.crawl_college(college)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Finished crawling {college['name']} in {duration:.2f} seconds")
    except Exception as e:
        logger.error(f"Error crawling {college['name']}: {e}")
        logger.error(traceback.format_exc())
    finally:
        await crawler.close()

async def process_crawled_data(college_name: str = None) -> None:
    """
    Process previously crawled data for a college
    
    Args:
        college_name: Name of the college to process (None for all)
    """
    from storage.mongodb import MongoDBConnector
    from extractors.admission import AdmissionExtractor
    from extractors.placement import PlacementExtractor
    
    db = MongoDBConnector()
    
    try:
        # Query to get raw data that hasn't been processed
        query = {}
        if college_name:
            query["college_name"] = college_name
        
        # Get raw data
        raw_data = db.get_raw_data(query)
        logger.info(f"Found {len(raw_data)} raw data documents to process")
        
        for data in raw_data:
            try:
                # Skip if already processed
                processed_query = {"raw_data_id": str(data["_id"])}
                if db.get_processed_data(processed_query):
                    continue
                
                logger.info(f"Processing {data['page_type']} data for {data['college_name']}")
                
                # Process based on page type
                if data['page_type'] == 'admission':
                    # Process admission data
                    admission_extractor = AdmissionExtractor()
                    processed_data = admission_extractor.extract_admission_data(
                        data['raw_content'], 
                        data['college_name']
                    )
                    
                    if processed_data:
                        processed_data["raw_data_id"] = str(data["_id"])
                        db.insert_processed_data(processed_data)
                        
                elif data['page_type'] == 'placement':
                    # Process placement data
                    placement_extractor = PlacementExtractor()
                    processed_data = placement_extractor.extract_placement_data(
                        data['raw_content'], 
                        data['college_name']
                    )
                    
                    if processed_data:
                        processed_data["raw_data_id"] = str(data["_id"])
                        db.insert_processed_data(processed_data)
                
                # Don't process too quickly
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing data for {data['college_name']}: {e}")
                logger.error(traceback.format_exc())
    
    except Exception as e:
        logger.error(f"Error in process_crawled_data: {e}")
        logger.error(traceback.format_exc())
    finally:
        db.close()

async def main() -> None:
    """Main execution function"""
    parser = argparse.ArgumentParser(description="College Website Data Extraction System")
    parser.add_argument('--college', type=str, help='Specific college to crawl (by name)')
    parser.add_argument('--list', action='store_true', help='List available target colleges')
    parser.add_argument('--process-only', action='store_true', help='Only process existing data, no crawling')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(LOG_LEVEL, LOG_FILE)
    
    logger.info(f"--- College Website Data Extraction System (Simplified) ---")
    logger.info(f"Started at: {format_datetime()}")
    
    # List colleges if requested
    if args.list:
        print("Available target colleges:")
        for i, college in enumerate(TARGET_COLLEGES, 1):
            print(f"{i}. {college['name']} - {college['base_url']}")
        return
    
    # Process-only mode
    if args.process_only:
        logger.info("Running in process-only mode (no crawling)")
        await process_crawled_data(args.college)
        return
    
    # Filter colleges by name if specified
    colleges_to_crawl = []
    if args.college:
        for college in TARGET_COLLEGES:
            if args.college.lower() in college['name'].lower():
                colleges_to_crawl.append(college)
        
        if not colleges_to_crawl:
            logger.error(f"No matching college found for: {args.college}")
            return
    else:
        colleges_to_crawl = TARGET_COLLEGES
    
    logger.info(f"Will crawl {len(colleges_to_crawl)} colleges")
    
    # Crawl each college sequentially
    for college in colleges_to_crawl:
        await crawl_college(college)
    
    # Process the crawled data
    logger.info("Crawling complete. Starting data processing...")
    await process_crawled_data(args.college)
    
    logger.info(f"All operations completed at: {format_datetime()}")

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 7):
        sys.exit("Python 3.7 or later is required.")
    
    # Run the main async function
    asyncio.run(main())