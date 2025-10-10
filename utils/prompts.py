import logging
from datetime import datetime, date, time
from utils.db import get_db_context

logger = logging.getLogger(__name__)

def get_next_default_prompt(table_id):
    """Get the next default prompt for a table"""
    try:
        with get_db_context() as conn:
            # Get the last prompt index used for this table
            cursor = conn.execute('''
                SELECT dp.id 
                FROM prompts p
                JOIN default_prompts dp ON p.prompt_text = dp.prompt_text
                WHERE p.table_id = ? AND p.is_custom = 0
                ORDER BY p.created_at DESC
                LIMIT 1
            ''', (table_id,))
            
            last_prompt = cursor.fetchone()
            last_id = last_prompt['id'] if last_prompt else 0
            
            # Get next prompt (circular)
            cursor = conn.execute('''
                SELECT * FROM default_prompts 
                WHERE id > ?
                ORDER BY id ASC
                LIMIT 1
            ''', (last_id,))
            
            next_prompt = cursor.fetchone()
            
            # If no next prompt, wrap around to first
            if not next_prompt:
                cursor = conn.execute('''
                    SELECT * FROM default_prompts 
                    ORDER BY id ASC
                    LIMIT 1
                ''')
                next_prompt = cursor.fetchone()
            
            return next_prompt['prompt_text'] if next_prompt else "What's on your mind today?"
    except Exception as e:
        logger.error(f"Error getting next default prompt: {str(e)}")
        return "What's on your mind today?"

def create_daily_prompt(table_id, prompt_date=None):
    """Create a daily prompt for a table"""
    if prompt_date is None:
        prompt_date = date.today()
    
    try:
        with get_db_context() as conn:
            # Check if prompt already exists
            cursor = conn.execute('''
                SELECT id FROM prompts 
                WHERE table_id = ? AND prompt_date = ?
            ''', (table_id, prompt_date))
            
            if cursor.fetchone():
                logger.info(f"Prompt already exists for table {table_id} on {prompt_date}")
                return True
            
            # Get next default prompt
            prompt_text = get_next_default_prompt(table_id)
            
            # Create prompt
            conn.execute('''
                INSERT INTO prompts (table_id, prompt_text, prompt_date, is_custom)
                VALUES (?, ?, ?, 0)
            ''', (table_id, prompt_text, prompt_date))
            
            logger.info(f"Created prompt for table {table_id} on {prompt_date}")
            return True
    except Exception as e:
        logger.error(f"Error creating daily prompt: {str(e)}")
        return False

def create_prompts_for_all_tables():
    """Create today's prompts for all tables (for cron job)"""
    try:
        with get_db_context() as conn:
            cursor = conn.execute('SELECT id FROM tables')
            tables = cursor.fetchall()
            
            success_count = 0
            for table in tables:
                if create_daily_prompt(table['id']):
                    success_count += 1
            
            logger.info(f"Created prompts for {success_count}/{len(tables)} tables")
            return True
    except Exception as e:
        logger.error(f"Error creating prompts for all tables: {str(e)}")
        return False

def get_prompt_for_date(table_id, prompt_date):
    """Get prompt for a specific date"""
    try:
        with get_db_context() as conn:
            cursor = conn.execute('''
                SELECT * FROM prompts 
                WHERE table_id = ? AND prompt_date = ?
            ''', (table_id, prompt_date))
            
            prompt = cursor.fetchone()
            
            if not prompt:
                return None
            
            return {
                'id': prompt['id'],
                'prompt_text': prompt['prompt_text'],
                'prompt_date': prompt['prompt_date'],
                'is_custom': bool(prompt['is_custom'])
            }
    except Exception as e:
        logger.error(f"Error getting prompt for date: {str(e)}")
        return None

def ensure_prompt_exists(table_id, prompt_date):
    """Ensure a prompt exists for the given date, create if missing"""
    prompt = get_prompt_for_date(table_id, prompt_date)
    if not prompt:
        create_daily_prompt(table_id, prompt_date)
        prompt = get_prompt_for_date(table_id, prompt_date)
    return prompt
