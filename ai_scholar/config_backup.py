import os
from dotenv import load_dotenv

load_dotenv()

class AIConfig:
    GOOGLE_API_KEYS = [
        os.getenv("GOOGLE_API_KEY"),
        os.getenv("GOOGLE_API_KEY2"),
        os.getenv("GOOGLE_API_KEY3")
    ]
    
    OPENROUTER_API_KEY = os.getenv("HORIZON_ALPHA_KEY")
    
    GEMINI_MODEL = "models/gemini-2.5-flash-lite"
    OPENROUTER_MODEL = "openrouter/horizon-alpha"
    
    GOOGLE_MAX_TOKENS = 65536
    OPENROUTER_MAX_TOKENS = 32768
    
    TEMPERATURE = 0.3
    TOP_P = 0.95
    TOP_K = 40
    
    GOOGLE_BATCH_SIZE = 35
    OPENROUTER_BATCH_SIZE = 25
    
    QUOTA_COOLDOWN_HOURS = 1
    RETRY_DELAY_SECONDS = 2

class SearchConfig:
    DEFAULT_LIMIT = 50
    MAX_AI_RESULT_LIMIT = 100
    DEFAULT_AI_RESULT_LIMIT = 50
    
    CITATION_WEIGHT_AI = 0.3
    CITATION_WEIGHT_CITATION = 0.5
    
    MIN_EXPLANATION_LENGTH = 20
    DESCRIPTION_WORD_RANGE = (40, 80)

class AppConfig:
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))
