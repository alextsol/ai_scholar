import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    """Database configuration"""
    
    # SQLite (default)
    SQLITE_DATABASE_URI = f"sqlite:///{os.path.join(os.getcwd(), 'data', 'ai_scholar.db')}"
    
    # PostgreSQL (production)
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER = os.getenv("POSTGRES_USER", "ai_scholar")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE", "ai_scholar")
    
    @property
    def POSTGRES_DATABASE_URI(self):
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE}"
    
    # Current database URI
    DATABASE_URI = os.getenv("DATABASE_URI", SQLITE_DATABASE_URI)
    
    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Flask-Login settings
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-in-production")
    REMEMBER_COOKIE_DURATION = int(os.getenv("REMEMBER_COOKIE_DURATION", "86400"))  # 24 hours
    
    @classmethod
    def validate(cls):
        """Validate database configuration"""
        errors = []
        
        if not cls.SECRET_KEY or cls.SECRET_KEY == "dev-key-change-in-production":
            if not cls.DEBUG:  # Only error in production
                errors.append("SECRET_KEY must be set to a secure value in production")
        
        if cls.DATABASE_URI.startswith("postgresql://"):
            if not cls.POSTGRES_PASSWORD:
                errors.append("POSTGRES_PASSWORD is required for PostgreSQL")
        
        if errors:
            raise ValueError(f"Database configuration errors: {', '.join(errors)}")
        
        return True
