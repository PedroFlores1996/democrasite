// UI utilities and modal management
class UIManager {
    constructor() {
        this.currentSection = 'commandCenter';
        this.activeModals = new Set();
        this.toastCounter = 0;
        this.init();
    }

    init() {
        // Initialize sections properly
        this.initializeSections();
        
        // Setup modal event listeners
        this.setupModals();
        
        // Setup section navigation
        this.setupNavigation();

        // Setup toast notifications
        this.setupToasts();
    }

    initializeSections() {
        // Hide all sections except command center by default
        const sections = ['topicsDashboard', 'topicDetail'];
        sections.forEach(sectionId => {
            const section = document.getElementById(sectionId);
            if (section) {
                section.classList.add('hidden');
            }
        });

        // Ensure command center is visible
        const commandCenter = document.getElementById('commandCenter');
        if (commandCenter) {
            commandCenter.classList.remove('hidden');
        }

        // Hide all modals by default
        const modals = ['authModal', 'createTopicModal'];
        modals.forEach(modalId => {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.style.display = 'none';
                modal.classList.remove('show');
            }
        });

        // Hide search bar by default (shown only when authenticated)
        const searchContainer = document.querySelector('.nav-center');
        if (searchContainer) {
            searchContainer.classList.add('hidden');
        }
    }

    setupModals() {
        // Close modal when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                const modal = e.target;
                this.hideModal(modal.id);
            }
        });

        // Close modal with close buttons
        document.querySelectorAll('.modal-close').forEach(button => {
            button.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal-overlay');
                if (modal) {
                    this.hideModal(modal.id);
                }
            });
        });

        // Escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeModals.size > 0) {
                const modals = Array.from(this.activeModals);
                const topModal = modals[modals.length - 1];
                this.hideModal(topModal);
            }
        });
    }

    setupNavigation() {
        // Hero buttons
        const exploreBtn = document.getElementById('exploreTopics');
        if (exploreBtn) {
            exploreBtn.addEventListener('click', () => {
                if (!authManager.isAuthenticated) {
                    showAuthModal('login');
                    showToast('Create an account or sign in to explore topics', 'info');
                    return;
                }
                this.showSection('topicsDashboard');
                loadTopics();
            });
        }

        const createTopicHeroBtn = document.getElementById('createTopicHero');
        if (createTopicHeroBtn) {
            createTopicHeroBtn.addEventListener('click', () => {
                if (!authManager.isAuthenticated) {
                    showAuthModal('login');
                    showToast('Sign in or create an account to start creating topics', 'info');
                    return;
                }
                this.showCreateTopicModal();
            });
        }

        // Dashboard new topic button
        const newTopicBtn = document.getElementById('newTopicBtn');
        if (newTopicBtn) {
            newTopicBtn.addEventListener('click', () => {
                this.showCreateTopicModal();
            });
        }
    }

    setupToasts() {
        // Auto-hide toasts after 5 seconds
        this.toastTimeout = null;
    }

    showSection(sectionId) {
        // Hide all sections
        document.querySelectorAll('main > section').forEach(section => {
            section.classList.add('hidden');
        });

        // Show target section
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.classList.remove('hidden');
            this.currentSection = sectionId;
            
            // Refresh topics when navigating to dashboard
            if (sectionId === 'topicsDashboard' && window.topicsManager && authManager.isAuthenticated) {
                // Small delay to let the UI settle
                setTimeout(() => {
                    topicsManager.loadTopics(topicsManager.searchQuery);
                    // Also refresh dashboard stats to show updated counts
                    authManager.loadDashboardStats();
                }, 100);
            }
        }
    }

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
            setTimeout(() => {
                modal.classList.add('show');
            }, 10);
            this.activeModals.add(modalId);
            
            // Focus first input
            const firstInput = modal.querySelector('input');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 150);
            }

            // Prevent body scroll
            document.body.style.overflow = 'hidden';
        }
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.style.display = 'none';
            }, 300);
            this.activeModals.delete(modalId);
            
            // Restore body scroll if no modals are open
            if (this.activeModals.size === 0) {
                document.body.style.overflow = '';
            }
        }
    }

    showCreateTopicModal() {
        try {
            authManager.requireAuth();
            this.showModal('createTopicModal');
        } catch (error) {
            // User will be prompted to login
        }
    }

    showToast(message, type = 'info', duration = 5000) {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        
        // Create toast element
        const toast = document.createElement('div');
        const toastId = `toast-${++this.toastCounter}`;
        toast.id = toastId;
        toast.className = `toast toast-${type}`;
        
        // Toast icon based on type
        let icon = 'fas fa-info-circle';
        if (type === 'success') icon = 'fas fa-check-circle';
        else if (type === 'error') icon = 'fas fa-exclamation-circle';
        else if (type === 'warning') icon = 'fas fa-exclamation-triangle';
        
        toast.innerHTML = `
            <div class="toast-content">
                <i class="${icon}"></i>
                <span class="toast-message">${message}</span>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Add to container
        container.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        // Auto-hide after duration
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.parentElement.removeChild(toast);
                }
            }, 300);
        }, duration);
    }

    hideToast(toastId) {
        const toast = document.getElementById(toastId);
        if (toast) {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.parentElement.removeChild(toast);
                }
            }, 300);
        }
    }

    // Loading states
    showLoading(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        
        if (element) {
            element.classList.add('loading');
            element.disabled = true;
        }
    }

    hideLoading(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        
        if (element) {
            element.classList.remove('loading');
            element.disabled = false;
        }
    }

    // Confirmation dialogs
    async confirm(message, title = 'Confirm') {
        return new Promise((resolve) => {
            // Create confirmation modal
            const modal = document.createElement('div');
            modal.className = 'modal show';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>${title}</h3>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-primary confirm-yes">Yes</button>
                        <button class="btn btn-outline confirm-no">No</button>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);
            document.body.style.overflow = 'hidden';

            // Handle responses
            const cleanup = () => {
                document.body.removeChild(modal);
                document.body.style.overflow = '';
            };

            modal.querySelector('.confirm-yes').addEventListener('click', () => {
                cleanup();
                resolve(true);
            });

            modal.querySelector('.confirm-no').addEventListener('click', () => {
                cleanup();
                resolve(false);
            });

            // Close on outside click
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    cleanup();
                    resolve(false);
                }
            });
        });
    }
}

// Initialize UI manager
const uiManager = new UIManager();

// Global functions for backward compatibility
window.showSection = (sectionId) => uiManager.showSection(sectionId);
window.showModal = (modalId) => uiManager.showModal(modalId);
window.hideModal = (modalId) => uiManager.hideModal(modalId);
window.showCreateTopicModal = () => uiManager.showCreateTopicModal();
window.showToast = (message, type, duration) => uiManager.showToast(message, type, duration);
window.confirm = (message, title) => uiManager.confirm(message, title);

