/**
 * VOT1 Cyberpunk AI Chat Interface v3.0
 * 
 * Enhanced with Claude 3.7 Sonnet hybrid streaming capabilities,
 * semantic caching, and advanced memory management integration.
 */

// Core chat state with enhanced metrics
const chatState = {
    conversationId: null,
    messageHistory: [],
    isProcessing: false,
    isStreaming: true,
    isPaused: false,
    currentStream: null,
    streamBuffer: '',
    telemetry: {
        tokensUsed: 0,
        responseTime: 0,
        memoryUtilization: 0,
        thinkingDepth: 0,
        tokenVelocity: 0,
        confidenceScore: 0,
        semanticDistance: 0
    },
    activeModel: 'claude-3-7-sonnet-20240620',
    memoryContext: true,
    thinkingMode: 'extended',
    systemContext: null,
    semanticCacheEnabled: true,
    hybridMode: true,
    tools: {
        webSearch: true,
        codeExecution: true,
        fileAccess: true,
        visualization: true,
        perplexityResearch: true
    }
};

// DOM Elements
let chatContainer;
let messagesContainer;
let inputContainer;
let chatInput;
let sendButton;
let streamToggle;
let thinkingToggle;
let modelSelector;
let telemetryDisplay;
let toolsContainer;
let thinkingIndicator;
let audienceIndicator;
let layoutSelector;
let commandsContainer;
let semanticCacheToggle;
let hybridModeToggle;

// Constants
const TYPING_SPEED = 1; // Milliseconds per character
const MAX_THINKING_TOKENS = 2000;
const MESSAGE_FADE_DELAY = 100;
const SEMANTIC_CACHE_THRESHOLD = 0.85;
const HYBRID_MODEL_ENDPOINT = '/api/hybrid-stream';
const MAX_RETRIES = 3;

// Sound effects
let typingSound;
let notificationSound;
let errorSound;
let connectSound;

// Advanced semantic cache for AI responses
class SemanticCache {
    constructor() {
        this.cacheSize = 1000;
        this.enabled = true;
        this.vectorCache = new Map();
        this.responseCache = new Map();
        this.recentQueries = [];
        this.maxRecentQueries = 20;
        
        // Load persisted cache if available
        this._loadCache();
        
        // Setup periodic cache persistence
        setInterval(() => this._persistCache(), 60000);
        
        // Setup cache cleanup
        setInterval(() => this._cleanupCache(), 3600000);
    }
    
    async _loadCache() {
        if (window.cyberStorage) {
            const cache = await window.cyberStorage.getState('semantic-cache');
            if (cache) {
                try {
                    const parsed = JSON.parse(cache);
                    this.recentQueries = parsed.recentQueries || [];
                    
                    // Rebuild caches from persisted data
                    parsed.entries.forEach(entry => {
                        this.vectorCache.set(entry.id, new Float32Array(entry.vector));
                        this.responseCache.set(entry.id, entry.response);
                    });
                    
                    console.log(`Semantic cache loaded with ${this.vectorCache.size} entries`);
                } catch (err) {
                    console.error('Failed to load semantic cache:', err);
                }
            }
        }
    }
    
    async _persistCache() {
        if (window.cyberStorage && this.vectorCache.size > 0) {
            try {
                // Convert to a serializable format
                const entries = Array.from(this.vectorCache.entries()).map(([id, vector]) => {
                    return {
                        id,
                        vector: Array.from(vector),
                        response: this.responseCache.get(id)
                    };
                });
                
                const cacheData = {
                    recentQueries: this.recentQueries,
                    entries: entries
                };
                
                await window.cyberStorage.setState('semantic-cache', JSON.stringify(cacheData));
                console.log(`Semantic cache persisted with ${entries.length} entries`);
            } catch (err) {
                console.error('Failed to persist semantic cache:', err);
            }
        }
    }
    
