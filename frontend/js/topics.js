// Topics management
class TopicsManager {
    constructor() {
        this.topics = [];
        this.currentTopic = null;
        this.searchQuery = '';
        this.selectedAnswer = null;
    }

    async loadTopics(search = '') {
        try {
            // Check if user is authenticated first
            if (!authManager.isAuthenticated) {
                this.renderUnauthenticatedState();
                return;
            }

            this.searchQuery = search;
            this.topics = await api.getTopics(search);
            this.renderTopics();
        } catch (error) {
            console.error('Error loading topics:', error);
            
            // Check if it's an authentication error
            if (error.message.includes('401') || error.message.includes('Unauthorized')) {
                this.renderUnauthenticatedState();
                showToast('Please log in to view topics', 'warning');
            } else {
                showToast('Error loading topics', 'error');
                this.topics = [];
                this.renderTopics();
            }
        }
    }

    renderUnauthenticatedState() {
        const grid = document.getElementById('topicsGrid');
        
        grid.innerHTML = `
            <div class="auth-required-state" style="grid-column: 1 / -1; text-align: center; padding: 4rem 2rem;">
                <div class="auth-required-icon">
                    <i class="fas fa-lock" style="font-size: 4rem; color: var(--primary-color); margin-bottom: 1.5rem; opacity: 0.8;"></i>
                </div>
                <h3 style="color: var(--text-primary); margin-bottom: 1rem; font-size: 1.5rem;">Authentication Required</h3>
                <p style="color: var(--text-secondary); margin-bottom: 2rem; max-width: 500px; margin-left: auto; margin-right: auto; line-height: 1.6;">
                    Join the digital democracy! Log in to explore topics, cast your vote, and make your voice heard in the community.
                </p>
                <div class="auth-actions" style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                    <button class="btn btn-primary btn-lg" onclick="showAuthModal('login')" style="min-width: 150px;">
                        <i class="fas fa-sign-in-alt"></i>
                        <span>Sign In</span>
                        <div class="btn-glow"></div>
                    </button>
                    <button class="btn btn-secondary btn-lg" onclick="showAuthModal('register')" style="min-width: 150px;">
                        <i class="fas fa-user-plus"></i>
                        <span>Create Account</span>
                        <div class="btn-glow"></div>
                    </button>
                </div>
                <div class="features-preview" style="margin-top: 3rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; max-width: 600px; margin-left: auto; margin-right: auto;">
                    <div class="feature-card" style="padding: 1.5rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; text-align: center;">
                        <i class="fas fa-poll" style="font-size: 2rem; color: var(--primary-color); margin-bottom: 1rem;"></i>
                        <h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">Create Topics</h4>
                        <p style="color: var(--text-secondary); font-size: 0.9rem;">Start discussions with custom voting options</p>
                    </div>
                    <div class="feature-card" style="padding: 1.5rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; text-align: center;">
                        <i class="fas fa-vote-yea" style="font-size: 2rem; color: var(--primary-color); margin-bottom: 1rem;"></i>
                        <h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">Cast Votes</h4>
                        <p style="color: var(--text-secondary); font-size: 0.9rem;">Make your voice heard on important topics</p>
                    </div>
                    <div class="feature-card" style="padding: 1.5rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; text-align: center;">
                        <i class="fas fa-users" style="font-size: 2rem; color: var(--primary-color); margin-bottom: 1rem;"></i>
                        <h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">Join Community</h4>
                        <p style="color: var(--text-secondary); font-size: 0.9rem;">Connect with others in democratic discussions</p>
                    </div>
                </div>
            </div>
        `;
    }

