import logging
import os
from flask import Blueprint, request, jsonify, make_response, render_template
from models.user import User
from utils.auth import (
    create_jwt_token, validate_email, validate_username, 
    validate_password, get_current_user
)

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

# Check if we're in development mode
IS_DEVELOPMENT = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG') == '1'

def set_auth_cookie(response, token):
    """Set authentication cookie with appropriate security settings"""
    response.set_cookie(
        'auth_token',
        token,
        httponly=True,
        secure=not IS_DEVELOPMENT,  # Only use secure in production
        samesite='Lax',
        max_age=30*24*60*60  # 30 days
    )
    return response

@auth_bp.route('/signup', methods=['GET'])
def signup_page():
    """Signup page"""
    user = get_current_user()
    if user:
        return render_template('redirect.html', url='/table')
    return render_template('auth.html', mode='signup')

@auth_bp.route('/login', methods=['GET'])
def login_page():
    """Login page"""
    user = get_current_user()
    if user:
        return render_template('redirect.html', url='/table')
    return render_template('auth.html', mode='login')

@auth_bp.route('/forgot-password', methods=['GET'])
def forgot_password_page():
    """Forgot password page"""
    return render_template('auth.html', mode='forgot')

@auth_bp.route('/reset-password/<token>', methods=['GET'])
def reset_password_page(token):
    """Reset password page"""
    return render_template('auth.html', mode='reset', token=token)

@auth_bp.route('/api/auth/signup', methods=['POST'])
def signup():
    """Sign up a new user"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        # Set display_name to username by default
        display_name = username
        
        # Validate inputs
        if not all([username, email, password]):
            return jsonify({'error': 'All fields are required'}), 400

        if not validate_username(username):
            return jsonify({
                'error': 'Username must be 3-20 characters and contain only letters, numbers, and underscores'
            }), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email address'}), 400
        
        valid, msg = validate_password(password)
        if not valid:
            return jsonify({'error': msg}), 400
        
        # Check if username or email exists
        if User.get_by_username(username):
            return jsonify({'error': 'Username already taken'}), 400
        
        if User.get_by_email(email):
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create user
        user_id = User.create(username, email, password, display_name)
        
        # Create JWT token
        token = create_jwt_token(user_id)
        
        # Set cookie
        response = make_response(jsonify({
            'message': 'Account created successfully',
            'redirect': '/create-table'
        }))
        response = set_auth_cookie(response, token)
        
        logger.info(f"New user signed up: {username}")
        return response
    
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        return jsonify({'error': 'An error occurred during signup'}), 500

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Log in a user"""
    try:
        data = request.get_json()
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username_or_email or not password:
            return jsonify({'error': 'Username/email and password required'}), 400
        
        # Authenticate
        user = User.authenticate(username_or_email, password)
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create JWT token
        token = create_jwt_token(user['id'])
        
        # Set cookie
        response = make_response(jsonify({
            'message': 'Login successful',
            'redirect': '/table'
        }))
        response = set_auth_cookie(response, token)
        
        logger.info(f"User logged in: {user['username']}")
        return response
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'An error occurred during login'}), 500

@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """Log out a user"""
    response = make_response(jsonify({'message': 'Logged out successfully'}))
    response.set_cookie('auth_token', '', expires=0)
    return response

@auth_bp.route('/api/auth/me', methods=['GET'])
def get_me():
    """Get current user info"""
    user = get_current_user()
    if not user:
        return jsonify({'authenticated': False}), 401
    
    return jsonify({
        'authenticated': True,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'display_name': user['display_name'],
            'email': user['email']
        }
    })

@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        user = User.get_by_email(email)
        
        # Always return success to prevent email enumeration
        if user:
            token = User.create_reset_token(email)
            # In production, send email with reset link
            # For now, just log it
            logger.info(f"Password reset requested for {email}, token: {token}")
            
            # Return token in response (only for development/demo)
            # In production, this would be sent via email
            return jsonify({
                'message': 'Password reset instructions sent',
                'reset_token': token  # Remove this in production
            })
        
        return jsonify({
            'message': 'If that email exists, password reset instructions have been sent'
        })
    
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

@auth_bp.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    try:
        data = request.get_json()
        token = data.get('token', '')
        new_password = data.get('password', '')
        
        if not token or not new_password:
            return jsonify({'error': 'Token and password required'}), 400
        
        valid, msg = validate_password(new_password)
        if not valid:
            return jsonify({'error': msg}), 400
        
        if User.reset_password(token, new_password):
            return jsonify({'message': 'Password reset successful'})
        else:
            return jsonify({'error': 'Invalid or expired reset token'}), 400
    
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500