    _cleanupCache() {
        // Keep cache size under limit
        if (this.vectorCache.size > this.cacheSize) {
            const entriesToDelete = this.vectorCache.size - this.cacheSize;
            const keys = Array.from(this.vectorCache.keys()).slice(0, entriesToDelete);
            
            keys.forEach(key => {
                this.vectorCache.delete(key);
                this.responseCache.delete(key);
            });
            
            console.log(`Cleaned up semantic cache, removed ${entriesToDelete} entries`);
        }
    }
    
    async getResponse(prompt) {
        if (!this.enabled || !chatState.semanticCacheEnabled) return null;
        
        // Generate embedding for prompt
        const embedding = await this._generateEmbedding(prompt);
        if (!embedding) return null;
        
        // Find semantically similar prompt
        const nearest = this._findNearestMatch(embedding);
        
        if (nearest && nearest.similarity >= SEMANTIC_CACHE_THRESHOLD) {
            console.log(`Semantic cache hit! Similarity: ${nearest.similarity.toFixed(3)}`);
            
            // Update telemetry
            chatState.telemetry.semanticDistance = nearest.similarity;
            
            // Add to recent queries
            this._addToRecentQueries(prompt, nearest.id);
            
            // Return cached response
            return {
                content: this.responseCache.get(nearest.id),
                fromCache: true,
                similarity: nearest.similarity
            };
        }
        
        return null;
    }
    
    async cacheResponse(prompt, response) {
        if (!this.enabled || !chatState.semanticCacheEnabled) return;
        
        // Generate embedding for prompt
        const embedding = await this._generateEmbedding(prompt);
        if (!embedding) return;
        
        // Create unique ID
        const id = `cache-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
        
        // Store in cache
        this.vectorCache.set(id, embedding);
        this.responseCache.set(id, response);
        
        // Add to recent queries
        this._addToRecentQueries(prompt, id);
        
        console.log(`Response cached with ID: ${id}`);
    }
    
    async _generateEmbedding(text) {
        try {
            // Make API call to get embedding
            const response = await fetch('/api/generate-embedding', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to generate embedding: ${response.statusText}`);
            }
            
            const data = await response.json();
            return new Float32Array(data.embedding);
        } catch (err) {
            console.error('Error generating embedding:', err);
            return null;
        }
    }
    
    _findNearestMatch(embedding) {
        let highestSimilarity = 0;
        let matchId = null;
        
        // Calculate similarity with all cached vectors
        for (const [id, vector] of this.vectorCache.entries()) {
            const similarity = this._cosineSimilarity(embedding, vector);
            
            if (similarity > highestSimilarity) {
                highestSimilarity = similarity;
                matchId = id;
            }
        }
        
        if (matchId) {
            return {
                id: matchId,
                similarity: highestSimilarity
            };
        }
        
        return null;
    }
    
    _cosineSimilarity(a, b) {
        let dotProduct = 0;
        let normA = 0;
        let normB = 0;
        
        for (let i = 0; i < a.length; i++) {
            dotProduct += a[i] * b[i];
            normA += a[i] * a[i];
            normB += b[i] * b[i];
        }
        
        return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
    }
    
    _addToRecentQueries(prompt, cacheId) {
        // Add to recent queries with timestamp
        this.recentQueries.unshift({
            prompt: prompt.substring(0, 100), // Store truncated prompt
            cacheId,
            timestamp: Date.now()
        });
        
        // Keep recent queries list at max size
        if (this.recentQueries.length > this.maxRecentQueries) {
            this.recentQueries.pop();
        }
    }
    
    getRecentQueries() {
        return this.recentQueries;
    }
    
    clearCache() {
        this.vectorCache.clear();
        this.responseCache.clear();
        this.recentQueries = [];
        
        if (window.cyberStorage) {
            window.cyberStorage.setState('semantic-cache', null);
        }
        
        console.log('Semantic cache cleared');
    }
}

// Initialize semantic cache
let semanticCache;

/**
 * Initialize the cyberpunk chat interface
 */
