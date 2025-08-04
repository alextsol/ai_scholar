/**
 * HISTORY.JS - Search History page functionality
 * Handles filtering, searching, view switching, and history management
 */

class HistoryPage {
    constructor() {
        this.currentView = 'list';
        this.currentFilter = 'all';
        this.currentTimeFilter = 7; // days
        this.searchTerm = '';
        this.init();
    }

    init() {
        this.setupViewToggle();
        this.setupFilters();
        this.setupSearch();
        this.setupHistoryActions();
        this.setupTimeFilters();
        this.applyInitialFilters();
    }

    /**
     * View Toggle (List vs Grid)
     */
    setupViewToggle() {
        const viewButtons = document.querySelectorAll('.view-btn');
        const listView = document.getElementById('historyList');
        const gridView = document.getElementById('historyGrid');

        viewButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const view = btn.dataset.view;
                this.switchView(view, viewButtons, listView, gridView);
            });
        });
    }

    switchView(view, buttons, listView, gridView) {
        this.currentView = view;

        // Update button states
        buttons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });

        // Switch views
        if (view === 'list') {
            listView.style.display = 'block';
            gridView.style.display = 'none';
        } else {
            listView.style.display = 'none';
            gridView.style.display = 'block';
        }

        // Reapply filters to new view
        this.applyAllFilters();
    }

    /**
     * Backend Filters
     */
    setupFilters() {
        const filterButtons = document.querySelectorAll('.filter-btn');
        
        filterButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.setActiveFilter(btn, filterButtons);
                this.currentFilter = btn.dataset.filter;
                this.applyAllFilters();
            });
        });
    }

    setActiveFilter(activeBtn, allButtons) {
        allButtons.forEach(btn => btn.classList.remove('active'));
        activeBtn.classList.add('active');
    }

    /**
     * Time Filters
     */
    setupTimeFilters() {
        const timeButtons = document.querySelectorAll('.time-filter');
        
        timeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.setActiveFilter(btn, timeButtons);
                this.currentTimeFilter = parseInt(btn.dataset.days);
                this.applyAllFilters();
            });
        });
    }

    /**
     * Search Functionality
     */
    setupSearch() {
        const searchInput = document.getElementById('historySearch');
        if (searchInput) {
            const debouncedSearch = this.debounce((e) => {
                this.searchTerm = e.target.value.toLowerCase();
                this.applyAllFilters();
            }, 300);

            searchInput.addEventListener('input', debouncedSearch);
        }
    }

    /**
     * History Actions
     */
    setupHistoryActions() {
        // Repeat search buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.repeat-search-btn')) {
                this.handleRepeatSearch(e.target.closest('.repeat-search-btn'));
            }
        });

        // Delete search buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.delete-search-btn')) {
                this.handleDeleteSearch(e.target.closest('.delete-search-btn'));
            }
        });

        // Toggle results buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.toggle-results-btn')) {
                this.handleToggleResults(e.target.closest('.toggle-results-btn'));
            }
        });

        // Clear all history
        const clearAllBtn = document.getElementById('clearAllHistory');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', this.handleClearAllHistory.bind(this));
        }
    }

    handleRepeatSearch(button) {
        const query = button.dataset.query;
        const backend = button.dataset.backend;
        const mode = button.dataset.mode;

        // Build URL with parameters
        const params = new URLSearchParams({
            query: query,
            backend: backend,
            mode: mode
        });

        // Redirect to home page with parameters
        window.location.href = `/?${params.toString()}`;
    }

    handleDeleteSearch(button) {
        const searchId = button.dataset.searchId;
        const query = button.dataset.query;
        
        if (confirm(`Delete search "${query}"?`)) {
            this.deleteSearchItem(searchId, button);
        }
    }

    async deleteSearchItem(searchId, button) {
        try {
            // Show loading state
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            button.disabled = true;

            const response = await fetch(`/history/delete/${searchId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();

            if (data.success) {
                // Remove the history item from DOM
                const historyItem = button.closest('.history-item, .history-card');
                if (historyItem) {
                    historyItem.style.transition = 'all 0.3s ease';
                    historyItem.style.transform = 'translateX(-100%)';
                    historyItem.style.opacity = '0';
                    
                    setTimeout(() => {
                        historyItem.remove();
                        this.updateStats();
                        this.checkEmptyState();
                    }, 300);
                }

                // Show success message
                this.showNotification('Search deleted from history', 'success');
            } else {
                throw new Error(data.error || 'Failed to delete search');
            }

        } catch (error) {
            console.error('Error deleting search:', error);
            this.showNotification('Failed to delete search', 'error');
            
            // Restore button
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }

    handleToggleResults(button) {
        const targetId = button.dataset.target;
        const resultsDiv = document.querySelector(targetId);
        
        if (resultsDiv) {
            const isCollapsed = !resultsDiv.classList.contains('show');
            
            // Close other open results first
            document.querySelectorAll('.search-results-preview.show, .card-results.show').forEach(other => {
                if (other !== resultsDiv) {
                    other.classList.remove('show');
                    const otherBtn = document.querySelector(`[data-target="#${other.id}"]`);
                    if (otherBtn) {
                        otherBtn.innerHTML = otherBtn.innerHTML.replace('Hide', 'View');
                    }
                }
            });

            // Toggle current results
            resultsDiv.classList.toggle('show');
            
            // Update button text
            if (isCollapsed) {
                button.innerHTML = button.innerHTML.replace('View', 'Hide');
            } else {
                button.innerHTML = button.innerHTML.replace('Hide', 'View');
            }
        }
    }

    async handleClearAllHistory() {
        if (confirm('Are you sure you want to clear all search history? This action cannot be undone.')) {
            try {
                const response = await fetch('/history/clear', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });

                const data = await response.json();

                if (data.success) {
                    // Reload the page to show empty state
                    window.location.reload();
                } else {
                    throw new Error(data.error || 'Failed to clear history');
                }

            } catch (error) {
                console.error('Error clearing history:', error);
                this.showNotification('Failed to clear history', 'error');
            }
        }
    }

    /**
     * Filtering Logic
     */
    applyInitialFilters() {
        // Apply time filter by default (last 7 days)
        this.applyAllFilters();
    }

    applyAllFilters() {
        const items = this.getCurrentViewItems();
        
        items.forEach(item => {
            let show = true;

            // Apply backend filter
            if (this.currentFilter !== 'all') {
                const backend = item.dataset.backend;
                if (backend !== this.currentFilter) {
                    show = false;
                }
            }

            // Apply time filter
            if (this.currentTimeFilter > 0) {
                const itemDate = new Date(item.dataset.date);
                const cutoffDate = new Date();
                cutoffDate.setDate(cutoffDate.getDate() - this.currentTimeFilter);
                
                if (itemDate < cutoffDate) {
                    show = false;
                }
            }

            // Apply search filter
            if (this.searchTerm) {
                const query = item.dataset.query || '';
                const queryText = item.querySelector('.query-text, .card-title');
                const text = queryText ? queryText.textContent.toLowerCase() : query.toLowerCase();
                
                if (!text.includes(this.searchTerm)) {
                    show = false;
                }
            }

            // Show/hide item
            if (show) {
                item.classList.remove('hidden');
                item.classList.add('fade-in');
            } else {
                item.classList.add('hidden');
                item.classList.remove('fade-in');
            }
        });

        this.checkEmptyState();
    }

    getCurrentViewItems() {
        if (this.currentView === 'list') {
            return document.querySelectorAll('#historyList .history-item');
        } else {
            return document.querySelectorAll('#historyGrid .history-card');
        }
    }

    checkEmptyState() {
        const items = this.getCurrentViewItems();
        const visibleItems = Array.from(items).filter(item => !item.classList.contains('hidden'));
        
        if (visibleItems.length === 0 && items.length > 0) {
            this.showEmptyFilterState();
        } else {
            this.hideEmptyFilterState();
        }
    }

    showEmptyFilterState() {
        let emptyState = document.querySelector('.filter-empty-state');
        if (!emptyState) {
            emptyState = document.createElement('div');
            emptyState.className = 'filter-empty-state empty-state';
            emptyState.innerHTML = `
                <div class="empty-icon">
                    <i class="fas fa-filter fa-3x text-muted"></i>
                </div>
                <h3>No Results Found</h3>
                <p class="text-muted">Try adjusting your filters or search terms.</p>
                <button class="btn btn-outline-primary clear-filters-btn">
                    <i class="fas fa-times me-2"></i>Clear Filters
                </button>
            `;

            const clearBtn = emptyState.querySelector('.clear-filters-btn');
            clearBtn.addEventListener('click', this.clearAllFilters.bind(this));

            document.querySelector('.history-content').appendChild(emptyState);
        }
        emptyState.style.display = 'block';
    }

    hideEmptyFilterState() {
        const emptyState = document.querySelector('.filter-empty-state');
        if (emptyState) {
            emptyState.style.display = 'none';
        }
    }

    clearAllFilters() {
        // Reset filters
        this.currentFilter = 'all';
        this.currentTimeFilter = 0;
        this.searchTerm = '';

        // Reset UI
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === 'all');
        });

        document.querySelectorAll('.time-filter').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.days === '0');
        });

        const searchInput = document.getElementById('historySearch');
        if (searchInput) {
            searchInput.value = '';
        }

        this.applyAllFilters();
    }

    /**
     * Utility Functions
     */
    updateStats() {
        // Update the stats cards if needed
        const totalElement = document.querySelector('.stat-number');
        if (totalElement) {
            const currentTotal = parseInt(totalElement.textContent);
            totalElement.textContent = Math.max(0, currentTotal - 1);
        }
    }

    showNotification(message, type = 'info') {
        // Use the global notification system if available
        if (window.aiScholar && window.aiScholar.showNotification) {
            window.aiScholar.showNotification(message, type);
        } else {
            // Fallback to alert
            alert(message);
        }
    }

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
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.history-page')) {
        window.historyPage = new HistoryPage();
    }
});

// Export for potential external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HistoryPage;
}
