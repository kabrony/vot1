/**
 * VOTai TRILOGY BRAIN - Composio Integration
 * Integrates with Composio for enhanced tool calling capabilities
 */

class ComposioIntegration {
    constructor(options = {}) {
        this.options = Object.assign({
            apiKey: null,
            integrationId: null,
            initialized: false,
            useLocalStorage: true,
            useEnv: true,
            debugMode: false
        }, options);

        // API credentials and state
        this.apiKey = this.options.apiKey || this.getStoredApiKey();
        this.integrationId = this.options.integrationId || this.getStoredIntegrationId();
        this.initialized = false;
        this.tools = [];
        this.activeConnections = [];
        this.lastResponse = null;
        
        // Bind methods
        this.initializeComposio = this.initializeComposio.bind(this);
        this.getConnectedAccounts = this.getConnectedAccounts.bind(this);
        this.executeToolCall = this.executeToolCall.bind(this);
        this.registerTerminalCommands = this.registerTerminalCommands.bind(this);
    }

    /**
     * Initialize the Composio integration
     * @returns {Promise<boolean>} - Whether initialization was successful
     */
    async initializeComposio() {
        if (this.initialized) return true;

        try {
            // Check if we have the API key
            if (!this.apiKey) {
                console.error("No Composio API key provided");
                return false;
            }

            // Initialize client based on whether we're in Node.js or browser environment
            if (typeof window === 'undefined') {
                // Node.js environment
                try {
                    const { ComposioToolSet } = await import('composio_openai');
                    this.toolset = new ComposioToolSet(this.apiKey);
                    this.log("Initialized Composio in Node.js environment");
                } catch (err) {
                    this.log("Error importing ComposioToolSet in Node environment", err);
                    return false;
                }
            } else {
                // Browser environment
                try {
                    // Using dynamic import for browser
                    const Composio = await import('composio-core').then(module => module.Composio);
                    this.composio = new Composio({ apiKey: this.apiKey });
                    this.log("Initialized Composio in browser environment");
                } catch (err) {
                    this.log("Error importing Composio in browser environment", err);
                    return false;
                }
            }

            // Get available tools
            await this.refreshAvailableTools();
            
            // Mark as initialized
            this.initialized = true;
            return true;
        } catch (error) {
            this.log("Error initializing Composio:", error);
            return false;
        }
    }

    /**
     * Get connected accounts from Composio
     * @returns {Promise<Array>} - List of connected accounts
     */
    async getConnectedAccounts() {
        if (!this.initialized) {
            await this.initializeComposio();
        }

        try {
            if (typeof window === 'undefined') {
                // Node.js environment
                const connections = await this.toolset.get_connected_accounts();
                this.activeConnections = connections;
                return connections;
            } else {
                // Browser environment
                const connections = await this.composio.connections.list();
                this.activeConnections = connections;
                return connections;
            }
        } catch (error) {
            this.log("Error getting connected accounts:", error);
            return [];
        }
    }

    /**
     * Get available tools from Composio
     * @returns {Promise<Array>} - List of available tools
     */
    async refreshAvailableTools() {
        if (!this.initialized) {
            await this.initializeComposio();
        }

        try {
            if (typeof window === 'undefined') {
                // Node.js environment
                // Get all tools or specific integration
                if (this.integrationId) {
                    const integration = await this.toolset.get_integration(this.integrationId);
                    this.tools = integration.tools || [];
                } else {
                    const allTools = await this.toolset.get_tools();
                    this.tools = allTools || [];
                }
            } else {
                // Browser environment
                if (this.integrationId) {
                    const integration = await this.composio.integrations.get({
                        integrationId: this.integrationId
                    });
                    this.tools = integration.tools || [];
                } else {
                    const allTools = await this.composio.tools.list();
                    this.tools = allTools || [];
                }
            }
            return this.tools;
        } catch (error) {
            this.log("Error refreshing available tools:", error);
            return [];
        }
    }

    /**
     * Execute a tool call through Composio
     * @param {string} toolName - Name of the tool to call
     * @param {Object} parameters - Parameters to pass to the tool
     * @returns {Promise<Object>} - Result of the tool call
     */
    async executeToolCall(toolName, parameters = {}) {
        if (!this.initialized) {
            await this.initializeComposio();
        }

        try {
            let result;
            if (typeof window === 'undefined') {
                // Node.js environment
                result = await this.toolset.execute_tool(toolName, parameters);
            } else {
                // Browser environment
                result = await this.composio.tools.execute({
                    tool: toolName,
                    parameters: parameters
                });
            }
            
            this.lastResponse = result;
            return result;
        } catch (error) {
            this.log("Error executing tool call:", error);
            throw error;
        }
    }

