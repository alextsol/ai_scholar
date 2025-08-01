#!/usr/bin/env python3
"""Quick test script to debug the application error"""

import sys
import os
import traceback

sys.path.insert(0, '.')

def test_app():
    """Test the application directly to find the error"""
    try:
        from ai_scholar.app_factory import ApplicationFactory
        app_factory = ApplicationFactory()
        
        app = app_factory.create_app(use_new_architecture=True)
        
        with app.test_client() as client:
            response = client.get('/')
            
            if response.status_code != 200:
                return 1
            
            response = client.get('/about')
            
            if response.status_code != 200:
                return 1
        
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    test_app()
