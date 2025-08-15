// Main application initialization and coordination
class App {
    constructor() {
        this.initialized = false;
        this.init();
    }

    async init() {
        try {
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.start());
            } else {
                this.start();
            }
        } catch (error) {
            console.error('Error initializing app:', error);
            showToast('Error initializing application', 'error');
        }
    }

    async start() {
        console.log('Starting Democrasite application...');

        try {
            // Test API connection
            await this.testAPIConnection();
            
            // Initialize authentication
            await authManager.init();
            
            // Handle initial routing
            this.handleInitialRoute();
            
            // Setup periodic updates
            this.setupPeriodicUpdates();
            
            this.initialized = true;
            console.log('Democrasite initialized successfully');
            
        } catch (error) {
            console.error('Error starting application:', error);
            this.handleInitializationError(error);
        }
    }

    async testAPIConnection() {
        try {
            // Test with a simple unauthenticated endpoint (health check)
            const response = await fetch(`${api.baseURL}/docs`);
            if (response.ok) {
                console.log('API connection successful');
            } else {
                throw new Error('API not responding');
            }
        } catch (error) {
            console.warn('API connection test failed:', error);
            
            // Only show error if we're sure it's a connection issue
            if (error.message.includes('Failed to fetch') || error.message.includes('API not responding')) {
                showToast('Unable to connect to server. Some features may not work.', 'error', 10000);
            }
            
            // Don't throw - allow app to continue in offline mode
        }
    }

    handleInitialRoute() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // Handle direct topic links
        const topicShareCode = urlParams.get('topic');
        if (topicShareCode) {
            showSection('topicDetail');
            showTopic(topicShareCode);
            return;
        }
        
        // Handle share codes
        const shareCode = urlParams.get('share');
        if (shareCode) {
            this.handleShareCode(shareCode);
            return;
        }
        
        // Default behavior based on auth status
        if (authManager.isAuthenticated) {
            showSection('topicsDashboard');
            loadTopics();
        } else {
            showSection('commandCenter');
        }
    }

    async handleShareCode(shareCode) {
        try {
            if (!authManager.isAuthenticated) {
                // Store share code and prompt for login
                sessionStorage.setItem('pendingShareCode', shareCode);
                showToast('Please log in to access this topic', 'info');
                showAuthModal('login');
                return;
            }
            
            // Try to access the topic directly using the share code
            showTopic(shareCode);
            
            // Clean up URL
            window.history.replaceState({}, document.title, window.location.pathname);
            
        } catch (error) {
            console.error('Error handling share code:', error);
            // The showTopic method will handle the specific error message and navigation
            // This catch block is mainly for other unexpected errors
        }
    }

    setupPeriodicUpdates() {
        // Refresh topic results every 30 seconds when viewing a topic
        setInterval(() => {
            if (uiManager.currentSection === 'topicDetail' && topicsManager.currentTopic) {
                // Silently refresh the topic data
                topicsManager.showTopic(topicsManager.currentTopic.share_code);
            }
        }, 30000);

        // Refresh topics list every 60 seconds when on dashboard
        setInterval(() => {
            if (uiManager.currentSection === 'topicsDashboard' && authManager.isAuthenticated) {
                // Silently refresh topics with force refresh to get latest data
                topicsManager.loadTopics(topicsManager.searchQuery, false, true);
            }
        }, 60000);
    }

    handleInitializationError(error) {
        console.error('Failed to initialize application:', error);
        
        // Show error message
        const errorHTML = `
            <div style="text-align: center; padding: 2rem; max-width: 500px; margin: 2rem auto;">
                <i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: var(--error-color); margin-bottom: 1rem;"></i>
                <h2>Application Error</h2>
                <p style="margin-bottom: 1.5rem;">Failed to initialize the application. Please try refreshing the page.</p>
                <button class="btn btn-primary" onclick="window.location.reload()">Refresh Page</button>
            </div>
        `;
        
        const mainContent = document.querySelector('.app-main');
        if (mainContent) {
            mainContent.innerHTML = errorHTML;
        }
    }

    // Utility methods for global state management
    updatePageTitle(title) {
        document.title = title ? `${title} - Democrasite` : 'Democrasite - Voting Platform';
    }

    updateURL(path, params = {}) {
        const url = new URL(window.location);
        url.pathname = path;
        
        // Clear existing params
        url.search = '';
        
        // Add new params
        Object.entries(params).forEach(([key, value]) => {
            if (value) url.searchParams.set(key, value);
        });
        
        window.history.pushState({}, '', url);
    }

    // Analytics and tracking (placeholder for future implementation)
    trackEvent(event, data = {}) {
        console.log('Event:', event, data);
        // Could integrate with analytics services here
    }

    trackPageView(page) {
        console.log('Page view:', page);
        // Could integrate with analytics services here
    }
}

