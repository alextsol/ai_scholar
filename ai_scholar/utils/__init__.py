"""
Utilities package - Shared utilities and helpers
"""
from .ai_utils import parse_ai_response, is_quota_error, create_paper_summary, create_description_summary
from .paper_processing_utils import PaperProcessingUtils
from .exceptions import (
    AIScholarError, ConfigurationError, ProviderError, RateLimitError,
    APIUnavailableError, AuthenticationError, SearchError, ValidationError,
    AIProcessingError, QuotaExceededError, NetworkError, TimeoutError,
    CacheError, DataProcessingError, create_rate_limit_error, create_api_error
)
from .error_handler import ErrorHandler, handle_api_error, handle_provider_error

__all__ = [
    "parse_ai_response", "is_quota_error", "create_paper_summary", "create_description_summary",
    "PaperProcessingUtils",
    "AIScholarError", "ConfigurationError", "ProviderError", "RateLimitError",
    "APIUnavailableError", "AuthenticationError", "SearchError", "ValidationError",
    "AIProcessingError", "QuotaExceededError", "NetworkError", "TimeoutError",
    "CacheError", "DataProcessingError", "create_rate_limit_error", "create_api_error",
    "ErrorHandler", "handle_api_error", "handle_provider_error"
]
