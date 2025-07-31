#!/usr/bin/env python3
"""
Database migration script to add new columns to existing tables
Run this script to update your database schema
"""

from app import create_app
from ai_scholar.models import db
from sqlalchemy import text

def migrate_database():
    app = create_app()
    
    with app.app_context():
        # Add new columns to users table
        try:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE users ADD COLUMN last_login DATETIME'))
                conn.commit()
            print("✅ Added last_login column to users table")
        except Exception as e:
            print(f"⚠️  last_login column might already exist: {e}")
        
        try:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE users ADD COLUMN history_cleared_at DATETIME'))
                conn.commit()
            print("✅ Added history_cleared_at column to users table")
        except Exception as e:
            print(f"⚠️  history_cleared_at column might already exist: {e}")
        
        # Add new columns to search_history table
        try:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE search_history ADD COLUMN mode VARCHAR(20) DEFAULT "single"'))
                conn.commit()
            print("✅ Added mode column to search_history table")
        except Exception as e:
            print(f"⚠️  mode column might already exist: {e}")
        
        try:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE search_history ADD COLUMN search_params TEXT'))
                conn.commit()
            print("✅ Added search_params column to search_history table")
        except Exception as e:
            print(f"⚠️  search_params column might already exist: {e}")
        
        print("✅ Database migration completed!")

if __name__ == '__main__':
    migrate_database()
