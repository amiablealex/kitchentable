import logging
from datetime import datetime, timedelta
from utils.db import get_db_context, dict_from_row
from utils.auth import hash_password, verify_password, generate_reset_token

logger = logging.getLogger(__name__)

class User:
    @staticmethod
    def create(username, email, password, display_name):
        """Create a new user"""
        try:
            password_hash = hash_password(password)
            
            with get_db_context() as conn:
                cursor = conn.execute('''
                    INSERT INTO users (username, email, password_hash, display_name)
                    VALUES (?, ?, ?, ?)
                ''', (username.lower(), email.lower(), password_hash, display_name))
                
                user_id = cursor.lastrowid
                logger.info(f"Created user: {username} (ID: {user_id})")
                return user_id
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        try:
            with get_db_context() as conn:
                cursor = conn.execute(
                    'SELECT * FROM users WHERE id = ?',
                    (user_id,)
                )
                user = cursor.fetchone()
                return dict_from_row(user) if user else None
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return None

    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        try:
            with get_db_context() as conn:
                cursor = conn.execute(
                    'SELECT * FROM users WHERE username = ?',
                    (username.lower(),)
                )
                user = cursor.fetchone()
                return dict_from_row(user) if user else None
        except Exception as e:
            logger.error(f"Error getting user by username: {str(e)}")
            return None

    @staticmethod
    def get_by_email(email):
        """Get user by email"""
        try:
            with get_db_context() as conn:
                cursor = conn.execute(
                    'SELECT * FROM users WHERE email = ?',
                    (email.lower(),)
                )
                user = cursor.fetchone()
                return dict_from_row(user) if user else None
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None

    @staticmethod
    def authenticate(username_or_email, password):
        """Authenticate user with username/email and password"""
        try:
            with get_db_context() as conn:
                cursor = conn.execute('''
                    SELECT * FROM users 
                    WHERE username = ? OR email = ?
                ''', (username_or_email.lower(), username_or_email.lower()))
                
                user = cursor.fetchone()
                
                if user and verify_password(password, user['password_hash']):
                    logger.info(f"User authenticated: {user['username']}")
                    return dict_from_row(user)
                
                logger.warning(f"Failed authentication attempt for: {username_or_email}")
                return None
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None

    @staticmethod
    def create_reset_token(email):
        """Create password reset token"""
        try:
            token = generate_reset_token()
            expires = datetime.utcnow() + timedelta(hours=1)
            
            with get_db_context() as conn:
                conn.execute('''
                    UPDATE users 
                    SET reset_token = ?, reset_token_expires = ?
                    WHERE email = ?
                ''', (token, expires, email.lower()))
                
                logger.info(f"Created reset token for: {email}")
                return token
        except Exception as e:
            logger.error(f"Error creating reset token: {str(e)}")
            return None

    @staticmethod
    def verify_reset_token(token):
        """Verify reset token and return user"""
        try:
            with get_db_context() as conn:
                cursor = conn.execute('''
                    SELECT * FROM users 
                    WHERE reset_token = ? AND reset_token_expires > ?
                ''', (token, datetime.utcnow()))
                
                user = cursor.fetchone()
                return dict_from_row(user) if user else None
        except Exception as e:
            logger.error(f"Error verifying reset token: {str(e)}")
            return None

    @staticmethod
    def reset_password(token, new_password):
        """Reset password with token"""
        try:
            user = User.verify_reset_token(token)
            if not user:
                return False
            
            password_hash = hash_password(new_password)
            
            with get_db_context() as conn:
                conn.execute('''
                    UPDATE users 
                    SET password_hash = ?, reset_token = NULL, reset_token_expires = NULL
                    WHERE id = ?
                ''', (password_hash, user['id']))
                
                logger.info(f"Password reset for user: {user['username']}")
                return True
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            return False
