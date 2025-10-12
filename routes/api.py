import logging
from flask import Blueprint, jsonify, request, session, make_response
from models.table import Table
from models.prompt import Prompt
from utils.auth import login_required
from utils.prompts import ensure_prompt_exists, get_prompt_for_date, get_current_prompt_date, get_time_until_next_prompt
from datetime import date, timedelta, datetime

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)

def get_current_table_id(user):
    """Get the current active table for the user"""
    table_id = session.get('current_table_id')
    
    if table_id and Table.is_member(table_id, user['id']):
        return table_id
    
    # Get user's first table
    tables = Table.get_user_tables(user['id'])
    if tables:
        table_id = tables[0]['id']
        session['current_table_id'] = table_id
        return table_id
    
    return None

@api_bp.route('/api/prompt/today', methods=['GET'])
@login_required
def get_today_prompt(user):
    """Get today's prompt and responses"""
    try:
        table_id = get_current_table_id(user)
        if not table_id:
            return jsonify({'error': 'Not in a table'}), 404
        
        # Get current prompt date (respects prompt time)
        current_date = get_current_prompt_date(table_id)
        prompt = ensure_prompt_exists(table_id, current_date)
        
        if not prompt:
            return jsonify({'error': 'Could not load prompt'}), 500
        
        # Get prompt with responses
        prompt_data = Prompt.get_prompt_with_responses(prompt['id'], user['id'], table_id)
        
        # Get user's response if exists
        user_response = Prompt.get_user_response(prompt['id'], user['id'])
        
        # Get time until next prompt
        seconds_until_next = get_time_until_next_prompt(table_id)
        
        return jsonify({
            'prompt': prompt_data,
            'user_response': user_response,
            'date': current_date.isoformat(),
            'seconds_until_next_prompt': seconds_until_next
        })
    
    except Exception as e:
        logger.error(f"Get today prompt error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

@api_bp.route('/api/prompt/date/<date_str>', methods=['GET'])
@login_required
def get_prompt_by_date(user, date_str):
    """Get prompt for a specific date"""
    try:
        table_id = get_current_table_id(user)
        if not table_id:
            return jsonify({'error': 'Not in a table'}), 404
        
        # Parse date
        try:
            prompt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        # Don't allow dates more than 7 days back
        current_date = get_current_prompt_date(table_id)
        days_back = (current_date - prompt_date).days
        
        if days_back > 7:
            return jsonify({'error': 'Can only view prompts from the last 7 days'}), 400
        
        if days_back < 0:
            return jsonify({'error': 'Cannot view future prompts'}), 400
        
        prompt = get_prompt_for_date(table_id, prompt_date)
        
        if not prompt:
            return jsonify({'error': 'No prompt for that date'}), 404
        
        # Get all responses (regardless of whether user responded)
        responses = Prompt.get_responses(prompt['id'], table_id)
        user_response = Prompt.get_user_response(prompt['id'], user['id'])
        
        # Check if prompt is still editable
        is_editable = Prompt.is_prompt_active(prompt['prompt_date'], table_id)
        
        return jsonify({
            'prompt': {
                'id': prompt['id'],
                'prompt_text': prompt['prompt_text'],
                'prompt_date': prompt['prompt_date'],
                'is_custom': prompt['is_custom'],
                'is_editable': is_editable
            },
            'responses': responses,
            'user_response': user_response,
            'date': prompt_date.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Get prompt by date error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

@api_bp.route('/api/prompt/yesterday', methods=['GET'])
@login_required
def get_yesterday_prompt(user):
    """Get yesterday's prompt and all responses"""
    try:
        table_id = get_current_table_id(user)
        if not table_id:
            return jsonify({'error': 'Not in a table'}), 404
        
        # Get current date and go back one day
        current_date = get_current_prompt_date(table_id)
        yesterday = current_date - timedelta(days=1)
        prompt = get_prompt_for_date(table_id, yesterday)
        
        if not prompt:
            return jsonify({'error': 'No prompt for yesterday'}), 404
        
        # Get all responses (regardless of whether user responded)
        responses = Prompt.get_responses(prompt['id'], table_id)
        user_response = Prompt.get_user_response(prompt['id'], user['id'])
        
        return jsonify({
            'prompt': {
                'id': prompt['id'],
                'prompt_text': prompt['prompt_text'],
                'prompt_date': prompt['prompt_date'],
                'is_custom': prompt['is_custom']
            },
            'responses': responses,
            'user_response': user_response,
            'date': yesterday.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Get yesterday prompt error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

@api_bp.route('/api/response/submit', methods=['POST'])
@login_required
def submit_response(user):
    """Submit response to today's prompt"""
    try:
        table_id = get_current_table_id(user)
        if not table_id:
            return jsonify({'error': 'Not in a table'}), 404
        
        data = request.get_json()
        response_text = data.get('response', '').strip()
        
        if not response_text:
            return jsonify({'error': 'Response cannot be empty'}), 400
        
        # Get today's prompt
        current_date = get_current_prompt_date(table_id)
        prompt = ensure_prompt_exists(table_id, current_date)
        
        if not prompt:
            return jsonify({'error': 'Could not load prompt'}), 500
        
        # Submit response
        success, message = Prompt.submit_response(prompt['id'], user['id'], response_text)
        
        if not success:
            return jsonify({'error': message}), 400
        
        logger.info(f"User {user['username']} submitted response to prompt {prompt['id']}")
        
        # Return updated prompt data with all responses
        prompt_data = Prompt.get_prompt_with_responses(prompt['id'], user['id'], table_id)
        
        return jsonify({
            'message': message,
            'prompt': prompt_data
        })
    
    except Exception as e:
        logger.error(f"Submit response error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

@api_bp.route('/api/response/edit', methods=['PUT'])
@login_required
def edit_response(user):
    """Edit an existing response"""
    try:
        table_id = get_current_table_id(user)
        if not table_id:
            return jsonify({'error': 'Not in a table'}), 404
        
        data = request.get_json()
        prompt_id = data.get('prompt_id')
        response_text = data.get('response', '').strip()
        
        if not prompt_id or not response_text:
            return jsonify({'error': 'Prompt ID and response text required'}), 400
        
        # Edit response
        success, message = Prompt.edit_response(prompt_id, user['id'], response_text, table_id)
        
        if not success:
            return jsonify({'error': message}), 400
        
        logger.info(f"User {user['username']} edited response to prompt {prompt_id}")
        
        # Return updated prompt data
        prompt_data = Prompt.get_prompt_with_responses(prompt_id, user['id'], table_id)
        
        return jsonify({
            'message': message,
            'prompt': prompt_data
        })
    
    except Exception as e:
        logger.error(f"Edit response error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

@api_bp.route('/api/response/poll', methods=['GET'])
@login_required
def poll_responses(user):
    """Poll for new responses (for live updates)"""
    try:
        table_id = get_current_table_id(user)
        if not table_id:
            return jsonify({'error': 'Not in a table'}), 404
        
        # Get today's prompt
        current_date = get_current_prompt_date(table_id)
        prompt = get_prompt_for_date(table_id, current_date)
        
        if not prompt:
            return jsonify({'new_responses': []})
        
        # Check if user has responded
        if not Prompt.user_has_responded(prompt['id'], user['id']):
            # Return response count even if user hasn't responded
            from utils.db import get_db_context
            with get_db_context() as conn:
                cursor = conn.execute(
                    'SELECT COUNT(*) as count FROM responses WHERE prompt_id = ?',
                    (prompt['id'],)
                )
                count = cursor.fetchone()['count']
                return jsonify({'response_count': count, 'responses': []})
        
        # Get all responses
        responses = Prompt.get_responses(prompt['id'], table_id)
        
        return jsonify({
            'responses': responses,
            'count': len(responses)
        })
    
    except Exception as e:
        logger.error(f"Poll responses error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

@api_bp.route('/api/user/profile', methods=['PUT'])
@login_required
def update_profile(user):
    """Update user profile (table-specific display name)"""
    try:
        table_id = get_current_table_id(user)
        if not table_id:
            return jsonify({'error': 'Not in a table'}), 404
        
        data = request.get_json()
        display_name = data.get('display_name', '').strip()
        
        if not display_name or len(display_name) > 50:
            return jsonify({'error': 'Display name must be 1-50 characters'}), 400
        
        if Table.update_member_display_name(table_id, user['id'], display_name):
            logger.info(f"User {user['username']} updated display name to {display_name} for table {table_id}")
            return jsonify({'message': 'Display name updated successfully'})
        else:
            return jsonify({'error': 'Failed to update display name'}), 500
    
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

@api_bp.route('/api/user/delete', methods=['POST'])
@login_required
def delete_account(user):
    """Delete user account permanently"""
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        if not password:
            return jsonify({'error': 'Password required'}), 400
        
        from models.user import User
        success, message = User.delete_account(user['id'], password)
        
        if not success:
            return jsonify({'error': message}), 401
        
        # Clear session/cookie
        response = make_response(jsonify({
            'message': message,
            'redirect': '/'
        }))
        response.set_cookie('auth_token', '', expires=0)
        
        logger.info(f"User {user['username']} deleted their account")
        return response
    
    except Exception as e:
        logger.error(f"Delete account error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500
