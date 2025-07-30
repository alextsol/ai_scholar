import os
from dotenv import load_dotenv

def setup_environment():
    load_dotenv()
    
    if not os.getenv('SECRET_KEY'):
        os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    
    if not os.getenv('DEV_DATABASE_URL'):
        os.environ['DEV_DATABASE_URL'] = 'sqlite:///scholar_search.db'
    
    if not os.getenv('FLASK_DEBUG'):
        os.environ['FLASK_DEBUG'] = 'True'

def get_config_name():
    if os.getenv('FLASK_DEBUG', 'True').lower() == 'false':
        return 'production'
    return 'development'
