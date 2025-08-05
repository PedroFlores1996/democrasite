// Authentication management
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.isAuthenticated = false;
        this.init();
    }

    async init() {
        // Check if user is already logged in
        const token = localStorage.getItem('authToken');
        if (token) {
            try {
                // Set the token in the API instance first
                api.setToken(token);
                const userData = await api.getCurrentUser();
                this.currentUser = userData;
                this.isAuthenticated = true;
                this.updateUI();
            } catch (error) {
                console.log('Token expired or invalid:', error.message);
                this.logout();
            }
        }
    }

    async register(username, password, confirmPassword) {
        if (password !== confirmPassword) {
            throw new Error('Passwords do not match');
        }

        if (password.length < 6) {
            throw new Error('Password must be at least 6 characters long');
        }

        try {
            const response = await api.register(username, password);
            // Get user info after successful registration
            const userData = await api.getCurrentUser();
            this.currentUser = userData;
            this.isAuthenticated = true;
            this.updateUI();
            return response;
        } catch (error) {
            throw error;
        }
    }

    async login(username, password) {
        try {
            const response = await api.login(username, password);
            // Get user info after successful login
            const userData = await api.getCurrentUser();
            this.currentUser = userData;
            this.isAuthenticated = true;
            this.updateUI();
            return response;
        } catch (error) {
            throw error;
        }
    }

    logout() {
        api.logout();
        this.currentUser = null;
        this.isAuthenticated = false;
        this.updateUI();
        
        // Clear any cached data
        if (window.topicsManager) {
            topicsManager.topics = [];
            topicsManager.currentTopic = null;
        }
        
        // Redirect to command center
        showSection('commandCenter');
    }

    updateUI() {
        const loginBtn = document.getElementById('loginBtn');
        const registerBtn = document.getElementById('registerBtn');
        const userMenu = document.getElementById('userMenu');
        const usernameSpan = document.getElementById('username');
        const userInitials = document.getElementById('userInitials');
        const searchContainer = document.querySelector('.nav-center');

        if (this.isAuthenticated && this.currentUser) {
            loginBtn.classList.add('hidden');
            registerBtn.classList.add('hidden');
            userMenu.classList.remove('hidden');
            usernameSpan.textContent = this.currentUser.username;
            if (userInitials) {
                userInitials.textContent = this.currentUser.username.charAt(0).toUpperCase();
            }
            
            // Show search bar for authenticated users
            if (searchContainer) {
                searchContainer.classList.remove('hidden');
            }
            
            // Update command center for authenticated users
            this.updateCommandCenterForAuth();
            
            // Load real stats for authenticated users
            this.loadDashboardStats();
        } else {
            loginBtn.classList.remove('hidden');
            registerBtn.classList.remove('hidden');
            userMenu.classList.add('hidden');
            
            // Hide search bar for unauthenticated users
            if (searchContainer) {
                searchContainer.classList.add('hidden');
            }
            
            // Update command center for guests
            this.updateCommandCenterForGuest();
        }
    }

    updateCommandCenterForAuth() {
        // Update subtitle to be more personal
        const subtitle = document.querySelector('.command-center .subtitle');
        if (subtitle) {
            subtitle.textContent = `Welcome back, ${this.currentUser.username}! Shape the future through collective decision-making.`;
        }
        
        // Ensure buttons are enabled and show authenticated actions
        const exploreBtn = document.getElementById('exploreTopics');
        const createBtn = document.getElementById('createTopicHero');
        
        if (exploreBtn) {
            exploreBtn.innerHTML = `
                <i class="fas fa-compass"></i>
                <span>Explore Topics</span>
                <div class="btn-glow"></div>
            `;
        }
        
        if (createBtn) {
            createBtn.innerHTML = `
                <i class="fas fa-plus"></i>
                <span>Create Topic</span>
                <div class="btn-glow"></div>
            `;
        }
    }

    updateCommandCenterForGuest() {
        // Reset subtitle to general message
        const subtitle = document.querySelector('.command-center .subtitle');
        if (subtitle) {
            subtitle.textContent = 'Join the digital democracy! Register to participate in collective decision-making.';
        }
        
        // Update buttons to show what the platform offers
        const exploreBtn = document.getElementById('exploreTopics');
        const createBtn = document.getElementById('createTopicHero');
        
        if (exploreBtn) {
            exploreBtn.innerHTML = `
                <i class="fas fa-compass"></i>
                <span>Explore Topics</span>
                <div class="btn-glow"></div>
            `;
        }
        
        if (createBtn) {
            createBtn.innerHTML = `
                <i class="fas fa-plus"></i>
                <span>Create Topic</span>
                <div class="btn-glow"></div>
            `;
        }
    }

    async loadDashboardStats() {
        try {
            // Get topics to calculate stats
            const topicsData = await api.getTopics('', '', 'popular', 100, 1); // Get topics for stats (max 100)
            
            // Update stats cards
            const activeTopicsEl = document.querySelector('[data-count="0"]');
            const votesCastEl = document.querySelectorAll('[data-count="0"]')[1];
            const participantsEl = document.querySelectorAll('[data-count="0"]')[2];
            
            if (activeTopicsEl) {
                activeTopicsEl.setAttribute('data-count', topicsData.total || 0);
                activeTopicsEl.textContent = topicsData.total || 0;
            }
            
            // Calculate total votes from all topics
            let totalVotes = 0;
            let totalParticipants = new Set();
            
            if (topicsData.topics) {
                topicsData.topics.forEach(topic => {
                    totalVotes += topic.total_votes || 0;
                    // Add creator as participant
                    totalParticipants.add(topic.creator_username);
                });
            }
            
            if (votesCastEl) {
                votesCastEl.setAttribute('data-count', totalVotes);
                votesCastEl.textContent = totalVotes;
            }
            
            if (participantsEl) {
                participantsEl.setAttribute('data-count', totalParticipants.size);
                participantsEl.textContent = totalParticipants.size;
            }
            
        } catch (error) {
            console.log('Could not load dashboard stats (user may not be authenticated)');
            // Keep default 0 values
        }
    }

    requireAuth() {
        if (!this.isAuthenticated) {
            showAuthModal('login');
            throw new Error('Authentication required');
        }
        return true;
    }
}

