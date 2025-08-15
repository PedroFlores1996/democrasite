// Topics management
class TopicsManager {
    constructor() {
        this.topics = [];
        this.currentTopic = null;
        this.searchQuery = '';
        this.selectedAnswer = null;
        this.currentFilter = 'all';
        this.currentSort = 'popular';
        this.favorites = new Set(); // Track favorite topic share codes
    }

    async loadTopics(search = '', showErrors = true) {
        try {
            // Check if user is authenticated first
            if (!authManager.isAuthenticated) {
                this.renderUnauthenticatedState();
                return;
            }

            this.searchQuery = search;
            const response = await api.getTopics(search, '', this.currentSort);
            // Extract topics array from the paginated response
            this.topics = Array.isArray(response) ? response : (response.topics || []);

            // Load favorites in parallel
            await this.loadFavorites();

            this.renderTopics();
        } catch (error) {
            console.error('Error loading topics:', error);
            console.error('Auth status:', authManager.isAuthenticated);
            console.error('Token:', localStorage.getItem('authToken'));

            // Check if it's an authentication error
            if (error.message.includes('401') || error.message.includes('Unauthorized')) {
                // Clear authentication state and redirect to login
                authManager.logout();
                this.renderUnauthenticatedState();
                if (showErrors) {
                    showToast('Please log in to view topics', 'warning');
                }
            } else {
                if (showErrors) {
                    showToast(`Error loading topics: ${error.message}`, 'error');
                }
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
                    Ask questions, cast your vote, and see how the world thinks.
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
        const filteredTopics = this.getFilteredTopics();

        if (filteredTopics.length === 0) {
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

        grid.innerHTML = filteredTopics.map((topic, index) => `
            <div class="topic-card" onclick="showTopic('${topic.share_code || topic.id}')" style="animation-delay: ${index * 0.1}s">
                <div class="topic-card-header">
                    <div class="topic-meta">
                        <span class="topic-badge ${topic.is_public ? 'badge-public' : 'badge-private'}">
                            <i class="fas fa-${topic.is_public ? 'globe' : 'lock'}"></i>
                            ${topic.is_public ? 'Public' : 'Private'}
                        </span>
                    </div>
                    ${topic.tags && topic.tags.length > 0 ? `
                        <div class="topic-tags">
                            ${topic.tags.slice(0, 2).map(tag => `<span class="topic-tag">${this.escapeHtml(tag)}</span>`).join('')}
                            ${topic.tags.length > 2 ? `<span class="topic-tag-more">+${topic.tags.length - 2}</span>` : ''}
                        </div>
                    ` : ''}
                </div>
                
                <div class="topic-content">
                    <h3 class="topic-title">${this.escapeHtml(topic.title)}</h3>
                    <p class="topic-description">${this.escapeHtml(topic.description || 'No description provided')}</p>
                </div>
                
                <div class="topic-footer">
                    <div class="topic-author">
                        <div class="author-info">
                            <span class="author-name">${this.escapeHtml(topic.creator_username)}</span>
                            <span class="topic-date">${this.formatDate(topic.created_at)}</span>
                        </div>
                    </div>
                    
                    <div class="topic-stats">
                        <div class="topic-stat">
                            <i class="fas fa-poll"></i>
                            <span>${topic.answer_count || 0}</span>
                        </div>
                        <div class="topic-stat">
                            <i class="fas fa-vote-yea"></i>
                            <span>${topic.total_votes || 0}</span>
                        </div>
                        <div class="topic-stat favorite-stat ${this.favorites.has(topic.share_code) ? 'is-favorited' : ''}" 
                             onclick="event.stopPropagation(); topicsManager.toggleFavoriteFromCard('${topic.share_code}')" 
                             title="${this.favorites.has(topic.share_code) ? 'Remove from favorites' : 'Add to favorites'}">
                            <i class="fas fa-star ${this.favorites.has(topic.share_code) ? 'favorited' : 'not-favorited'}"></i>
                            <span>${topic.favorite_count || 0}</span>
                        </div>
                    </div>
                </div>
                
                <div class="topic-card-glow"></div>
            </div>
        `).join('');
    }

    async showTopic(shareCode) {
        try {
            this.currentTopic = await api.getTopic(shareCode);
            this.renderTopicDetail();
            showSection('topicDetail');
        } catch (error) {
            console.error('Error loading topic:', error);

            // Check if it's an access denied error (403) or not found (404)
            if (error.message.includes('403') || error.message.includes('Access denied') ||
                error.message.includes('404') || error.message.includes('Not found')) {
                showToast('Topic not found or access denied', 'error');
                // Stay on dashboard if user is authenticated, otherwise go to command center
                if (authManager.isAuthenticated) {
                    showSection('topicsDashboard');
                    loadTopics();
                } else {
                    showSection('commandCenter');
                }
            } else {
                showToast('Error loading topic', 'error');
            }
        }
    }

    renderTopicDetail() {
        if (!this.currentTopic) return;

        document.getElementById('topicTitle').textContent = this.currentTopic.title;
        document.getElementById('topicDescription').textContent = this.currentTopic.description || 'No description provided';
        document.getElementById('topicAuthor').textContent = this.currentTopic.created_by;
        document.getElementById('topicDate').textContent = this.formatDate(this.currentTopic.created_at);

        // Update visibility badge
        const visibilityBadge = document.getElementById('topicVisibility');
        const icon = this.currentTopic.is_public ? 'fa-globe' : 'fa-lock';
        const text = this.currentTopic.is_public ? 'Public' : 'Private';
        visibilityBadge.innerHTML = `<i class="fas ${icon}"></i> ${text}`;
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

        // Show/hide delete button based on creator status
        this.updateDeleteButton();

        // Show/hide leave button for private topics
        this.updateLeaveButton();

        // Update favorite button state
        this.updateFavoriteButton();

        // Show/hide description edit button for creators
        this.updateDescriptionEditButton();

        this.renderVotingSection();
    }

    renderVotingSection() {
        const votingOptions = document.getElementById('votingOptions');
        const votingResults = document.getElementById('votingResults');

        // Update the vote count in the header
        const totalVotesElement = document.querySelector('.total-votes');
        if (totalVotesElement && this.currentTopic) {
            const voteCount = this.currentTopic.total_votes || 0;
            const voteLabel = voteCount === 1 ? 'vote' : 'votes';
            totalVotesElement.textContent = `${voteCount} ${voteLabel}`;
        }

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
            const isMultiSelect = this.currentTopic.allow_multi_select;
            const inputType = isMultiSelect ? 'checkbox' : 'radio';
            const radioClass = isMultiSelect ? 'option-checkbox' : 'option-radio';
            
            let optionsHTML = this.currentTopic.answers.map((answer, index) => `
                <div class="voting-option" data-answer="${this.escapeHtml(answer)}" onclick="selectAnswer('${this.escapeHtml(answer)}', ${isMultiSelect})">
                    <div class="${radioClass}"></div>
                    <span class="option-text">${this.escapeHtml(answer)}</span>
                    <div class="option-glow"></div>
                </div>
            `).join('');

            // Add "Add Option" section for editable topics
            if (this.currentTopic.is_editable) {
                optionsHTML += `
                    <div class="add-option-section">
                        <div class="add-option-form" id="addOptionForm" style="display: none;">
                            <div class="input-wrapper">
                                <input type="text" id="newOptionInput" placeholder="Enter new option..." maxlength="200">
                            </div>
                            <div class="add-option-buttons">
                                <button class="btn btn-primary btn-sm" onclick="submitNewOption()">
                                    <i class="fas fa-plus"></i>
                                    Add
                                </button>
                                <button class="btn btn-ghost btn-sm" onclick="cancelAddOption()">
                                    Cancel
                                </button>
                            </div>
                        </div>
                        <button class="btn btn-outline btn-add-option" id="showAddOptionBtn" onclick="showAddOptionForm()">
                            <i class="fas fa-plus"></i>
                            <span>Add Option</span>
                        </button>
                    </div>
                `;
            }

            optionsHTML += `
                <button class="btn btn-primary btn-vote" onclick="submitVote()" disabled>
                    <i class="fas fa-check"></i>
                    <span>Submit Vote</span>
                    <div class="btn-glow"></div>
                </button>
            `;

            votingOptions.innerHTML = optionsHTML;
            
            // Pre-select user's current votes
            this.preselectCurrentVotes();
        }

        // Render results if available
        if (this.currentTopic.vote_breakdown) {
            this.renderResults();
        }
    }

    renderResults() {
        const votingResults = document.getElementById('votingResults');
        const voteCounts = this.currentTopic.vote_breakdown;
        const totalVotes = this.currentTopic.total_votes || 0;

        if (totalVotes === 0) {
            votingResults.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No votes yet</p>';
            return;
        }

        const isMultiSelect = this.currentTopic.allow_multi_select;
        const voteLabel = isMultiSelect ? 'selections' : 'votes';
        
        // Calculate total selections (sum of all vote counts for multi-select)
        const totalSelections = Object.values(voteCounts).reduce((sum, count) => sum + count, 0);
        const totalForPercentage = isMultiSelect ? totalSelections : totalVotes;
        
        const resultsHTML = Object.entries(voteCounts)
            .sort(([, a], [, b]) => b - a) // Sort by vote count descending
            .map(([answer, count], index) => {
                const percentage = totalForPercentage > 0 ? Math.round((count / totalForPercentage) * 100) : 0;
                return `
                    <div class="result-item" style="animation: slideInLeft 0.5s ease-out ${index * 0.1}s both">
                        <div class="result-header">
                            <span class="result-text">${this.escapeHtml(answer)}</span>
                            <span class="result-count">${count} ${voteLabel} (${percentage}%)</span>
                        </div>
                        <div class="result-bar">
                            <div class="result-fill" style="width: ${percentage}%"></div>
                        </div>
                    </div>
                `;
            }).join('');

        const resultTitle = isMultiSelect 
            ? `Results (${totalSelections} total selections)`
            : `Results (${totalVotes} total votes)`;

        votingResults.innerHTML = `
            <h4>${resultTitle}</h4>
            ${resultsHTML}
        `;
    }

    preselectCurrentVotes() {
        if (!this.currentTopic.user_votes || this.currentTopic.user_votes.length === 0) {
            return;
        }

        const isMultiSelect = this.currentTopic.allow_multi_select;
        
        if (isMultiSelect) {
            // For multi-select, initialize selectedAnswers and mark multiple options as selected
            this.selectedAnswers = new Set(this.currentTopic.user_votes);
            
            // Mark each voted option as selected
            this.currentTopic.user_votes.forEach(choice => {
                const optionElement = document.querySelector(`[data-answer="${this.escapeHtml(choice)}"]`);
                if (optionElement) {
                    optionElement.classList.add('selected');
                }
            });
        } else {
            // For single-select, initialize selectedAnswer and mark one option as selected
            this.selectedAnswer = this.currentTopic.user_votes[0];
            this.selectedAnswers = null; // Clear multi-select
            
            // Mark the voted option as selected
            const optionElement = document.querySelector(`[data-answer="${this.escapeHtml(this.selectedAnswer)}"]`);
            if (optionElement) {
                optionElement.classList.add('selected');
            }
        }
        
        // Enable submit button if user has votes
        const submitBtn = document.querySelector('.btn-vote');
        if (submitBtn && this.currentTopic.user_votes.length > 0) {
            submitBtn.disabled = false;
        }
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

            let choices = [];
            
            // Handle multi-select vs single-select
            if (this.currentTopic.allow_multi_select) {
                if (!this.selectedAnswers || this.selectedAnswers.size === 0) {
                    showToast('Please select at least one answer', 'error');
                    return;
                }
                choices = Array.from(this.selectedAnswers);
            } else {
                if (!this.selectedAnswer) {
                    showToast('Please select an answer', 'error');
                    return;
                }
                choices = [this.selectedAnswer];
            }

            await api.vote(this.currentTopic.share_code, choices);
            
            const message = choices.length > 1 
                ? `Vote submitted successfully! (${choices.length} choices)`
                : 'Vote submitted successfully!';
            showToast(message, 'success');

            // Reload topic to get updated results
            await this.showTopic(this.currentTopic.share_code);

            // Force refresh the topics list in background to update vote counts
            await this.refreshTopicsData();

        } catch (error) {
            console.error('Error submitting vote:', error);
            showToast(error.message, 'error');
        }
    }

    selectAnswer(answer, isMultiSelect = false) {
        if (isMultiSelect) {
            // Handle multi-select
            if (!this.selectedAnswers) {
                this.selectedAnswers = new Set();
            }
            
            const selectedOption = document.querySelector(`[data-answer="${this.escapeHtml(answer)}"]`);
            if (selectedOption) {
                if (this.selectedAnswers.has(answer)) {
                    // Deselect
                    this.selectedAnswers.delete(answer);
                    selectedOption.classList.remove('selected');
                } else {
                    // Select
                    this.selectedAnswers.add(answer);
                    selectedOption.classList.add('selected');
                }
            }
            
            // Enable submit button if at least one option is selected
            const submitBtn = document.querySelector('.btn-vote');
            if (submitBtn) {
                submitBtn.disabled = this.selectedAnswers.size === 0;
            }
        } else {
            // Handle single-select (original behavior)
            this.selectedAnswer = answer;
            this.selectedAnswers = null; // Clear multi-select

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
    }

    // Silently refresh topics data to update vote counts
    async refreshTopicsData() {
        try {
            const response = await api.getTopics(this.searchQuery, '', this.currentSort);
            this.topics = Array.isArray(response) ? response : (response.topics || []);
        } catch (error) {
            // Silently fail - don't show error to user for background refresh
            console.log('Background topics refresh failed:', error);
        }
    }

    // Apply filter to topics
    async applyFilter(filter) {
        this.currentFilter = filter;
        // Reload topics to ensure we have fresh data, then apply filter
        await this.loadTopics(this.searchQuery);
    }

    // Apply sort to topics
    async applySort(sort) {
        this.currentSort = sort;
        await this.loadTopics(this.searchQuery);
    }

    // Get filtered topics based on current filter
    getFilteredTopics() {
        if (this.currentFilter === 'all') {
            return this.topics;
        } else if (this.currentFilter === 'public') {
            return this.topics.filter(topic => topic.is_public);
        } else if (this.currentFilter === 'private') {
            return this.topics.filter(topic => !topic.is_public);
        } else if (this.currentFilter === 'trending') {
            // Sort by vote count descending and take topics with > 0 votes
            return this.topics
                .filter(topic => (topic.total_votes || 0) > 0)
                .sort((a, b) => (b.total_votes || 0) - (a.total_votes || 0));
        } else if (this.currentFilter === 'favorites') {
            // Filter topics that are in user's favorites
            return this.topics.filter(topic => this.favorites.has(topic.share_code));
        }
        return this.topics;
    }

    // Add new option to editable topic
    async addOption(option) {
        try {
            authManager.requireAuth();

            if (!this.currentTopic) {
                showToast('No topic selected', 'error');
                return;
            }

            const response = await api.addOptionToTopic(this.currentTopic.share_code, option);
            showToast('Option added successfully!', 'success');

            // Reload topic to show the new option
            await this.showTopic(this.currentTopic.share_code);

        } catch (error) {
            console.error('Error adding option:', error);
            showToast(error.message || 'Error adding option', 'error');
        }
    }

    // Delete topic functionality
    async deleteTopic(shareCode) {
        try {
            authManager.requireAuth();

            const confirmed = await confirm('Are you sure you want to delete this topic? This action cannot be undone.');
            if (!confirmed) {
                return;
            }

            await api.deleteTopic(shareCode);
            showToast('Topic deleted successfully', 'success');

            // Navigate back to dashboard
            showSection('topicsDashboard');
            await this.loadTopics();

        } catch (error) {
            console.error('Error deleting topic:', error);
            showToast(error.message || 'Error deleting topic', 'error');
        }
    }

    // Favorites functionality
    async loadFavorites() {
        try {
            if (!authManager.isAuthenticated) return;

            const favorites = await api.getFavorites();
            this.favorites = new Set(favorites.map(fav => fav.share_code));
        } catch (error) {
            console.error('Error loading favorites:', error);
            // Don't show error to user, just fail silently
        }
    }

    async toggleFavorite(shareCode) {
        try {
            authManager.requireAuth();

            const isFavorited = this.favorites.has(shareCode);


            if (isFavorited) {
                await api.removeFromFavorites(shareCode);
                this.favorites.delete(shareCode);
                showToast('Removed from favorites', 'success');
            } else {
                await api.addToFavorites(shareCode);
                this.favorites.add(shareCode);
                showToast('Added to favorites', 'success');
            }

            // Update UI
            this.updateFavoriteButton();

        } catch (error) {
            console.error('Error toggling favorite:', error);
            showToast(error.message || 'Error updating favorites', 'error');
        }
    }

    async toggleFavoriteFromCard(shareCode) {
        try {
            authManager.requireAuth();

            const isFavorited = this.favorites.has(shareCode);
            
            // Find the topic to update its favorite count optimistically
            const topic = this.topics.find(t => t.share_code === shareCode);
            
            if (isFavorited) {
                await api.removeFromFavorites(shareCode);
                this.favorites.delete(shareCode);
                
                // Optimistically decrease the counter
                if (topic && topic.favorite_count > 0) {
                    topic.favorite_count -= 1;
                }
                
                showToast('Removed from favorites', 'success');
            } else {
                await api.addToFavorites(shareCode);
                this.favorites.add(shareCode);
                
                // Optimistically increase the counter
                if (topic) {
                    topic.favorite_count = (topic.favorite_count || 0) + 1;
                }
                
                showToast('Added to favorites! ⭐', 'success');
            }

            // Re-render topics to update the visual state
            this.renderTopics();

        } catch (error) {
            console.error('Error toggling favorite:', error);
            showToast(error.message || 'Error updating favorites', 'error');
            
            // On error, revert the optimistic update by reloading topics
            await this.loadTopics('', false);
        }
    }

    updateDeleteButton() {
        const deleteBtn = document.getElementById('deleteTopicBtn');
        if (!deleteBtn || !this.currentTopic) return;

        // Show delete button only if current user is the creator
        const currentUser = authManager.currentUser;
        const isCreator = currentUser && currentUser.username === this.currentTopic.created_by;


        if (isCreator) {
            deleteBtn.classList.remove('hidden');
        } else {
            deleteBtn.classList.add('hidden');
        }
    }

    updateLeaveButton() {
        const leaveBtn = document.getElementById('leaveTopicBtn');
        if (!leaveBtn || !this.currentTopic) return;

        // Show leave button only for private topics where user is not the creator
        const currentUser = authManager.currentUser;
        const isCreator = currentUser && currentUser.username === this.currentTopic.created_by;
        const isPrivate = !this.currentTopic.is_public;

        if (isPrivate && !isCreator && authManager.isAuthenticated) {
            leaveBtn.classList.remove('hidden');
        } else {
            leaveBtn.classList.add('hidden');
        }
    }

    async leaveTopic(shareCode) {
        try {
            authManager.requireAuth();

            const confirmed = await confirm('Are you sure you want to leave this topic? You will no longer be able to see it unless you access it via share code again.');
            if (!confirmed) {
                return;
            }

            // Remove current user from the topic
            const currentUser = authManager.currentUser;
            if (!currentUser) {
                showToast('User not found', 'error');
                return;
            }

            await api.removeTopicUser(shareCode, currentUser.username);
            showToast('You have left the topic', 'success');

            // Navigate back to dashboard
            showSection('topicsDashboard');
            await this.loadTopics();

        } catch (error) {
            console.error('Error leaving topic:', error);
            showToast(error.message || 'Error leaving topic', 'error');
        }
    }

    updateFavoriteButton() {
        const favoriteBtn = document.getElementById('favoriteTopicBtn');
        if (!favoriteBtn || !this.currentTopic) return;

        const isFavorited = this.favorites.has(this.currentTopic.share_code);


        if (isFavorited) {
            favoriteBtn.classList.add('btn-favorite', 'favorited');
            favoriteBtn.title = 'Remove from favorites';
            favoriteBtn.innerHTML = '<i class="fas fa-star"></i>';
        } else {
            favoriteBtn.classList.add('btn-favorite');
            favoriteBtn.classList.remove('favorited');
            favoriteBtn.title = 'Add to favorites';
            favoriteBtn.innerHTML = '<i class="far fa-star"></i>';
        }
    }





    // Description Editing Functionality
    updateDescriptionEditButton() {
        const editBtn = document.getElementById('editDescriptionBtn');
        if (!editBtn || !this.currentTopic) return;

        // Show edit button only if current user is the creator
        const currentUser = authManager.currentUser;
        const isCreator = currentUser && currentUser.username === this.currentTopic.created_by;

        if (isCreator) {
            editBtn.classList.remove('hidden');
        } else {
            editBtn.classList.add('hidden');
        }
    }

    showDescriptionEditForm() {
        const description = document.getElementById('topicDescription');
        const editBtn = document.getElementById('editDescriptionBtn');
        const editForm = document.getElementById('descriptionEditForm');
        const editInput = document.getElementById('descriptionEditInput');

        if (!description || !editBtn || !editForm || !editInput) return;

        // Hide description text and edit button
        description.classList.add('hidden');
        editBtn.classList.add('hidden');

        // Set current description in textarea
        const currentDescription = this.currentTopic?.description || '';
        editInput.value = currentDescription;

        // Show edit form and focus textarea
        editForm.classList.remove('hidden');
        editInput.focus();
    }

    hideDescriptionEditForm() {
        const description = document.getElementById('topicDescription');
        const editBtn = document.getElementById('editDescriptionBtn');
        const editForm = document.getElementById('descriptionEditForm');
        const editInput = document.getElementById('descriptionEditInput');

        if (!description || !editBtn || !editForm || !editInput) return;

        // Show description text and edit button (if creator)
        description.classList.remove('hidden');
        const currentUser = authManager.currentUser;
        const isCreator = currentUser && currentUser.username === this.currentTopic.created_by;
        if (isCreator) {
            editBtn.classList.remove('hidden');
        }

        // Hide edit form and clear input
        editForm.classList.add('hidden');
        editInput.value = '';
    }

    async saveDescription() {
        const editInput = document.getElementById('descriptionEditInput');
        const saveBtn = document.getElementById('saveDescriptionBtn');
        
        if (!editInput || !saveBtn || !this.currentTopic) return;

        const newDescription = editInput.value.trim();
        const originalDescription = this.currentTopic.description || '';

        // Check if description actually changed
        if (newDescription === originalDescription) {
            this.hideDescriptionEditForm();
            return;
        }

        try {
            // Disable save button and show loading
            saveBtn.disabled = true;
            const originalContent = saveBtn.innerHTML;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

            // Update description via API
            await api.updateTopicDescription(this.currentTopic.share_code, newDescription);

            // Update the current topic data
            this.currentTopic.description = newDescription;

            // Update the description text on the page
            const descriptionElement = document.getElementById('topicDescription');
            if (descriptionElement) {
                descriptionElement.textContent = newDescription || 'No description provided';
            }

            // Hide the edit form
            this.hideDescriptionEditForm();

            // Show success message
            showToast('Description updated successfully!', 'success');

        } catch (error) {
            console.error('Error updating description:', error);
            showToast(error.message || 'Error updating description', 'error');
        } finally {
            // Re-enable save button
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-check"></i> Save';
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

// Make topicsManager globally accessible
window.topicsManager = topicsManager;

// Global functions for event handlers
window.loadTopics = () => topicsManager.loadTopics();
window.showTopic = (id) => topicsManager.showTopic(id);
window.selectAnswer = (answer, isMultiSelect) => topicsManager.selectAnswer(answer, isMultiSelect);
window.submitVote = () => topicsManager.submitVote();

// Global functions for add option functionality
window.showAddOptionForm = () => {
    const form = document.getElementById('addOptionForm');
    const btn = document.getElementById('showAddOptionBtn');
    if (form && btn) {
        form.style.display = 'block';
        btn.style.display = 'none';
        document.getElementById('newOptionInput').focus();
    }
};

window.cancelAddOption = () => {
    const form = document.getElementById('addOptionForm');
    const btn = document.getElementById('showAddOptionBtn');
    const input = document.getElementById('newOptionInput');
    if (form && btn && input) {
        form.style.display = 'none';
        btn.style.display = 'block';
        input.value = '';
    }
};

window.submitNewOption = async () => {
    const input = document.getElementById('newOptionInput');
    if (!input) return;

    const option = input.value.trim();
    if (!option) {
        showToast('Please enter an option', 'error');
        return;
    }

    await topicsManager.addOption(option);
    window.cancelAddOption();
};

// Global functions for description editing
window.showDescriptionEditForm = () => topicsManager.showDescriptionEditForm();
window.hideDescriptionEditForm = () => topicsManager.hideDescriptionEditForm();
window.saveDescription = () => topicsManager.saveDescription();

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Search functionality
    const searchInput = document.getElementById('globalSearch');
    let searchTimeout;

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                // Suppress error messages during search to avoid spam
                topicsManager.loadTopics(e.target.value, false);
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
        const editable = document.querySelector('input[name="editable"]:checked').value;
        const multiSelect = document.querySelector('input[name="multiSelect"]:checked').value;

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
            is_editable: editable === 'true',
            allow_multi_select: multiSelect === 'true',
            tags: tags.length > 0 ? tags : null
        };

        try {
            await topicsManager.createTopic(topicData);
            resetCreateTopicForm();
        } catch (error) {
            // Error already handled in createTopic
        }
    });

    // Add voting option functionality is handled in app.js to avoid conflicts

    // Share topic button
    document.getElementById('shareTopicBtn').addEventListener('click', async () => {
        if (!topicsManager.currentTopic) {
            console.error('No current topic available for sharing');
            showToast('No topic selected for sharing', 'error');
            return;
        }

        try {
            if (!topicsManager.currentTopic.share_code) {
                throw new Error('Topic does not have a share code');
            }

            let shareUrl;
            if (topicsManager.currentTopic.is_public) {
                // For public topics, just copy the URL with share code
                shareUrl = `${window.location.origin}${window.location.pathname}?topic=${topicsManager.currentTopic.share_code}`;
            } else {
                // For private topics, use existing share code or get a new one
                shareUrl = `${window.location.origin}${window.location.pathname}?share=${topicsManager.currentTopic.share_code}`;
            }

            // Try modern clipboard API first, fall back to legacy method
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(shareUrl);
            } else {
                // Fallback for browsers that don't support clipboard API
                const textArea = document.createElement('textarea');
                textArea.value = shareUrl;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                document.execCommand('copy');
                textArea.remove();
            }

            if (topicsManager.currentTopic.is_public) {
                showToast('Topic URL copied to clipboard!', 'success');
            } else {
                showToast('Share code copied to clipboard!', 'success');
            }
        } catch (error) {
            console.error('Error sharing topic:', error);
            showToast('Error generating share link', 'error');
        }
    });