    renderTopics() {
        const grid = document.getElementById('topicsGrid');
        
        if (this.topics.length === 0) {
            grid.innerHTML = `
                <div class="no-topics" style="grid-column: 1 / -1; text-align: center; padding: 3rem;">
                    <i class="fas fa-vote-yea" style="font-size: 3rem; color: var(--text-secondary); margin-bottom: 1rem;"></i>
                    <h3>No topics found</h3>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
                        ${this.searchQuery ? 'Try a different search term' : 'Be the first to create a topic!'}
                    </p>
                    ${authManager.isAuthenticated ? '<button class="btn btn-primary" onclick="showCreateTopicModal()">Create Topic</button>' : ''}
                </div>
            `;
            return;
        }

        grid.innerHTML = this.topics.map((topic, index) => `
            <div class="topic-card" onclick="showTopic('${topic.id}')" style="animation-delay: ${index * 0.1}s">
                <div class="topic-card-header">
                    <div class="topic-meta">
                        <span class="topic-badge ${topic.is_public ? 'badge-public' : 'badge-private'}">
                            <i class="fas fa-${topic.is_public ? 'globe' : 'lock'}"></i>
                            ${topic.is_public ? 'Public' : 'Private'}
                        </span>
                        ${topic.tags && topic.tags.length > 0 ? topic.tags.slice(0, 2).map(tag => `<span class="topic-tag">${this.escapeHtml(tag)}</span>`).join('') : ''}
                    </div>
                </div>
                
                <div class="topic-content">
                    <h3 class="topic-title">${this.escapeHtml(topic.title)}</h3>
                    <p class="topic-description">${this.escapeHtml(topic.description || 'No description provided')}</p>
                </div>
                
                <div class="topic-footer">
                    <div class="topic-author">
                        <div class="author-avatar">
                            <span>${this.escapeHtml(topic.created_by).charAt(0).toUpperCase()}</span>
                        </div>
                        <div class="author-info">
                            <span class="author-name">${this.escapeHtml(topic.created_by)}</span>
                            <span class="topic-date">${this.formatDate(topic.created_at)}</span>
                        </div>
                    </div>
                    
                    <div class="topic-stats">
                        <div class="stat-item">
                            <i class="fas fa-poll"></i>
                            <span>${topic.answers ? topic.answers.length : 0}</span>
                        </div>
                        <div class="stat-item">
                            <i class="fas fa-vote-yea"></i>
                            <span>${topic.total_votes || 0}</span>
                        </div>
                    </div>
                </div>
                
                <div class="topic-card-glow"></div>
            </div>
        `).join('');
    }

    async showTopic(topicId) {
        try {
            this.currentTopic = await api.getTopic(topicId);
            this.renderTopicDetail();
            showSection('topicDetail');
        } catch (error) {
            console.error('Error loading topic:', error);
            showToast('Error loading topic', 'error');
        }
    }

    renderTopicDetail() {
        if (!this.currentTopic) return;

        document.getElementById('topicTitle').textContent = this.currentTopic.title;
        document.getElementById('topicDescription').textContent = this.currentTopic.description || 'No description';
        document.getElementById('topicAuthor').textContent = this.currentTopic.created_by;
        document.getElementById('topicDate').textContent = this.formatDate(this.currentTopic.created_at);
        
        // Update visibility badge
        const visibilityBadge = document.getElementById('topicVisibility');
        visibilityBadge.textContent = this.currentTopic.is_public ? 'Public' : 'Private';
        visibilityBadge.className = `badge ${this.currentTopic.is_public ? 'badge-public' : 'badge-private'}`;
        
        // Update author initials
        const authorInitials = document.getElementById('authorInitials');
        if (authorInitials) {
            authorInitials.textContent = this.currentTopic.created_by.charAt(0).toUpperCase();
        }
        
        // Render tags
        const tagsContainer = document.getElementById('topicTags');
        if (this.currentTopic.tags && this.currentTopic.tags.length > 0) {
            tagsContainer.innerHTML = this.currentTopic.tags
                .map(tag => `<span class="tag">${this.escapeHtml(tag)}</span>`)
                .join('');
        } else {
            tagsContainer.innerHTML = '';
        }

        this.renderVotingSection();
    }

