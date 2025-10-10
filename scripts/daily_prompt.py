#!/usr/bin/env python3
"""
Daily prompt generation script
Run this via cron to create daily prompts for all tables
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.prompts import create_prompts_for_all_tables
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if __name__ == '__main__':
    logging.info("Starting daily prompt generation...")
    success = create_prompts_for_all_tables()
    
    if success:
        logging.info("Daily prompt generation completed successfully")
        sys.exit(0)
    else:
        logging.error("Daily prompt generation failed")
        sys.exit(1)
