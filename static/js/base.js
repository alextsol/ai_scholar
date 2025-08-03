/**
 * BASE.JS - Core JavaScript functionality for AI Scholar
 * Handles common features like dark mode, loader, and basic interactions
 */

class AIScholarBase {
    constructor() {
        this.init();
    }

    init() {
        this.setupDarkMode();
        this.setupLoader();
        this.setupSmoothScrolling();
        this.setupTooltips();
        this.setupAnimations();
    }

    /**
     * Dark Mode Functionality
     */
    setupDarkMode() {
        const darkModeToggle = document.getElementById('darkModeToggle');
        if (!darkModeToggle) return;

        // Load saved theme preference
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
        darkModeToggle.checked = savedTheme === 'dark';

        // Handle toggle
        darkModeToggle.addEventListener('change', (e) => {
            const theme = e.target.checked ? 'dark' : 'light';
            this.setTheme(theme);
            localStorage.setItem('theme', theme);
        });
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
        
        // Update meta theme color for mobile browsers
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            metaThemeColor.setAttribute('content', theme === 'dark' ? '#1a1a1a' : '#ffffff');
        }
    }

    /**
     * Loader Functionality
     */
    setupLoader() {
        this.loader = document.getElementById('loader-overlay');
        if (!this.loader) return;

        // Auto-hide loader on page load
        window.addEventListener('load', () => {
            this.hideLoader();
        });
    }

    showLoader(message = 'Loading...') {
        if (!this.loader) return;
        
        const messageElement = this.loader.querySelector('p');
        if (messageElement) {
            messageElement.textContent = message;
        }
        
        this.loader.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    hideLoader() {
        if (!this.loader) return;
        
        this.loader.classList.remove('show');
        document.body.style.overflow = '';
    }

    /**
     * Smooth Scrolling for Anchor Links
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
     * Initialize Bootstrap Tooltips
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
     * Setup Page Animations
     */
    setupAnimations() {
        // Fade in elements on scroll
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
     * Utility Functions
     */
    
    // Show notification
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
        
        // Auto remove after duration
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, duration);
    }

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

    // Format numbers with commas
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    // Debounce function for search inputs
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

    // Copy text to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showNotification('Copied to clipboard!', 'success', 2000);
        } catch (err) {
            // Fallback for older browsers
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

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.aiScholar = new AIScholarBase();
    
    // Add Font Awesome if not present
    if (!document.querySelector('link[href*="font-awesome"]')) {
        const fontAwesome = document.createElement('link');
        fontAwesome.rel = 'stylesheet';
        fontAwesome.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css';
        document.head.appendChild(fontAwesome);
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIScholarBase;
}
