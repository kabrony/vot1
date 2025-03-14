/**
 * VOT1 Development Assistant Integration
 * 
 * This module integrates the Python-based Development Assistant with the
 * Cyberpunk Chat interface, allowing for real-time code analysis,
 * research with Perplexity, and leveraging Claude 3.7's extended thinking
 */

// Development Assistant state and configuration
const devAssistantState = {
    initialized: false,
    analyzing: false,
    lastAnalysis: null,
    lastResearch: null,
    memoryEnabled: true,
    maxThinkingTokens: 60000,
    hybridEnabled: true,
    
    config: {
        codebaseRoot: null,
        memoryPath: null,
        defaultResearchDepth: 'deep',
        generateDocs: true,
        autoTroubleshoot: true,
        persistResults: true
    }
};

/**
 * Initialize the Development Assistant integration
 */
async function initDevAssistant() {
    console.log('Initializing Development Assistant integration...');
    
    try {
        // Check if backend is available
        const response = await fetch('/api/dev-assistant/status');
        
        if (!response.ok) {
            console.warn('Development Assistant API not available, some features will be limited');
            addDevAssistantMessage('Warning: Development Assistant backend not available. Running in limited mode.');
            return false;
        }
        
        const data = await response.json();
        
        devAssistantState.initialized = data.initialized;
        devAssistantState.config = {
            ...devAssistantState.config,
            ...data.config
        };
        
        // Register commands
        registerDevAssistantCommands();
        
        // Add welcome message
        addDevAssistantMessage('VOT1 Development Assistant initialized. Type /analyze to analyze your codebase or /research to perform research with Perplexity AI.');
        
        console.log('Development Assistant integration initialized');
        return true;
    } catch (error) {
        console.error('Error initializing Development Assistant:', error);
        addDevAssistantMessage('Error initializing Development Assistant: ' + error.message);
        return false;
    }
}

/**
 * Register Development Assistant commands with the chat interface
 */
function registerDevAssistantCommands() {
    // Make sure we have access to command registration
    if (!window.registerChatCommands) {
        console.warn('Chat command registration not available');
        window.devAssistantCommands = getDevAssistantCommands();
        return;
    }
    
    // Register commands with chat interface
    window.registerChatCommands(getDevAssistantCommands());
}

/**
 * Get Development Assistant commands
 */
function getDevAssistantCommands() {
    return [
        {
            name: '/analyze',
            description: 'Analyze codebase structure or specific files',
            icon: 'fa-code',
            handler: (args) => handleAnalyzeCommand(args)
        },
        {
            name: '/research',
            description: 'Perform deep research with Perplexity integration',
            icon: 'fa-search',
            handler: (args) => handleResearchCommand(args)
        },
        {
            name: '/generate',
            description: 'Generate scripts, docs, or code snippets',
            icon: 'fa-file-code',
            handler: (args) => handleGenerateCommand(args)
        },
        {
            name: '/troubleshoot',
            description: 'Troubleshoot code with Claude 3.7 + Perplexity',
            icon: 'fa-bug',
            handler: (args) => handleTroubleshootCommand(args)
        },
        {
            name: '/architecture',
            description: 'Get project architecture analysis and recommendations',
            icon: 'fa-sitemap',
            handler: (args) => handleArchitectureCommand(args)
        },
        {
            name: '/memory',
            description: 'Access dev assistant memory subsystem',
            icon: 'fa-database',
            handler: (args) => handleMemoryCommand(args)
        }
    ];
}

/**
 * Handle /analyze command
 */