// Initialize auth manager
const authManager = new AuthManager();

// Event listeners for auth forms
document.addEventListener('DOMContentLoaded', () => {
    // Login form
    const loginForm = document.getElementById('loginForm');
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const submitBtn = loginForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        
        try {
            // Add loading state
            submitBtn.classList.add('loading');
            submitBtn.textContent = 'Signing in...';
            submitBtn.disabled = true;
            
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;
            
            await authManager.login(username, password);
            hideModal('authModal');
            showToast('Welcome back! 🎉', 'success');
            loginForm.reset();
            
            // Check for pending share code
            const pendingShareCode = sessionStorage.getItem('pendingShareCode');
            if (pendingShareCode) {
                sessionStorage.removeItem('pendingShareCode');
                showTopic(pendingShareCode);
                showSection('topicDetail');
                showToast('Topic accessed successfully!', 'success');
            } else {
                // Show topics dashboard
                showSection('topicsDashboard');
                loadTopics();
            }
        } catch (error) {
            showToast(error.message, 'error');
        } finally {
            // Remove loading state
            submitBtn.classList.remove('loading');
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    });

    // Register form
    const registerForm = document.getElementById('registerForm');
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const submitBtn = registerForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        
        try {
            // Add loading state
            submitBtn.classList.add('loading');
            submitBtn.textContent = 'Creating account...';
            submitBtn.disabled = true;
            
            const username = document.getElementById('registerUsername').value;
            const password = document.getElementById('registerPassword').value;
            const confirmPassword = document.getElementById('registerConfirmPassword').value;
            
            await authManager.register(username, password, confirmPassword);
            hideModal('authModal');
            showToast('Welcome to Democrasite! 🚀', 'success');
            registerForm.reset();
            
            // Check for pending share code
            const pendingShareCode = sessionStorage.getItem('pendingShareCode');
            if (pendingShareCode) {
                sessionStorage.removeItem('pendingShareCode');
                showTopic(pendingShareCode);
                showSection('topicDetail');
                showToast('Topic accessed successfully!', 'success');
            } else {
                // Show topics dashboard after registration
                showSection('topicsDashboard');
                loadTopics();
            }
        } catch (error) {
            showToast(error.message, 'error');
        } finally {
            // Remove loading state
            submitBtn.classList.remove('loading');
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    });

    // Login button
    document.getElementById('loginBtn').addEventListener('click', () => {
        showAuthModal('login');
    });

    // Register button
    document.getElementById('registerBtn').addEventListener('click', () => {
        showAuthModal('register');
    });

    // Logout button
    document.getElementById('logoutBtn').addEventListener('click', () => {
        authManager.logout();
        showToast('Logged out successfully!', 'success');
    });
});