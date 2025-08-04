/**
 * INDEX.JS - Home page functionality for AI Scholar
 * Handles search form, history management, and dynamic form updates
 */

class IndexPage {
    constructor() {
        this.searchForm = document.getElementById('searchForm');
        this.searchHistory = document.getElementById('searchHistoryTabs');
        this.init();
    }

    init() {
        if (this.searchForm) {
            this.setupSearchForm();
            this.setupDynamicFormGroups();
            this.setupFormValidation();
        }
        
        if (this.searchHistory) {
            this.setupSearchHistory();
        }
        
        this.setupQuickSearch();
    }

    /**
     * Search Form Setup
     */
    setupSearchForm() {
        // Handle form submission
        this.searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSearch();
        });

        // Auto-complete functionality
        const queryInput = this.searchForm.querySelector('input[name="query"]');
        if (queryInput) {
            const debouncedAutoComplete = window.aiScholar.debounce(
                this.showAutoComplete.bind(this), 
                300
            );
            queryInput.addEventListener('input', debouncedAutoComplete);
        }

        // Mode change handlers
        const modeInputs = this.searchForm.querySelectorAll('input[name="mode"]');
        modeInputs.forEach(input => {
            input.addEventListener('change', this.handleModeChange.bind(this));
        });
    }

    async handleSearch() {
        const formData = new FormData(this.searchForm);
        const searchData = Object.fromEntries(formData);

        // Validate form
        if (!this.validateSearchForm(searchData)) {
            return;
        }

        // Show loading
        window.aiScholar.showLoader('Searching academic papers...');

        try {
            // Add to search history (localStorage for quick access)
            this.addToLocalHistory(searchData);
            
            // Submit form
            this.searchForm.submit();
            
        } catch (error) {
            console.error('Search error:', error);
            window.aiScholar.hideLoader();
            window.aiScholar.showNotification('Search failed. Please try again.', 'error');
        }
    }

    validateSearchForm(data) {
        if (!data.query || data.query.trim().length < 2) {
            window.aiScholar.showNotification('Please enter a search query with at least 2 characters', 'warning');
            const queryInput = this.searchForm.querySelector('input[name="query"]');
            queryInput.focus();
            return false;
        }

        // Validate year range
        if (data.min_year && data.max_year) {
            const minYear = parseInt(data.min_year);
            const maxYear = parseInt(data.max_year);
            
            if (minYear > maxYear) {
                window.aiScholar.showNotification('Minimum year cannot be greater than maximum year', 'warning');
                return false;
            }
        }

        // Validate result limits
        if (data.result_limit && parseInt(data.result_limit) > 500) {
            window.aiScholar.showNotification('Result limit cannot exceed 500', 'warning');
            return false;
        }

        if (data.ai_result_limit && parseInt(data.ai_result_limit) > 100) {
            window.aiScholar.showNotification('AI result limit cannot exceed 100', 'warning');
            return false;
        }

        return true;
    }

    /**
     * Dynamic Form Groups
     */
    setupDynamicFormGroups() {
        const modeInputs = this.searchForm.querySelectorAll('input[name="mode"]');
        
        modeInputs.forEach(input => {
            input.addEventListener('change', this.updateDynamicGroups.bind(this));
        });

        // Initial setup
        this.updateDynamicGroups();
    }

    updateDynamicGroups() {
        const selectedMode = this.searchForm.querySelector('input[name="mode"]:checked')?.value;
        
        // Get dynamic groups
        const rankingModeGroup = document.getElementById('rankingModeGroup');
        const resultLimitGroup = document.getElementById('resultLimitGroup');
        const aiResultLimitGroup = document.getElementById('aiResultLimitGroup');

        if (selectedMode === 'aggregate') {
            this.showGroup(rankingModeGroup);
            this.hideGroup(resultLimitGroup);
            this.showGroup(aiResultLimitGroup);
        } else {
            this.hideGroup(rankingModeGroup);
            this.showGroup(resultLimitGroup);
            this.hideGroup(aiResultLimitGroup);
        }
    }

    showGroup(element) {
        if (element) {
            element.style.display = 'block';
            element.classList.add('active');
            element.classList.remove('fade-out');
            element.classList.add('fade-in');
        }
    }

    hideGroup(element) {
        if (element) {
            element.classList.remove('active', 'fade-in');
            element.classList.add('fade-out');
            setTimeout(() => {
                element.style.display = 'none';
            }, 200);
        }
    }

    handleModeChange(event) {
        const mode = event.target.value;
        
        if (mode === 'aggregate') {
            window.aiScholar.showNotification(
                'Aggregate mode will search multiple providers and rank results using AI', 
                'info', 
                4000
            );
        }
        
        this.updateDynamicGroups();
    }

    /**
     * Form Validation
     */
    setupFormValidation() {
        const inputs = this.searchForm.querySelectorAll('input[required]');
        
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearFieldError(input));
        });
    }

    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let message = '';

        if (field.hasAttribute('required') && !value) {
            isValid = false;
            message = 'This field is required';
        } else if (field.name === 'query' && value.length < 2) {
            isValid = false;
            message = 'Search query must be at least 2 characters';
        } else if (field.type === 'number' && value) {
            const num = parseInt(value);
            if (isNaN(num) || num < 1) {
                isValid = false;
                message = 'Please enter a valid positive number';
            }
        }

        this.setFieldValidation(field, isValid, message);
        return isValid;
    }

    setFieldValidation(field, isValid, message) {
        field.classList.remove('is-invalid', 'is-valid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        
        if (isValid) {
            field.classList.add('is-valid');
            if (feedback) feedback.remove();
        } else {
            field.classList.add('is-invalid');
            
            if (!feedback) {
                const feedbackDiv = document.createElement('div');
                feedbackDiv.className = 'invalid-feedback';
                feedbackDiv.textContent = message;
                field.parentNode.appendChild(feedbackDiv);
            } else {
                feedback.textContent = message;
            }
        }
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid', 'is-valid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) feedback.remove();
    }

    /**
     * Auto-complete
     */
    async showAutoComplete(event) {
        const query = event.target.value.trim();
        if (query.length < 3) {
            this.clearAutoComplete();
            return;
        }

        const suggestions = await this.fetchAutoCompleteSuggestions(query);
        if (suggestions.length > 0) {
            this.displayAutoComplete(event.target, suggestions);
        }
    }

    async fetchAutoCompleteSuggestions(query) {
        // Get suggestions from localStorage history
        const localHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');
        const historySuggestions = localHistory
            .filter(item => item.query.toLowerCase().includes(query.toLowerCase()))
            .map(item => item.query)
            .slice(0, 3);

        // Add some common academic terms
        const commonTerms = [
            'machine learning', 'artificial intelligence', 'deep learning',
            'neural networks', 'computer vision', 'natural language processing',
            'data science', 'quantum computing', 'blockchain', 'cybersecurity'
        ];

        const termSuggestions = commonTerms
            .filter(term => term.toLowerCase().includes(query.toLowerCase()))
            .slice(0, 3);

        return [...new Set([...historySuggestions, ...termSuggestions])].slice(0, 5);
    }

    displayAutoComplete(input, suggestions) {
        this.clearAutoComplete();

        const dropdown = document.createElement('div');
        dropdown.className = 'autocomplete-dropdown';
        dropdown.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 0 0 8px 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            max-height: 200px;
            overflow-y: auto;
        `;

        suggestions.forEach((suggestion, index) => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.innerHTML = `
                <i class="fas fa-search me-2 text-muted"></i>
                ${this.highlightMatch(suggestion, input.value)}
            `;
            item.style.cssText = `
                padding: 12px 16px;
                cursor: pointer;
                border-bottom: 1px solid #f0f0f0;
                transition: background-color 0.2s;
                display: flex;
                align-items: center;
            `;

            item.addEventListener('mouseenter', () => {
                item.style.backgroundColor = '#f8f9fa';
            });

            item.addEventListener('mouseleave', () => {
                item.style.backgroundColor = '';
            });

            item.addEventListener('click', () => {
                input.value = suggestion;
                this.clearAutoComplete();
                input.focus();
            });

            dropdown.appendChild(item);
        });

        input.parentNode.style.position = 'relative';
        input.parentNode.appendChild(dropdown);

        // Close on outside click
        setTimeout(() => {
            document.addEventListener('click', this.handleAutoCompleteClickOutside.bind(this), { once: true });
        }, 100);
    }

    highlightMatch(text, query) {
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<strong class="text-primary">$1</strong>');
    }

    handleAutoCompleteClickOutside(event) {
        const dropdown = document.querySelector('.autocomplete-dropdown');
        if (dropdown && !dropdown.contains(event.target)) {
            this.clearAutoComplete();
        }
    }

    clearAutoComplete() {
        const existing = document.querySelector('.autocomplete-dropdown');
        if (existing) existing.remove();
    }

    /**
     * Search History Management
     */
    setupSearchHistory() {
        // Handle history item clicks
        this.searchHistory.addEventListener('click', (event) => {
            const historyItem = event.target.closest('.search-history-item');
            if (historyItem && !event.target.classList.contains('delete-search-btn')) {
                event.preventDefault();
                this.loadHistoryResults(historyItem);
            }
        });

        // Handle delete buttons
        this.searchHistory.addEventListener('click', (event) => {
            if (event.target.classList.contains('delete-search-btn')) {
                event.stopPropagation();
                this.deleteHistoryItem(event.target);
            }
        });

        // Clear history button
        const clearButton = document.getElementById('clearHistoryButtonIndex');
        if (clearButton) {
            clearButton.addEventListener('click', this.clearAllHistory.bind(this));
        }
    }

    async loadHistoryResults(historyItem) {
        const searchId = historyItem.dataset.searchId;
        
        if (!searchId) {
            window.aiScholar.showNotification('Search ID not found', 'error', 3000);
            return;
        }

        try {
            // Show loading state
            window.aiScholar.showLoader('Loading search results...');

            // Fetch the search details including results
            const response = await fetch(`/search/history/${searchId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const searchData = await response.json();
            
            // Display the results if they exist
            if (searchData.results_html) {
                this.displayResultsInMainArea(searchData);
            } else {
                // If no cached results, show notification
                window.aiScholar.showNotification(
                    'No cached results found for this search.', 
                    'warning', 
                    4000
                );
            }

        } catch (error) {
            console.error('Error loading search history:', error);
            window.aiScholar.showNotification(
                'Failed to load search results. Please try again.', 
                'error', 
                3000
            );
        } finally {
            window.aiScholar.hideLoader();
        }
    }

    displayResultsInMainArea(searchData) {
        // Find or create the results container
        let resultsContainer = document.querySelector('.results-section');
        
        if (!resultsContainer) {
            // Create the results container if it doesn't exist
            resultsContainer = document.createElement('div');
            resultsContainer.className = 'results-section animate-on-scroll mt-4';
            
            // Insert after the search form
            const searchSection = document.querySelector('.main-search-section');
            if (searchSection) {
                searchSection.insertAdjacentElement('afterend', resultsContainer);
            }
        }

        // Clear existing results
        resultsContainer.innerHTML = '';

        // Add header with search info
        const headerHtml = `
            <div class="result-stats">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h4>
                            <i class="fas fa-history me-2"></i>Previous Search Results
                        </h4>
                        <p class="mb-0">
                            Query: "${searchData.query}" • Backend: ${searchData.backend} • 
                            Found <strong>${searchData.results_count || 0}</strong> results • 
                            Date: ${new Date(searchData.created_at).toLocaleString()}
                        </p>
                    </div>
                    <button class="btn btn-outline-secondary btn-sm" onclick="this.closest('.results-section').style.display = 'none'">
                        <i class="fas fa-times me-1"></i>Clear
                    </button>
                </div>
            </div>
        `;

        // Add the results content in a result-grid wrapper to match normal results styling
        const resultsContentHtml = `
            <div class="result-grid">
                <div class="historical-results">
                    ${searchData.results_html || '<div class="alert alert-info">No results available for this search.</div>'}
                </div>
            </div>
        `;

        resultsContainer.innerHTML = headerHtml + resultsContentHtml;

        // Show the results container
        resultsContainer.style.display = 'block';

        // Scroll to results
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Show success notification
        window.aiScholar.showNotification(
            `Loaded ${searchData.results_count || 0} results for "${searchData.query}"`, 
            'success', 
            3000
        );
    }

    deleteHistoryItem(button) {
        const searchId = button.dataset.searchId;
        const query = button.dataset.query;
        
        if (confirm(`Delete search "${query}"?`)) {
            // Make AJAX call to delete from server
            fetch(`/history/delete/${searchId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Remove from DOM
                    button.closest('.search-history-item').remove();
                    window.aiScholar.showNotification('Search deleted from history', 'success', 2000);
                } else {
                    window.aiScholar.showNotification('Failed to delete search: ' + (data.error || 'Unknown error'), 'error');
                }
            })
            .catch(error => {
                console.error('Error deleting search:', error);
                window.aiScholar.showNotification('Failed to delete search', 'error');
            });
        }
    }

    clearAllHistory() {
        if (confirm('Are you sure you want to clear all search history?')) {
            // Make AJAX call to clear server history
            fetch('/history/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Clear from localStorage
                    localStorage.removeItem('searchHistory');
                    
                    // Clear all history items from DOM
                    const historyContainer = document.getElementById('searchHistoryTabs');
                    if (historyContainer) {
                        historyContainer.innerHTML = '<p class="text-muted">No recent searches</p>';
                    }
                    
                    window.aiScholar.showNotification('Search history cleared', 'success', 2000);
                } else {
                    window.aiScholar.showNotification('Failed to clear history: ' + (data.error || 'Unknown error'), 'error');
                }
            })
            .catch(error => {
                console.error('Error clearing history:', error);
                window.aiScholar.showNotification('Failed to clear history', 'error');
            });
        }
    }

    addToLocalHistory(searchData) {
        const history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
        
        const newEntry = {
            query: searchData.query,
            backend: searchData.backend,
            mode: searchData.mode,
            timestamp: new Date().toISOString()
        };

        // Remove duplicate queries
        const filtered = history.filter(item => item.query !== searchData.query);
        
        // Add new entry at beginning
        filtered.unshift(newEntry);
        
        // Keep only last 20 entries
        const trimmed = filtered.slice(0, 20);
        
        localStorage.setItem('searchHistory', JSON.stringify(trimmed));
    }

    /**
     * Quick Search
     */
    setupQuickSearch() {
        // Add quick search buttons for common queries
        const quickSearchContainer = document.getElementById('quickSearchContainer');
        if (quickSearchContainer) {
            const commonQueries = [
                'machine learning',
                'artificial intelligence',
                'climate change',
                'quantum computing',
                'gene therapy'
            ];

            commonQueries.forEach(query => {
                const button = document.createElement('button');
                button.className = 'btn btn-outline-primary btn-sm me-2 mb-2';
                button.textContent = query;
                button.addEventListener('click', () => {
                    const queryInput = this.searchForm.querySelector('input[name="query"]');
                    if (queryInput) {
                        queryInput.value = query;
                        queryInput.focus();
                    }
                });
                quickSearchContainer.appendChild(button);
            });
        }
    }

}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('searchForm')) {
        window.indexPage = new IndexPage();
    }
});