    // Favorite topic button
    document.getElementById('favoriteTopicBtn').addEventListener('click', async () => {
        if (!topicsManager.currentTopic) {
            console.error('No current topic available for favoriting');
            return;
        }
        await topicsManager.toggleFavorite(topicsManager.currentTopic.share_code);
    });

    // Delete topic button
    document.getElementById('deleteTopicBtn').addEventListener('click', async () => {
        if (!topicsManager.currentTopic) {
            console.error('No current topic available for deletion');
            return;
        }
        await topicsManager.deleteTopic(topicsManager.currentTopic.share_code);
    });

    // Leave topic button
    document.getElementById('leaveTopicBtn').addEventListener('click', async () => {
        if (!topicsManager.currentTopic) {
            console.error('No current topic available for leaving');
            return;
        }
        await topicsManager.leaveTopic(topicsManager.currentTopic.share_code);
    });


    // Description editing event listeners
    document.getElementById('editDescriptionBtn').addEventListener('click', () => {
        topicsManager.showDescriptionEditForm();
    });

    document.getElementById('saveDescriptionBtn').addEventListener('click', async () => {
        await topicsManager.saveDescription();
    });

    document.getElementById('cancelDescriptionBtn').addEventListener('click', () => {
        topicsManager.hideDescriptionEditForm();
    });

