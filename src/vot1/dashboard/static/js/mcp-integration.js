/**
 * VOT1 Cyberpunk Chat - MCP Integration Module
 * 
 * Integrates Machine Capability Providers (MCPs) like Perplexity AI and Firecrawl
 * to enhance the cyberpunk chat experience with advanced research capabilities
 * and web data collection.
 */

// MCP Integration state management
const mcpState = {
    // Connection status for various providers
    connections: {
        perplexity: {
            active: false,
            connectionId: null,
            status: 'disconnected'
        },
        firecrawl: {
            active: false,
            connectionId: null,
            status: 'disconnected'
        }
    },
    
    // Research caching
    researchCache: new Map(),
    
    // Request tracking
    pendingRequests: new Map(),
    
    // Configuration options
    config: {
        autoResearch: true,
        researchDepth: 'medium', // basic, medium, deep
        researchTimeout: 30000, // 30 seconds
        enableWebCrawling: true,
        maxCrawlPages: 5,
        cacheTimeToLive: 24 * 60 * 60 * 1000 // 24 hours
    }
};

/**
 * Initialize MCP integration with the chat interface
 */
async function initMCPIntegration() {
    console.log('Initializing MCP Integration...');
    
    // Check connections status
    await checkConnectionStatus();
    
    // Initialize connection to Perplexity if needed
    if (!mcpState.connections.perplexity.active) {
        await connectToPerplexity();
    }
    
    // Initialize research cache
    initResearchCache();
    
    // Add MCP commands to the chat interface
    registerMCPCommands();
    
    console.log('MCP Integration initialized');
}

/**
 * Check connection status for all MCPs
 */
async function checkConnectionStatus() {
    try {
        // Check Perplexity connection
        const perplexityStatus = await checkPerplexityConnection();
        mcpState.connections.perplexity = perplexityStatus;
        
        // Check Firecrawl connection
        const firecrawlStatus = await checkFirecrawlConnection();
        mcpState.connections.firecrawl = firecrawlStatus;
        
        // Update UI with connection status
        updateConnectionStatusUI();
        
        return {
            perplexity: perplexityStatus,
            firecrawl: firecrawlStatus
        };
    } catch (error) {
        console.error('Error checking MCP connections:', error);
        return {
            error: error.message
        };
    }
}

/**
 * Check Perplexity AI connection status
 */