async function handleAnalyzeCommand(args) {
    if (devAssistantState.analyzing) {
        return 'Analysis already in progress, please wait...';
    }
    
    // Show loading indicator
    if (window.showThinkingIndicator) {
        window.showThinkingIndicator('Analyzing codebase...');
    }
    
    devAssistantState.analyzing = true;
    
    try {
        let path = args.length > 0 ? args[0] : null;
        let fileExtension = args.length > 1 ? args[1] : '.py';
        
        // Make the API call
        const response = await fetch('/api/dev-assistant/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: path,
                file_extension: fileExtension
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const result = await response.json();
        devAssistantState.lastAnalysis = result;
        
        // Format the result for display
        const summary = formatAnalysisSummary(result);
        
        // Hide loading indicator
        if (window.hidThinkingIndicator) {
            window.hidThinkingIndicator();
        }
        
        devAssistantState.analyzing = false;
        return summary;
    } catch (error) {
        console.error('Error analyzing codebase:', error);
        
        // Hide loading indicator
        if (window.hidThinkingIndicator) {
            window.hidThinkingIndicator();
        }
        
        devAssistantState.analyzing = false;
        return `Error analyzing codebase: ${error.message}`;
    }
}

/**
 * Format analysis summary for display
 */
function formatAnalysisSummary(analysis) {
    if (!analysis) return 'No analysis data available';
    
    let summary = '## Codebase Analysis Summary\n\n';
    
    summary += `**Files analyzed:** ${analysis.total_files}\n`;
    summary += `**Total lines:** ${analysis.total_lines} (${analysis.total_code_lines} code, ${analysis.total_comment_lines} comments, ${analysis.total_blank_lines} blank)\n`;
    summary += `**Classes:** ${analysis.total_classes}\n`;
    summary += `**Functions:** ${analysis.total_functions}\n`;
    summary += `**Unique imports:** ${analysis.unique_import_count}\n\n`;
    
    summary += '### Key imports:\n';
    
    // Group imports by category
    const frameworkImports = [];
    const utilityImports = [];
    const standardLibImports = [];
    
    analysis.unique_imports.forEach(imp => {
        if (imp.startsWith('flask') || imp.startsWith('django') || imp.startsWith('fastapi') || 
            imp.startsWith('tensorflow') || imp.startsWith('torch') || imp.startsWith('sklearn')) {
            frameworkImports.push(imp);
        } else if (imp.startsWith('os') || imp.startsWith('sys') || imp.startsWith('json') || 
                  imp.startsWith('datetime') || imp.startsWith('logging') || imp.startsWith('typing')) {
            standardLibImports.push(imp);
        } else {
            utilityImports.push(imp);
        }
    });
    
    if (frameworkImports.length > 0) {
        summary += '- **Frameworks:** ' + frameworkImports.slice(0, 5).join(', ');
        if (frameworkImports.length > 5) summary += ` and ${frameworkImports.length - 5} more`;
        summary += '\n';
    }
    
    if (utilityImports.length > 0) {
        summary += '- **Utilities:** ' + utilityImports.slice(0, 5).join(', ');
        if (utilityImports.length > 5) summary += ` and ${utilityImports.length - 5} more`;
        summary += '\n';
    }
    
    return summary;
}

/**
 * Handle /research command
 */
async function handleResearchCommand(args) {
    if (args.length === 0) {
        return 'Please provide a research query. Usage: /research [query]';
    }
    
    const query = args.join(' ');
    
    // Show loading indicator
    if (window.showThinkingIndicator) {
        window.showThinkingIndicator('Researching with Perplexity AI...');
    }
    
    try {
        // Make the API call
        const response = await fetch('/api/dev-assistant/research', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                depth: devAssistantState.config.defaultResearchDepth
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const result = await response.json();
        devAssistantState.lastResearch = result;
        
        // Hide loading indicator
        if (window.hidThinkingIndicator) {
            window.hidThinkingIndicator();
        }
        
        // Format the results
        let formattedResult = `## Research Results: ${query}\n\n`;
        formattedResult += result.content;
        
        if (result.citations && result.citations.length > 0) {
            formattedResult += '\n\n### Sources\n';
            result.citations.forEach((citation, index) => {
                formattedResult += `${index + 1}. [${citation.title || 'Source'}](${citation.url})\n`;
            });
        }
        
        return formattedResult;
    } catch (error) {
        console.error('Error performing research:', error);
        
        // Hide loading indicator
        if (window.hidThinkingIndicator) {
            window.hidThinkingIndicator();
        }
        
        return `Error performing research: ${error.message}`;
    }
}

/**
 * Handle /generate command
 */
async function handleGenerateCommand(args) {
    if (args.length === 0) {
        return 'Please specify what to generate. Usage: /generate [script|docs|test] [description]';
    }
    
    const type = args[0].toLowerCase();
    if (!['script', 'docs', 'test'].includes(type)) {
        return 'Invalid generation type. Supported types: script, docs, test';
    }
    
    if (args.length < 2) {
        return `Please provide a description for the ${type} to generate`;
    }
    
    const description = args.slice(1).join(' ');
    
    // Show loading indicator
    if (window.showThinkingIndicator) {
        window.showThinkingIndicator(`Generating ${type}...`);
    }
    
    try {
        // Map UI type to backend script type
        const scriptType = type === 'script' ? 'python' : 
                         type === 'docs' ? 'markdown' : 
                         'python'; // test defaults to python
        
        // Make the API call
        const response = await fetch('/api/dev-assistant/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                description: description,
                script_type: scriptType,
                generate_type: type
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Hide loading indicator
        if (window.hidThinkingIndicator) {
            window.hidThinkingIndicator();
        }
        
        // Format the results
        let formattedResult = `## Generated ${type.charAt(0).toUpperCase() + type.slice(1)}\n\n`;
        formattedResult += `**Description:** ${description}\n\n`;
        formattedResult += '```' + (scriptType === 'python' ? 'python' : scriptType) + '\n';
        formattedResult += result.script;
        formattedResult += '\n```\n\n';
        
        formattedResult += `To save this file, use: /memory save ${result.key}`;
        
        return formattedResult;
    } catch (error) {
        console.error(`Error generating ${type}:`, error);
        
        // Hide loading indicator
        if (window.hidThinkingIndicator) {
            window.hidThinkingIndicator();
        }
        
        return `Error generating ${type}: ${error.message}`;
    }
}

/**
 * Handle /troubleshoot command
 */
async function handleTroubleshootCommand(args) {
    if (args.length === 0) {
        return 'Please provide code to troubleshoot or a path to a file. Usage: /troubleshoot [code] or /troubleshoot file [path]';
    }
    
    let code = '';
    let errorMessage = null;
    let isFile = false;
    
    if (args[0] === 'file') {
        if (args.length < 2) {
            return 'Please provide a file path. Usage: /troubleshoot file [path]';
        }
        
        isFile = true;
        const filePath = args[1];
        
        // Show loading indicator
        if (window.showThinkingIndicator) {
            window.showThinkingIndicator('Loading file for troubleshooting...');
        }
        
        // Get file content first
        try {
            const fileResponse = await fetch(`/api/dev-assistant/read-file?path=${encodeURIComponent(filePath)}`);
            
            if (!fileResponse.ok) {
                throw new Error(`Error reading file: ${fileResponse.status}`);
            }
            
            const fileData = await fileResponse.json();
            code = fileData.content;
            
            // Look for error message in the remaining args
            if (args.length > 2 && args[2] === 'error') {
                errorMessage = args.slice(3).join(' ');
            }
        } catch (error) {
            console.error('Error reading file:', error);
            
            // Hide loading indicator
            if (window.hidThinkingIndicator) {
                window.hidThinkingIndicator();
            }
            
            return `Error reading file: ${error.message}`;
        }
    } else {
        // Direct code input
        // Find if there's an 'error' marker to separate code from error message
        const errorIndex = args.indexOf('error');
        
        if (errorIndex !== -1) {
            code = args.slice(0, errorIndex).join(' ');
            errorMessage = args.slice(errorIndex + 1).join(' ');
        } else {
            code = args.join(' ');
        }
    }
    
    // Update loading indicator
    if (window.showThinkingIndicator) {
        window.showThinkingIndicator('Troubleshooting code with Claude 3.7 + Perplexity...');
    }
    
    try {
        // Make the API call
        const response = await fetch('/api/dev-assistant/troubleshoot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                code: code,
                error_message: errorMessage,
                is_file: isFile
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Hide loading indicator
        if (window.hidThinkingIndicator) {
            window.hidThinkingIndicator();
        }
        
        return result.analysis;
    } catch (error) {
        console.error('Error troubleshooting code:', error);
        
        // Hide loading indicator
        if (window.hidThinkingIndicator) {
            window.hidThinkingIndicator();
        }
        
        return `Error troubleshooting code: ${error.message}`;
    }
}

/**
 * Handle /architecture command
 */
async function handleArchitectureCommand(args) {
    // Show loading indicator
    if (window.showThinkingIndicator) {
        window.showThinkingIndicator('Analyzing project architecture (this may take a minute)...');
    }
    
    try {
        // Make the API call
        const response = await fetch('/api/dev-assistant/architecture', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Hide loading indicator
        if (window.hidThinkingIndicator) {
            window.hidThinkingIndicator();
        }
        
        // Return the architecture analysis
        return result.analysis;
    } catch (error) {
        console.error('Error analyzing architecture:', error);
        
        // Hide loading indicator
        if (window.hidThinkingIndicator) {
            window.hidThinkingIndicator();
        }
        
        return `Error analyzing architecture: ${error.message}`;
    }
}

/**
 * Handle /memory command
 */
async function handleMemoryCommand(args) {
    if (args.length === 0) {
        return 'Please specify a memory action. Usage: /memory [list|get|save|delete] [category] [key] [file_path]';
    }
    
    const action = args[0].toLowerCase();
    
    if (action === 'list') {
        // List categories or keys
        try {
            const category = args.length > 1 ? args[1] : null;
            const url = category
                ? `/api/dev-assistant/memory/list?category=${encodeURIComponent(category)}`
                : '/api/dev-assistant/memory/list';
                
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (category) {
                if (result.keys.length === 0) {
                    return `No keys found in category "${category}"`;
                }
                
                let output = `## Keys in category "${category}":\n\n`;
                result.keys.forEach(key => {
                    output += `- ${key}\n`;
                });
                
                return output;
            } else {
                if (result.categories.length === 0) {
                    return 'No memory categories found';
                }
                
                let output = '## Memory Categories:\n\n';
                result.categories.forEach(cat => {
                    output += `- ${cat}\n`;
                });
                
                return output;
            }
        } catch (error) {
            console.error('Error listing memory:', error);
            return `Error listing memory: ${error.message}`;
        }
    } else if (action === 'get') {
        // Get memory entry
        if (args.length < 3) {
            return 'Please specify category and key. Usage: /memory get [category] [key]';
        }
        
        const category = args[1];
        const key = args[2];
        
        try {
            const response = await fetch(`/api/dev-assistant/memory/get?category=${encodeURIComponent(category)}&key=${encodeURIComponent(key)}`);
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (!result.data) {
                return `No data found for key "${key}" in category "${category}"`;
            }
            
            // If the data is a simple string, return it directly
            if (typeof result.data === 'string') {
                return result.data;
            }
            
            // If it's a script, return it as code block
            if (category === 'generated_scripts') {
                let output = `## Generated Script: ${key}\n\n`;
                output += '```\n';
                output += result.data.content || 'No content available';
                output += '\n```\n';
                
                return output;
            }
            
            // Otherwise format as JSON
            return '```json\n' + JSON.stringify(result.data, null, 2) + '\n```';
        } catch (error) {
            console.error('Error getting memory:', error);
            return `Error getting memory: ${error.message}`;
        }
    } else if (action === 'save') {
        // Save script to file
        if (args.length < 3) {
            return 'Please specify script key and optional file path. Usage: /memory save [script_key] [file_path]';
        }
        
        const scriptKey = args[1];
        const filePath = args.length > 2 ? args[2] : null;
        
        try {
            const response = await fetch('/api/dev-assistant/memory/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    script_key: scriptKey,
                    file_path: filePath
                })
            });
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (!result.success) {
                return `Error saving script: ${result.error}`;
            }
            
            return `Script saved successfully to: ${result.file_path}`;
        } catch (error) {
            console.error('Error saving script:', error);
            return `Error saving script: ${error.message}`;
        }
    } else if (action === 'delete') {
        // Delete memory entry
        if (args.length < 3) {
            return 'Please specify category and key. Usage: /memory delete [category] [key]';
        }
        
        const category = args[1];
        const key = args[2];
        
        try {
            const response = await fetch('/api/dev-assistant/memory/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    category: category,
                    key: key
                })
            });
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (!result.success) {
                return `Error deleting memory: ${result.error}`;
            }
            
            return `Successfully deleted key "${key}" from category "${category}"`;
        } catch (error) {
            console.error('Error deleting memory:', error);
            return `Error deleting memory: ${error.message}`;
        }
    } else {
        return `Unknown memory action: ${action}. Available actions: list, get, save, delete`;
    }
}

