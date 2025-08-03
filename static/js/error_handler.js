/**
 * Enhanced error handling for AI Scholar frontend
 */

class ErrorHandler {
    constructor() {
        this.initializeErrorDisplay();
    }

    initializeErrorDisplay() {
        // Create error container if it doesn't exist
        if (!document.getElementById('error-container')) {
            const container = document.createElement('div');
            container.id = 'error-container';
            container.className = 'fixed-top mt-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
    }

    /**
     * Display user-friendly error messages
     */
    displayError(error, type = 'error') {
        const container = document.getElementById('error-container');
        if (!container) return;

        let message = error.message || error.toString();
        let alertClass = 'alert-danger';
        let title = 'Error';

        // Handle different error types
        if (error.error_code) {
            switch (error.error_code) {
                case 'RATE_LIMIT_EXCEEDED':
                    alertClass = 'alert-warning';
                    title = 'Service Temporarily Limited';
                    if (error.retry_after_seconds) {
                        const timeStr = this.formatWaitTime(error.retry_after_seconds);
                        message += ` Please wait ${timeStr} before trying again.`;
                    }
                    break;
                    
                case 'API_UNAVAILABLE':
                    alertClass = 'alert-warning';
                    title = 'Service Unavailable';
                    message = error.message || `${error.provider || 'Search service'} is temporarily unavailable. Please try a different search provider or try again later.`;
                    break;
                    
                case 'AUTH_FAILED':
                    alertClass = 'alert-danger';
                    title = 'Authentication Error';
                    break;
                    
                case 'VALIDATION_ERROR':
                    alertClass = 'alert-info';
                    title = 'Input Error';
                    break;
                    
                case 'NETWORK_ERROR':
                    alertClass = 'alert-warning';
                    title = 'Connection Problem';
                    break;
                    
                case 'TIMEOUT_ERROR':
                    alertClass = 'alert-warning';
                    title = 'Request Timed Out';
                    break;
                    
                case 'QUOTA_EXCEEDED':
                    alertClass = 'alert-warning';
                    title = 'Service Limit Reached';
                    break;
            }
        }

        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert ${alertClass} alert-dismissible fade show mx-3`;
        alert.setAttribute('role', 'alert');
        
        alert.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-${this.getIconForType(error.error_code)} me-2"></i>
                <div>
                    <strong>${title}:</strong> ${message}
                </div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        // Add to container
        container.appendChild(alert);

        // Auto-hide after delay (longer for rate limit errors)
        const hideDelay = error.error_code === 'RATE_LIMIT_EXCEEDED' ? 10000 : 7000;
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, hideDelay);
    }

    /**
     * Format wait times in user-friendly format
     */
    formatWaitTime(seconds) {
        if (seconds < 60) {
            return `${seconds} seconds`;
        } else if (seconds < 3600) {
            const minutes = Math.ceil(seconds / 60);
            return `${minutes} minute${minutes > 1 ? 's' : ''}`;
        } else {
            const hours = Math.ceil(seconds / 3600);
            return `${hours} hour${hours > 1 ? 's' : ''}`;
        }
    }

    /**
     * Get appropriate icon for error type
     */
    getIconForType(errorCode) {
        switch (errorCode) {
            case 'RATE_LIMIT_EXCEEDED':
                return 'clock';
            case 'API_UNAVAILABLE':
                return 'server';
            case 'AUTH_FAILED':
                return 'lock';
            case 'VALIDATION_ERROR':
                return 'info-circle';
            case 'NETWORK_ERROR':
                return 'wifi';
            case 'TIMEOUT_ERROR':
                return 'clock';
            case 'QUOTA_EXCEEDED':
                return 'gauge-high';
            default:
                return 'exclamation-triangle';
        }
    }

    /**
     * Handle AJAX errors with better user experience
     */
    handleAjaxError(xhr, textStatus, errorThrown) {
        let errorMessage = 'An unexpected error occurred.';
        let errorObject = null;

        try {
            if (xhr.responseJSON) {
                errorObject = xhr.responseJSON;
                errorMessage = errorObject.message || errorMessage;
            } else if (xhr.responseText) {
                const parsed = JSON.parse(xhr.responseText);
                errorObject = parsed;
                errorMessage = parsed.message || errorMessage;
            }
        } catch (e) {
            // Handle non-JSON responses
            if (xhr.status === 429) {
                errorObject = {
                    error_code: 'RATE_LIMIT_EXCEEDED',
                    message: 'Rate limit exceeded. Please wait before trying again.',
                    retry_after_seconds: 60
                };
            } else if (xhr.status >= 500) {
                errorObject = {
                    error_code: 'API_UNAVAILABLE',
                    message: 'Server error. Please try again later.'
                };
            } else if (xhr.status === 0) {
                errorObject = {
                    error_code: 'NETWORK_ERROR',
                    message: 'Network connection problem. Please check your internet connection.'
                };
            }
        }

        if (errorObject) {
            this.displayError(errorObject);
        } else {
            this.displayError({ message: errorMessage });
        }
    }

    /**
     * Show provider-specific guidance
     */
    showProviderGuidance(provider) {
        const guidelines = {
            'crossref': {
                name: 'CrossRef',
                rateLimit: '50 requests per second',
                suggestion: 'Try searching for more specific terms or use fewer concurrent searches.'
            },
            'core': {
                name: 'CORE',
                rateLimit: '10 requests per minute',
                suggestion: 'CORE has stricter rate limits. Consider using different search terms or trying again in a few minutes.'
            },
            'semantic_scholar': {
                name: 'Semantic Scholar',
                rateLimit: '100 requests per 5 minutes',
                suggestion: 'Try using more specific search terms or wait a few minutes before searching again.'
            },
            'arxiv': {
                name: 'arXiv',
                rateLimit: '3 seconds between requests',
                suggestion: 'arXiv prefers slower request rates. Please wait a moment between searches.'
            }
        };

        const info = guidelines[provider.toLowerCase()];
        if (info) {
            this.displayError({
                error_code: 'RATE_LIMIT_EXCEEDED',
                message: `${info.name} rate limit: ${info.rateLimit}. ${info.suggestion}`
            });
        }
    }
}

// Initialize global error handler
const globalErrorHandler = new ErrorHandler();

// Enhanced AJAX setup with error handling
$(document).ready(function() {
    // Set up global AJAX error handling
    $(document).ajaxError(function(event, xhr, settings, thrownError) {
        globalErrorHandler.handleAjaxError(xhr, 'error', thrownError);
    });

    // Override default error display for forms
    window.showError = function(message, type = 'error') {
        globalErrorHandler.displayError({ message: message }, type);
    };

    // Provider status check
    window.checkProviderStatus = function(provider) {
        globalErrorHandler.showProviderGuidance(provider);
    };
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorHandler;
}
