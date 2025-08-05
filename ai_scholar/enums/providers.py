from enum import Enum

class ProviderType(Enum):
    CROSSREF = "crossref"
    ARXIV = "arxiv" 
    SEMANTIC_SCHOLAR = "semantic_scholar"
    CORE = "core"
    OPENALEX = "openalex"
    
class AIProviderType(Enum):
    """Enum for AI providers"""
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    