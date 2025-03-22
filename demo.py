#!/usr/bin/env python
"""
Demonstration script to showcase data extraction capabilities
"""
import asyncio
import logging
import argparse
import pprint

from storage.mongodb import MongoDBConnector
from extractors.admission import AdmissionExtractor
from extractors.placement import PlacementExtractor
from extractors.pdf import PDFExtractor
from extractors.image import ImageExtractor
from processors.ai_processor import AIProcessor
from config.settings import MONGODB_DB_NAME
from utils.helpers import setup_logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def show_extracted_data(college_name=None, data_type=None):
    """Show extracted data from MongoDB"""
    db = MongoDBConnector()
    
    try:
        # Build query
        query = {}
        if college_name:
            query["college_name"] = college_name
        
        # Get processed data
        processed_data = db.get_processed_data(query)
        
        print(f"\n{'='*80}")
        print(f"Found {len(processed_data)} processed data documents")
        print(f"{'='*80}\n")
        
        # Filter by data type if specified
        if data_type:
            processed_data = [data for data in processed_data 
                             if (data_type == "admission" and "admission_data" in data) or 
                                (data_type == "placement" and "placement_data" in data)]
            
            print(f"Filtered to {len(processed_data)} {data_type} documents\n")
        
        # Display data
        for i, data in enumerate(processed_data[:5], 1):  # Show first 5 only
            print(f"\nDocument {i}/{min(5, len(processed_data))}:")
            print(f"College: {data.get('college_name')}")
            print(f"Last Updated: {data.get('last_updated')}")
            print(f"Confidence: {data.get('confidence_score')}")
            
            # Show specific data based on type
            if "admission_data" in data:
                print("\nAdmission Data:")
                admission_data = data["admission_data"]
                
                # Show deadlines
                if "application_deadlines" in admission_data and admission_data["application_deadlines"]:
                    print("\n  Application Deadlines:")
                    for deadline in admission_data["application_deadlines"][:3]:  # First 3
                        print(f"  - {deadline.get('date_str')} ({deadline.get('event_type')})")
                
                # Show courses
                if "courses_offered" in admission_data and admission_data["courses_offered"]:
                    print("\n  Courses Offered:")
                    for course in admission_data["courses_offered"][:3]:  # First 3
                        print(f"  - {course.get('name')}")
                
                # Show seats
                if "seats_available" in admission_data:
                    seats = admission_data["seats_available"]
                    print("\n  Seats:")
                    print(f"  - Total: {seats.get('total')}")
                    if "category_wise" in seats and seats["category_wise"]:
                        print("  - Categories:")
                        for category, count in list(seats["category_wise"].items())[:3]:  # First 3
                            print(f"    * {category}: {count}")
                
                # Show fees
                if "fee_structure" in admission_data:
                    fees = admission_data["fee_structure"]
                    print("\n  Fee Structure:")
                    if "course_wise" in fees and fees["course_wise"]:
                        print("  - Course-wise Fees:")
                        for course, fee in list(fees["course_wise"].items())[:3]:  # First 3
                            print(f"    * {course}: {fee}")
                
                # Show hostel
                if "hostel_facilities" in admission_data:
                    hostel = admission_data["hostel_facilities"]
                    print("\n  Hostel Facilities:")
                    print(f"  - Boys Hostel: {hostel.get('boys_hostel')}")
                    print(f"  - Girls Hostel: {hostel.get('girls_hostel')}")
                    print(f"  - Hostel Fee: {hostel.get('hostel_fee')}")
                
                # Show eligibility
                if "eligibility_criteria" in admission_data:
                    eligibility = admission_data["eligibility_criteria"]
                    print("\n  Eligibility:")
                    print(f"  - Academic Requirements: {eligibility.get('academic_requirements')}")
                    if "entrance_exams" in eligibility and eligibility["entrance_exams"]:
                        print("  - Entrance Exams:")
                        for exam in eligibility["entrance_exams"]:
                            print(f"    * {exam}")
            
            # Show placement data
            elif "placement_data" in data:
                print("\nPlacement Data:")
                placement_data = data["placement_data"]
                
                # Show statistics
                if "statistics" in placement_data:
                    stats = placement_data["statistics"]
                    print("\n  Placement Statistics:")
                    print(f"  - Average Package: {stats.get('avg_package')}")
                    print(f"  - Highest Package: {stats.get('highest_package')}")
                    print(f"  - Placement %: {stats.get('placement_percentage')}%")
                    print(f"  - Students Placed: {stats.get('students_placed_count')}/{stats.get('total_students')}")
                
                # Show recruiters
                if "recruiters" in placement_data:
                    recruiters = placement_data["recruiters"]
                    print("\n  Recruiters:")
                    print(f"  - Total Companies: {recruiters.get('total_companies_visited')}")
                    if "top_companies" in recruiters and recruiters["top_companies"]:
                        print("  - Top Companies:")
                        for company in recruiters["top_companies"][:5]:  # First 5
                            print(f"    * {company}")
                
                # Show historical data
                if "historical_data" in placement_data and "year_wise" in placement_data["historical_data"]:
                    historical = placement_data["historical_data"]["year_wise"]
                    if historical:
                        print("\n  Historical Data:")
                        for year, data in list(historical.items())[:3]:  # First 3 years
                            print(f"  - {year}: {data}")
                
                # Show internships
                if "internships" in placement_data:
                    internships = placement_data["internships"]
                    print("\n  Internships:")
                    print(f"  - Count: {internships.get('count')}")
                    print(f"  - Percentage: {internships.get('percentage')}%")
                    if "companies" in internships and internships["companies"]:
                        print("  - Companies:")
                        for company in internships["companies"][:3]:  # First 3
                            print(f"    * {company}")
            
            print("\n" + "-"*80)
    
    finally:
        db.close()

