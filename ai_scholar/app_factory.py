"""
Application factory for the new architecture
Handles initialization of all components in the correct order
"""

from flask import Flask
from typing import Optional, Dict, Any
from .services.service_factory import service_factory
from .controllers import controller_registry
from .providers import provider_registry
from .ai_bridge import ai_bridge
from .config.settings import Settings

class ApplicationFactory:
    """Factory for creating and configuring the Flask application with new architecture"""
    
    def __init__(self):
        self.app: Optional[Flask] = None
        self.config: Optional[Settings] = None
        self._initialized = False
    
    def create_app(self, config_name: Optional[str] = None) -> Flask:
        """
        Create Flask application with new architecture
        
        Args:
            config_name: Configuration name to use
        """
        
        # Initialize configuration
        self.config = Settings()
        
        return self._create_app_with_new_architecture(config_name)
    
    def _create_app_with_new_architecture(self, config_name: Optional[str]) -> Flask:
        """Create app with new MVC architecture"""
        
        import os
        template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
        static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
        
        app = Flask(__name__, 
                   template_folder=template_dir,
                   static_folder=static_dir)
        
        # Configure Flask app
        self._configure_flask_app(app, config_name)
        
        # Initialize all components in order
        self._initialize_providers()
        self._initialize_services()
        self._initialize_controllers(app)
        self._initialize_ai_bridge()
        
        self.app = app
        self._initialized = True
        
        return app

    def _configure_flask_app(self, app: Flask, config_name: Optional[str]):
        """Configure Flask application"""
        from config import config
        from runtime import get_config_name
        
        if config_name is None:
            config_name = get_config_name()
        
        app.config.from_object(config[config_name])
        
        # Initialize database
        from .models import db
        db.init_app(app)
        
        # Initialize login manager
        from flask_login import LoginManager
        from .models import User
        
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        login_manager.login_message = 'Please log in to access this page.'
        login_manager.login_message_category = 'info'
        
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))
        
        # Create database tables
        with app.app_context():
            db.create_all()
    
    def _initialize_providers(self):
        """Initialize all providers"""
        provider_registry.initialize_providers(self.config)
        
        available_search = provider_registry.get_available_search_backends()
        available_ai = provider_registry.get_available_ai_providers()
    
    def _initialize_services(self):
        """Initialize all services"""
        service_factory.initialize_services(self.config)
        
        services = list(service_factory.get_all_services().keys())
    
    def _initialize_controllers(self, app: Flask):
        """Initialize all controllers"""
        
        search_service = service_factory.get_search_service()
        paper_service = service_factory.get_paper_service()
        ai_service = service_factory.get_ai_service()
        controller_registry.initialize_controllers(
            app,
            search_service=search_service,
            paper_service=paper_service,
            ai_service=ai_service
        )
        
        controllers = list(controller_registry.get_all_controllers().keys())
        
        # Register auth blueprint (still needed for user authentication)
        try:
            from .endpoints.auth import auth_bp
            app.register_blueprint(auth_bp, url_prefix='/auth')
        except ImportError as e:
            pass
    
    def _initialize_ai_bridge(self):
        """Initialize AI bridge for backward compatibility"""
        ai_bridge.initialize()

    def get_app(self) -> Optional[Flask]:
        """Get the Flask application instance"""
        return self.app
    
    def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name"""
        return service_factory.get_service(name)
    
    def get_controller(self, name: str) -> Optional[Any]:
        """Get a controller by name"""
        return controller_registry.get_controller(name)
    
    def is_initialized(self) -> bool:
        """Check if application is initialized"""
        return self._initialized

# Global application factory
app_factory = ApplicationFactory()