function initCyberpunkChat() {
    console.log('Initializing Cyberpunk Chat Interface v3.0...');
    
    // Initialize DOM elements
    chatContainer = document.getElementById('cyberpunk-chat');
    messagesContainer = document.getElementById('chat-messages');
    inputContainer = document.getElementById('chat-input-container');
    chatInput = document.getElementById('chat-input');
    sendButton = document.getElementById('chat-send');
    streamToggle = document.getElementById('stream-toggle');
    thinkingToggle = document.getElementById('thinking-toggle');
    modelSelector = document.getElementById('model-selector');
    telemetryDisplay = document.getElementById('telemetry-display');
    toolsContainer = document.getElementById('tools-container');
    thinkingIndicator = document.getElementById('thinking-indicator');
    audienceIndicator = document.getElementById('audience-indicator');
    layoutSelector = document.getElementById('layout-selector');
    commandsContainer = document.getElementById('commands-container');
    semanticCacheToggle = document.getElementById('semantic-cache-toggle');
    hybridModeToggle = document.getElementById('hybrid-mode-toggle');
    
    // Initialize semantic cache
    semanticCache = new SemanticCache();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load sound effects
    loadSoundEffects();
    
    // Load chat history
    loadChatHistory();
    
    // Load user preferences
    loadUserPreferences();
    
    // Apply cyberpunk effects
    applyCyberpunkEffects();
    
    console.log('Cyberpunk Chat Interface initialized');
}

/**
 * Set up event listeners for UI interaction
 */
function setupEventListeners() {
    // Send message on button click
    sendButton.addEventListener('click', () => {
        const message = chatInput.value.trim();
        if (message) {
            sendMessage(message);
        }
    });
    
    // Send message on Enter key press
    chatInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            const message = chatInput.value.trim();
            if (message) {
                sendMessage(message);
            }
        }
    });
    
    // Toggle streaming responses
    if (streamToggle) {
        streamToggle.addEventListener('change', () => {
            chatState.isStreaming = streamToggle.checked;
            saveUserPreferences();
        });
    }
    
    // Toggle thinking mode
    if (thinkingToggle) {
        thinkingToggle.addEventListener('change', () => {
            chatState.thinkingMode = thinkingToggle.checked ? 'extended' : 'minimal';
            saveUserPreferences();
        });
    }
    
    // Change AI model
    if (modelSelector) {
        modelSelector.addEventListener('change', () => {
            chatState.activeModel = modelSelector.value;
            saveUserPreferences();
        });
    }
    
    // Command suggestions
    if (commandsContainer) {
        commandsContainer.addEventListener('click', (event) => {
            if (event.target.classList.contains('command-item')) {
                chatInput.value = event.target.textContent;
                chatInput.focus();
            }
        });
    }
    
    // Toggle semantic cache
    if (semanticCacheToggle) {
        semanticCacheToggle.addEventListener('change', () => {
            chatState.semanticCacheEnabled = semanticCacheToggle.checked;
            saveUserPreferences();
        });
    }
    
    // Toggle hybrid mode
    if (hybridModeToggle) {
        hybridModeToggle.addEventListener('change', () => {
            chatState.hybridMode = hybridModeToggle.checked;
            saveUserPreferences();
        });
    }
    
    // Handle pause/resume streaming
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && chatState.isProcessing && chatState.isStreaming) {
            toggleStreamPause();
        }
    });
    
    // Add resize observer for responsive layout
    const resizeObserver = new ResizeObserver(entries => {
        for (const entry of entries) {
            adjustLayout(entry.contentRect.width);
        }
    });
    
    if (chatContainer) {
        resizeObserver.observe(chatContainer);
    }
}

/**
 * Send a message to the AI
 * @param {string} message The message to send
 */