async def demo_extraction(url=None, college_name="Demo College"):
    """Demonstrate extraction capabilities with a given URL"""
    if not url:
        print("Please provide a URL to demonstrate extraction")
        return
    
    # Initialize components
    ai_processor = AIProcessor()
    
    try:
        # Initialize crawler and navigate to URL
        from crawler.crawler import CollegeCrawler
        
        print(f"\n{'='*80}")
        print(f"Demonstrating extraction from: {url}")
        print(f"{'='*80}\n")
        
        crawler = CollegeCrawler(use_browser=True)
        await crawler.init_browser()
        
        # Navigate to URL
        print(f"Navigating to URL...")
        page_data = await crawler.browser_manager.navigate(url)
        
        if not page_data['success']:
            print(f"Failed to navigate to URL: {url}")
            return
        
        print(f"Successfully loaded page: {page_data['url']}")
        
        # Determine page type
        page_type = crawler._determine_page_type(page_data['content'])
        print(f"Detected page type: {page_type}")
        
        # Extract content
        content = crawler._extract_main_content(page_data['content'])
        print(f"Extracted {len(content)} characters of content")
        
        # Process based on page type
        if page_type == "admission":
            print("\nProcessing as admission page...")
            admission_extractor = AdmissionExtractor(ai_processor)
            processed_data = admission_extractor.extract_admission_data(content, college_name)
            
            print("\nExtracted Admission Data:")
            pprint.pprint(processed_data["admission_data"])
            
        elif page_type == "placement":
            print("\nProcessing as placement page...")
            placement_extractor = PlacementExtractor(ai_processor)
            processed_data = placement_extractor.extract_placement_data(content, college_name)
            
            print("\nExtracted Placement Data:")
            pprint.pprint(processed_data["placement_data"])
        
        # Extract tables
        from extractors.base import BaseExtractor
        base_extractor = BaseExtractor()
        tables = base_extractor.extract_tables(page_data['content'])
        
        if tables:
            print(f"\nFound {len(tables)} tables on the page")
            for i, table in enumerate(tables[:2], 1):  # Show first 2 tables
                print(f"\nTable {i} Headers: {table.get('headers')}")
                print(f"Table {i} Rows: {len(table.get('rows', []))}")
                if table.get('rows'):
                    print(f"First row: {table['rows'][0]}")
        
        print("\nExtraction demo completed")
        
    except Exception as e:
        logger.error(f"Error in demo: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close browser and other resources
        if 'crawler' in locals():
            await crawler.close()
        await ai_processor.close()

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="College Data Extraction Demo")
    parser.add_argument('--view', action='store_true', help='View extracted data in MongoDB')
    parser.add_argument('--college', type=str, help='College name to filter')
    parser.add_argument('--type', choices=['admission', 'placement'], help='Data type to filter')
    parser.add_argument('--url', type=str, help='URL to demonstrate extraction on')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging("INFO")
    
    print(f"\nCollege Website Data Extraction System Demo")
    print(f"MongoDB Database: {MONGODB_DB_NAME}\n")
    
    if args.view:
        await show_extracted_data(args.college, args.type)
    elif args.url:
        await demo_extraction(args.url, args.college or "Demo College")
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())