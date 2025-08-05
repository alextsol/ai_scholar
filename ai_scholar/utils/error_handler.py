"""
Centralized error handling utility for AI Scholar application
"""
import logging
from typing import Tuple, Dict, Any, Optional
from flask import jsonify
import requests

from .exceptions import (
    AIScholarError, RateLimitError, APIUnavailableError, AuthenticationError,
    NetworkError, TimeoutError, create_api_error, create_rate_limit_error
)

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling for consistent user experience"""
    
    @staticmethod
    def handle_provider_request_error(provider_name: str, error: Exception, response: requests.Response = None) -> AIScholarError:
        """Convert various provider errors into appropriate AIScholarError types"""
        
        # Handle requests exceptions
        if isinstance(error, requests.exceptions.ConnectionError):
            logger.error(f"{provider_name} connection error: {error}")
            return NetworkError(f"Connection failed to {provider_name}", 
                              f"Unable to connect to {provider_name}. Please check your internet connection.")
        
        elif isinstance(error, requests.exceptions.Timeout):
            logger.error(f"{provider_name} timeout: {error}")
            return TimeoutError(provider_name, message=str(error))
        
        elif isinstance(error, requests.exceptions.RequestException):
            logger.error(f"{provider_name} request error: {error}")
            return NetworkError(f"Network error with {provider_name}: {error}")
        
        # Handle HTTP response errors
        if response is not None:
            status_code = response.status_code
            
            if status_code == 429:
                # Extract retry time from headers if available
                retry_after = response.headers.get('Retry-After')
                rate_limit_reset = response.headers.get('X-RateLimit-Reset')
                
                retry_seconds = None
                if retry_after:
                    try:
                        retry_seconds = int(retry_after)
                    except (ValueError, TypeError):
                        pass
                elif rate_limit_reset:
                    try:
                        retry_seconds = int(rate_limit_reset)
                    except (ValueError, TypeError):
                        pass
                
                logger.warning(f"{provider_name} rate limited (429). Retry after: {retry_seconds}")
                return create_rate_limit_error(provider_name, retry_seconds, response.headers)
            
            else:
                logger.error(f"{provider_name} HTTP error {status_code}: {response.text[:200]}")
                return create_api_error(provider_name, status_code, response.text)
        
        # Generic error
        logger.error(f"{provider_name} unexpected error: {error}")
        return APIUnavailableError(provider_name, message=str(error))
    
    @staticmethod
    def format_error_response(error: Exception, include_details: bool = False) -> Tuple[Dict[str, Any], int]:
        """Format error for JSON API response"""
        
        if isinstance(error, AIScholarError):
            response_data = {
                'error': True,
                'message': error.user_message,
                'error_code': error.error_code,
                'timestamp': getattr(error, 'timestamp', None)
            }
            
            # Add specific error details
            if isinstance(error, RateLimitError):
                response_data['retry_after_seconds'] = error.retry_after_seconds
                response_data['provider'] = error.provider_name
                status_code = 429
            
            elif isinstance(error, AuthenticationError):
                response_data['provider'] = error.provider_name
                status_code = 401
            
            elif isinstance(error, APIUnavailableError):
                response_data['provider'] = error.provider_name
                response_data['status_code'] = error.status_code
                status_code = 503
            
            elif isinstance(error, (NetworkError, TimeoutError)):
                status_code = 503
            
            else:
                status_code = 400
            
            if include_details:
                response_data['technical_message'] = str(error)
                response_data['error_type'] = type(error).__name__
        
        else:
            logger.error(f"Unhandled error: {error}")
            response_data = {
                'error': True,
                'message': "An unexpected error occurred. Please try again later.",
                'error_code': 'UNKNOWN_ERROR'
            }
            status_code = 500
            
            if include_details:
                response_data['technical_message'] = str(error)
                response_data['error_type'] = type(error).__name__
        
        return response_data, status_code
    
    @staticmethod
    def format_flash_message(error: Exception) -> Tuple[str, str]:
        """Format error for Flask flash messages"""
        
        if isinstance(error, AIScholarError):
            return error.user_message, 'error'
        else:
            return "An unexpected error occurred. Please try again later.", 'error'
    
    @staticmethod
    def log_error(error: Exception, context: str = "", user_id: str = None):
        """Log error with context"""
        
        log_data = {
            'error_type': type(error).__name__,
            'message': str(error),
            'context': context
        }
        
        if user_id:
            log_data['user_id'] = user_id
        
        if isinstance(error, AIScholarError):
            log_data['error_code'] = error.error_code
            log_data['user_message'] = error.user_message
            
            if hasattr(error, 'provider_name'):
                log_data['provider'] = error.provider_name
        
        logger.error(f"Error in {context}: {log_data}")

def handle_api_error(func):
    """Decorator for consistent API error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AIScholarError as e:
            ErrorHandler.log_error(e, func.__name__)
            response_data, status_code = ErrorHandler.format_error_response(e)
            return jsonify(response_data), status_code
        except Exception as e:
            ErrorHandler.log_error(e, func.__name__)
            response_data, status_code = ErrorHandler.format_error_response(e)
            return jsonify(response_data), status_code
    
    wrapper.__name__ = func.__name__
    return wrapper

def handle_provider_error(provider_name: str):
    """Decorator for provider-specific error handling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                # Get response if available
                response = getattr(e, 'response', None)
                error = ErrorHandler.handle_provider_request_error(provider_name, e, response)
                raise error
            except AIScholarError:
                # Re-raise AIScholarError as-is
                raise
            except Exception as e:
                # Convert generic errors to provider errors
                logger.error(f"{provider_name} unexpected error in {func.__name__}: {e}")
                raise APIUnavailableError(provider_name, message=str(e))
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator
