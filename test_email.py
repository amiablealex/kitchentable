#!/usr/bin/env python3
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from config import Config
from utils.email import test_email_config

def main():
    print("=" * 60)
    print("Kitchen Table - Email Configuration Test")
    print("=" * 60)
    print()
    
    # Debug: show what we loaded
    print("Loaded from .env:")
    print(f"  SMTP_ENABLED: {os.environ.get('SMTP_ENABLED')}")
    print(f"  SMTP_SERVER: {os.environ.get('SMTP_SERVER')}")
    print(f"  SMTP_USERNAME: {os.environ.get('SMTP_USERNAME')}")
    print()
    
    # Check if SMTP is enabled
    print(f"Config.SMTP_ENABLED = {Config.SMTP_ENABLED}")
    print(f"Type: {type(Config.SMTP_ENABLED)}")
    print()
    
    if not Config.SMTP_ENABLED:
        print("❌ SMTP is DISABLED in your configuration")
        print()
        print("The .env file was loaded, but SMTP_ENABLED evaluated to False")
        print("This might be a string comparison issue.")
        print()
        return 1
    
    print("✓ SMTP is enabled")
    print()
    print("Configuration:")
    print(f"  Server: {Config.SMTP_SERVER}:{Config.SMTP_PORT}")
    print(f"  Username: {Config.SMTP_USERNAME}")
    print(f"  From Email: {Config.SMTP_FROM_EMAIL}")
    print(f"  App URL: {Config.APP_URL}")
    print()
    
    # Test connection
    print("Testing SMTP connection...")
    success, message = test_email_config()
    
    if success:
        print(f"✓ {message}")
        print()
        print("=" * 60)
        print("Email configuration is working correctly! ✓")
        print("=" * 60)
        return 0
    else:
        print(f"❌ {message}")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())
