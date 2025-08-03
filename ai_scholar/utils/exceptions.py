"""
Custom exceptions for AI Scholar application with user-friendly error messages
"""
from typing import Optional, Dict, Any
import time

class AIScholarError(Exception):
    """Base exception for AI Scholar application"""
    
    def __init__(self, message: str, user_message: Optional[str] = None, error_code: Optional[str] = None):
        super().__init__(message)
        self.user_message = user_message or message
        self.error_code = error_code
        self.timestamp = time.time()

class ConfigurationError(AIScholarError):
    """Exception raised for configuration-related errors"""
    pass

class ProviderError(AIScholarError):
    """Exception raised for provider-related errors"""
    
    def __init__(self, provider_name: str, message: str, user_message: Optional[str] = None, error_code: Optional[str] = None):
        self.provider_name = provider_name
        final_user_message = user_message or f"Service temporarily unavailable: {provider_name}"
        super().__init__(f"{provider_name}: {message}", final_user_message, error_code)

class RateLimitError(ProviderError):
    """Exception raised when API rate limits are exceeded"""
    
    def __init__(self, provider_name: str, retry_after_seconds: int = None, message: str = None):
        self.retry_after_seconds = retry_after_seconds or self._get_default_retry_time(provider_name)
        
        default_message = f"Rate limit exceeded for {provider_name}"
        if message:
            default_message = message
            
        # Create user-friendly message
        if self.retry_after_seconds:
            if self.retry_after_seconds < 60:
                time_str = f"{self.retry_after_seconds} seconds"
            elif self.retry_after_seconds < 3600:
                time_str = f"{self.retry_after_seconds // 60} minutes"
            else:
                time_str = f"{self.retry_after_seconds // 3600} hours"
            
            user_message = f"{provider_name} is temporarily rate-limited. Please wait {time_str} before trying again."
        else:
            user_message = f"{provider_name} is temporarily unavailable due to rate limiting. Please try again in a few minutes."
        
        super().__init__(provider_name, default_message, user_message, "RATE_LIMIT_EXCEEDED")

    @staticmethod
    def _get_default_retry_time(provider_name: str) -> int:
        """Get default retry time based on provider"""
        defaults = {
            'crossref': 60,      # 1 minute - CrossRef is usually quick to recover
            'core': 300,         # 5 minutes - CORE can be more restrictive
            'semantic_scholar': 120,  # 2 minutes - Semantic Scholar moderate
            'arxiv': 60          # 1 minute - arXiv is generally lenient
        }
        return defaults.get(provider_name.lower(), 180)  # Default 3 minutes

class APIUnavailableError(ProviderError):
    """Exception raised when API service is completely unavailable"""
    
    def __init__(self, provider_name: str, status_code: Optional[int] = None, message: str = None):
        self.status_code = status_code
        
        default_message = f"{provider_name} API is unavailable"
        if status_code:
            default_message += f" (HTTP {status_code})"
        if message:
            default_message = message
            
        user_message = f"{provider_name} service is currently unavailable. Please try again later or use a different search provider."
        
        super().__init__(provider_name, default_message, user_message, "API_UNAVAILABLE")

class AuthenticationError(ProviderError):
    """Exception raised for authentication/authorization errors"""
    
    def __init__(self, provider_name: str, message: str = None):
        default_message = message or f"Authentication failed for {provider_name}"
        user_message = f"{provider_name} authentication failed. Please check API key configuration or contact support."
        
        super().__init__(provider_name, default_message, user_message, "AUTH_FAILED")

class SearchError(AIScholarError):
    """Exception raised for search-related errors"""
    
    def __init__(self, message: str, user_message: str = None):
        final_user_message = user_message or "Search failed. Please try again with different terms."
        super().__init__(message, final_user_message, "SEARCH_FAILED")

class ValidationError(AIScholarError):
    """Exception raised for validation errors"""
    
    def __init__(self, message: str, field: str = None, user_message: str = None):
        self.field = field
        final_user_message = user_message or f"Invalid input: {message}"
        super().__init__(message, final_user_message, "VALIDATION_ERROR")

