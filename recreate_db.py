#!/usr/bin/env python3

from app import create_app
from ai_scholar.models import db
import os

def recreate_database():
    app = create_app()
    
    with app.app_context():
        confirm = input("Type 'yes' to continue: ")
        
        if confirm.lower() != 'yes':
            return
        
        db.drop_all()
        db.create_all()

if __name__ == '__main__':
    recreate_database()
