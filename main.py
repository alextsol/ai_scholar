from ai_scholar.app_factory import app_factory

def main():
    """Main entry point for AI Scholar"""
    try:
        app = app_factory.create_app()
        app.run(debug=True, host='127.0.0.1', port=5000)
        
    except Exception as e:
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
