# Production Deployment Guide for PythonAnywhere

## File Upload
1. Upload all files except:
   - __pycache__/ folders
   - .env file (create new on server)
   - .git/ folder
   - README.md (optional)

## Required Files on PythonAnywhere
- passenger_wsgi.py (already created)
- requirements-prod.txt (production dependencies)
- app.py (Flask application factory)
- All ai_scholar/ folder contents
- All searches/ folder contents
- All utils/ folder contents
- All static/ folder contents
- All templates/ folder contents

## Environment Setup
Create .env file in project root with:
```
OPENAI_API_KEY=your_openai_key
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_key
CORE_API_KEY=your_core_api_key
CROSSREF_MAILTO=your_email@domain.com
GEMINI_API_KEY=your_gemini_key
SECRET_KEY=your_secret_key_for_sessions
```

## Installation Steps
1. Open Bash console on PythonAnywhere
2. Navigate to project directory
3. Install dependencies: pip3.10 install --user -r requirements-prod.txt
4. Initialize database: python3.10 -c "from app import create_app; app = create_app('production'); app.app_context().push(); from ai_scholar.endpoints import db; db.create_all()"

## Web App Configuration
- Source code: /home/yourusername/mysite/
- WSGI configuration file: /var/www/yourusername_pythonanywhere_com_wsgi.py
- Copy contents of passenger_wsgi.py to the WSGI file
- Set Python version to 3.10 (recommended for pandas compatibility)

## Python Version Notes
- Use Python 3.10 or 3.11 for best compatibility
- Avoid Python 3.13 due to pandas compilation issues
- PythonAnywhere supports Python 3.10 and 3.11

## Static Files
Configure static files mapping:
- URL: /static/
- Directory: /home/yourusername/mysite/static/

## Domain Access
Your app will be available at: yourusername.pythonanywhere.com
