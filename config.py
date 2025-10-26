import os
from datetime import timedelta

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-jwt-secret-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    
    # Database
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'kitchen_table.db'
    
    # Application
    MAX_CONTENT_LENGTH = 16 * 1024  # 16KB max request size
    TABLE_MIN_MEMBERS = 2
    TABLE_MAX_MEMBERS = 10
    RESPONSE_MAX_LENGTH = 500
    DEFAULT_PROMPT_TIME = '17:00'  # 5 PM
    APP_URL = os.environ.get('APP_URL') or 'http://localhost:5000'
    
    # Email Configuration (for password resets)
    SMTP_ENABLED = os.environ.get('SMTP_ENABLED', 'false').lower() == 'true'
    SMTP_SERVER = os.environ.get('SMTP_SERVER') or 'smtp.gmail.com'
    SMTP_PORT = int(os.environ.get('SMTP_PORT') or 587)
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')  # Your Gmail address
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')  # Gmail app password
    SMTP_FROM_EMAIL = os.environ.get('SMTP_FROM_EMAIL') or SMTP_USERNAME
    
    # Logging
    LOG_FILE = 'kitchen_table.log'
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
    # Rate Limiting
    LOGIN_RATE_LIMIT = 5  # attempts per minute
    SIGNUP_RATE_LIMIT = 3  # attempts per minute
