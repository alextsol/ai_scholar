#!/usr/bin/env python3
"""
Quick test script to debug the application error
"""

import sys
import os
import traceback

# Add current directory to Python path
sys.path.insert(0, '.')

def test_app():
    """Test the application directly to find the error"""
    try:
        print("🔧 Testing AI Scholar application...")
        
        from ai_scholar.app_factory import ApplicationFactory
        app_factory = ApplicationFactory()
        
        print("📱 Creating app with new architecture...")
        app = app_factory.create_app(use_new_architecture=True)
        
        print("🧪 Testing routes...")
        with app.test_client() as client:
            # Test main route
            print("  Testing GET /")
            response = client.get('/')
            print(f"    Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"    Error response: {response.get_data(as_text=True)}")
            else:
                print("    ✅ Main route works!")
            
            # Test about route
            print("  Testing GET /about")
            response = client.get('/about')
            print(f"    Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"    Error response: {response.get_data(as_text=True)}")
            else:
                print("    ✅ About route works!")
        
        print("✅ Application test completed")
        
    except Exception as e:
        print(f"❌ Error testing application: {e}")
        print("\n🔍 Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_app()
