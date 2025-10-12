import logging
from datetime import date, datetime
from utils.db import get_db_context, dict_from_row
from config import Config

logger = logging.getLogger(__name__)

class Prompt:
    @staticmethod
    def get_responses(prompt_id, table_id):
        """Get all responses for a prompt with table-specific display names"""
        try:
            with get_db_context() as conn:
                cursor = conn.execute('''
                    SELECT r.*, tm.display_name, u.username
                    FROM responses r
                    JOIN users u ON r.user_id = u.id
                    JOIN table_members tm ON r.user_id = tm.user_id 
                    JOIN prompts p ON r.prompt_id = p.id
                    WHERE r.prompt_id = ? AND tm.table_id = p.table_id
                    ORDER BY r.created_at ASC
                ''', (prompt_id,))
                
                responses = cursor.fetchall()
                return [dict_from_row(r) for r in responses]
        except Exception as e:
            logger.error(f"Error getting responses: {str(e)}")
            return []

    @staticmethod
    def user_has_responded(prompt_id, user_id):
        """Check if user has responded to prompt"""
        try:
            with get_db_context() as conn:
                cursor = conn.execute('''
                    SELECT id FROM responses 
                    WHERE prompt_id = ? AND user_id = ?
                ''', (prompt_id, user_id))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking response: {str(e)}")
            return False

    @staticmethod
    def submit_response(prompt_id, user_id, response_text):
        """Submit a response to a prompt"""
        try:
            # Validate length
            if len(response_text) > Config.RESPONSE_MAX_LENGTH:
                return False, f"Response too long (max {Config.RESPONSE_MAX_LENGTH} characters)"
            
            if len(response_text.strip()) == 0:
                return False, "Response cannot be empty"
            
            with get_db_context() as conn:
                # Check if already responded
                cursor = conn.execute('''
                    SELECT id FROM responses 
                    WHERE prompt_id = ? AND user_id = ?
                ''', (prompt_id, user_id))
                
                if cursor.fetchone():
                    return False, "You've already responded to this prompt"
                
                # Insert response
                conn.execute('''
                    INSERT INTO responses (prompt_id, user_id, response_text)
                    VALUES (?, ?, ?)
                ''', (prompt_id, user_id, response_text.strip()))
                
                logger.info(f"User {user_id} responded to prompt {prompt_id}")
                return True, "Response submitted successfully"
        except Exception as e:
            logger.error(f"Error submitting response: {str(e)}")
            return False, "Error submitting response"

    @staticmethod
    def edit_response(prompt_id, user_id, response_text, table_id):
        """Edit an existing response (only if prompt is still active)"""
        try:
            # Validate length
            if len(response_text) > Config.RESPONSE_MAX_LENGTH:
                return False, f"Response too long (max {Config.RESPONSE_MAX_LENGTH} characters)"
            
            if len(response_text.strip()) == 0:
                return False, "Response cannot be empty"
            
            with get_db_context() as conn:
                # Get prompt info
                cursor = conn.execute('''
                    SELECT p.prompt_date, t.prompt_time 
                    FROM prompts p
                    JOIN tables t ON p.table_id = t.id
                    WHERE p.id = ?
                ''', (prompt_id,))
                
                prompt = cursor.fetchone()
                if not prompt:
                    return False, "Prompt not found"
                
                # Check if prompt is still active
                prompt_date = datetime.strptime(prompt['prompt_date'], '%Y-%m-%d').date()
                prompt_time = datetime.strptime(prompt['prompt_time'], '%H:%M').time()
                
                now = datetime.now()
                today = now.date()
                current_time = now.time()
                
                # Determine if we're still in the same prompt period
                if today == prompt_date:
                    # Same day, check if we've passed the prompt time yet
                    if current_time < prompt_time:
                        # We haven't reached the prompt time yet, so this is still yesterday's prompt
                        is_active = False
                    else:
                        # We've passed the prompt time, so this is today's active prompt
                        is_active = True
                elif today > prompt_date:
                    # Check if we're before today's prompt time
                    next_day = prompt_date
                    while next_day < today:
                        next_day = date.fromordinal(next_day.toordinal() + 1)
                    
                    if today == next_day and current_time < prompt_time:
                        # We're on the next day but before the prompt time
                        is_active = True
                    else:
                        is_active = False
                else:
                    is_active = False
                
                if not is_active:
                    return False, "Cannot edit responses from previous days"
                
                # Update response
                conn.execute('''
                    UPDATE responses 
                    SET response_text = ?, edited_at = CURRENT_TIMESTAMP
                    WHERE prompt_id = ? AND user_id = ?
                ''', (response_text.strip(), prompt_id, user_id))
                
                logger.info(f"User {user_id} edited response to prompt {prompt_id}")
                return True, "Response updated successfully"
        except Exception as e:
            logger.error(f"Error editing response: {str(e)}")
            return False, "Error editing response"

    @staticmethod
    def get_prompt_with_responses(prompt_id, user_id, table_id):
        """Get prompt with responses (only if user has responded)"""
        try:
            with get_db_context() as conn:
                # Get prompt
                cursor = conn.execute('SELECT * FROM prompts WHERE id = ?', (prompt_id,))
                prompt = cursor.fetchone()
                
                if not prompt:
                    return None
                
                prompt_dict = dict_from_row(prompt)
                
                # Check if user has responded
                user_responded = Prompt.user_has_responded(prompt_id, user_id)
                prompt_dict['user_has_responded'] = user_responded
                
                # Get responses only if user has responded
                if user_responded:
                    prompt_dict['responses'] = Prompt.get_responses(prompt_id, table_id)
                else:
                    prompt_dict['responses'] = []
                
                # Get response count
                cursor = conn.execute(
                    'SELECT COUNT(*) as count FROM responses WHERE prompt_id = ?',
                    (prompt_id,)
                )
                prompt_dict['response_count'] = cursor.fetchone()['count']
                
                # Check if prompt is still editable
                prompt_dict['is_editable'] = Prompt.is_prompt_active(prompt_dict['prompt_date'], prompt_dict['table_id'])
                
                return prompt_dict
        except Exception as e:
            logger.error(f"Error getting prompt with responses: {str(e)}")
            return None

    @staticmethod
    def get_user_response(prompt_id, user_id):
        """Get user's response to a prompt"""
        try:
            with get_db_context() as conn:
                cursor = conn.execute('''
                    SELECT * FROM responses 
                    WHERE prompt_id = ? AND user_id = ?
                ''', (prompt_id, user_id))
                
                response = cursor.fetchone()
                return dict_from_row(response) if response else None
        except Exception as e:
            logger.error(f"Error getting user response: {str(e)}")
            return None

    @staticmethod
    def is_prompt_active(prompt_date_str, table_id):
        """Check if a prompt is still active (editable)"""
        try:
            with get_db_context() as conn:
                cursor = conn.execute('SELECT prompt_time FROM tables WHERE id = ?', (table_id,))
                table = cursor.fetchone()
                
                if not table:
                    return False
                
                prompt_date = datetime.strptime(prompt_date_str, '%Y-%m-%d').date()
                prompt_time = datetime.strptime(table['prompt_time'], '%H:%M').time()
                
                now = datetime.now()
                today = now.date()
                current_time = now.time()
                
                # Check if we're in the same prompt period
                if today == prompt_date:
                    return current_time >= prompt_time
                elif today > prompt_date:
                    # Check if we're still before today's prompt time
                    days_diff = (today - prompt_date).days
                    if days_diff == 1 and current_time < prompt_time:
                        return True
                    return False
                else:
                    return False
        except Exception as e:
            logger.error(f"Error checking if prompt is active: {str(e)}")
            return False
