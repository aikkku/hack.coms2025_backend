"""
Database migration utilities
Handles schema updates for existing databases
"""
import sqlite3
import os
from database import SQLALCHEMY_DATABASE_URL

def add_karma_column_if_not_exists():
    """
    Add karma column to users table if it doesn't exist.
    This ensures backward compatibility with existing databases.
    """
    try:
        # Extract database path from SQLAlchemy URL
        # SQLAlchemy URL format: 'sqlite:///./courses.db'
        db_path = SQLALCHEMY_DATABASE_URL.replace('sqlite:///', '')
        
        # Handle relative paths
        if db_path.startswith('./'):
            db_path = db_path[2:]
        elif not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)
        
        # Check if database file exists
        if not os.path.exists(db_path):
            print(f"ℹ️ Database file {db_path} does not exist yet. It will be created with karma column.")
            return True
        
        # Connect directly to SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if karma column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'karma' not in columns:
            print("📝 Adding karma column to users table...")
            try:
                # Add karma column with default value of 0
                cursor.execute("ALTER TABLE users ADD COLUMN karma INTEGER DEFAULT 0")
                conn.commit()
                print("✅ Successfully added karma column to users table")
            except sqlite3.OperationalError as e:
                print(f"⚠️ Could not add karma column: {e}")
                conn.rollback()
                return False
        else:
            print("ℹ️ karma column already exists in users table")
        
        conn.close()
        return True
    except Exception as e:
        print(f"⚠️ Error checking/adding karma column: {e}")
        import traceback
        traceback.print_exc()
        # Don't fail if migration fails - the code will handle missing karma gracefully
        return False

def run_migrations():
    """
    Run all database migrations
    """
    print("🔄 Running database migrations...")
    success = add_karma_column_if_not_exists()
    if success:
        print("✅ Migrations complete")
    else:
        print("⚠️ Some migrations may have failed, but continuing anyway...")
    return success

