#!/usr/bin/env python
"""
Simple script to run the crawler with API health check bypass
"""
import os
import sys
import subprocess

# Set environment variable to bypass API health check
os.environ["FORCE_API_HEALTHY"] = "true"

# Forward all arguments to run_crawler_debug.py
args = sys.argv[1:]
cmd = ["python", "run_crawler_debug.py"] + args

print(f"Running command with API health check bypass: {' '.join(cmd)}")
try:
    subprocess.run(cmd, check=True)
except subprocess.CalledProcessError as e:
    print(f"Crawler failed with error code: {e.returncode}")
    sys.exit(1)
except KeyboardInterrupt:
    print("\nCrawler interrupted by user")
    sys.exit(130)