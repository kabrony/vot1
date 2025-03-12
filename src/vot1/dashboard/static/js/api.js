/**
 * VOT1 Dashboard API Client
 * 
 * This file provides functions for interacting with the VOT1 API.
 */

class VOT1Api {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl || window.location.origin;
    }

    /**
     * Get system status
     * @returns {Promise<Object>} System status data
     */
    async getStatus() {
        try {
            const response = await fetch(`${this.baseUrl}/api/status`);
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error getting status:', error);
            throw error;
        }
    }

    /**
     * Get memory contents
     * @param {string} query - Optional search query
     * @param {number} limit - Maximum number of results to return
     * @returns {Promise<Object>} Memory data
     */
    async getMemory(query = '', limit = 10) {
        try {
            const url = new URL(`${this.baseUrl}/api/memory`);
            if (query) {
                url.searchParams.append('query', query);
            }
            url.searchParams.append('limit', limit.toString());

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error getting memory:', error);
            throw error;
        }
    }

    /**
     * Get memory statistics
     * @returns {Promise<Object>} Memory statistics
     */
    async getMemoryStats() {
        try {
            const response = await fetch(`${this.baseUrl}/api/memory/stats`);
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error getting memory stats:', error);
            throw error;
        }
    }

    /**
     * Send a message to Claude
     * @param {string} prompt - The user's message
     * @param {string} systemPrompt - Optional system prompt
     * @param {boolean} useMemory - Whether to use memory
     * @param {boolean} usePerplexity - Whether to use web search
     * @returns {Promise<Object>} Response from Claude
     */
    async sendMessage(prompt, systemPrompt = null, useMemory = true, usePerplexity = false) {
        try {
            const response = await fetch(`${this.baseUrl}/api/message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prompt,
                    system_prompt: systemPrompt,
                    use_memory: useMemory,
                    use_perplexity: usePerplexity
                })
            });

            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error sending message:', error);
            throw error;
        }
    }

    /**
     * Add knowledge to semantic memory
     * @param {string} content - The knowledge content
     * @param {Object} metadata - Optional metadata
     * @returns {Promise<Object>} Response with memory ID
     */
    async addKnowledge(content, metadata = {}) {
        try {
            const response = await fetch(`${this.baseUrl}/api/knowledge`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content,
                    metadata
                })
            });

            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error adding knowledge:', error);
            throw error;
        }
    }
}

// Create and export API instance
const api = new VOT1Api();
window.vot1Api = api; 