    /**
     * Register Composio commands with the terminal
     * @param {TerminalInterface} terminal - Terminal interface instance
     */
    registerTerminalCommands(terminal) {
        if (!terminal) return;

        // Add Composio command handler
        terminal.addCommandHandler('composio', async (args) => {
            const subCommand = args[0] || 'help';
            
            switch (subCommand) {
                case 'init':
                    const initialized = await this.initializeComposio();
                    if (initialized) {
                        terminal.logSuccess('Composio initialized successfully');
                    } else {
                        terminal.logError('Failed to initialize Composio');
                    }
                    break;
                    
                case 'connect':
                    const connections = await this.getConnectedAccounts();
                    terminal.logInfo(`Connected accounts: ${connections.length}`);
                    connections.forEach(conn => {
                        terminal.logInfo(`- ${conn.name || conn.id}: ${conn.status || 'connected'}`);
                    });
                    break;
                    
                case 'tools':
                    const tools = await this.refreshAvailableTools();
                    terminal.logInfo(`Available tools: ${tools.length}`);
                    tools.slice(0, 10).forEach(tool => {
                        terminal.logInfo(`- ${tool.name || tool.id}: ${tool.description || 'No description'}`);
                    });
                    if (tools.length > 10) {
                        terminal.logInfo(`... and ${tools.length - 10} more`);
                    }
                    break;
                    
                case 'run':
                    if (args.length < 2) {
                        terminal.logError('Usage: composio run <toolName> [params]');
                        break;
                    }
                    const toolName = args[1];
                    let params = {};
                    
                    // Parse parameters if provided
                    if (args.length > 2) {
                        try {
                            params = JSON.parse(args.slice(2).join(' '));
                        } catch (e) {
                            terminal.logError('Invalid JSON parameters');
                            break;
                        }
                    }
                    
                    terminal.logInfo(`Running tool: ${toolName}`);
                    try {
                        const result = await this.executeToolCall(toolName, params);
                        terminal.logSuccess('Tool execution completed');
                        terminal.logInfo(JSON.stringify(result, null, 2));
                    } catch (error) {
                        terminal.logError(`Failed to execute tool: ${error.message}`);
                    }
                    break;
                    
                case 'setkey':
                    if (args.length < 2) {
                        terminal.logError('Usage: composio setkey <apiKey>');
                        break;
                    }
                    this.apiKey = args[1];
                    this.storeApiKey(this.apiKey);
                    terminal.logSuccess('API key updated');
                    this.initialized = false; // Force re-initialization
                    break;
                    
                case 'help':
                default:
                    terminal.logInfo('Composio Commands:');
                    terminal.logInfo('  composio init - Initialize Composio');
                    terminal.logInfo('  composio connect - List connected accounts');
                    terminal.logInfo('  composio tools - List available tools');
                    terminal.logInfo('  composio run <toolName> [params] - Execute a tool');
                    terminal.logInfo('  composio setkey <apiKey> - Set API key');
                    terminal.logInfo('  composio help - Show this help');
                    break;
            }
        });

        // Add command completion for Composio commands
        terminal.addCommandCompletion('composio', ['init', 'connect', 'tools', 'run', 'setkey', 'help']);
        
        // Register helper commands
        this.registerHelperCommands(terminal);
    }

    /**
     * Register additional helper commands for common operations
     * @param {TerminalInterface} terminal - Terminal interface instance
     */
    registerHelperCommands(terminal) {
        // Web search command using Composio
        terminal.addCommandHandler('search', async (args) => {
            if (args.length === 0) {
                terminal.logError('Usage: search <query>');
                return;
            }
            
            const query = args.join(' ');
            terminal.logInfo(`Searching for: ${query}`);
            
            try {
                const result = await this.executeToolCall('FIRECRAWL_SEARCH', {
                    query: query,
                    limit: 5
                });
                
                terminal.logSuccess('Search results:');
                
                if (result && result.results) {
                    result.results.forEach((item, index) => {
                        terminal.logInfo(`[${index + 1}] ${item.title}`);
                        terminal.logSystem(item.snippet || 'No description');
                        terminal.logInfo(`URL: ${item.url}`);
                        terminal.logInfo('---');
                    });
                } else {
                    terminal.logWarning('No results found');
                }
            } catch (error) {
                terminal.logError(`Search failed: ${error.message}`);
            }
        });
    }

    /**
     * Get the stored API key from localStorage or .env
     * @returns {string|null} - Stored API key or null
     */
    getStoredApiKey() {
        // Try local storage if in browser
        if (typeof window !== 'undefined' && this.options.useLocalStorage) {
            const storedKey = localStorage.getItem('composio_api_key');
            if (storedKey) return storedKey;
        }
        
        // Try environment variables
        if (this.options.useEnv) {
            if (typeof process !== 'undefined' && process.env) {
                return process.env.COMPOSIO_API_KEY;
            }
        }
        
        // Default to the hardcoded key from the request (only for development)
        return "af20c9ht05ouuhwo6zkzs7";
    }

    /**
     * Store the API key in localStorage and/or .env
     * @param {string} apiKey - API key to store
     */
    storeApiKey(apiKey) {
        if (typeof window !== 'undefined' && this.options.useLocalStorage) {
            localStorage.setItem('composio_api_key', apiKey);
        }
        
        // Note: We can't modify .env from browser JavaScript
        // This would need to be handled by a backend service
    }

    /**
     * Get the stored integration ID from localStorage or .env
     * @returns {string|null} - Stored integration ID or null
     */
    getStoredIntegrationId() {
        // Try local storage if in browser
        if (typeof window !== 'undefined' && this.options.useLocalStorage) {
            const storedId = localStorage.getItem('composio_integration_id');
            if (storedId) return storedId;
        }
        
        // Try environment variables
        if (this.options.useEnv) {
            if (typeof process !== 'undefined' && process.env) {
                return process.env.COMPOSIO_INTEGRATION_ID;
            }
        }
        
        // Default to the hardcoded ID from the request
        return "7cc53fd7-ed35-442f-bc6d-10b1ed3cf85e";
    }

    /**
     * Store the integration ID in localStorage and/or .env
     * @param {string} integrationId - Integration ID to store
     */
    storeIntegrationId(integrationId) {
        if (typeof window !== 'undefined' && this.options.useLocalStorage) {
            localStorage.setItem('composio_integration_id', integrationId);
        }
        
        // Note: We can't modify .env from browser JavaScript
        // This would need to be handled by a backend service
    }

    /**
     * Log messages if debug mode is enabled
     * @param {...any} args - Arguments to log
     */
    log(...args) {
        if (this.options.debugMode) {
            console.log('[ComposioIntegration]', ...args);
        }
    }
}

// Export the class
window.ComposioIntegration = ComposioIntegration; 