async function sendMessage(message) {
    if (chatState.isProcessing) return;
    
    // Clear input
    chatInput.value = '';
    
    // Add user message to UI
    addMessageToUI('user', message);
    
    // Update state
    chatState.isProcessing = true;
    chatState.messageHistory.push({ role: 'user', content: message });
    
    // Show thinking indicator
    showThinkingIndicator();
    
    // Check semantic cache first
    let cachedResponse = null;
    if (chatState.semanticCacheEnabled) {
        cachedResponse = await semanticCache.getResponse(message);
    }
    
    if (cachedResponse) {
        // Use cached response
        hidThinkingIndicator();
        addMessageToUI('assistant', cachedResponse.content, true);
        
        // Update telemetry with cache info
        updateTelemetry({
            responseTime: 50, // Fast response from cache
            tokensUsed: cachedResponse.content.length / 4, // Estimate
            semanticDistance: cachedResponse.similarity,
            memoryUtilization: window.cyberStorage?.memoryUsage?.heapUsed || 0
        });
        
        // Reset state
        chatState.isProcessing = false;
        chatState.messageHistory.push({ role: 'assistant', content: cachedResponse.content });
        
        // Save chat history
        saveChatHistory();
    } else {
        // Process request
        if (chatState.isStreaming) {
            // Stream response
            processStreamingRequest(message);
        } else {
            // Get full response
            processRequest(message);
        }
    }
}

/**
 * Process a streaming request to the AI
 * @param {string} message The message to process
 */
async function processStreamingRequest(message) {
    const startTime = performance.now();
    let retryCount = 0;
    let success = false;
    
    // Track request for telemetry
    const requestId = `req-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    
    // Check if we should use enhanced hybrid mode with Perplexity deep research
    const requiresDeepResearch = message.length > 100 && 
        (/research|analyze|explain|compare|find|investigate|understand/.test(message.toLowerCase()) ||
         message.includes('?'));
        
    while (retryCount < MAX_RETRIES && !success) {
        try {
            // Prepare request based on hybrid mode
            const endpoint = chatState.hybridMode ? HYBRID_MODEL_ENDPOINT : '/api/streaming';
            
            console.log(`Processing request ${requestId} with ${chatState.hybridMode ? 'hybrid' : 'standard'} mode`);
            
            // Add research enhancement flag for server-side processing
            const body = {
                message,
                history: chatState.messageHistory.slice(-10), // Last 10 messages for context
                model: chatState.activeModel,
                thinking_mode: chatState.thinkingMode,
                hybrid_mode: chatState.hybridMode,
                deep_research: chatState.hybridMode && requiresDeepResearch && chatState.tools.perplexityResearch,
                memory_context: chatState.memoryContext,
                system_context: chatState.systemContext,
                tools: chatState.tools,
                request_id: requestId,
                max_thinking_tokens: chatState.thinkingMode === 'extended' ? 60000 : 1000,
                max_tokens: 20000 // Request larger context
            };
            
            // Show research indicator if using deep research
            if (body.deep_research) {
                addMessageToUI('system', 'Leveraging Perplexity for deep research...');
                if (thinkingIndicator) {
                    thinkingIndicator.classList.add('deep-research');
                }
            }
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(body)
            });
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.status} ${response.statusText}`);
            }
            
            chatState.streamBuffer = '';
            
            // Create message container now
            const messageElement = createMessageElement('assistant', '');
            messagesContainer.appendChild(messageElement);
            
            // Read from stream
            chatState.currentStream = response.body;
            await readFromStream(messageElement, startTime);
            
            success = true;
        } catch (error) {
            retryCount++;
            console.error(`Streaming error (attempt ${retryCount}):`, error);
            
            if (retryCount >= MAX_RETRIES) {
                // Show error message
                hidThinkingIndicator();
                addMessageToUI('system', `Error: Failed to get response after ${MAX_RETRIES} attempts. ${error.message}`);
                chatState.isProcessing = false;
                
                if (errorSound) errorSound.play();
            } else {
                // Retry with exponential backoff
                await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, retryCount)));
            }
        } finally {
            // Reset research indicator
            if (thinkingIndicator) {
                thinkingIndicator.classList.remove('deep-research');
            }
        }
    }
}

/**
 * Read from the stream and process chunks
 * @param {HTMLElement} messageElement The message element to update
 * @param {number} startTime The start time for telemetry
 */