class AIProcessingError(AIScholarError):
    """Exception raised for AI processing errors"""
    
    def __init__(self, message: str, user_message: str = None, ai_provider: str = None):
        self.ai_provider = ai_provider
        final_user_message = user_message or "AI processing temporarily unavailable. Please try again later."
        super().__init__(message, final_user_message, "AI_PROCESSING_ERROR")

class QuotaExceededError(AIProcessingError):
    """Exception raised when AI service quota is exceeded"""
    
    def __init__(self, ai_provider: str, reset_time: Optional[int] = None, message: str = None):
        self.reset_time = reset_time
        
        default_message = message or f"Quota exceeded for {ai_provider}"
        
        if reset_time:
            time_str = f"{reset_time // 3600} hours" if reset_time >= 3600 else f"{reset_time // 60} minutes"
            user_message = f"AI service quota exceeded. Service will reset in approximately {time_str}."
        else:
            user_message = "AI service quota exceeded. Please try again later or contact support."
        
        super().__init__(default_message, user_message, ai_provider)
        self.error_code = "QUOTA_EXCEEDED"

class NetworkError(AIScholarError):
    """Exception raised for network-related errors"""
    
    def __init__(self, message: str, user_message: str = None):
        final_user_message = user_message or "Network connection issue. Please check your internet connection and try again."
        super().__init__(message, final_user_message, "NETWORK_ERROR")

class TimeoutError(AIScholarError):
    """Exception raised for timeout errors"""
    
    def __init__(self, service: str = None, timeout_seconds: int = None, message: str = None):
        self.service = service
        self.timeout_seconds = timeout_seconds
        
        default_message = message or f"Request timed out"
        if service:
            default_message += f" for {service}"
        if timeout_seconds:
            default_message += f" after {timeout_seconds}s"
            
        user_message = f"Request timed out. The service may be slow or unavailable. Please try again."
        
        super().__init__(default_message, user_message, "TIMEOUT_ERROR")

class CacheError(AIScholarError):
    """Exception raised for cache-related errors"""
    
    def __init__(self, message: str, user_message: str = None):
        final_user_message = user_message or "Cache system error. Results may be slower than usual."
        super().__init__(message, final_user_message, "CACHE_ERROR")

class DataProcessingError(AIScholarError):
    """Exception raised for data processing errors"""
    
    def __init__(self, message: str, user_message: str = None):
        final_user_message = user_message or "Error processing search results. Please try again or contact support."
        super().__init__(message, final_user_message, "DATA_PROCESSING_ERROR")

# Helper functions for creating specific errors
def create_rate_limit_error(provider_name: str, retry_after: int = None, headers: Dict[str, str] = None) -> RateLimitError:
    """Create a rate limit error, optionally parsing retry time from headers"""
    if headers and not retry_after:
        # Try to parse retry time from common headers
        retry_after = (
            headers.get('Retry-After') or
            headers.get('X-RateLimit-Reset') or 
            headers.get('X-Rate-Limit-Reset')
        )
        if retry_after:
            try:
                retry_after = int(retry_after)
            except (ValueError, TypeError):
                retry_after = None
    
    return RateLimitError(provider_name, retry_after)

def create_api_error(provider_name: str, status_code: int, response_text: str = None) -> ProviderError:
    """Create appropriate error based on HTTP status code"""
    if status_code == 401:
        return AuthenticationError(provider_name)
    elif status_code == 403:
        return AuthenticationError(provider_name, "Access forbidden. Check API permissions.")
    elif status_code == 429:
        return create_rate_limit_error(provider_name)
    elif status_code >= 500:
        return APIUnavailableError(provider_name, status_code, "Server error")
    else:
        message = f"HTTP {status_code}"
        if response_text:
            message += f": {response_text[:100]}"
        return APIUnavailableError(provider_name, status_code, message)
