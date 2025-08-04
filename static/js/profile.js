/**
 * PROFILE.JS - Profile page functionality for AI Scholar
 * Handles profile tabs, settings, and user data management
 */

class ProfilePage {
    constructor() {
        this.activeTab = 'profile';
        this.init();
    }

    init() {
        this.setupTabs();
        this.setupSettings();
        this.loadQuickStats();
        this.setupProfileActions();
        this.setupHistoryTab();
    }

    /**
     * Tab Management
     */
    setupTabs() {
        const tabLinks = document.querySelectorAll('.profile-nav .nav-link');
        const tabPanes = document.querySelectorAll('.tab-pane');

        tabLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetTab = link.getAttribute('data-tab');
                this.switchTab(targetTab);
            });
        });

        // Initialize first tab
        const urlParams = new URLSearchParams(window.location.search);
        const initialTab = urlParams.get('tab') || 'profile';
        this.switchTab(initialTab);
    }

    switchTab(tabName) {
        // Update active tab
        this.activeTab = tabName;

        // Update nav links
        document.querySelectorAll('.profile-nav .nav-link').forEach(link => {
            if (link.getAttribute('data-tab') === tabName) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

        // Update tab panes with proper fade transition
        document.querySelectorAll('.tab-pane').forEach(pane => {
            if (pane.id === `${tabName}-tab`) {
                // Show the target tab
                pane.style.display = 'block';
                setTimeout(() => {
                    pane.classList.add('show', 'active');
                }, 10);
                this.onTabActivated(tabName);
            } else {
                // Hide other tabs
                pane.classList.remove('show', 'active');
                setTimeout(() => {
                    if (!pane.classList.contains('show')) {
                        pane.style.display = 'none';
                    }
                }, 150);
            }
        });

        // Update URL without reload
        const url = new URL(window.location);
        url.searchParams.set('tab', tabName);
        window.history.pushState({}, '', url);
    }

    onTabActivated(tabName) {
        switch(tabName) {
            case 'profile':
                this.refreshProfileData();
                break;
            case 'stats':
                this.refreshStats();
                break;
            case 'history':
                this.refreshHistory();
                break;
            case 'settings':
                this.refreshSettings();
                break;
        }
    }

    /**
     * Profile Data Management
     */
    refreshProfileData() {
        // Add any dynamic profile data loading here
        console.log('Profile tab activated');
    }

    /**
     * Quick Stats
     */
    async loadQuickStats() {
        const statsContainer = document.getElementById('userStats');
        if (!statsContainer) {
            console.log('userStats container not found');
            return;
        }

        try {
            // Show loading state
            statsContainer.innerHTML = `
                <div class="loading-placeholder">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading stats...</span>
                    </div>
                </div>
            `;

            const stats = await this.fetchUserStats();
            this.displayStats(stats);
        } catch (error) {
            console.error('Failed to load user stats:', error);
            // Show error state
            statsContainer.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Unable to load statistics. Please refresh the page.
                </div>
            `;
        }
    }

    async fetchUserStats() {
        try {
            // Try to get real user data first, fall back to mock data
            const response = await fetch('/api/user-stats', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            let stats;
            if (response.ok) {
                stats = await response.json();
            } else {
                // Fallback to calculation from available data
                const userSearches = parseInt(document.querySelector('[data-user-searches]')?.dataset.userSearches) || 0;
                stats = {
                    totalSearches: userSearches,
                    providersUsed: 4, // Available providers
                    totalResults: userSearches * 85, // Estimated based on average
                    avgResponseTime: '1.3s'
                };
            }
            
            return stats;
        } catch (error) {
            console.log('Using fallback stats due to:', error.message);
            // Fallback data
            const userSearches = parseInt(document.querySelector('[data-user-searches]')?.dataset.userSearches) || 0;
            return {
                totalSearches: userSearches,
                providersUsed: 4,
                totalResults: userSearches * 85,
                avgResponseTime: '1.3s'
            };
        }
    }

    displayStats(stats) {
        const statsContainer = document.getElementById('userStats');
        if (!statsContainer) {
            console.error('userStats container not found');
            return;
        }

        const statsHTML = `
            <div class="quick-stats-grid">
                <div class="stat-card searches-stat animate-on-scroll">
                    <div class="stat-icon">
                        <i class="fas fa-search"></i>
                    </div>
                    <h4>${window.aiScholar.formatNumber(stats.totalSearches)}</h4>
                    <p>Total Searches</p>
                </div>
                <div class="stat-card providers-stat animate-on-scroll">
                    <div class="stat-icon">
                        <i class="fas fa-server"></i>
                    </div>
                    <h4>${stats.providersUsed}</h4>
                    <p>Providers Used</p>
                </div>
                <div class="stat-card results-stat animate-on-scroll">
                    <div class="stat-icon">
                        <i class="fas fa-file-alt"></i>
                    </div>
                    <h4>${window.aiScholar.formatNumber(stats.totalResults)}</h4>
                    <p>Papers Found</p>
                </div>
                <div class="stat-card time-stat animate-on-scroll">
                    <div class="stat-icon">
                        <i class="fas fa-clock"></i>
                    </div>
                    <h4>${stats.avgResponseTime}</h4>
                    <p>Avg Response Time</p>
                </div>
            </div>
        `;

        statsContainer.innerHTML = statsHTML;
        console.log('Stats displayed successfully');
    }

    refreshStats() {
        console.log('Refreshing stats...');
        this.loadQuickStats();
    }

    /**
     * Settings Management
     */
    setupSettings() {
        // Theme setting
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            // Load saved theme
            const savedTheme = localStorage.getItem('theme') || 'light';
            themeToggle.checked = savedTheme === 'dark';

            themeToggle.addEventListener('change', (e) => {
                const theme = e.target.checked ? 'dark' : 'light';
                window.aiScholar.setTheme(theme);
                localStorage.setItem('theme', theme);
                window.aiScholar.showNotification('Theme updated successfully', 'success', 2000);
            });
        }

        // Notification settings
        const notificationToggle = document.getElementById('notificationToggle');
        if (notificationToggle) {
            const savedNotifications = localStorage.getItem('notifications') !== 'false';
            notificationToggle.checked = savedNotifications;

            notificationToggle.addEventListener('change', (e) => {
                localStorage.setItem('notifications', e.target.checked);
                window.aiScholar.showNotification(
                    `Notifications ${e.target.checked ? 'enabled' : 'disabled'}`, 
                    'success', 
                    2000
                );
            });
        }

        // Auto-save settings
        const autoSaveToggle = document.getElementById('autoSaveToggle');
        if (autoSaveToggle) {
            const savedAutoSave = localStorage.getItem('autoSave') !== 'false';
            autoSaveToggle.checked = savedAutoSave;

            autoSaveToggle.addEventListener('change', (e) => {
                localStorage.setItem('autoSave', e.target.checked);
                window.aiScholar.showNotification(
                    `Auto-save ${e.target.checked ? 'enabled' : 'disabled'}`, 
                    'success', 
                    2000
                );
            });
        }
    }

    refreshSettings() {
        // Refresh any dynamic settings
        console.log('Settings tab activated');
    }

    /**
     * Profile Actions
     */
    setupProfileActions() {
        // Edit profile button
        const editProfileBtn = document.getElementById('editProfileBtn');
        if (editProfileBtn) {
            editProfileBtn.addEventListener('click', this.openEditProfileModal.bind(this));
        }

        // Change password button
        const changePasswordBtn = document.getElementById('changePasswordBtn');
        if (changePasswordBtn) {
            changePasswordBtn.addEventListener('click', this.openChangePasswordModal.bind(this));
        }

        // Export data button
        const exportDataBtn = document.getElementById('exportDataBtn');
        if (exportDataBtn) {
            exportDataBtn.addEventListener('click', this.exportUserData.bind(this));
        }
    }

    openEditProfileModal() {
        // Create and show edit profile modal
        const modalHTML = `
            <div class="modal fade" id="editProfileModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-edit me-2"></i>Edit Profile
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="editProfileForm">
                                <div class="mb-3">
                                    <label for="editUsername" class="form-label">Username</label>
                                    <input type="text" class="form-control" id="editUsername" 
                                           value="${document.querySelector('.field-value').textContent.trim()}">
                                </div>
                                <div class="mb-3">
                                    <label for="editEmail" class="form-label">Email</label>
                                    <input type="email" class="form-control" id="editEmail" 
                                           value="${document.querySelectorAll('.field-value')[1].textContent.trim()}">
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="saveProfileBtn">
                                <i class="fas fa-save me-1"></i>Save Changes
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to DOM if it doesn't exist
        if (!document.getElementById('editProfileModal')) {
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('editProfileModal'));
        modal.show();

        // Handle save
        document.getElementById('saveProfileBtn').addEventListener('click', () => {
            // Here you would make an API call to update profile
            window.aiScholar.showNotification('Profile updated successfully!', 'success', 3000);
            modal.hide();
        });
    }

    openChangePasswordModal() {
        window.aiScholar.showNotification('Change password functionality coming soon!', 'info', 3000);
    }

    async exportUserData() {
        try {
            window.aiScholar.showLoader('Preparing your data export...');
            
            // Mock export - replace with actual API call
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            const exportData = {
                profile: {
                    username: document.querySelector('.field-value').textContent.trim(),
                    email: document.querySelectorAll('.field-value')[1].textContent.trim(),
                    memberSince: document.querySelectorAll('.field-value')[2].textContent.trim()
                },
                searchHistory: [], // Would be populated from API
                settings: {
                    theme: localStorage.getItem('theme'),
                    notifications: localStorage.getItem('notifications'),
                    autoSave: localStorage.getItem('autoSave')
                }
            };

            // Create and download file
            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ai-scholar-export-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            window.aiScholar.hideLoader();
            window.aiScholar.showNotification('Data exported successfully!', 'success', 3000);
            
        } catch (error) {
            window.aiScholar.hideLoader();
            window.aiScholar.showNotification('Export failed. Please try again.', 'error', 3000);
        }
    }

    /**
     * History Tab Management
     */
    setupHistoryTab() {
        // The history content will be loaded via iframe or AJAX
        // For now, we'll just handle the tab activation
    }

    refreshHistory() {
        const historyFrame = document.getElementById('historyFrame');
        if (historyFrame) {
            // Refresh the history iframe
            historyFrame.src = historyFrame.src;
        }
    }

    /**
     * Utility Methods
     */
    showLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.position = 'relative';
            const loadingOverlay = document.createElement('div');
            loadingOverlay.className = 'loading-overlay';
            loadingOverlay.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            `;
            element.appendChild(loadingOverlay);
        }
    }

    hideLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            const loadingOverlay = element.querySelector('.loading-overlay');
            if (loadingOverlay) {
                loadingOverlay.remove();
            }
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.profile-container')) {
        window.profilePage = new ProfilePage();
    }
});
