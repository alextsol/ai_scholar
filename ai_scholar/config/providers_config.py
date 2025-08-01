import os
from dotenv import load_dotenv

load_dotenv()

class ProvidersConfig:
    """Configuration for all external providers"""
    
    class AI:
        GOOGLE_API_KEYS = [
            os.getenv("GOOGLE_API_KEY"),
            os.getenv("GOOGLE_API_KEY2"),
            os.getenv("GOOGLE_API_KEY3")
        ]
        GEMINI_MODEL = "models/gemini-2.5-flash-lite"
        GOOGLE_MAX_TOKENS = 65536
        GOOGLE_BATCH_SIZE = 35
        
        OPENROUTER_API_KEY = os.getenv("HORIZON_ALPHA_KEY")
        OPENROUTER_MODEL = "openrouter/horizon-alpha"
        OPENROUTER_MAX_TOKENS = 32768
        OPENROUTER_BATCH_SIZE = 25
        
        TEMPERATURE = 0.3
        TOP_P = 0.95
        TOP_K = 40
        QUOTA_COOLDOWN_HOURS = 1
        RETRY_DELAY_SECONDS = 2
    
    class Search:
        SEMANTIC_SCHOLAR_API_URL = os.getenv("SEMANTIC_SCHOLAR_API_URL", "https://api.semanticscholar.org/graph/v1/paper/search")
        
        CROSSREF_API_URL = os.getenv("CROSSREF_API_URL", "https://api.crossref.org/works")
        
        CORE_API_URL = os.getenv("CORE_API_URL", "https://api.core.ac.uk/v3/search/works")
        CORE_API_KEY = os.getenv("CORE_API_KEY")
        
        DEFAULT_SEARCH_BACKEND = os.getenv("DEFAULT_SEARCH_BACKEND", "semantic_scholar")
    
    @classmethod 
    def validate_ai_config(cls):
        """Validate AI provider configuration"""
        errors = []
        
        google_keys = [key for key in cls.AI.GOOGLE_API_KEYS if key]
        if not google_keys and not cls.AI.OPENROUTER_API_KEY:
            errors.append("At least one AI API key (Google or OpenRouter) is required")
        
        if errors:
            raise ValueError(f"AI configuration errors: {', '.join(errors)}")
        
        return True
    
    @classmethod
    def validate_search_config(cls):
        """Validate search provider configuration"""
        errors = []
        
        if cls.Search.DEFAULT_SEARCH_BACKEND == "core" and not cls.Search.CORE_API_KEY:
            errors.append("CORE_API_KEY is required when using CORE as default backend")
        
        if errors:
            raise ValueError(f"Search configuration errors: {', '.join(errors)}")
        
        return True
