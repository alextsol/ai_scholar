/**
 * SEARCH.JS - Search page functionality for AI Scholar
 * Handles search form interactions, result display, and search-specific features
 */

class SearchPage {
    constructor() {
        this.searchForm = document.querySelector('.search-form form');
        this.resultsContainer = document.querySelector('.results-container');
        this.init();
    }

    init() {
        if (this.searchForm) {
            this.setupSearchForm();
            this.setupFormValidation();
            this.setupAutoSave();
        }
        
        this.setupResultInteractions();
        this.setupProviderStatus();
    }

    /**
     * Search Form Setup
     */
    setupSearchForm() {
        this.searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSearch();
        });

        // Real-time search suggestions (debounced)
        const queryInput = document.getElementById('query');
        if (queryInput) {
            const debouncedSuggestions = window.aiScholar.debounce(
                this.showSearchSuggestions.bind(this), 
                300
            );
            queryInput.addEventListener('input', debouncedSuggestions);
        }

        // Dynamic form updates
        const modeSelect = document.getElementById('mode');
        if (modeSelect) {
            modeSelect.addEventListener('change', this.handleModeChange.bind(this));
        }
    }

    async handleSearch() {
        const formData = new FormData(this.searchForm);
        const searchData = Object.fromEntries(formData);

        // Validate required fields
        if (!searchData.query || searchData.query.trim().length < 2) {
            window.aiScholar.showNotification('Please enter a search query with at least 2 characters', 'warning');
            return;
        }

        // Show loader with search message
        window.aiScholar.showLoader('Searching academic papers...');

        try {
            // Submit form normally for now, but prepare for AJAX
            this.searchForm.submit();
            
        } catch (error) {
            console.error('Search error:', error);
            window.aiScholar.hideLoader();
            window.aiScholar.showNotification('Search failed. Please try again.', 'error');
        }
    }

    /**
     * Form Validation
     */
    setupFormValidation() {
        const inputs = this.searchForm.querySelectorAll('input[required], select[required]');
        
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearFieldError(input));
        });
    }

    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let message = '';

        switch(field.type) {
            case 'text':
                if (field.hasAttribute('required') && !value) {
                    isValid = false;
                    message = 'This field is required';
                } else if (field.name === 'query' && value.length < 2) {
                    isValid = false;
                    message = 'Search query must be at least 2 characters';
                }
                break;
                
            case 'number':
                const num = parseInt(value);
                if (value && (isNaN(num) || num < 1)) {
                    isValid = false;
                    message = 'Please enter a valid positive number';
                }
                break;
        }

        this.setFieldValidation(field, isValid, message);
        return isValid;
    }

    setFieldValidation(field, isValid, message) {
        const feedbackElement = field.parentNode.querySelector('.invalid-feedback');
        
        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
            if (feedbackElement) feedbackElement.remove();
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
            
            if (!feedbackElement) {
                const feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.textContent = message;
                field.parentNode.appendChild(feedback);
            } else {
                feedbackElement.textContent = message;
            }
        }
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid', 'is-valid');
        const feedbackElement = field.parentNode.querySelector('.invalid-feedback');
        if (feedbackElement) feedbackElement.remove();
    }

    /**
     * Auto-save Form State
     */
    setupAutoSave() {
        const formInputs = this.searchForm.querySelectorAll('input, select');
        
        formInputs.forEach(input => {
            // Load saved value
            const savedValue = localStorage.getItem(`search_${input.name}`);
            if (savedValue && !input.value) {
                input.value = savedValue;
            }

            // Save on change
            input.addEventListener('change', () => {
                localStorage.setItem(`search_${input.name}`, input.value);
            });
        });
    }

    /**
     * Search Suggestions
     */
    async showSearchSuggestions(event) {
        const query = event.target.value.trim();
        if (query.length < 3) return;

        // Remove existing suggestions
        this.clearSuggestions();

        // Create suggestions dropdown
        const suggestions = await this.fetchSuggestions(query);
        if (suggestions.length > 0) {
            this.displaySuggestions(event.target, suggestions);
        }
    }

    async fetchSuggestions(query) {
        // Mock suggestions for now - replace with actual API call
        const mockSuggestions = [
            'machine learning algorithms',
            'machine learning applications',
            'machine learning in healthcare',
            'machine learning neural networks'
        ];

        return mockSuggestions.filter(s => 
            s.toLowerCase().includes(query.toLowerCase())
        ).slice(0, 5);
    }

    displaySuggestions(input, suggestions) {
        const dropdown = document.createElement('div');
        dropdown.className = 'search-suggestions';
        dropdown.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 0 0 8px 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            z-index: 1000;
            max-height: 200px;
            overflow-y: auto;
        `;

        suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            item.textContent = suggestion;
            item.style.cssText = `
                padding: 12px 16px;
                cursor: pointer;
                border-bottom: 1px solid #f0f0f0;
                transition: background-color 0.2s;
            `;

            item.addEventListener('mouseenter', () => {
                item.style.backgroundColor = '#f8f9fa';
            });

            item.addEventListener('mouseleave', () => {
                item.style.backgroundColor = '';
            });

            item.addEventListener('click', () => {
                input.value = suggestion;
                this.clearSuggestions();
                input.focus();
            });

            dropdown.appendChild(item);
        });

        input.parentNode.style.position = 'relative';
        input.parentNode.appendChild(dropdown);

        // Close suggestions when clicking outside
        setTimeout(() => {
            document.addEventListener('click', this.handleSuggestionClickOutside.bind(this), { once: true });
        }, 100);
    }

    handleSuggestionClickOutside(event) {
        const suggestions = document.querySelector('.search-suggestions');
        if (suggestions && !suggestions.contains(event.target)) {
            this.clearSuggestions();
        }
    }

    clearSuggestions() {
        const existing = document.querySelector('.search-suggestions');
        if (existing) existing.remove();
    }

    /**
     * Mode Change Handler
     */
    handleModeChange(event) {
        const mode = event.target.value;
        const aiResultsGroup = document.querySelector('.ai-results-group');
        
        if (mode === 'aggregate') {
            if (aiResultsGroup) aiResultsGroup.style.display = 'block';
            window.aiScholar.showNotification('Aggregate mode will search multiple providers and rank results using AI', 'info', 4000);
        } else {
            if (aiResultsGroup) aiResultsGroup.style.display = 'none';
        }
    }

    /**
     * Result Interactions
     */
    setupResultInteractions() {
        // Copy citation functionality
        document.querySelectorAll('.copy-citation').forEach(button => {
            button.addEventListener('click', this.copyCitation.bind(this));
        });

        // Expand/collapse abstracts
        document.querySelectorAll('.abstract-toggle').forEach(button => {
            button.addEventListener('click', this.toggleAbstract.bind(this));
        });

        // Result item hover effects
        document.querySelectorAll('.result-item').forEach(item => {
            this.setupResultItemInteractions(item);
        });
    }

    copyCitation(event) {
        const button = event.target;
        const resultItem = button.closest('.result-item');
        const title = resultItem.querySelector('h4 a').textContent;
        const authors = resultItem.querySelector('.result-meta').textContent;
        
        const citation = `${title}. ${authors}`;
        window.aiScholar.copyToClipboard(citation);
    }

    toggleAbstract(event) {
        const button = event.target;
        const abstract = button.nextElementSibling;
        
        if (abstract.style.display === 'none' || !abstract.style.display) {
            abstract.style.display = 'block';
            button.textContent = 'Hide Abstract';
        } else {
            abstract.style.display = 'none';
            button.textContent = 'Show Abstract';
        }
    }

    setupResultItemInteractions(item) {
        // Add click tracking
        const link = item.querySelector('h4 a');
        if (link) {
            link.addEventListener('click', () => {
                // Track click analytics
                console.log('Paper clicked:', link.textContent);
            });
        }

        // Add keyboard navigation
        item.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && link) {
                link.click();
            }
        });
    }

    /**
     * Provider Status
     */
    setupProviderStatus() {
        const statusIndicators = document.querySelectorAll('.provider-badge');
        
        statusIndicators.forEach(badge => {
            // Add click handler to show provider info
            badge.addEventListener('click', () => {
                this.showProviderInfo(badge.textContent.trim());
            });

            // Add hover tooltip
            badge.setAttribute('data-bs-toggle', 'tooltip');
            badge.setAttribute('title', `Click for ${badge.textContent} information`);
        });
    }

    showProviderInfo(providerName) {
        const providerInfo = {
            'CrossRef': 'CrossRef provides comprehensive academic metadata and DOI services.',
            'arXiv': 'arXiv is a repository of electronic preprints approved for publication.',
            'Semantic Scholar': 'Semantic Scholar uses AI to understand scientific literature.',
            'CORE': 'CORE aggregates research papers from repositories and journals worldwide.'
        };

        const info = providerInfo[providerName] || 'Academic search provider';
        window.aiScholar.showNotification(`${providerName}: ${info}`, 'info', 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.search-form')) {
        window.searchPage = new SearchPage();
    }
});
