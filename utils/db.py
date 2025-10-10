import sqlite3
import logging
from config import Config
from contextlib import contextmanager

logger = logging.getLogger(__name__)

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(Config.DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute('PRAGMA foreign_keys = ON')
    # Enable WAL mode for better concurrency
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

@contextmanager
def get_db_context():
    """Context manager for database connections"""
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        conn.close()

def init_db():
    """Initialize database with schema"""
    try:
        with get_db_context() as conn:
            # Read and execute schema
            with open('schema.sql', 'r') as f:
                conn.executescript(f.read())
            
            # Seed default prompts
            with open('seed_prompts.sql', 'r') as f:
                conn.executescript(f.read())
            
            logger.info("Database initialized successfully")
            return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return False

def dict_from_row(row):
    """Convert sqlite3.Row to dictionary"""
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}