async function readFromStream(messageElement, startTime) {
    const reader = chatState.currentStream.getReader();
    const decoder = new TextDecoder();
    let messageContent = '';
    let tokenCount = 0;
    let lastUpdateTime = performance.now();
    let isThinking = false;
    let thinkingContent = '';
    
    try {
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
                break;
            }
            
            // Decode the chunk
            const chunk = decoder.decode(value, { stream: true });
            chatState.streamBuffer += chunk;
            
            // Process the buffer
            processStreamBuffer(messageElement, messageContent, isThinking, thinkingContent);
            
            // Extract complete JSON objects from the buffer
            while (chatState.streamBuffer.includes('\n')) {
                const newlineIndex = chatState.streamBuffer.indexOf('\n');
                const jsonString = chatState.streamBuffer.substring(0, newlineIndex);
                chatState.streamBuffer = chatState.streamBuffer.substring(newlineIndex + 1);
                
                try {
                    const data = JSON.parse(jsonString);
                    
                    if (data.type === 'thinking') {
                        // Update thinking indicator
                        isThinking = true;
                        thinkingContent = data.content;
                        updateThinkingIndicator(data.content);
                        
                        // Update thinking telemetry
                        chatState.telemetry.thinkingDepth = (data.content.length / 10) || 0;
                    } 
                    else if (data.type === 'content') {
                        // Hide thinking indicator when content starts
                        if (isThinking) {
                            hidThinkingIndicator();
                            isThinking = false;
                        }
                        
                        // Update message content
                        messageContent = data.content;
                        messageElement.querySelector('.message-content').innerHTML = 
                            marked.parse(messageContent);
                        
                        // Apply syntax highlighting
                        messageElement.querySelectorAll('pre code').forEach((block) => {
                            hljs.highlightBlock(block);
                        });
                        
                        // Update token count
                        tokenCount = messageContent.length / 4; // Rough estimation
                        
                        // Calculate token velocity
                        const currentTime = performance.now();
                        const timeDiff = currentTime - lastUpdateTime;
                        if (timeDiff > 500) { // Update every 500ms
                            const velocity = (messageContent.length / 4) / ((currentTime - startTime) / 1000);
                            chatState.telemetry.tokenVelocity = velocity;
                            updateTelemetryDisplay();
                            lastUpdateTime = currentTime;
                        }
                    } 
                    else if (data.type === 'function_call') {
                        // Handle function calls
                        processFunctionCall(data.function_name, data.parameters);
                    }
                    else if (data.type === 'telemetry') {
                        // Update telemetry
                        updateTelemetry(data.metrics);
                    }
                    else if (data.type === 'end') {
                        // Finalize message
                        finalizeMessage(messageElement, messageContent);
                    }
                } catch (error) {
                    console.error('Error parsing JSON chunk:', error);
                }
            }
            
            // If paused, wait until resumed
            while (chatState.isPaused) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }
        
        // Process any remaining buffer content
        if (chatState.streamBuffer.length > 0) {
            try {
                const data = JSON.parse(chatState.streamBuffer);
                if (data.type === 'content') {
                    messageContent = data.content;
                    messageElement.querySelector('.message-content').innerHTML = 
                        marked.parse(messageContent);
                }
            } catch (error) {
                console.error('Error parsing final chunk:', error);
            }
        }
        
        // Finalize message
        finalizeMessage(messageElement, messageContent);
        
        // Update telemetry
        updateTelemetry({
            responseTime: performance.now() - startTime,
            tokensUsed: tokenCount,
            memoryUtilization: window.cyberStorage?.memoryUsage?.heapUsed || 0
        });
        
        // Cache the response
        if (messageContent && chatState.semanticCacheEnabled) {
            // Get last user message
            const lastUserMessage = chatState.messageHistory
                .filter(msg => msg.role === 'user')
                .pop()?.content;
                
            if (lastUserMessage) {
                semanticCache.cacheResponse(lastUserMessage, messageContent);
            }
        }
        
        // Add to message history
        chatState.messageHistory.push({ role: 'assistant', content: messageContent });
        
        // Save chat history
        saveChatHistory();
        
        // Reset state
        chatState.isProcessing = false;
        chatState.currentStream = null;
        
        // Hide thinking indicator
        hidThinkingIndicator();
    } catch (error) {
        console.error('Error reading from stream:', error);
        hidThinkingIndicator();
        addMessageToUI('system', `Error: Failed to read stream. ${error.message}`);
        chatState.isProcessing = false;
        
        if (errorSound) errorSound.play();
    }
}

