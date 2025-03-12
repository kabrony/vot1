/**
 * VOT1 Dashboard Application
 * 
 * This file contains the main application logic for the VOT1 dashboard.
 */

// DOM Elements
const elements = {
    // Status elements
    statusIndicator: document.getElementById('status-indicator'),
    statusText: document.getElementById('status-text'),
    modelInfo: document.getElementById('model-info'),
    memoryStats: document.getElementById('memory-stats'),
    githubStatus: document.getElementById('github-status'),
    perplexityStatus: document.getElementById('perplexity-status'),
    
    // Tab navigation
    tabs: document.querySelectorAll('.sidebar a'),
    tabContents: document.querySelectorAll('.tab-content'),
    
    // Memory tab
    memorySearch: document.getElementById('memory-search'),
    memorySearchBtn: document.getElementById('memory-search-btn'),
    conversationMemory: document.getElementById('conversation-memory'),
    semanticMemory: document.getElementById('semantic-memory'),
    knowledgeContent: document.getElementById('knowledge-content'),
    addKnowledgeBtn: document.getElementById('add-knowledge-btn'),
    
    // Chat tab
    chatMessages: document.getElementById('chat-messages'),
    chatPrompt: document.getElementById('chat-prompt'),
    systemPrompt: document.getElementById('system-prompt'),
    useMemory: document.getElementById('use-memory'),
    usePerplexity: document.getElementById('use-perplexity'),
    sendMessageBtn: document.getElementById('send-message-btn'),
    
    // Settings tab
    apiKey: document.getElementById('api-key'),
    modelSelect: document.getElementById('model-select'),
    githubToken: document.getElementById('github-token'),
    githubRepo: document.getElementById('github-repo'),
    memoryPath: document.getElementById('memory-path'),
    clearMemoryBtn: document.getElementById('clear-memory-btn'),
    saveSettingsBtn: document.getElementById('save-settings-btn'),
    resetSettingsBtn: document.getElementById('reset-settings-btn'),
    
    // Activity list
    recentActivity: document.getElementById('recent-activity')
};

// Initialize the application
class DashboardApp {
    constructor(api) {
        this.api = api;
        this.initEventListeners();
        this.refreshSystemStatus();
        this.refreshMemoryData();
        
        // Set polling interval for system status (every 60 seconds)
        setInterval(() => this.refreshSystemStatus(), 60000);
    }
    
