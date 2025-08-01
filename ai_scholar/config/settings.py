import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Main application settings"""
    
    # Application settings
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))
    
    # Search settings
    DEFAULT_LIMIT = 50
    MAX_AI_RESULT_LIMIT = 100
    DEFAULT_AI_RESULT_LIMIT = 50
    
    # Ranking settings
    CITATION_WEIGHT_AI = 0.3
    CITATION_WEIGHT_CITATION = 0.5
    MIN_EXPLANATION_LENGTH = 20
    DESCRIPTION_WORD_RANGE = (40, 80)
    
    # Cache settings
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # 1 hour
    CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))
    
    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "data/logs/ai_scholar.log")
    
    @classmethod
    def validate(cls):
        """Validate configuration settings"""
        errors = []
        
        if cls.PORT < 1 or cls.PORT > 65535:
            errors.append("PORT must be between 1 and 65535")
        
        if cls.DEFAULT_LIMIT <= 0:
            errors.append("DEFAULT_LIMIT must be positive")
        
        if cls.MAX_AI_RESULT_LIMIT <= 0:
            errors.append("MAX_AI_RESULT_LIMIT must be positive")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True
