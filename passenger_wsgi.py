import sys
import os

project_home = '/home/yourusername/ai_scholar'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

os.environ['FLASK_DEBUG'] = 'False'

from app import create_app
application = create_app()

if __name__ == "__main__":
    application.run()
