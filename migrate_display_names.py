#!/usr/bin/env python3
"""
Database migration script to add display_name to table_members
Run this ONCE after updating your code to add per-table display names
"""

import sqlite3
import sys
import os

def migrate_database(db_path='kitchen_table.db'):
    """Add display_name column to table_members and populate from users table"""
    
    print(f"Starting migration for database: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found: {db_path}")
        sys.exit(1)
    
    # Create backup
    backup_path = f"{db_path}.backup_before_migration"
    print(f"Creating backup: {backup_path}")
    
    import shutil
    shutil.copy2(db_path, backup_path)
    print("Backup created successfully")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(table_members)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'display_name' in columns:
            print("Migration already completed - display_name column exists")
            conn.close()
            return
        
        print("Adding display_name column to table_members...")
        
        # Add the column
        cursor.execute("ALTER TABLE table_members ADD COLUMN display_name TEXT")
        
        print("Populating display_name from users table...")
        
        # Populate display_name for all existing members
        cursor.execute("""
            UPDATE table_members 
            SET display_name = (
                SELECT display_name 
                FROM users 
                WHERE users.id = table_members.user_id
            )
        """)
        
        rows_updated = cursor.rowcount
        print(f"Updated {rows_updated} table member records")
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully!")
        
        # Verify
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM table_members 
            WHERE display_name IS NULL
        """)
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            print(f"WARNING: {null_count} records have NULL display_name")
        else:
            print("Verification passed - all records have display names")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR during migration: {str(e)}")
        print(f"You can restore from backup: {backup_path}")
        sys.exit(1)

if __name__ == '__main__':
    # Get database path from command line or use default
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'kitchen_table.db'
    
    print("=" * 60)
    print("Kitchen Table - Display Name Migration")
    print("=" * 60)
    print()
    
    migrate_database(db_path)
    
    print()
    print("=" * 60)
    print("Migration complete! You can now restart your application.")
    print("=" * 60)
