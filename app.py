from flask import Flask
from ai_scholar.endpoints import bp as main_bp
from ai_scholar.endpoints.auth import auth_bp
from ai_scholar.endpoints.history import history_bp
from ai_scholar.models import db, User
from flask_login import LoginManager
from config import config
from runtime import setup_environment, get_config_name

def create_app(config_name=None):
    setup_environment()
    
    if config_name is None:
        config_name = get_config_name()
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(history_bp)

    with app.app_context():
        db.create_all()
    
    return app

def get_app():
    return create_app()