/**
 * Process the stream buffer to extract events
 */
function processStreamBuffer(messageElement, currentContent, isThinking, thinkingContent) {
    // This function is now simpler as we're handling the JSON parsing inline in readFromStream
    // but keeping it for extensibility
}

/**
 * Finalize a message once streaming is complete
 */
function finalizeMessage(messageElement, content) {
    // Apply syntax highlighting to code blocks
    messageElement.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightBlock(block);
    });
    
    // Add copy buttons to code blocks
    messageElement.querySelectorAll('pre').forEach((pre) => {
        const copyButton = document.createElement('button');
        copyButton.className = 'code-copy-button';
        copyButton.innerHTML = '<i class="fas fa-copy"></i>';
        copyButton.addEventListener('click', () => {
            const code = pre.querySelector('code').textContent;
            navigator.clipboard.writeText(code);
            copyButton.innerHTML = '<i class="fas fa-check"></i>';
            setTimeout(() => {
                copyButton.innerHTML = '<i class="fas fa-copy"></i>';
            }, 2000);
        });
        pre.appendChild(copyButton);
    });
    
    // Add scroll animation to bring latest message into view
    messageElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

/**
 * Toggle pause/resume of the stream
 */
function toggleStreamPause() {
    chatState.isPaused = !chatState.isPaused;
    
    // Update UI to show paused state
    if (thinkingIndicator) {
        if (chatState.isPaused) {
            thinkingIndicator.classList.add('paused');
        } else {
            thinkingIndicator.classList.remove('paused');
        }
    }
}

/**
 * Process function calls from the AI
 */
function processFunctionCall(functionName, parameters) {
    console.log(`Processing function call: ${functionName}`, parameters);
    
    // Handle different function calls
    switch (functionName) {
        case 'search_web':
            // Implement web search
            break;
        case 'execute_code':
            // Implement code execution
            break;
        case 'visualize_data':
            // Implement data visualization
            break;
        default:
            console.warn(`Unknown function: ${functionName}`);
    }
}

/**
 * Update telemetry display
 */
function updateTelemetryDisplay() {
    if (!telemetryDisplay) return;
    
    // Update telemetry display elements
    const tokensElement = telemetryDisplay.querySelector('.telemetry-tokens');
    const responseElement = telemetryDisplay.querySelector('.telemetry-response');
    const memoryElement = telemetryDisplay.querySelector('.telemetry-memory');
    const velocityElement = telemetryDisplay.querySelector('.telemetry-velocity');
    const thinkingElement = telemetryDisplay.querySelector('.telemetry-thinking');
    
    if (tokensElement) {
        tokensElement.textContent = Math.round(chatState.telemetry.tokensUsed);
    }
    
    if (responseElement) {
        responseElement.textContent = `${Math.round(chatState.telemetry.responseTime)}ms`;
    }
    
    if (memoryElement && chatState.telemetry.memoryUtilization) {
        const memoryMB = (chatState.telemetry.memoryUtilization / (1024 * 1024)).toFixed(2);
        memoryElement.textContent = `${memoryMB}MB`;
    }
    
    if (velocityElement) {
        velocityElement.textContent = `${Math.round(chatState.telemetry.tokenVelocity)}/s`;
    }
    
    if (thinkingElement) {
        thinkingElement.textContent = Math.round(chatState.telemetry.thinkingDepth);
    }
}

/**
 * Update telemetry metrics
 */
