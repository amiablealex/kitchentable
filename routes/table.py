import logging
from flask import Blueprint, render_template, request, jsonify, session
from models.table import Table
from models.prompt import Prompt
from utils.auth import login_required
from utils.prompts import ensure_prompt_exists
from datetime import date, timedelta

logger = logging.getLogger(__name__)
table_bp = Blueprint('table', __name__)

def get_current_table_id(user):
    """Get the current active table for the user"""
    # Check session first
    table_id = session.get('current_table_id')
    
    if table_id:
        # Verify user is still a member of this table
        if Table.is_member(table_id, user['id']):
            return table_id
    
    # If no valid table in session, get user's first table
    tables = Table.get_user_tables(user['id'])
    if tables:
        table_id = tables[0]['id']
        session['current_table_id'] = table_id
        return table_id
    
    return None

@table_bp.route('/create-table', methods=['GET'])
@login_required
def create_table_page(user):
    """Create table page"""
    return render_template('create_table.html')

@table_bp.route('/join-table', methods=['GET'])
@login_required
def join_table_page(user):
    """Join table page"""
    return render_template('join_table.html')

@table_bp.route('/table', methods=['GET'])
@login_required
def table_page(user):
    """Main table page"""
    # Check if user has any tables
    tables = Table.get_user_tables(user['id'])
    if not tables:
        return render_template('redirect.html', url='/create-table')
    
    # Ensure we have a current table set
    get_current_table_id(user)
    
    return render_template('table.html')

@table_bp.route('/table/yesterday', methods=['GET'])
@login_required
def yesterday_page(user):
    """Yesterday's prompt page"""
    # Check if user has any tables
    table_id = get_current_table_id(user)
    if not table_id:
        return render_template('redirect.html', url='/create-table')
    
    return render_template('yesterday.html')

@table_bp.route('/table/settings', methods=['GET'])
@login_required
def settings_page(user):
    """Table settings page"""
    # Check if user has any tables
    table_id = get_current_table_id(user)
    if not table_id:
        return render_template('redirect.html', url='/create-table')
    
    return render_template('settings.html')

@table_bp.route('/api/table/create', methods=['POST'])
@login_required
def create_table(user):
    """Create a new table"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        prompt_time = data.get('prompt_time', '00:00')
        
        if not name:
            return jsonify({'error': 'Table name required'}), 400
        
        if len(name) < 3 or len(name) > 50:
            return jsonify({'error': 'Table name must be 3-50 characters'}), 400
        
        # Create table
        table_id, invite_code = Table.create(name, user['id'], prompt_time)
        
        # Set as current table
        session['current_table_id'] = table_id
        
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
        
        # Set as current table
        session['current_table_id'] = table['id']
        
        logger.info(f"User {user['username']} joined table {table['name']}")
        
        return jsonify({
            'message': message,
            'redirect': '/table'
        })
    
    except Exception as e:
        logger.error(f"Join table error: {str(e)}")
        return jsonify({'error': 'An error occurred joining the table'}), 500

@table_bp.route('/api/table/switch', methods=['POST'])
@login_required
def switch_table(user):
    """Switch to a different table"""
    try:
        data = request.get_json()
        table_id = data.get('table_id')
        
        if not table_id:
            return jsonify({'error': 'Table ID required'}), 400
        
        # Verify user is a member of this table
        if not Table.is_member(table_id, user['id']):
            return jsonify({'error': 'You are not a member of this table'}), 403
        
        # Update session
        session['current_table_id'] = table_id
        
        logger.info(f"User {user['username']} switched to table {table_id}")
        
        return jsonify({'message': 'Table switched successfully'})
    
    except Exception as e:
        logger.error(f"Switch table error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

@table_bp.route('/api/table/list', methods=['GET'])
@login_required
def list_tables(user):
    """Get all tables user belongs to"""
    try:
        tables = Table.get_user_tables(user['id'])
        current_table_id = get_current_table_id(user)
        
        table_list = []
        for table in tables:
            table_list.append({
                'id': table['id'],
                'name': table['name'],
                'role': table['role'],
                'is_current': table['id'] == current_table_id
            })
        
        return jsonify({
            'tables': table_list,
            'current_table_id': current_table_id
        })
    
    except Exception as e:
        logger.error(f"List tables error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

@table_bp.route('/api/table/info', methods=['GET'])
@login_required
def get_table_info(user):
    """Get current table information"""
    try:
        table_id = get_current_table_id(user)
        if not table_id:
            return jsonify({'error': 'Not in a table'}), 404
        
        table = Table.get_by_id(table_id)
        if not table:
            return jsonify({'error': 'Table not found'}), 404
        
        members = Table.get_members(table_id)
        is_owner = Table.is_owner(table_id, user['id'])
        
        return jsonify({
            'table': {
                'id': table['id'],
                'name': table['name'],
                'invite_code': table['invite_code'],
                'prompt_time': table['prompt_time'],
                'is_owner': is_owner
            },
            'members': members,
            'user': {
                'username': user['username'],
                'display_name': user['display_name']
            }
        })
    
    except Exception as e:
        logger.error(f"Get table info error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

@table_bp.route('/api/table/settings', methods=['PUT'])
@login_required
def update_table_settings(user):
    """Update table settings (owner only)"""
    try:
        table_id = get_current_table_id(user)
        if not table_id:
            return jsonify({'error': 'Not in a table'}), 404
        
        if not Table.is_owner(table_id, user['id']):
            return jsonify({'error': 'Only the table owner can update settings'}), 403
        
        data = request.get_json()
        name = data.get('name')
        prompt_time = data.get('prompt_time')
        
        if name:
            if len(name.strip()) < 3 or len(name.strip()) > 50:
                return jsonify({'error': 'Table name must be 3-50 characters'}), 400
        
        if Table.update_settings(table_id, name, prompt_time):
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
        table_id = get_current_table_id(user)
        if not table_id:
            return jsonify({'error': 'Not in a table'}), 404
        
        table = Table.get_by_id(table_id)
        
        success, message = Table.leave_table(table_id, user['id'])
        
        if not success:
            return jsonify({'error': message}), 400
        
        # Clear from session
        session.pop('current_table_id', None)
        
        # Check if user has other tables
        remaining_tables = Table.get_user_tables(user['id'])
        if remaining_tables:
            # Switch to first remaining table
            session['current_table_id'] = remaining_tables[0]['id']
            redirect_url = '/table'
        else:
            redirect_url = '/create-table'
        
        logger.info(f"User {user['username']} left table {table['name']}")
        
        return jsonify({
            'message': message,
            'redirect': redirect_url
        })
    
    except Exception as e:
        logger.error(f"Leave table error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500
