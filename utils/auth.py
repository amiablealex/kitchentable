import jwt
import bcrypt
import secrets
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from config import Config
from utils.db import get_db_context, dict_from_row

logger = logging.getLogger(__name__)

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_jwt_token(user_id):
    """Create JWT token for user"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + Config.JWT_ACCESS_TOKEN_EXPIRES,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')

def decode_jwt_token(token):
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token")
        return None

def get_current_user():
    """Get current user from JWT token"""
    token = request.cookies.get('auth_token')
    if not token:
        return None
    
    user_id = decode_jwt_token(token)
    if not user_id:
        return None
    
    try:
        with get_db_context() as conn:
            cursor = conn.execute(
                'SELECT * FROM users WHERE id = ?',
                (user_id,)
            )
            user = cursor.fetchone()
            
            if user:
                # Update last active
                conn.execute(
                    'UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE id = ?',
                    (user_id,)
                )
                return dict_from_row(user)
            return None
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return None

def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return jsonify({'error': 'Authentication required', 'redirect': '/login'}), 401
        return f(user, *args, **kwargs)
    return decorated_function

def generate_invite_code():
    """Generate a readable invite code"""
    # Use readable characters (avoid 0, O, 1, I, etc.)
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    code = ''.join(secrets.choice(chars) for _ in range(4))
    code += '-'
    code += ''.join(secrets.choice(chars) for _ in range(4))
    return code

def generate_reset_token():
    """Generate password reset token"""
    return secrets.token_urlsafe(32)

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username format"""
    import re
    # 3-20 chars, alphanumeric and underscore only
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None

def validate_password(password):
    """Validate password strength"""
    # At least 8 characters
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    return True, ""