function updateTelemetry(metrics) {
    // Update chat state telemetry
    if (metrics.responseTime !== undefined) {
        chatState.telemetry.responseTime = metrics.responseTime;
    }
    
    if (metrics.tokensUsed !== undefined) {
        chatState.telemetry.tokensUsed = metrics.tokensUsed;
    }
    
    if (metrics.memoryUtilization !== undefined) {
        chatState.telemetry.memoryUtilization = metrics.memoryUtilization;
    }
    
    if (metrics.thinkingDepth !== undefined) {
        chatState.telemetry.thinkingDepth = metrics.thinkingDepth;
    }
    
    if (metrics.tokenVelocity !== undefined) {
        chatState.telemetry.tokenVelocity = metrics.tokenVelocity;
    }
    
    if (metrics.confidenceScore !== undefined) {
        chatState.telemetry.confidenceScore = metrics.confidenceScore;
    }
    
    if (metrics.semanticDistance !== undefined) {
        chatState.telemetry.semanticDistance = metrics.semanticDistance;
    }
    
    // Update telemetry display
    updateTelemetryDisplay();
}

/**
 * Visualize thinking process using the THREE.js visualization system
 * @param {string} thinkingContent The thinking content to visualize
 */
function visualizeThinking(thinkingContent) {
    // Skip if thinking content is too short or visualization isn't available
    if (!thinkingContent || thinkingContent.length < 100) {
        return;
    }
    
    // Initialize visualization container if not already done
    const visualizationContainer = document.getElementById('thinking-visualization');
    if (!visualizationContainer) return;
    
    // Make visualization container active
    visualizationContainer.classList.add('active');
    
    // Extract key concepts from thinking content
    const concepts = extractKeyTerms(thinkingContent);
    
    // Create floating word animations for key concepts
    concepts.forEach((concept, index) => {
        setTimeout(() => {
            createFloatingWord(concept);
        }, index * 200); // Stagger appearance
    });
    
    // Use THREE.js visualization if available
    if (window.VOT1MemoryVisualization) {
        // Create a thinking node for the visualization
        const thinkingNode = {
            id: `thinking-${Date.now()}`,
            label: 'Thinking Process',
            type: 'semantic',
            content: thinkingContent.substring(0, 500), // Limit content size
            size: 20 + Math.min(thinkingContent.length / 1000, 30), // Size based on content length
            timestamp: Date.now()
        };
        
        // Create conceptual nodes connected to the main thinking node
        const conceptNodes = concepts.map((concept, index) => {
            return {
                id: `concept-${Date.now()}-${index}`,
                label: concept,
                type: 'swarm',
                content: concept,
                size: 5 + Math.min(concept.length, 15),
                timestamp: Date.now()
            };
        });
        
        // Create connections between nodes
        const links = conceptNodes.map(node => {
            return {
                source: thinkingNode.id,
                target: node.id,
                strength: 0.8,
                value: 1
            };
        });
        
        // Create additional connections between related concepts
        for (let i = 0; i < conceptNodes.length; i++) {
            for (let j = i + 1; j < conceptNodes.length; j++) {
                // Only connect some nodes to avoid cluttering
                if (Math.random() < 0.3) {
                    links.push({
                        source: conceptNodes[i].id,
                        target: conceptNodes[j].id,
                        strength: 0.3,
                        value: 0.5
                    });
                }
            }
        }
        
        // Update visualization with new nodes and links
        const nodes = [thinkingNode, ...conceptNodes];
        
        // Use the visualization API to update the graph
        window.VOT1MemoryVisualization.update({
            nodes: nodes,
            links: links
        });
        
        // Focus on the main thinking node
        window.VOT1MemoryVisualization.focusNode(thinkingNode.id);
    }
    
    // Schedule cleanup
    setTimeout(() => {
        visualizationContainer.classList.remove('active');
    }, 8000);
}

/**
 * Create a floating word animation for thinking visualization
 * @param {string} word The word to animate
 */