    renderVotingSection() {
        const votingOptions = document.getElementById('votingOptions');
        const votingResults = document.getElementById('votingResults');

        if (!authManager.isAuthenticated) {
            votingOptions.innerHTML = `
                <div class="text-center">
                    <p style="margin-bottom: 1rem;">Please log in to vote</p>
                    <button class="btn btn-primary" onclick="showAuthModal('login')">Login</button>
                </div>
            `;
            votingResults.innerHTML = '';
            return;
        }

        // Render voting options
        if (this.currentTopic.answers && this.currentTopic.answers.length > 0) {
            votingOptions.innerHTML = this.currentTopic.answers.map((answer, index) => `
                <div class="voting-option" data-answer="${this.escapeHtml(answer)}" onclick="selectAnswer('${this.escapeHtml(answer)}')">
                    <div class="option-radio"></div>
                    <span class="option-text">${this.escapeHtml(answer)}</span>
                    <div class="option-glow"></div>
                </div>
            `).join('') + `
                <button class="btn btn-primary btn-vote" onclick="submitVote()" disabled>
                    <i class="fas fa-check"></i>
                    <span>Submit Vote</span>
                    <div class="btn-glow"></div>
                </button>
            `;
        }

        // Render results if available
        if (this.currentTopic.vote_counts) {
            this.renderResults();
        }
    }

    renderResults() {
        const votingResults = document.getElementById('votingResults');
        const voteCounts = this.currentTopic.vote_counts;
        const totalVotes = this.currentTopic.total_votes || 0;

        if (totalVotes === 0) {
            votingResults.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No votes yet</p>';
            return;
        }

        const resultsHTML = Object.entries(voteCounts)
            .sort(([, a], [, b]) => b - a) // Sort by vote count descending
            .map(([answer, count], index) => {
                const percentage = totalVotes > 0 ? Math.round((count / totalVotes) * 100) : 0;
                return `
                    <div class="result-item" style="animation: slideInLeft 0.5s ease-out ${index * 0.1}s both">
                        <div class="result-header">
                            <span class="result-text">${this.escapeHtml(answer)}</span>
                            <span class="result-count">${count} votes (${percentage}%)</span>
                        </div>
                        <div class="result-bar">
                            <div class="result-fill" style="width: ${percentage}%"></div>
                        </div>
                    </div>
                `;
            }).join('');

        votingResults.innerHTML = `
            <h4>Results (${totalVotes} total votes)</h4>
            ${resultsHTML}
        `;
    }

    async createTopic(topicData) {
        try {
            authManager.requireAuth();
            const newTopic = await api.createTopic(topicData);
            showToast('Topic created successfully!', 'success');
            hideModal('createTopicModal');
            
            // Refresh topics list
            await this.loadTopics();
            
            return newTopic;
        } catch (error) {
            console.error('Error creating topic:', error);
            showToast(error.message, 'error');
            throw error;
        }
    }

    async submitVote(answer) {
        try {
            authManager.requireAuth();
            
            if (!this.selectedAnswer) {
                showToast('Please select an answer', 'error');
                return;
            }

            await api.vote(this.currentTopic.id, this.selectedAnswer);
            showToast('Vote submitted successfully!', 'success');
            
            // Reload topic to get updated results
            await this.showTopic(this.currentTopic.id);
        } catch (error) {
            console.error('Error submitting vote:', error);
            showToast(error.message, 'error');
        }
    }

    selectAnswer(answer) {
        this.selectedAnswer = answer;
        
        // Update UI
        document.querySelectorAll('.voting-option').forEach(option => {
            option.classList.remove('selected');
        });
        
        const selectedOption = document.querySelector(`[data-answer="${this.escapeHtml(answer)}"]`);
        if (selectedOption) {
            selectedOption.classList.add('selected');
        }
        
        // Enable submit button
        const submitBtn = document.querySelector('.btn-vote');
        if (submitBtn) {
            submitBtn.disabled = false;
        }
    }

