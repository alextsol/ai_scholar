#!/usr/bin/env python3
"""
AI Scholar - New Architecture Entry Point

This is the new main entry point that supports both the new MVC architecture
and fallback to the legacy system for backward compatibility.

Usage:
    python main_new.py [--legacy] [--config CONFIG_NAME]
    
    --legacy: Use legacy architecture instead of new MVC
    --config: Specify configuration name (development, production, testing)
"""

import os
import sys
import argparse
from ai_scholar.app_factory import app_factory

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='AI Scholar Application')
    parser.add_argument('--legacy', action='store_true', 
                       help='Use legacy architecture instead of new MVC')
    parser.add_argument('--config', type=str, default=None,
                       help='Configuration name (development, production, testing)')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                       help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    
    return parser.parse_args()

def main():
    """Main entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up environment
    if args.debug:
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = '1'
    
    try:
        # Create Flask application
        print("🔧 Creating AI Scholar application...")
        
        use_new_architecture = not args.legacy
        app = app_factory.create_app(
            config_name=args.config,
            use_new_architecture=use_new_architecture
        )
        
        if use_new_architecture:
            print("\n🎉 AI Scholar is running with new MVC architecture!")
            print("   - Professional controllers, services, and providers")
            print("   - Interface-driven design with dependency injection")
            print("   - Backward compatibility with legacy endpoints")
            print(f"   - Legacy endpoints available at: http://{args.host}:{args.port}/legacy/")
        else:
            print("\n⚠️  AI Scholar is running in legacy mode")
        
        print(f"\n🌐 Access the application at: http://{args.host}:{args.port}/")
        print("Press Ctrl+C to stop the server")
        
        # Run the application
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=args.debug
        )
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down AI Scholar...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting AI Scholar: {e}")
        print("\n🔄 Trying legacy mode as fallback...")
        
        try:
            # Fallback to legacy mode
            app = app_factory.create_app(
                config_name=args.config,
                use_new_architecture=False
            )
            
            print(f"🌐 Legacy mode running at: http://{args.host}:{args.port}/")
            app.run(host=args.host, port=args.port, debug=args.debug)
            
        except Exception as fallback_error:
            print(f"❌ Legacy fallback also failed: {fallback_error}")
            print("\n🛠️  Please check your configuration and dependencies")
            sys.exit(1)

if __name__ == '__main__':
    main()