async function checkPerplexityConnection() {
    try {
        const response = await fetch('/api/mcp/perplexity/check-connection', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        return {
            active: data.active_connection || false,
            connectionId: data.connection_details?.connection_id || null,
            status: data.active_connection ? 'connected' : 'disconnected'
        };
    } catch (error) {
        console.error('Error checking Perplexity connection:', error);
        return {
            active: false,
            connectionId: null,
            status: 'error',
            error: error.message
        };
    }
}

/**
 * Check Firecrawl connection status
 */
async function checkFirecrawlConnection() {
    try {
        const response = await fetch('/api/mcp/firecrawl/check-connection', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        return {
            active: data.active_connection || false,
            connectionId: data.connection_details?.connection_id || null,
            status: data.active_connection ? 'connected' : 'disconnected'
        };
    } catch (error) {
        console.error('Error checking Firecrawl connection:', error);
        return {
            active: false,
            connectionId: null,
            status: 'error',
            error: error.message
        };
    }
}

/**
 * Connect to Perplexity AI
 */
async function connectToPerplexity() {
    try {
        // This is a mock function - in a real application, you'd make an API call to your backend
        // which would then use the MCP_PERPLEXITY_PERPLEXITYAI_INITIATE_CONNECTION function
        
        const response = await fetch('/api/mcp/perplexity/connect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        mcpState.connections.perplexity = {
            active: true,
            connectionId: data.connection_id,
            status: 'connected'
        };
        
        updateConnectionStatusUI();
        
        return data;
    } catch (error) {
        console.error('Error connecting to Perplexity:', error);
        mcpState.connections.perplexity.status = 'error';
        updateConnectionStatusUI();
        return {
            error: error.message
        };
    }
}

/**
 * Connect to Firecrawl
 * @param {Object} credentials API key and optional base URL for Firecrawl
 */
async function connectToFirecrawl(credentials) {
    try {
        // This is a mock function - in a real application, you'd make an API call to your backend
        // which would then use the MCP_FIRECRAWL_FIRECRAWL_INITIATE_CONNECTION function
        
        const response = await fetch('/api/mcp/firecrawl/connect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(credentials)
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        mcpState.connections.firecrawl = {
            active: true,
            connectionId: data.connection_id,
            status: 'connected'
        };
        
        updateConnectionStatusUI();
        
        return data;
    } catch (error) {
        console.error('Error connecting to Firecrawl:', error);
        mcpState.connections.firecrawl.status = 'error';
        updateConnectionStatusUI();
        return {
            error: error.message
        };
    }
}

/**
 * Initialize research cache
 */
function initResearchCache() {
    // Load cached research data if available
    if (window.cyberStorage) {
        window.cyberStorage.getState('mcp-research-cache')
            .then(cache => {
                if (cache) {
                    try {
                        const parsed = JSON.parse(cache);
                        
                        // Load cache entries, filtering out expired ones
                        const now = Date.now();
                        Object.entries(parsed).forEach(([key, value]) => {
                            if (value.expiresAt > now) {
                                mcpState.researchCache.set(key, value);
                            }
                        });
                        
                        console.log(`Research cache loaded with ${mcpState.researchCache.size} entries`);
                    } catch (err) {
                        console.error('Failed to load research cache:', err);
                    }
                }
            });
    }
}

/**
 * Persist research cache to storage
 */
function persistResearchCache() {
    if (window.cyberStorage && mcpState.researchCache.size > 0) {
        try {
            // Convert to a serializable format
            const cacheObj = {};
            mcpState.researchCache.forEach((value, key) => {
                cacheObj[key] = value;
            });
            
            window.cyberStorage.setState('mcp-research-cache', JSON.stringify(cacheObj));
            console.log(`Research cache persisted with ${mcpState.researchCache.size} entries`);
        } catch (err) {
            console.error('Failed to persist research cache:', err);
        }
    }
}

/**
 * Perform research using Perplexity AI
 * @param {string} query The research query
 * @param {Object} options Optional parameters for the research
 * @return {Promise<Object>} Research results
 */
async function performResearch(query, options = {}) {
    const requestId = `research-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    
    // Set default options
    const researchOptions = {
        depth: options.depth || mcpState.config.researchDepth,
        includeSourceUrls: options.includeSourceUrls !== undefined ? options.includeSourceUrls : true,
        returnCitations: options.returnCitations !== undefined ? options.returnCitations : true,
        timeout: options.timeout || mcpState.config.researchTimeout,
        useCache: options.useCache !== undefined ? options.useCache : true,
        systemPrompt: options.systemPrompt || "You are a research assistant. Provide thorough, accurate information with relevant details, examples, and context."
    };
    
    // Check cache first if enabled
    if (researchOptions.useCache) {
        const cacheKey = `${query}-${researchOptions.depth}`;
        const cachedResult = mcpState.researchCache.get(cacheKey);
        
        if (cachedResult && cachedResult.expiresAt > Date.now()) {
            console.log(`Research cache hit for query: ${query}`);
            return {
                ...cachedResult.data,
                fromCache: true,
                cacheTimestamp: cachedResult.timestamp
            };
        }
    }
    
    try {
        // Track the request
        mcpState.pendingRequests.set(requestId, {
            type: 'research',
            query,
            options: researchOptions,
            startTime: Date.now(),
            status: 'pending'
        });
        
        // This is a mock function - in a real application, you'd make an API call to your backend
        // which would then use the MCP_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH function
        
        const response = await fetch('/api/mcp/perplexity/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query,
                options: researchOptions
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Update request status
        mcpState.pendingRequests.set(requestId, {
            ...mcpState.pendingRequests.get(requestId),
            status: 'completed',
            completedAt: Date.now()
        });
        
        // Cache the result if caching is enabled
        if (researchOptions.useCache) {
            const cacheKey = `${query}-${researchOptions.depth}`;
            mcpState.researchCache.set(cacheKey, {
                data,
                timestamp: Date.now(),
                expiresAt: Date.now() + mcpState.config.cacheTimeToLive
            });
            
            // Persist cache periodically
            persistResearchCache();
        }
        
        return data;
    } catch (error) {
        console.error('Error performing research:', error);
        
        // Update request status
        mcpState.pendingRequests.set(requestId, {
            ...mcpState.pendingRequests.get(requestId),
            status: 'error',
            error: error.message,
            completedAt: Date.now()
        });
        
        return {
            error: error.message
        };
    }
}

/**
 * Crawl web pages using Firecrawl
 * @param {string} url The base URL to crawl
 * @param {Object} options Optional parameters for the crawl
 * @return {Promise<Object>} Crawl results
 */
async function crawlWebPages(url, options = {}) {
    // Check if Firecrawl is connected
    if (!mcpState.connections.firecrawl.active) {
        console.error('Firecrawl is not connected');
        return {
            error: 'Firecrawl is not connected'
        };
    }
    
    const requestId = `crawl-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    
    // Set default options
    const crawlOptions = {
        limit: options.limit || mcpState.config.maxCrawlPages,
        maxDepth: options.maxDepth || 2,
        allowExternalLinks: options.allowExternalLinks !== undefined ? options.allowExternalLinks : false,
        scrapeOptions: {
            onlyMainContent: options.onlyMainContent !== undefined ? options.onlyMainContent : true,
            formats: options.formats || ['markdown', 'html']
        }
    };
    
    try {
        // Track the request
        mcpState.pendingRequests.set(requestId, {
            type: 'crawl',
            url,
            options: crawlOptions,
            startTime: Date.now(),
            status: 'pending'
        });
        
        // This is a mock function - in a real application, you'd make an API call to your backend
        // which would then use the MCP_FIRECRAWL_FIRECRAWL_CRAWL_URLS function
        
        const response = await fetch('/api/mcp/firecrawl/crawl', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url,
                options: crawlOptions
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Update request status
        mcpState.pendingRequests.set(requestId, {
            ...mcpState.pendingRequests.get(requestId),
            status: 'completed',
            completedAt: Date.now()
        });
        
        return data;
    } catch (error) {
        console.error('Error crawling web pages:', error);
        
        // Update request status
        mcpState.pendingRequests.set(requestId, {
            ...mcpState.pendingRequests.get(requestId),
            status: 'error',
            error: error.message,
            completedAt: Date.now()
        });
        
        return {
            error: error.message
        };
    }
}

/**
 * Register MCP commands with the chat interface
 */
function registerMCPCommands() {
    // Add commands if the chat has a commands container
    const commandsContainer = document.getElementById('commands-container');
    if (!commandsContainer) return;
    
    // Get command item template
    const commandTemplate = document.getElementById('command-item-template');
    if (!commandTemplate) return;
    
    // Define MCP commands
    const mcpCommands = [
        {
            name: '/research',
            description: 'Perform in-depth research on a topic using Perplexity AI',
            icon: 'fa-search',
            handler: (args) => {
                const query = args.join(' ');
                if (!query) return 'Please provide a research topic';
                
                // Show thinking indicator
                if (window.showThinkingIndicator) {
                    window.showThinkingIndicator('Researching using Perplexity AI...');
                }
                
                // Perform research
                return performResearch(query)
                    .then(result => {
                        if (window.hidThinkingIndicator) {
                            window.hidThinkingIndicator();
                        }
                        
                        if (result.error) {
                            return `Error performing research: ${result.error}`;
                        }
                        
                        return result.response || result.content || 'No results found';
                    })
                    .catch(error => {
                        if (window.hidThinkingIndicator) {
                            window.hidThinkingIndicator();
                        }
                        
                        return `Error performing research: ${error.message}`;
                    });
            }
        },
        {
            name: '/crawl',
            description: 'Crawl a website for information using Firecrawl',
            icon: 'fa-spider',
            handler: (args) => {
                const url = args[0];
                if (!url) return 'Please provide a URL to crawl';
                
                // Show thinking indicator
                if (window.showThinkingIndicator) {
                    window.showThinkingIndicator('Crawling website...');
                }
                
                // Parse options if provided
                const options = {};
                if (args.length > 1) {
                    args.slice(1).forEach(arg => {
                        if (arg.startsWith('limit=')) {
                            options.limit = parseInt(arg.split('=')[1], 10);
                        } else if (arg.startsWith('depth=')) {
                            options.maxDepth = parseInt(arg.split('=')[1], 10);
                        } else if (arg === 'external') {
                            options.allowExternalLinks = true;
                        }
                    });
                }
                
                // Crawl web pages
                return crawlWebPages(url, options)
                    .then(result => {
                        if (window.hidThinkingIndicator) {
                            window.hidThinkingIndicator();
                        }
                        
                        if (result.error) {
                            return `Error crawling website: ${result.error}`;
                        }
                        
                        return `Crawl completed. Found ${result.results?.length || 0} pages.`;
                    })
                    .catch(error => {
                        if (window.hidThinkingIndicator) {
                            window.hidThinkingIndicator();
                        }
                        
                        return `Error crawling website: ${error.message}`;
                    });
            }
        },
        {
            name: '/firecrawl-connect',
            description: 'Connect to Firecrawl with your API key',
            icon: 'fa-link',
            handler: (args) => {
                const apiKey = args[0];
                if (!apiKey) return 'Please provide your Firecrawl API key';
                
                return connectToFirecrawl({ api_key: apiKey })
                    .then(result => {
                        if (result.error) {
                            return `Error connecting to Firecrawl: ${result.error}`;
                        }
                        
                        return 'Successfully connected to Firecrawl!';
                    })
                    .catch(error => {
                        return `Error connecting to Firecrawl: ${error.message}`;
                    });
            }
        }
    ];
    
    // Register commands with the chat interface
    if (window.registerChatCommands) {
        window.registerChatCommands(mcpCommands);
    } else {
        // If the chat doesn't have a command registration function,
        // we'll create a shim that will be called when the chat is initialized
        window.mcpCommands = mcpCommands;
    }
}

/**
 * Update connection status in the UI
 */
function updateConnectionStatusUI() {
    // Update Perplexity connection status
    const perplexityStatus = document.getElementById('perplexity-status');
    if (perplexityStatus) {
        perplexityStatus.textContent = mcpState.connections.perplexity.status;
        perplexityStatus.className = `status-indicator ${mcpState.connections.perplexity.status}`;
    }
    
    // Update Firecrawl connection status
    const firecrawlStatus = document.getElementById('firecrawl-status');
    if (firecrawlStatus) {
        firecrawlStatus.textContent = mcpState.connections.firecrawl.status;
        firecrawlStatus.className = `status-indicator ${mcpState.connections.firecrawl.status}`;
    }
}

/**
 * Update chat interface with custom hybrid functionality
 */
function enhanceChatWithMCP() {
    // Only proceed if we have an active chat interface
    if (!window.chatState) return;
    
    // Enhance the chat's sendMessage function to automatically use research when needed
    const originalSendMessage = window.sendMessage;
    if (originalSendMessage && mcpState.config.autoResearch) {
        window.sendMessage = async function(message) {
            // Check if the message might benefit from research
            const needsResearch = mcpState.config.autoResearch && 
                (message.length > 50) && 
                (/who|what|when|where|why|how|explain|research|find|look up|search|tell me about/i.test(message));
                
            if (needsResearch && mcpState.connections.perplexity.active) {
                // Show research indicator
                const systemMessage = "Enhancing response with Perplexity research...";
                if (window.addMessageToUI) {
                    window.addMessageToUI('system', systemMessage);
                }
                
                try {
                    // Perform research in parallel
                    const researchPromise = performResearch(message);
                    
                    // Continue with original message sending
                    const result = await originalSendMessage.call(window, message);
                    
                    // Wait for research to complete
                    const research = await researchPromise;
                    
                    // Enhance thinking with research results
                    if (research && !research.error) {
                        // Update system context with research
                        if (window.chatState.systemContext) {
                            window.chatState.systemContext += `\n\nRecent research findings: ${research.content || research.response}`;
                        } else {
                            window.chatState.systemContext = `Recent research findings: ${research.content || research.response}`;
                        }
                    }
                    
                    return result;
                } catch (error) {
                    console.error('Error in enhanced sendMessage:', error);
                    return originalSendMessage.call(window, message);
                }
            } else {
                // Use original function for messages that don't need research
                return originalSendMessage.call(window, message);
            }
        };
    }
}

// Export function for global access
window.mcpIntegration = {
    init: initMCPIntegration,
    performResearch,
    crawlWebPages,
    enhanceChatWithMCP,
    connectToFirecrawl,
    getConnectionStatus: () => ({
        perplexity: mcpState.connections.perplexity,
        firecrawl: mcpState.connections.firecrawl
    }),
    state: mcpState
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait a brief moment for the chat interface to initialize first
    setTimeout(() => {
        initMCPIntegration()
            .then(() => {
                enhanceChatWithMCP();
                console.log('MCP Integration enhanced the chat interface');
            })
            .catch(error => {
                console.error('Error initializing MCP integration:', error);
            });
    }, 500);
}); 