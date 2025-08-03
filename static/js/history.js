// Handle clicking on previous search items and history management
document.addEventListener("DOMContentLoaded", function() {
    // Add click handlers to search history items (for index page sidebar)
    const historyItems = document.querySelectorAll('#searchHistoryTabs li[data-query]');
    
    historyItems.forEach((item, index) => {
        // Set cursor pointer only for the main content div
        const contentDiv = item.querySelector('.flex-grow-1');
        if (contentDiv) {
            contentDiv.style.cursor = 'pointer';
            
            contentDiv.addEventListener('click', function(e) {
                e.stopPropagation();
                
                const query = item.dataset.query;
                const backend = item.dataset.backend;
                const mode = item.dataset.mode;
                
                // Fill the form with the previous search data
                const queryInput = document.querySelector('input[name="query"]');
                const backendSelect = document.querySelector('select[name="backend"]');
                
                if (queryInput) queryInput.value = query;
                if (backendSelect) backendSelect.value = backend;
                
                // Set the mode radio button
                const modeRadio = document.querySelector(`input[name="mode"][value="${mode}"]`);
                if (modeRadio) {
                    modeRadio.checked = true;
                    modeRadio.dispatchEvent(new Event('change'));
                }
                
                // Highlight the selected item
                historyItems.forEach(h => h.classList.remove('active'));
                item.classList.add('active');
            });
        }
    });
    
    // Handle delete buttons (for both index page sidebar and history page)
    const deleteButtons = document.querySelectorAll('.delete-search-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            
            const searchId = this.dataset.searchId;
            const query = this.dataset.query;
            
            if (confirm(`Are you sure you want to delete the search "${query}"?`)) {
                fetch(`/history/delete/${searchId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Remove from sidebar (index page)
                        const sidebarItem = this.closest('li');
                        if (sidebarItem) {
                            sidebarItem.remove();
                            
                            const remainingItems = document.querySelectorAll('#searchHistoryTabs li[data-query]');
                            if (remainingItems.length === 0) {
                                const tabsContainer = document.getElementById("searchHistoryTabs");
                                if (tabsContainer) {
                                    tabsContainer.innerHTML = '<div class="text-center text-muted py-4"><i class="fas fa-search fa-2x mb-3 opacity-50"></i><p><em>No previous searches</em></p></div>';
                                }
                            }
                        }
                        
                        // Remove from history page table
                        const tableRow = this.closest('tr');
                        if (tableRow) {
                            tableRow.remove();
                            
                            // Check if table is empty and reload page to show "no history" message
                            const remainingRows = document.querySelectorAll('tbody tr');
                            if (remainingRows.length === 0) {
                                window.location.reload();
                            }
                        }
                    } else {
                        alert('Failed to delete search. Please try again.');
                    }
                })
                .catch(error => {
                    console.error('Error deleting search:', error);
                    alert('Failed to delete search. Please try again.');
                });
            }
        });
    });
    
    // Handle clear history button on dedicated history page
    const clearButtonHistory = document.getElementById('clearHistoryButtonHistory');
    if (clearButtonHistory) {
        clearButtonHistory.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (confirm('Are you sure you want to clear all search history? This action cannot be undone.')) {
                fetch('/history/clear', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                }).then(response => {
                    if (response.ok) {
                        window.location.reload();
                    } else {
                        alert('Failed to clear history. Please try again.');
                    }
                }).catch(error => {
                    console.error('Error clearing history:', error);
                    alert('Failed to clear history. Please try again.');
                });
            }
        });
    }
    
    // Handle repeat search buttons (for history page)
    const repeatButtons = document.querySelectorAll('.repeat-search-btn');
    repeatButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            
            const query = this.dataset.query;
            const backend = this.dataset.backend;
            const mode = this.dataset.mode;
            
            // Redirect to index page with search parameters
            const params = new URLSearchParams({
                query: query,
                backend: backend,
                mode: mode || ''
            });
            
            window.location.href = `/?${params.toString()}`;
        });
    });
    
    // Handle view results buttons (for history page)
    const viewButtons = document.querySelectorAll('.view-results-btn');
    viewButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            
            const searchId = this.dataset.searchId;
            
            // Show loading in modal
            const resultsContent = document.getElementById('resultsContent');
            resultsContent.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
            
            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('resultsModal'));
            modal.show();
            
            // Fetch results
            fetch(`/history/results/${searchId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        resultsContent.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    } else {
                        // Display results (you can customize this format)
                        resultsContent.innerHTML = `
                            <div class="mb-3">
                                <strong>Query:</strong> ${data.query}<br>
                                <strong>Results Found:</strong> ${data.results_count || 0}
                            </div>
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-1"></i>
                                Detailed results display can be implemented here.
                            </div>
                        `;
                    }
                })
                .catch(error => {
                    console.error('Error fetching results:', error);
                    resultsContent.innerHTML = '<div class="alert alert-danger">Failed to load results. Please try again.</div>';
                });
        });
    });
    
    // Initialize tooltips for history page
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Legacy functions for backward compatibility
function clearSearchHistory() {
    fetch('/history/clear', { method: 'POST' }).then(() => {
        window.location.reload();
    });
}

// Export for use by main.js
window.clearSearchHistory = clearSearchHistory;