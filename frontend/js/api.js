// API Configuration and utilities
class API {
    constructor(baseURL = window.location.origin) {
        this.baseURL = baseURL;
        this.token = localStorage.getItem('authToken');
    }

    // Set authentication token
    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('authToken', token);
        } else {
            localStorage.removeItem('authToken');
        }
    }

    // Get authentication headers
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        return headers;
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.getAuthHeaders(),
            ...options,
        };

        try {
            const response = await fetch(url, config);
            
            // Handle different response types
            if (response.status === 204) {
                return null; // No content
            }
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    // GET request
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    // POST request
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    // PUT request
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    // DELETE request
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // PATCH request
    async patch(endpoint, data) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    // Authentication endpoints
    async register(username, email, password) {
        const response = await this.post('/api/register', { username, email, password });
        if (response.access_token) {
            this.setToken(response.access_token);
        }
        return response;
    }

    async login(username, password) {
        // FastAPI expects form data for OAuth2
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch(`${this.baseURL}/api/token`, {
            method: 'POST',
            body: formData,
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }
        
        const data = await response.json();
        if (data.access_token) {
            this.setToken(data.access_token);
        }
        return data;
    }

    async logout() {
        this.setToken(null);
    }

    // Get current user
    async getCurrentUser() {
        return this.get('/api/users/me');
    }

    // Get user stats
    async getUserStats() {
        return this.get('/api/users/me/stats');
    }

    // Delete user account
    async deleteAccount() {
        return this.delete('/api/users/me');
    }

    // Topic endpoints
    async getTopics(search = '', tags = '', sort = 'popular', limit = 20, page = 1) {
        const params = new URLSearchParams();
        if (search) params.append('title', search);  // Backend expects 'title' not 'search'
        if (tags) params.append('tags', tags);
        if (sort) params.append('sort', sort);
        params.append('limit', limit.toString());
        params.append('page', page.toString());      // Backend expects 'page' not 'skip'
        
        const query = params.toString();
        return this.get(`/api/topics${query ? '?' + query : ''}`);
    }

    async getTopic(shareCode) {
        return this.get(`/api/topics/${shareCode}`);
    }

    async createTopic(topicData) {
        return this.post('/api/topics', topicData);
    }

    async deleteTopic(shareCode) {
        return this.delete(`/api/topics/${shareCode}`);
    }


    async updateTopicDescription(shareCode, description) {
        return this.patch(`/api/topics/${shareCode}/description`, { description });
    }

    async vote(shareCode, choices) {
        // Handle both single choice (string) and multiple choices (array)
        const choicesArray = Array.isArray(choices) ? choices : [choices];
        return this.post(`/api/topics/${shareCode}/votes`, { choices: choicesArray });
    }

    async removeTopicUser(shareCode, username) {
        return this.delete(`/api/topics/${shareCode}/users/${username}`);
    }


    // Add option to editable topic
    async addOptionToTopic(shareCode, option) {
        return this.post(`/api/topics/${shareCode}/options`, { option });
    }

    // Favorites endpoints
    async getFavorites() {
        return this.get('/api/favorites');
    }

    async addToFavorites(shareCode) {
        return this.post(`/api/favorites/${shareCode}`);
    }

    async removeFromFavorites(shareCode) {
        return this.delete(`/api/favorites/${shareCode}`);
    }

}

// Global API instance - force current origin to handle different ports
window.api = new API(window.location.origin);