    initEventListeners() {
        // Tab navigation
        elements.tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(tab.getAttribute('data-tab'));
            });
        });
        
        // Memory search
        elements.memorySearchBtn.addEventListener('click', () => {
            this.searchMemory(elements.memorySearch.value);
        });
        
        elements.memorySearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchMemory(elements.memorySearch.value);
            }
        });
        
        // Add knowledge
        elements.addKnowledgeBtn.addEventListener('click', () => {
            this.addKnowledge(elements.knowledgeContent.value);
        });
        
        // Send message
        elements.sendMessageBtn.addEventListener('click', () => {
            this.sendMessage(
                elements.chatPrompt.value,
                elements.systemPrompt.value,
                elements.useMemory.checked,
                elements.usePerplexity.checked
            );
        });
        
        elements.chatPrompt.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.sendMessage(
                    elements.chatPrompt.value,
                    elements.systemPrompt.value,
                    elements.useMemory.checked,
                    elements.usePerplexity.checked
                );
            }
        });
        
        // Settings buttons
        elements.saveSettingsBtn.addEventListener('click', () => {
            this.saveSettings();
        });
        
        elements.resetSettingsBtn.addEventListener('click', () => {
            this.resetSettings();
        });
        
        elements.clearMemoryBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to clear all memory? This cannot be undone.')) {
                // This would require a new API endpoint
                alert('Memory clearing functionality not implemented yet.');
            }
        });
        
        // Listen for memory selection events from the visualization
        document.addEventListener('memory-selected', (e) => {
            this.handleMemorySelection(e.detail);
        });
    }
    
    switchTab(tabId) {
        // Update active tab
        elements.tabs.forEach(tab => {
            if (tab.getAttribute('data-tab') === tabId) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
        
        // Show the selected tab content
        elements.tabContents.forEach(content => {
            if (content.id === tabId) {
                content.classList.add('active');
            } else {
                content.classList.remove('active');
            }
        });
    }
    
    async refreshSystemStatus() {
        try {
            const status = await this.api.getStatus();
            
            // Update status indicator
            elements.statusIndicator.classList.add('online');
            elements.statusText.textContent = 'Online';
            
            // Update system info
            elements.modelInfo.textContent = `Model: ${status.model}`;
            elements.githubStatus.textContent = `GitHub: ${status.github_enabled ? 'Enabled' : 'Disabled'}`;
            elements.perplexityStatus.textContent = `Perplexity: ${status.perplexity_enabled ? 'Enabled' : 'Disabled'}`;
            
            // Update memory stats
            this.refreshMemoryStats();
        } catch (error) {
            console.error('Failed to refresh system status:', error);
            elements.statusIndicator.classList.remove('online');
            elements.statusIndicator.classList.add('offline');
            elements.statusText.textContent = 'Offline';
        }
    }
    
    async refreshMemoryStats() {
        try {
            const stats = await this.api.getMemoryStats();
            elements.memoryStats.textContent = `Memory: ${stats.conversation_items + stats.semantic_items} items`;
            
            // Update memory chart if it exists
            if (window.updateMemoryChart) {
                window.updateMemoryChart(stats);
            }
        } catch (error) {
            console.error('Failed to refresh memory stats:', error);
            elements.memoryStats.textContent = 'Memory: Unknown';
        }
    }
    
    async refreshMemoryData(query = '') {
        try {
            const memory = await this.api.getMemory(query);
            
            // Update visualization
            if (window.memoryVisualization) {
                window.memoryVisualization.updateMemoryNodes(memory);
            }
            
            // Update memory lists
            this.updateMemoryLists(memory);
            
            // Update recent activity
            this.updateRecentActivity(memory.conversation);
        } catch (error) {
            console.error('Failed to refresh memory data:', error);
        }
    }
    
    updateMemoryLists(memory) {
        // Clear existing lists
        elements.conversationMemory.innerHTML = '';
        elements.semanticMemory.innerHTML = '';
        
        // Update conversation memory list
        if (memory.conversation) {
            memory.conversation.forEach(item => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <strong>${item.role || 'system'}:</strong> 
                    ${this.truncateText(item.content, 50)}
                    <small>${this.formatTimestamp(item.timestamp)}</small>
                `;
                li.addEventListener('click', () => this.handleMemorySelection(item));
                elements.conversationMemory.appendChild(li);
            });
        }
        
        // Update semantic memory list
        if (memory.semantic) {
            memory.semantic.forEach(item => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <strong>Knowledge:</strong> 
                    ${this.truncateText(item.content, 50)}
                    <small>${this.formatTimestamp(item.timestamp)}</small>
                `;
                li.addEventListener('click', () => this.handleMemorySelection(item));
                elements.semanticMemory.appendChild(li);
            });
        }
    }
    
    updateRecentActivity(conversations = []) {
        if (!elements.recentActivity) return;
        
        // Clear existing activity list
        elements.recentActivity.innerHTML = '';
        
        // Take the 10 most recent conversations
        const recentItems = conversations.slice(0, 10);
        
        // Add each item to the activity list
        recentItems.forEach(item => {
            const div = document.createElement('div');
            div.className = 'activity-item';
            div.innerHTML = `
                <strong>${item.role || 'system'}</strong>
                <p>${this.truncateText(item.content, 40)}</p>
                <small>${this.formatTimestamp(item.timestamp)}</small>
            `;
            elements.recentActivity.appendChild(div);
        });
    }
    
    async searchMemory(query) {
        if (!query.trim()) {
            this.refreshMemoryData();
            return;
        }
        
        try {
            this.refreshMemoryData(query);
        } catch (error) {
            console.error('Search failed:', error);
            alert('Failed to search memory: ' + error.message);
        }
    }
    
    async addKnowledge(content) {
        if (!content.trim()) {
            alert('Please enter some content to add to memory.');
            return;
        }
        
        try {
            const result = await this.api.addKnowledge(content);
            alert('Knowledge added successfully!');
            elements.knowledgeContent.value = '';
            this.refreshMemoryData();
        } catch (error) {
            console.error('Failed to add knowledge:', error);
            alert('Failed to add knowledge: ' + error.message);
        }
    }
    
    async sendMessage(prompt, systemPrompt, useMemory, usePerplexity) {
        if (!prompt.trim()) {
            alert('Please enter a message to send.');
            return;
        }
        
        // Add user message to chat
        this.addChatMessage('user', prompt);
        
        // Clear input
        elements.chatPrompt.value = '';
        
        try {
            // Disable send button during request
            elements.sendMessageBtn.disabled = true;
            elements.sendMessageBtn.textContent = 'Sending...';
            
            // Send the message
            const response = await this.api.sendMessage(
                prompt,
                systemPrompt || null,
                useMemory,
                usePerplexity
            );
            
            // Add assistant response to chat
            this.addChatMessage('assistant', response.response.content);
            
            // Refresh memory data to reflect new messages
            this.refreshMemoryData();
            
        } catch (error) {
            console.error('Failed to send message:', error);
            this.addChatMessage('system', 'Error: Failed to send message. ' + error.message, true);
        } finally {
            // Re-enable send button
            elements.sendMessageBtn.disabled = false;
            elements.sendMessageBtn.textContent = 'Send';
        }
    }
    
    addChatMessage(role, content, isError = false) {
        const div = document.createElement('div');
        div.className = `message ${role}`;
        
        if (isError) {
            div.classList.add('error');
        }
        
        div.innerHTML = `
            <div class="message-header">
                <span class="message-role">${role.charAt(0).toUpperCase() + role.slice(1)}</span>
                <span class="message-time">${this.formatTimestamp(new Date().toISOString())}</span>
            </div>
            <div class="message-content">${this.formatMessage(content)}</div>
        `;
        
        elements.chatMessages.appendChild(div);
        
        // Scroll to bottom
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    }
    
    formatMessage(text) {
        // Simple markdown-like formatting
        // Replace code blocks
        text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        // Replace inline code
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Replace line breaks with <br>
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }
    
    handleMemorySelection(item) {
        // Show memory details
        let details = '';
        
        // Create HTML string with item details
        const keys = Object.keys(item);
        keys.forEach(key => {
            if (key === 'content') {
                details += `<h3>Content:</h3><div class="item-content">${item[key]}</div>`;
            } else if (key === 'metadata' && item[key]) {
                details += `<h3>Metadata:</h3><pre>${JSON.stringify(item[key], null, 2)}</pre>`;
            } else if (key !== 'id') {
                details += `<p><strong>${key}:</strong> ${item[key]}</p>`;
            }
        });
        
        // Create and show a modal with the memory details
        const modal = document.createElement('div');
        modal.className = 'memory-modal';
        modal.innerHTML = `
            <div class="memory-modal-content">
                <span class="close-button">&times;</span>
                <h2>Memory Details</h2>
                ${details}
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Add close button functionality
        const closeButton = modal.querySelector('.close-button');
        closeButton.addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        
        // Close when clicking outside the modal content
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
    }
    
    saveSettings() {
        const settings = {
            apiKey: elements.apiKey.value,
            model: elements.modelSelect.value,
            githubToken: elements.githubToken.value,
            githubRepo: elements.githubRepo.value,
            memoryPath: elements.memoryPath.value
        };
        
        // Save to local storage
        localStorage.setItem('vot1_settings', JSON.stringify(settings));
        
        alert('Settings saved! Please note that applying these settings requires restarting the server.');
    }
    
    resetSettings() {
        // Clear settings from local storage
        localStorage.removeItem('vot1_settings');
        
        // Reset form fields
        elements.apiKey.value = '';
        elements.modelSelect.value = 'claude-3.7-sonnet-20240620';
        elements.githubToken.value = '';
        elements.githubRepo.value = '';
        elements.memoryPath.value = '.vot1/memory';
        
        alert('Settings reset to defaults.');
    }
    
    loadSettings() {
        const savedSettings = localStorage.getItem('vot1_settings');
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            
            elements.apiKey.value = settings.apiKey || '';
            elements.modelSelect.value = settings.model || 'claude-3.7-sonnet-20240620';
            elements.githubToken.value = settings.githubToken || '';
            elements.githubRepo.value = settings.githubRepo || '';
            elements.memoryPath.value = settings.memoryPath || '.vot1/memory';
        }
    }
    
    // Helper functions
    truncateText(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }
    
    formatTimestamp(timestamp) {
        if (!timestamp) return '';
        
        const date = new Date(timestamp);
        return date.toLocaleString();
    }
}

// Initialize the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new DashboardApp(window.vot1Api);
    
    // Load saved settings
    app.loadSettings();
    
    // Make app available globally (for debugging)
    window.dashboardApp = app;
}); 