    // Allow saving description with Ctrl+Enter
    document.getElementById('descriptionEditInput').addEventListener('keydown', async (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            await topicsManager.saveDescription();
        }
        if (e.key === 'Escape') {
            e.preventDefault();
            topicsManager.hideDescriptionEditForm();
        }
    });
});

// Utility function to reset the entire create topic form
function resetCreateTopicForm() {
    const form = document.getElementById('createTopicForm');
    
    // Reset text inputs
    document.getElementById('topicTitleInput').value = '';
    document.getElementById('topicDescriptionInput').value = '';
    document.getElementById('topicTagsInput').value = '';
    
    // Reset radio buttons to default values
    document.getElementById('visibilityPublic').checked = true;
    document.getElementById('editableFalse').checked = true;
    document.getElementById('singleSelect').checked = true;
    
    // Reset voting options
    resetVotingOptions();
}

// Utility function to reset voting options
function resetVotingOptions() {
    const container = document.getElementById('votingOptionsContainer');
    container.innerHTML = `
        <div class="option-item">
            <div class="input-wrapper">
                <input type="text" placeholder="Option 1" required>
            </div>
            <button type="button" class="btn btn-ghost btn-sm remove-option">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="option-item">
            <div class="input-wrapper">
                <input type="text" placeholder="Option 2" required>
            </div>
            <button type="button" class="btn btn-ghost btn-sm remove-option">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;

    // Re-attach remove event listeners for the reset options
    container.querySelectorAll('.remove-option').forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (container.children.length > 2) { // Keep at least 2 options
                e.target.closest('.option-item').remove();
            }
        });
    });
}