    // Utility methods
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
}

// Initialize topics manager
const topicsManager = new TopicsManager();

// Global functions for event handlers
window.loadTopics = () => topicsManager.loadTopics();
window.showTopic = (id) => topicsManager.showTopic(id);
window.selectAnswer = (answer) => topicsManager.selectAnswer(answer);
window.submitVote = () => topicsManager.submitVote();

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Search functionality
    const searchInput = document.getElementById('globalSearch');
    let searchTimeout;
    
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                topicsManager.loadTopics(e.target.value);
            }, 300);
        });
    }

    // Back button
    document.getElementById('backBtn').addEventListener('click', () => {
        showSection('topicsDashboard');
    });

    // Create topic form
    const createTopicForm = document.getElementById('createTopicForm');
    createTopicForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const title = document.getElementById('topicTitleInput').value;
        const description = document.getElementById('topicDescriptionInput').value;
        const tagsInput = document.getElementById('topicTagsInput').value;
        const visibility = document.querySelector('input[name="visibility"]:checked').value;
        
        // Get voting options
        const optionInputs = document.querySelectorAll('#votingOptionsContainer input');
        const answers = Array.from(optionInputs)
            .map(input => input.value.trim())
            .filter(value => value.length > 0);

        if (answers.length < 2) {
            showToast('Please provide at least 2 voting options', 'error');
            return;
        }

        const tags = tagsInput
            .split(',')
            .map(tag => tag.trim())
            .filter(tag => tag.length > 0);

        const topicData = {
            title,
            description: description || null,
            answers,
            is_public: visibility === 'public',
            tags: tags.length > 0 ? tags : null
        };

        try {
            await topicsManager.createTopic(topicData);
            createTopicForm.reset();
            resetVotingOptions();
        } catch (error) {
            // Error already handled in createTopic
        }
    });

    // Add voting option
    document.getElementById('addOptionBtn').addEventListener('click', () => {
        const container = document.getElementById('votingOptionsContainer');
        const optionCount = container.children.length + 1;
        
        const optionDiv = document.createElement('div');
        optionDiv.className = 'voting-option-input';
        optionDiv.innerHTML = `
            <input type="text" placeholder="Option ${optionCount}" required>
            <button type="button" class="btn-remove-option" onclick="this.parentElement.remove()">&times;</button>
        `;
        
        container.appendChild(optionDiv);
    });

    // Share topic button
    document.getElementById('shareTopicBtn').addEventListener('click', async () => {
        if (!topicsManager.currentTopic) return;
        
        try {
            if (topicsManager.currentTopic.is_public) {
                // For public topics, just copy the URL
                const url = `${window.location.origin}${window.location.pathname}?topic=${topicsManager.currentTopic.id}`;
                await navigator.clipboard.writeText(url);
                showToast('Topic URL copied to clipboard!', 'success');
            } else {
                // For private topics, get share code
                const response = await api.getShareCode(topicsManager.currentTopic.id);
                const shareUrl = `${window.location.origin}${window.location.pathname}?share=${response.share_code}`;
                await navigator.clipboard.writeText(shareUrl);
                showToast('Share code copied to clipboard!', 'success');
            }
        } catch (error) {
            console.error('Error sharing topic:', error);
            showToast('Error generating share link', 'error');
        }
    });
});

// Utility function to reset voting options
function resetVotingOptions() {
    const container = document.getElementById('votingOptionsContainer');
    container.innerHTML = `
        <div class="voting-option-input">
            <input type="text" placeholder="Option 1" required>
            <button type="button" class="btn-remove-option">&times;</button>
        </div>
        <div class="voting-option-input">
            <input type="text" placeholder="Option 2" required>
            <button type="button" class="btn-remove-option">&times;</button>
        </div>
    `;
}