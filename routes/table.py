import logging
from flask import Blueprint, render_template, request, jsonify
from models.table import Table
from models.prompt import Prompt
from utils.auth import login_required
from utils.prompts import ensure_prompt_exists
from datetime import date, timedelta

logger = logging.getLogger(__name__)
table_bp = Blueprint('table', __name__)

@table_bp.route('/create-table', methods=['GET'])
@login_required
def create_table_page(user):
    """Create table page"""
    # Check if user already has a table
    existing_table = Table.get_user_table(user['id'])
    if existing_table:
        return render_template('redirect.html', url='/table')
    return render_template('create_table.html')

@table_bp.route('/join-table', methods=['GET'])
@login_required
def join_table_page(user):
    """Join table page"""
    # Check if user already has a table
    existing_table = Table.get_user_table(user['id'])
    if existing_table:
        return render_template('redirect.html', url='/table')
    return render_template('join_table.html')

@table_bp.route('/table', methods=['GET'])
@login_required
def table_page(user):
    """Main table page"""
    # Check if user has a table
    table = Table.get_user_table(user['id'])
    if not table:
        return render_template('redirect.html', url='/create-table')
    
    return render_template('table.html')

@table_bp.route('/table/yesterday', methods=['GET'])
@login_required
def yesterday_page(user):
    """Yesterday's prompt page"""
    # Check if user has a table
    table = Table.get_user_table(user['id'])
    if not table:
        return render_template('redirect.html', url='/create-table')
    
    return render_template('yesterday.html')

@table_bp.route('/table/settings', methods=['GET'])
@login_required
def settings_page(user):
    """Table settings page"""
    # Check if user has a table
    table = Table.get_user_table(user['id'])
    if not table:
        return render_template('redirect.html', url='/create-table')
    
    return render_template('settings.html')

@table_bp.route('/api/table/create', methods=['POST'])
@login_required
def create_table(user):
    """Create a new table"""
    try:
        # Check if user already has a table
        existing_table = Table.get_user_table(user['id'])
        if existing_table:
            return jsonify({'error': 'You already have a kitchen table'}), 400
        
        data = request.get_json()
        name = data.get('name', '').strip()
        prompt_time = data.get('prompt_time', '00:00')
        
        if not name:
            return jsonify({'error': 'Table name required'}), 400
        
        if len(name) < 3 or len(name) > 50:
            return jsonify({'error': 'Table name must be 3-50 characters'}), 400
        
        # Create table
        table_id, invite_code = Table.create(name, user['id'], prompt_time)
        
        # Create first prompt
        ensure_prompt_exists(table_id, date.today())
        
        logger.info(f"User {user['username']} created table {name}")
        
        return jsonify({
            'message': 'Table created successfully',
            'table_id': table_id,
            'invite_code': invite_code,
            'redirect': '/table'
        })
    
    except Exception as e:
        logger.error(f"Create table error: {str(e)}")
        return jsonify({'error': 'An error occurred creating the table'}), 500

@table_bp.route('/api/table/join', methods=['POST'])
@login_required
def join_table(user):
    """Join a table with invite code"""
    try:
        data = request.get_json()
        invite_code = data.get('invite_code', '').strip().upper()
        
        if not invite_code:
            return jsonify({'error': 'Invite code required'}), 400
        
        # Get table
        table = Table.get_by_invite_code(invite_code)
        if not table:
            return jsonify({'error': 'Invalid invite code'}), 404
        
        # Add member
        success, message = Table.add_member(table['id'], user['id'])
        
        if not success:
            return jsonify({'error': message}), 400
        
        logger.info(f"User {user['username']} joined table {table['name']}")
        
        return jsonify({
            'message': message,
            'redirect': '/table'
        })
    
    except Exception as e:
        logger.error(f"Join table error: {str(e)}")
        return jsonify({'error': 'An error occurred joining the table'}), 500

@table_bp.route('/api/table/info', methods=['GET'])
@login_required
def get_table_info(user):
    """Get table information"""
    try:
        table = Table.get_user_table(user['id'])
        if not table:
            return jsonify({'error': 'Not in a table'}), 404
        
        members = Table.get_members(table['id'])
        is_owner = Table.is_owner(table['id'], user['id'])
        
        return jsonify({
            'table': {
                'id': table['id'],
                'name': table['name'],
                'invite_code': table['invite_code'],
                'prompt_time': table['prompt_time'],
                'is_owner': is_owner
            },
            'members': members
        })
    
    except Exception as e:
        logger.error(f"Get table info error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

@table_bp.route('/api/table/settings', methods=['PUT'])
@login_required
def update_table_settings(user):
    """Update table settings (owner only)"""
    try:
        table = Table.get_user_table(user['id'])
        if not table:
            return jsonify({'error': 'Not in a table'}), 404
        
        if not Table.is_owner(table['id'], user['id']):
            return jsonify({'error': 'Only the table owner can update settings'}), 403
        
        data = request.get_json()
        name = data.get('name')
        prompt_time = data.get('prompt_time')
        
        if name:
            if len(name.strip()) < 3 or len(name.strip()) > 50:
                return jsonify({'error': 'Table name must be 3-50 characters'}), 400
        
        if Table.update_settings(table['id'], name, prompt_time):
            return jsonify({'message': 'Settings updated successfully'})
        else:
            return jsonify({'error': 'Failed to update settings'}), 500
    
    except Exception as e:
        logger.error(f"Update settings error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

@table_bp.route('/api/table/leave', methods=['POST'])
@login_required
def leave_table(user):
    """Leave current table"""
    try:
        table = Table.get_user_table(user['id'])
        if not table:
            return jsonify({'error': 'Not in a table'}), 404
        
        success, message = Table.leave_table(table['id'], user['id'])
        
        if not success:
            return jsonify({'error': message}), 400
        
        logger.info(f"User {user['username']} left table {table['name']}")
        
        return jsonify({
            'message': message,
            'redirect': '/create-table'
        })
    
    except Exception as e:
        logger.error(f"Leave table error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500
