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
    
    def create_app(self, config_name: Optional[str] = None, use_new_architecture: bool = True) -> Flask:
        """
        Create Flask application with new architecture
        
        Args:
            config_name: Configuration name to use
            use_new_architecture: Whether to use new architecture (True) or legacy (False)
        """
        
        # Initialize configuration
        self.config = Settings()
        
        if use_new_architecture:
            return self._create_app_with_new_architecture(config_name)
        else:
            return self._create_app_legacy_mode(config_name)
    
    def _create_app_with_new_architecture(self, config_name: Optional[str]) -> Flask:
        """Create app with new MVC architecture"""
        print("🚀 Initializing AI Scholar with new architecture...")
        
        # Create Flask app with correct template and static paths
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
        
        # Register legacy blueprints for backward compatibility
        self._register_legacy_blueprints(app)
        
        self.app = app
        self._initialized = True
        
        print("✅ AI Scholar initialized with new architecture")
        return app
    
    def _create_app_legacy_mode(self, config_name: Optional[str]) -> Flask:
        """Create app with legacy architecture (fallback)"""
        print("⚠️  Initializing AI Scholar in legacy mode...")
        
        # Use existing create_app function
        from app import create_app
        return create_app(config_name)
    
    def _configure_flask_app(self, app: Flask, config_name: Optional[str]):
        """Configure Flask application"""
        # Import existing config
        from config import config
        from runtime import get_config_name
        
        if config_name is None:
            config_name = get_config_name()
        
        app.config.from_object(config[config_name])
        
        # Initialize database
        from .models.database import db
        db.init_app(app)
        
        # Initialize login manager
        from flask_login import LoginManager
        from .models.database import User
        
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
        print("📡 Initializing providers...")
        provider_registry.initialize_providers(self.config)
        
        available_search = provider_registry.get_available_search_backends()
        available_ai = provider_registry.get_available_ai_providers()
        
        print(f"   - Search providers: {available_search}")
        print(f"   - AI providers: {available_ai}")
    
    def _initialize_services(self):
        """Initialize all services"""
        print("⚙️  Initializing services...")
        service_factory.initialize_services(self.config)
        
        services = list(service_factory.get_all_services().keys())
        print(f"   - Services: {services}")
    
    def _initialize_controllers(self, app: Flask):
        """Initialize all controllers"""
        print("🎮 Initializing controllers...")
        
        # Get services for dependency injection
        search_service = service_factory.get_search_service()
        paper_service = service_factory.get_paper_service()
        ai_service = service_factory.get_ai_service()
        
        # Initialize controllers with services
        controller_registry.initialize_controllers(
            app,
            search_service=search_service,
            paper_service=paper_service,
            ai_service=ai_service
        )
        
        controllers = list(controller_registry.get_all_controllers().keys())
        print(f"   - Controllers: {controllers}")
    
    def _initialize_ai_bridge(self):
        """Initialize AI bridge for backward compatibility"""
        print("🌉 Initializing AI bridge...")
        ai_bridge.initialize()
    
    def _register_legacy_blueprints(self, app: Flask):
        """Register legacy blueprints for backward compatibility"""
        print("🔗 Registering legacy blueprints...")
        
        try:
            # Try to register existing blueprints
            from .endpoints.endpoints import bp as main_bp
            app.register_blueprint(main_bp, url_prefix='/legacy')
            print("   - Legacy main blueprint registered")
        except ImportError as e:
            print(f"   - Warning: Could not register legacy main blueprint: {e}")
        
        try:
            from .endpoints.auth import auth_bp
            app.register_blueprint(auth_bp, url_prefix='/auth')
            print("   - Auth blueprint registered")
        except ImportError as e:
            print(f"   - Warning: Could not register auth blueprint: {e}")
        
        try:
            from .endpoints.history import history_bp
            app.register_blueprint(history_bp, url_prefix='/legacy/history')
            print("   - History blueprint registered")
        except ImportError as e:
            print(f"   - Warning: Could not register history blueprint: {e}")
        
        print("   - Legacy blueprints registration completed")
    
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
