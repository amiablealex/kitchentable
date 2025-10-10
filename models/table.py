import logging
from utils.db import get_db_context, dict_from_row
from utils.auth import generate_invite_code
from config import Config

logger = logging.getLogger(__name__)

class Table:
    @staticmethod
    def create(name, created_by, prompt_time='00:00'):
        """Create a new table"""
        try:
            invite_code = generate_invite_code()
            
            # Ensure unique invite code
            while Table.get_by_invite_code(invite_code):
                invite_code = generate_invite_code()
            
            with get_db_context() as conn:
                cursor = conn.execute('''
                    INSERT INTO tables (name, invite_code, created_by, prompt_time)
                    VALUES (?, ?, ?, ?)
                ''', (name, invite_code, created_by, prompt_time))
                
                table_id = cursor.lastrowid
                
                # Add creator as owner
                conn.execute('''
                    INSERT INTO table_members (table_id, user_id, role)
                    VALUES (?, ?, 'owner')
                ''', (table_id, created_by))
                
                logger.info(f"Created table: {name} (ID: {table_id}, Code: {invite_code})")
                return table_id, invite_code
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            raise

    @staticmethod
    def get_by_id(table_id):
        """Get table by ID"""
        try:
            with get_db_context() as conn:
                cursor = conn.execute('SELECT * FROM tables WHERE id = ?', (table_id,))
                table = cursor.fetchone()
                return dict_from_row(table) if table else None
        except Exception as e:
            logger.error(f"Error getting table by ID: {str(e)}")
            return None

    @staticmethod
    def get_by_invite_code(invite_code):
        """Get table by invite code"""
        try:
            with get_db_context() as conn:
                cursor = conn.execute(
                    'SELECT * FROM tables WHERE invite_code = ?',
                    (invite_code.upper(),)
                )
                table = cursor.fetchone()
                return dict_from_row(table) if table else None
        except Exception as e:
            logger.error(f"Error getting table by invite code: {str(e)}")
            return None

    @staticmethod
    def get_user_table(user_id):
        """Get the table a user belongs to"""
        try:
            with get_db_context() as conn:
                cursor = conn.execute('''
                    SELECT t.*, tm.role 
                    FROM tables t
                    JOIN table_members tm ON t.id = tm.table_id
                    WHERE tm.user_id = ?
                ''', (user_id,))
                
                table = cursor.fetchone()
                return dict_from_row(table) if table else None
        except Exception as e:
            logger.error(f"Error getting user table: {str(e)}")
            return None

    @staticmethod
    def add_member(table_id, user_id):
        """Add a member to a table"""
        try:
            with get_db_context() as conn:
                # Check if user is already in a table
                cursor = conn.execute(
                    'SELECT table_id FROM table_members WHERE user_id = ?',
                    (user_id,)
                )
                existing = cursor.fetchone()
                if existing:
                    logger.warning(f"User {user_id} already in table {existing['table_id']}")
                    return False, "You're already in a kitchen table"
                
                # Check member count
                cursor = conn.execute(
                    'SELECT COUNT(*) as count FROM table_members WHERE table_id = ?',
                    (table_id,)
                )
                count = cursor.fetchone()['count']
                
                if count >= Config.TABLE_MAX_MEMBERS:
                    logger.warning(f"Table {table_id} is full")
                    return False, f"This table is full (max {Config.TABLE_MAX_MEMBERS} members)"
                
                # Add member
                conn.execute('''
                    INSERT INTO table_members (table_id, user_id, role)
                    VALUES (?, ?, 'member')
                ''', (table_id, user_id))
                
                logger.info(f"Added user {user_id} to table {table_id}")
                return True, "Successfully joined table"
        except Exception as e:
            logger.error(f"Error adding member: {str(e)}")
            return False, "Error joining table"

    @staticmethod
    def get_members(table_id):
        """Get all members of a table"""
        try:
            with get_db_context() as conn:
                cursor = conn.execute('''
                    SELECT u.id, u.username, u.display_name, u.last_active,
                           tm.role, tm.joined_at
                    FROM users u
                    JOIN table_members tm ON u.id = tm.user_id
                    WHERE tm.table_id = ?
                    ORDER BY tm.joined_at ASC
                ''', (table_id,))
                
                members = cursor.fetchall()
                return [dict_from_row(m) for m in members]
        except Exception as e:
            logger.error(f"Error getting table members: {str(e)}")
            return []

    @staticmethod
    def is_member(table_id, user_id):
        """Check if user is a member of table"""
        try:
            with get_db_context() as conn:
                cursor = conn.execute('''
                    SELECT id FROM table_members 
                    WHERE table_id = ? AND user_id = ?
                ''', (table_id, user_id))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking membership: {str(e)}")
            return False

    @staticmethod
    def is_owner(table_id, user_id):
        """Check if user is owner of table"""
        try:
            with get_db_context() as conn:
                cursor = conn.execute('''
                    SELECT id FROM table_members 
                    WHERE table_id = ? AND user_id = ? AND role = 'owner'
                ''', (table_id, user_id))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking ownership: {str(e)}")
            return False

    @staticmethod
    def update_settings(table_id, name=None, prompt_time=None):
        """Update table settings"""
        try:
            with get_db_context() as conn:
                if name:
                    conn.execute(
                        'UPDATE tables SET name = ? WHERE id = ?',
                        (name, table_id)
                    )
                
                if prompt_time:
                    conn.execute(
                        'UPDATE tables SET prompt_time = ? WHERE id = ?',
                        (prompt_time, table_id)
                    )
                
                logger.info(f"Updated settings for table {table_id}")
                return True
        except Exception as e:
            logger.error(f"Error updating table settings: {str(e)}")
            return False

    @staticmethod
    def leave_table(table_id, user_id):
        """Remove user from table"""
        try:
            with get_db_context() as conn:
                # Check if user is owner
                if Table.is_owner(table_id, user_id):
                    # Count remaining members
                    cursor = conn.execute(
                        'SELECT COUNT(*) as count FROM table_members WHERE table_id = ?',
                        (table_id,)
                    )
                    count = cursor.fetchone()['count']
                    
                    if count > 1:
                        return False, "Owner cannot leave while others are in the table"
                
                # Remove member
                conn.execute(
                    'DELETE FROM table_members WHERE table_id = ? AND user_id = ?',
                    (table_id, user_id)
                )
                
                logger.info(f"User {user_id} left table {table_id}")
                return True, "Successfully left table"
        except Exception as e:
            logger.error(f"Error leaving table: {str(e)}")
            return False, "Error leaving table"
