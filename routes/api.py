import logging
from flask import Blueprint, jsonify, request, session
from models.table import Table
from models.prompt import Prompt
from utils.auth import login_required
from utils.prompts import ensure_prompt_exists, get_prompt_for_date
from datetime import date, timedelta

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
        
        # Ensure today's prompt exists
        today = date.today()
        prompt = ensure_prompt_exists(table_id, today)
        
        if not prompt:
            return jsonify({'error': 'Could not load prompt'}), 500
        
        # Get prompt with responses
        prompt_data = Prompt.get_prompt_with_responses(prompt['id'], user['id'])
        
        # Get user's response if exists
        user_response = Prompt.get_user_response(prompt['id'], user['id'])
        
        return jsonify({
            'prompt': prompt_data,
            'user_response': user_response,
            'date': today.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Get today prompt error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

@api_bp.route('/api/prompt/yesterday', methods=['GET'])
@login_required
def get_yesterday_prompt(user):
    """Get yesterday's prompt and all responses"""
    try:
        table_id = get_current_table_id(user)
        if not table_id:
            return jsonify({'error': 'Not in a table'}), 404
        
        yesterday = date.today() - timedelta(days=1)
        prompt = get_prompt_for_date(table_id, yesterday)
        
        if not prompt:
            return jsonify({'error': 'No prompt for yesterday'}), 404
        
        # Get all responses (regardless of whether user responded)
        responses = Prompt.get_responses(prompt['id'])
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
        today = date.today()
        prompt = ensure_prompt_exists(table_id, today)
        
        if not prompt:
            return jsonify({'error': 'Could not load prompt'}), 500
        
        # Submit response
        success, message = Prompt.submit_response(prompt['id'], user['id'], response_text)
        
        if not success:
            return jsonify({'error': message}), 400
        
        logger.info(f"User {user['username']} submitted response to prompt {prompt['id']}")
        
        # Return updated prompt data with all responses
        prompt_data = Prompt.get_prompt_with_responses(prompt['id'], user['id'])
        
        return jsonify({
            'message': message,
            'prompt': prompt_data
        })
    
    except Exception as e:
        logger.error(f"Submit response error: {str(e)}")
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
        today = date.today()
        prompt = get_prompt_for_date(table_id, today)
        
        if not prompt:
            return jsonify({'new_responses': []})
        
        # Check if user has responded
        if not Prompt.user_has_responded(prompt['id'], user['id']):
            return jsonify({'new_responses': []})
        
        # Get all responses
        responses = Prompt.get_responses(prompt['id'])
        
        # Get timestamp from query param (last known response time)
        last_check = request.args.get('last_check', '')
        
        # Return all responses (client will filter new ones)
        return jsonify({
            'responses': responses,
            'count': len(responses)
        })
    
    except Exception as e:
        logger.error(f"Poll responses error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500