/**
 * Add a development assistant message to the chat interface
 */
function addDevAssistantMessage(message) {
    // If we have a chat message function, use it
    if (window.addMessageToUI) {
        window.addMessageToUI('system', message);
    } else {
        // Otherwise log to console
        console.log('Development Assistant:', message);
    }
}

/**
 * Enhance the chat with the Development Assistant
 */
function enhanceChatWithDevAssistant() {
    // Only proceed if we have an active chat interface
    if (!window.chatState) return;
    
    // Patch thinking toggle to enable max tokens
    const thinkingToggle = document.getElementById('thinking-toggle');
    if (thinkingToggle) {
        const originalOnChange = thinkingToggle.onchange;
        thinkingToggle.onchange = function(event) {
            // Call original handler if it exists
            if (originalOnChange) {
                originalOnChange.call(this, event);
            }
            
            // Update max thinking tokens
            if (this.checked) {
                // Enable deep thinking with max tokens
                window.chatState.maxThinkingTokens = devAssistantState.maxThinkingTokens;
                console.log(`Set max thinking tokens to ${devAssistantState.maxThinkingTokens}`);
            } else {
                // Reset to default
                window.chatState.maxThinkingTokens = 2000;
                console.log('Reset max thinking tokens to default (2000)');
            }
        };
    }
    
    // Enhance the existing thinking visualization to show code analysis
    if (window.visualizeThinking) {
        const originalVisualizeThinking = window.visualizeThinking;
        window.visualizeThinking = function(thinking) {
            // Call original visualizer
            originalVisualizeThinking.call(window, thinking);
            
            // Check if thinking contains code analysis or research
            if (thinking && thinking.toLowerCase().includes('analyze') && 
                devAssistantState.lastAnalysis) {
                // Create additional visualization nodes for code structure
                const visualization = document.getElementById('thinking-visualization');
                if (visualization) {
                    // Add code structure visualization
                    visualizeCodeStructure(visualization, devAssistantState.lastAnalysis);
                }
            }
        };
    }
}

