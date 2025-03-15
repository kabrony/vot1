/**
 * VOT1 Dashboard API Client
 * 
 * JavaScript client for interacting with the VOT1 API from the dashboard.
 */

class VOT1ApiClient {
    /**
     * Initialize the API client
     * @param {string} baseUrl - Base URL for the API (defaults to current origin)
     */
    constructor(baseUrl = window.location.origin) {
        this.baseUrl = baseUrl;
        this.socketConnected = false;
        this.socket = null;
        
        // Initialize socket.io connection if available
        if (typeof io !== 'undefined') {
            this.socket = io(baseUrl);
            
            this.socket.on('connect', () => {
                console.log('Socket connected');
                this.socketConnected = true;
            });
            
            this.socket.on('disconnect', () => {
                console.log('Socket disconnected');
                this.socketConnected = false;
            });
        }
    }
    
    /**
     * Make a request to the API
     * @param {string} endpoint - API endpoint
     * @param {string} method - HTTP method
     * @param {Object} data - Request data
     * @returns {Promise<Object>} - Response data
     */
    async request(endpoint, method = 'GET', data = null) {
        const url = `${this.baseUrl}/api/${endpoint}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url, options);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.message || 'API request failed');
            }
            
            return result;
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }
    
    /**
     * Get the system status
     * @returns {Promise<Object>} - System status
     */
    async getStatus() {
        return this.request('status');
    }
    
    /**
     * Get memory content
     * @param {string} query - Optional search query
     * @param {number} limit - Maximum number of results
     * @returns {Promise<Object>} - Memory content
     */
    async getMemory(query = '', limit = 100) {
        const queryParams = new URLSearchParams();
        if (query) queryParams.append('query', query);
        if (limit) queryParams.append('limit', limit);
        
        return this.request(`memory?${queryParams.toString()}`);
    }
    
    /**
     * Get memory statistics
     * @returns {Promise<Object>} - Memory statistics
     */
    async getMemoryStats() {
        return this.request('memory/stats');
    }
    
    /**
     * Send a message to VOT1
     * @param {string} prompt - User prompt
     * @param {string} conversationId - Conversation ID
     * @param {boolean} useMemory - Whether to use memory
     * @param {boolean} useWebSearch - Whether to use web search
     * @param {string} systemPrompt - Optional system prompt
     * @returns {Promise<Object>} - Response from VOT1
     */
    async sendMessage(prompt, conversationId = null, useMemory = true, useWebSearch = true, systemPrompt = null) {
        const data = {
            prompt,
            use_memory: useMemory,
            use_web_search: useWebSearch
        };
        
        if (conversationId) data.conversation_id = conversationId;
        if (systemPrompt) data.system_prompt = systemPrompt;
        
        return this.request('message', 'POST', data);
    }
    
    /**
     * Perform a web search
     * @param {string} query - Search query
     * @param {boolean} includeLinks - Whether to include source links
     * @param {boolean} detailedResponses - Whether to provide detailed responses
     * @returns {Promise<Object>} - Search results
     */
    async searchWeb(query, includeLinks = true, detailedResponses = true) {
        const data = {
            query,
            include_links: includeLinks,
            detailed_responses: detailedResponses
        };
        
        return this.request('search', 'POST', data);
    }
    
    /**
     * Add knowledge to semantic memory
     * @param {string} content - Knowledge content
     * @param {Object} metadata - Knowledge metadata
     * @returns {Promise<Object>} - Response data
     */
    async addKnowledge(content, metadata = {}) {
        const data = {
            content,
            metadata
        };
        
        return this.request('knowledge', 'POST', data);
    }
}

// Create global API client instance
const vot1Api = new VOT1ApiClient(); 