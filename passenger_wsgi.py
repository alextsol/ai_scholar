import sys
import os

# Add your project directory to Python path
# Replace 'yourusername' with your actual PythonAnywhere username
project_home = '/home/yourusername/ai_scholar'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables for production
os.environ['FLASK_DEBUG'] = 'False'

# Import your Flask application
from app import create_app
application = create_app()

# Required for PythonAnywhere WSGI
if __name__ == "__main__":
    application.run()
