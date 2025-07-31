// Handle clicking on previous search items and history management
document.addEventListener("DOMContentLoaded", function() {
    // Add click handlers to search history items
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
                const searchId = item.dataset.searchId;
                
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
                
                // Fetch and display stored results if available
                if (searchId) {
                    fetch(`/history/results/${searchId}`)
                        .then(response => response.json())
                        .then(data => {
                            const resultsContent = document.getElementById('resultsContent');
                            const resultsSection = document.getElementById('resultsSection');
                            
                            if (resultsContent && data.results_html) {
                                resultsContent.innerHTML = data.results_html;
                                
                                const queryDisplay = document.getElementById('queryDisplay');
                                if (queryDisplay) {
                                    queryDisplay.textContent = data.query;
                                }
                                
                                const resultsCount = document.getElementById('resultsCount');
                                if (resultsCount) {
                                    resultsCount.textContent = `${data.results_count} papers found`;
                                }
                                
                                if (resultsSection) {
                                    resultsSection.style.display = 'block';
                                }
                            }
                        })
                        .catch(error => {
                            console.error('Error fetching stored results:', error);
                        });
                }
            });
        }
    });
    
    // Handle delete buttons
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
                        const listItem = this.closest('li');
                        if (listItem) {
                            listItem.remove();
                        }
                        
                        const remainingItems = document.querySelectorAll('#searchHistoryTabs li[data-query]');
                        if (remainingItems.length === 0) {
                            const tabsContainer = document.getElementById("searchHistoryTabs");
                            if (tabsContainer) {
                                tabsContainer.innerHTML = '<li class="list-group-item text-muted text-center"><em>No previous searches</em></li>';
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
    
    // Handle clear history button
    const clearButton = document.getElementById('clearHistoryButton');
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            if (confirm('Are you sure you want to clear your search history?')) {
                fetch('/history/clear', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                }).then(() => {
                    window.location.reload();
                }).catch(error => {
                    console.error('Error clearing history:', error);
                    alert('Failed to clear history. Please try again.');
                });
            }
        });
    }
});

// Add some CSS for better interaction
const style = document.createElement('style');
style.textContent = `
    #searchHistoryTabs li[data-query] .flex-grow-1:hover {
        background-color: #f8f9fa !important;
    }
    #searchHistoryTabs li[data-query].active {
        background-color: #e3f2fd !important;
        border-left: 4px solid #2196f3 !important;
    }
    .delete-search-btn {
        border: 1px solid #dc3545 !important;
        background-color: transparent !important;
        color: #dc3545 !important;
        padding: 4px 8px !important;
        font-size: 16px !important;
        font-weight: bold !important;
        line-height: 1 !important;
        width: 32px !important;
        height: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 50% !important;
        transition: all 0.2s ease !important;
    }
    .delete-search-btn:hover {
        background-color: #dc3545 !important;
        color: white !important;
        border-color: #dc3545 !important;
        transform: scale(1.1) !important;
    }
    .delete-search-btn:active {
        transform: scale(0.95) !important;
    }
`;
document.head.appendChild(style);

// Legacy functions for backward compatibility
function getSearchHistory() { return []; }
function saveSearchHistory(history) {}
function addSearchHistory(query, resultsHTML, source) {}
function clearSearchHistory() {
    fetch('/history/clear', { method: 'POST' }).then(() => {
        window.location.reload();
    });
}
function updateHistoryTabs() {}
function displayHistory(index) {}

window.SearchHistory = {
    addSearchHistory,
    clearSearchHistory,
    updateHistoryTabs,
    getSearchHistory,
    displayHistory,
};

window.getSearchHistory = getSearchHistory;
window.saveSearchHistory = saveSearchHistory;
window.addSearchHistory = addSearchHistory;
window.clearSearchHistory = clearSearchHistory;
window.updateHistoryTabs = updateHistoryTabs;
window.displayHistory = displayHistory;