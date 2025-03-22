#!/usr/bin/env python
"""
Simple script to run the simplified crawler
"""
import os
import sys
import subprocess
import argparse

def main():
    """Main function to parse arguments and run crawler"""
    parser = argparse.ArgumentParser(description="College Data Crawler Runner")
    parser.add_argument('--college', type=str, help='College name to crawl')
    parser.add_argument('--process', action='store_true', help='Only process existing data')
    parser.add_argument('--list', action='store_true', help='List available colleges')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Build command
    cmd = ["python", "main_simplified.py"]
    
    if args.college:
        cmd.extend(["--college", args.college])
    
    if args.process:
        cmd.append("--process-only")
    
    if args.list:
        cmd.append("--list")
    
    if args.debug:
        # Set environment variable for debug logging
        os.environ["LOG_LEVEL"] = "DEBUG"
    
    # Run the command
    print(f"Running command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Crawler failed with error code: {e.returncode}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCrawler interrupted by user")
        sys.exit(130)

if __name__ == "__main__":
    main()  