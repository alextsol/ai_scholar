#!/usr/bin/env python3
"""
Recreate database with new schema
This will drop and recreate all tables
WARNING: This will delete all existing data!
"""

from app import create_app
from ai_scholar.models import db
import os

def recreate_database():
    app = create_app()
    
    with app.app_context():
        print("⚠️  WARNING: This will delete all existing data!")
        confirm = input("Type 'yes' to continue: ")
        
        if confirm.lower() != 'yes':
            print("❌ Operation cancelled")
            return
        
        # Drop all tables
        print("🗑️  Dropping all tables...")
        db.drop_all()
        
        # Create all tables with new schema
        print("🏗️  Creating all tables with new schema...")
        db.create_all()
        
        print("✅ Database recreated successfully!")
        print("ℹ️   You can now register new users and test the functionality")

if __name__ == '__main__':
    recreate_database()