function createFloatingWord(word) {
    const container = document.getElementById('thinking-visualization');
    if (!container) return;
    
    // Create word element
    const wordElement = document.createElement('div');
    wordElement.className = 'thinking-word';
    wordElement.textContent = word;
    
    // Position randomly in the container
    const x = Math.random() * (container.offsetWidth - 100);
    const y = Math.random() * (container.offsetHeight - 50) + container.offsetHeight / 2;
    
    wordElement.style.left = `${x}px`;
    wordElement.style.top = `${y}px`;
    
    // Add random rotation
    const rotation = (Math.random() - 0.5) * 10;
    wordElement.style.transform = `rotate(${rotation}deg)`;
    
    // Add color variation
    const hue = Math.random() * 60 + 180; // Cyan to purple range
    wordElement.style.color = `hsl(${hue}, 100%, 80%)`;
    wordElement.style.textShadow = `0 0 5px hsl(${hue}, 100%, 60%)`;
    
    // Add to container
    container.appendChild(wordElement);
    
    // Remove after animation completes
    setTimeout(() => {
        if (wordElement.parentNode === container) {
            container.removeChild(wordElement);
        }
    }, 3000);
}

// Update the updateThinkingIndicator function to use visualization
function updateThinkingIndicator(content) {
    if (!thinkingIndicator) return;
    
    // Show thinking indicator
    thinkingIndicator.classList.add('active');
    
    // Update content if available
    const contentElement = thinkingIndicator.querySelector('.thinking-content');
    if (contentElement && content) {
        contentElement.textContent = content.substring(0, 200) + (content.length > 200 ? '...' : '');
        
        // Visualize thinking if in extended mode
        if (chatState.thinkingMode === 'extended') {
            visualizeThinking(content);
        }
    }
}

// Update the hidThinkingIndicator function to clean up visualizations
function hidThinkingIndicator() {
    if (!thinkingIndicator) return;
    
    // Hide thinking indicator
    thinkingIndicator.classList.remove('active');
    thinkingIndicator.classList.remove('deep-research');
    
    // Clean up visualization
    const visualizationContainer = document.getElementById('thinking-visualization');
    if (visualizationContainer) {
        visualizationContainer.classList.remove('active');
        
        // Clear all thinking words
        visualizationContainer.innerHTML = '';
    }
    
    // Reset thinking visualization if using THREE.js
    if (window.VOT1MemoryVisualization) {
        // Optional: Clear the visualization or reset the camera
        // window.VOT1MemoryVisualization.clear();
    }
}

/**
 * Extract key terms from thinking content
 * @param {string} text The text to analyze
 * @return {Array} Array of key terms
 */
function extractKeyTerms(text) {
    const terms = [];
    
    // Simple regex-based extraction of potential key terms
    // We look for capitalized phrases, quoted text, and technical terms
    
    // Extract capitalized phrases (likely concepts, proper nouns)
    const capitalizedRegex = /\b[A-Z][a-zA-Z]{2,}\b/g;
    const capitalizedMatches = text.match(capitalizedRegex) || [];
    
    // Extract quoted phrases (likely important concepts)
    const quotedRegex = /"([^"]+)"|'([^']+)'/g;
    const quotedText = [];
    let match;
    while ((match = quotedRegex.exec(text)) !== null) {
        quotedText.push(match[1] || match[2]);
    }
    
    // Extract technical terms and programming concepts
    const technicalRegex = /\b(API|function|class|object|algorithm|data|code|system|module|interface|component|model|variable|parameter|async|cache|tokens|vector|embedding|similarity|stream|buffer|request|response)\w*\b/gi;
    const technicalMatches = text.match(technicalRegex) || [];
    
    // Combine all matches, remove duplicates, and limit to top 10
    const allTerms = [...new Set([...capitalizedMatches, ...quotedText, ...technicalMatches])];
    
    // Filter terms to be at least 3 characters long
    const filteredTerms = allTerms.filter(term => term && term.length >= 3);
    
    // Return a slice of the terms (up to 10)
    return filteredTerms.slice(0, 10);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initCyberpunkChat);

// ... keep existing visualization and utility functions ... 