// Initialize the application
const app = new App();

// Global error handling
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    showToast('An unexpected error occurred', 'error');
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    showToast('An unexpected error occurred', 'error');
    event.preventDefault(); // Prevent console spam
});

// Service worker registration (for future PWA features)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', async () => {
        try {
            // Uncomment when you add a service worker
            // const registration = await navigator.serviceWorker.register('/sw.js');
            // console.log('ServiceWorker registration successful');
        } catch (error) {
            console.log('ServiceWorker registration failed');
        }
    });
}

// Authentication Modal Management
function showAuthModal(mode = 'login') {
    const modal = document.getElementById('authModal');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const modalTitle = document.getElementById('authModalTitle');
    const authSwitchText = document.getElementById('authSwitchText');
    const authSwitchBtn = document.getElementById('authSwitchBtn');

    if (!modal) return;

    if (mode === 'login') {
        modalTitle.textContent = 'Welcome Back';
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
        authSwitchText.textContent = "Don't have an account?";
        authSwitchBtn.textContent = 'Sign up';
        authSwitchBtn.onclick = () => showAuthModal('register');
    } else {
        modalTitle.textContent = 'Create Account';
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
        authSwitchText.textContent = 'Already have an account?';
        authSwitchBtn.textContent = 'Sign in';
        authSwitchBtn.onclick = () => showAuthModal('login');
    }

    showModal('authModal');
}

// Global function for auth modal
window.showAuthModal = showAuthModal;

// Dashboard functionality
document.addEventListener('DOMContentLoaded', () => {
    // Filter chips functionality
    const filterChips = document.querySelectorAll('.filter-chips .chip');
    filterChips.forEach(chip => {
        chip.addEventListener('click', (e) => {
            // Remove active from all chips
            filterChips.forEach(c => c.classList.remove('active'));
            // Add active to clicked chip
            e.target.classList.add('active');
            
            // Apply the filter by calling topicsManager
            const filter = e.target.getAttribute('data-filter');
            if (window.topicsManager) {
                window.topicsManager.applyFilter(filter);
            }
        });
    });

    // Sort dropdown functionality
    const sortDropdown = document.getElementById('sortBy');
    if (sortDropdown) {
        sortDropdown.addEventListener('change', (e) => {
            const sort = e.target.value;
            if (window.topicsManager) {
                window.topicsManager.applySort(sort);
            }
        });
    }

    // Add option button in create topic modal
    const addOptionBtn = document.getElementById('addOptionBtn');
    if (addOptionBtn) {
        addOptionBtn.addEventListener('click', () => {
            const container = document.getElementById('votingOptionsContainer');
            const optionCount = container.children.length + 1;
            
            const optionDiv = document.createElement('div');
            optionDiv.className = 'option-item';
            optionDiv.innerHTML = `
                <div class="input-wrapper">
                    <input type="text" placeholder="Option ${optionCount}" required>
                </div>
                <button type="button" class="btn btn-ghost btn-sm remove-option">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            container.appendChild(optionDiv);
            
            // Add remove functionality to the new option
            optionDiv.querySelector('.remove-option').addEventListener('click', () => {
                if (container.children.length > 2) { // Keep at least 2 options
                    optionDiv.remove();
                }
            });
        });
    }

    // Initialize remove buttons for existing options
    document.querySelectorAll('.remove-option').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const container = document.getElementById('votingOptionsContainer');
            if (container.children.length > 2) { // Keep at least 2 options
                e.target.closest('.option-item').remove();
            }
        });
    });

    // Stats counter animation
    const animateCounters = () => {
        const counters = document.querySelectorAll('[data-count]');
        counters.forEach(counter => {
            const target = parseInt(counter.getAttribute('data-count'));
            const duration = 2000; // 2 seconds
            const step = target / (duration / 16); // 60fps
            let current = 0;
            
            const timer = setInterval(() => {
                current += step;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                counter.textContent = Math.floor(current);
            }, 16);
        });
    };

    // Trigger counter animation when command center is visible
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounters();
                observer.unobserve(entry.target);
            }
        });
    });

    const statsGrid = document.querySelector('.stats-grid');
    if (statsGrid) {
        observer.observe(statsGrid);
    }

    // Delete account button
    const deleteAccountBtn = document.getElementById('deleteAccountBtn');
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', async () => {
            await uiManager.deleteAccount();
        });
    }

    // Profile button
    const profileBtn = document.getElementById('profileBtn');
    if (profileBtn) {
        profileBtn.addEventListener('click', async () => {
            await uiManager.showProfileModal();
        });
    }
});

// Export for testing/debugging
window.app = app;