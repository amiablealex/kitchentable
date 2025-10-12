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
    
    # Logging
    LOG_FILE = 'kitchen_table.log'
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
    # Rate Limiting
    LOGIN_RATE_LIMIT = 5  # attempts per minute
    SIGNUP_RATE_LIMIT = 3  # attempts per minute