/**
 * Visualize code structure in the thinking visualization element
 */
function visualizeCodeStructure(visualizationElement, analysis) {
    // Create a code structure map
    if (!analysis || !analysis.file_details || analysis.file_details.length === 0) return;
    
    // Create a container for the code structure
    const container = document.createElement('div');
    container.className = 'code-structure-visualization';
    container.style.position = 'absolute';
    container.style.right = '20px';
    container.style.top = '20px';
    container.style.width = '200px';
    container.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    container.style.borderRadius = '5px';
    container.style.padding = '10px';
    container.style.color = 'var(--primary-color)';
    container.style.fontSize = '12px';
    container.style.fontFamily = 'var(--mono-font)';
    container.style.maxHeight = '80%';
    container.style.overflow = 'auto';
    container.style.zIndex = '1000';
    
    // Add title
    const title = document.createElement('div');
    title.textContent = 'Code Structure';
    title.style.fontWeight = 'bold';
    title.style.borderBottom = '1px solid var(--primary-color)';
    title.style.marginBottom = '5px';
    title.style.paddingBottom = '5px';
    container.appendChild(title);
    
    // Create a simple tree representation of the files
    const fileCount = Math.min(analysis.file_details.length, 15); // Limit to 15 files
    
    for (let i = 0; i < fileCount; i++) {
        const file = analysis.file_details[i];
        const fileName = file.file_path.split('/').pop();
        
        const fileElement = document.createElement('div');
        fileElement.textContent = fileName;
        fileElement.style.marginTop = '5px';
        fileElement.style.color = 'var(--tertiary-color)';
        
        // Add class/function count
        const countElement = document.createElement('div');
        countElement.textContent = `⚙️ ${file.class_count} classes, ${file.function_count} functions`;
        countElement.style.fontSize = '10px';
        countElement.style.color = 'var(--secondary-color)';
        countElement.style.marginLeft = '10px';
        
        fileElement.appendChild(countElement);
        container.appendChild(fileElement);
    }
    
    if (analysis.file_details.length > fileCount) {
        const moreElement = document.createElement('div');
        moreElement.textContent = `... and ${analysis.file_details.length - fileCount} more files`;
        moreElement.style.marginTop = '5px';
        moreElement.style.fontStyle = 'italic';
        moreElement.style.opacity = '0.7';
        container.appendChild(moreElement);
    }
    
    visualizationElement.appendChild(container);
}

// Export functions for global access
window.devAssistant = {
    init: initDevAssistant,
    analyze: handleAnalyzeCommand,
    research: handleResearchCommand,
    generate: handleGenerateCommand,
    troubleshoot: handleTroubleshootCommand,
    state: devAssistantState,
    visualizeCodeStructure
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait for the chat interface to initialize first
    setTimeout(() => {
        initDevAssistant()
            .then(() => {
                enhanceChatWithDevAssistant();
                console.log('Development Assistant integration enhanced the chat interface');
            })
            .catch(error => {
                console.error('Error initializing Development Assistant integration:', error);
            });
    }, 1000);
}); 