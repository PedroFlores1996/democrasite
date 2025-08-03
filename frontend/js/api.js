// API Configuration and utilities
class API {
    constructor(baseURL = 'http://localhost:8000') {
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

    // Authentication endpoints
    async register(username, password) {
        const response = await this.post('/api/register', { username, password });
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

    // Topic endpoints
    async getTopics(search = '', tags = '', limit = 20, page = 1) {
        const params = new URLSearchParams();
        if (search) params.append('title', search);  // Backend expects 'title' not 'search'
        if (tags) params.append('tags', tags);
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

    async vote(shareCode, answer) {
        return this.post(`/api/topics/${shareCode}/votes`, { choice: answer });
    }

    async getTopicUsers(shareCode) {
        return this.get(`/api/topics/${shareCode}/users`);
    }

    async addTopicUsers(shareCode, usernames) {
        return this.post(`/api/topics/${shareCode}/users`, { usernames });
    }

    async removeTopicUser(shareCode, username) {
        return this.delete(`/api/topics/${shareCode}/users/${username}`);
    }

    // Share code endpoints
    async getShareCode(shareCode) {
        return this.get(`/api/topics/${shareCode}/share-code`);
    }

    async joinByShareCode(shareCode) {
        return this.post(`/api/topics/join/${shareCode}`);
    }
}

// Global API instance
window.api = new API();