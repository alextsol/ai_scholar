#!/usr/bin/env python3
"""
AI Scholar - New Architecture Entry Point
Uses the new MVC architecture with providers, services, and controllers
"""

from ai_scholar.app_factory import app_factory

def main():
    """Main entry point for AI Scholar"""
    try:
        print("🔧 Creating AI Scholar application...")
        
        # Create app with new architecture
        app = app_factory.create_app()
        
        # Run the application
        print(f"\n🎉 AI Scholar is running with new MVC architecture!")
        print(f"🌐 Access the application at: http://127.0.0.1:5000/")
        print("Press Ctrl+C to stop the server")
        
        app.run(debug=True, host='127.0.0.1', port=5000)
        
    except Exception as e:
        print(f"❌ Failed to start AI Scholar: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
