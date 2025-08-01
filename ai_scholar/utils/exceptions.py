"""
Custom exceptions for AI Scholar
"""

class AIScholarError(Exception):
    """Base exception for AI Scholar application"""
    pass

class ConfigurationError(AIScholarError):
    """Exception raised for configuration-related errors"""
    pass

class ProviderError(AIScholarError):
    """Exception raised for provider-related errors"""
    
    def __init__(self, provider_name: str, message: str):
        self.provider_name = provider_name
        super().__init__(f"{provider_name}: {message}")

class SearchError(AIScholarError):
    """Exception raised for search-related errors"""
    pass

class AIProcessingError(AIScholarError):
    """Exception raised for AI processing errors"""
    pass

class CacheError(AIScholarError):
    """Exception raised for cache-related errors"""
    pass

class ValidationError(AIScholarError):
    """Exception raised for validation errors"""
    pass
