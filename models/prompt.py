import logging
from datetime import date, timedelta
from utils.db import get_db_context, dict_from_row
from config import Config

logger = logging.getLogger(__name__)

class Prompt:
    @staticmethod
    def get_responses(prompt_id):
        """Get all responses for a prompt"""
        try:
            with get_db_context() as conn:
                cursor = conn.execute('''
                    SELECT r.*, u.display_name, u.username
                    FROM responses r
                    JOIN users u ON r.user_id = u.id
                    WHERE r.prompt_id = ?
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
    def get_prompt_with_responses(prompt_id, user_id):
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
                    prompt_dict['responses'] = Prompt.get_responses(prompt_id)
                else:
                    prompt_dict['responses'] = []
                
                # Get response count
                cursor = conn.execute(
                    'SELECT COUNT(*) as count FROM responses WHERE prompt_id = ?',
                    (prompt_id,)
                )
                prompt_dict['response_count'] = cursor.fetchone()['count']
                
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
