/**
 * AIScholarBase - Core functionality for AI Scholar application
 * Provides dark mode, loading states, smooth scrolling, and UI utilities
 */
class AIScholarBase {
    constructor() {
        this.init();
    }

    /**
     * Initialize all base functionality
     */
    init() {
        this.setupDarkMode();
        this.setupLoader();
        this.setupSmoothScrolling();
        this.setupTooltips();
        this.setupAnimations();
    }

    /**
     * Set up dark mode toggle functionality
     * Manages theme switching and localStorage persistence
     */
    setupDarkMode() {
        const darkModeToggle = document.getElementById('darkModeToggle');
        if (!darkModeToggle) return;

        // Load saved theme preference or default to light
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
        darkModeToggle.checked = savedTheme === 'dark';

        // Handle theme toggle events
        darkModeToggle.addEventListener('change', (e) => {
            const theme = e.target.checked ? 'dark' : 'light';
            this.setTheme(theme);
            localStorage.setItem('theme', theme);
        });
    }

    /**
     * Apply theme to document and update meta theme color
     * @param {string} theme - 'dark' or 'light'
     */
    setTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
        
        // Update meta theme color for mobile browsers
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            metaThemeColor.setAttribute('content', theme === 'dark' ? '#1a1a1a' : '#ffffff');
        }
    }

    /**
     * Initialize loader overlay functionality
     */
    setupLoader() {
        this.loader = document.getElementById('loader-overlay');
        if (!this.loader) return;

        // Auto-hide loader when page fully loads
        window.addEventListener('load', () => {
            this.hideLoader();
        });
    }

    /**
     * Show loading overlay with optional message
     * @param {string} message - Loading message to display
     */
    showLoader(message = 'Loading...') {
        if (!this.loader) return;
        
        const messageElement = this.loader.querySelector('p');
        if (messageElement) {
            messageElement.textContent = message;
        }
        
        this.loader.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    /**
     * Hide loading overlay and restore scrolling
     */
    hideLoader() {
        if (!this.loader) return;
        
        this.loader.classList.remove('show');
        document.body.style.overflow = '';
    }

    /**
     * Enable smooth scrolling for anchor links
     */
    setupSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    /**
     * Initialize Bootstrap tooltips
     */
    setupTooltips() {
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    }

    /**
     * Set up scroll-based animations using Intersection Observer
     */
    setupAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        }, observerOptions);

        // Observe elements with animation class
        document.querySelectorAll('.animate-on-scroll').forEach(el => {
            observer.observe(el);
        });
    }

    /**
     * Display notification toast message
     * @param {string} message - Message to display
     * @param {string} type - Alert type (success, error, warning, info, danger)
     * @param {number} duration - Auto-dismiss duration in milliseconds
     */
    showNotification(message, type = 'info', duration = 5000) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
        
        alertDiv.innerHTML = `
            <i class="fas fa-${this.getIconForType(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove notification after specified duration
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, duration);
    }

    /**
     * Get Font Awesome icon name for alert type
     * @param {string} type - Alert type
     * @returns {string} Icon name
     */
    getIconForType(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle',
            danger: 'exclamation-triangle'
        };
        return icons[type] || 'info-circle';
    }

    /**
     * Format numbers with comma separators
     * @param {number} num - Number to format
     * @returns {string} Formatted number string
     */
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    /**
     * Debounce function to limit execution frequency
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} Debounced function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Copy text to clipboard with fallback for older browsers
     * @param {string} text - Text to copy
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showNotification('Copied to clipboard!', 'success', 2000);
        } catch (err) {
            // Fallback for browsers without clipboard API
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {
                document.execCommand('copy');
                this.showNotification('Copied to clipboard!', 'success', 2000);
            } catch (err) {
                this.showNotification('Failed to copy text', 'error', 3000);
            }
            document.body.removeChild(textArea);
        }
    }
}

// Initialize AIScholar base functionality when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.aiScholar = new AIScholarBase();
    
    // Ensure Font Awesome is available for icons
    if (!document.querySelector('link[href*="font-awesome"]')) {
        const fontAwesome = document.createElement('link');
        fontAwesome.rel = 'stylesheet';
        fontAwesome.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css';
        document.head.appendChild(fontAwesome);
    }
});

// Export for CommonJS environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIScholarBase;
}
