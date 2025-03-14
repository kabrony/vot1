/**
 * VOT1 Dashboard Chat Module v2.4 (2025)
 * Handles chat functionality in the dashboard including:
 * - Sending and receiving messages
 * - Managing conversation history
 * - Handling visualization commands from chat responses
 * - Integrating with memory context
 * - Composio tool integration (2025 feature)
 */

// Chat state
const chatState = {
    conversationId: null,
    messageHistory: [],
    isProcessing: false,
    visualizationMode: 'auto', // auto, manual, disabled
    systemPrompt: null,
    selectedModel: 'gpt-4o-turbo', // Default to latest 2025 model
    memoryContextLevel: 'high', // none, low, medium, high
    composioEnabled: true       // Enable Composio integration
};

// DOM Elements
let chatPanel;
let chatMessages;
let chatInput;
let sendButton;
let clearButton;
let chatToggle;
let visualizationModeSelect;
let modelSelect;
let memoryContextSelect;
let composioToggle;
let expandedView;

// Initialize chat functionality
function initChat() {
    console.log('Initializing chat module v2.4...');
    
    // Get DOM elements
    chatPanel = document.getElementById('chat-panel');
    chatMessages = document.getElementById('chat-messages');
    chatInput = document.getElementById('chat-input');
    sendButton = document.getElementById('chat-send');
    clearButton = document.getElementById('chat-clear');
    chatToggle = document.getElementById('chat-toggle');
    visualizationModeSelect = document.getElementById('visualization-mode');
    modelSelect = document.getElementById('model-select');
    memoryContextSelect = document.getElementById('memory-context-level');
    composioToggle = document.getElementById('composio-toggle');
    expandedView = document.getElementById('expanded-view-toggle');
    
    // Initialize a new conversation
    chatState.conversationId = 'conv-' + generateUUID();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load any saved chat history from localStorage
    loadChatHistory();
    
    // Check for available models
    fetchAvailableModels();
    
    // Check Composio connection
    checkComposioConnection();
    
    console.log('Chat module initialized with conversation ID:', chatState.conversationId);
}

// Set up event listeners for chat functionality
function setupEventListeners() {
    // Send message on button click
    sendButton.addEventListener('click', () => {
        sendMessage();
    });
    
    // Send message on Enter key (but allow Shift+Enter for new lines)
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Clear chat history
    clearButton.addEventListener('click', () => {
        clearChat();
    });
    
    // Toggle chat panel visibility
    chatToggle.addEventListener('click', () => {
        toggleChatPanel();
    });
    
    // Change visualization mode
    visualizationModeSelect?.addEventListener('change', (e) => {
        chatState.visualizationMode = e.target.value;
        console.log('Visualization mode changed to:', chatState.visualizationMode);
        localStorage.setItem('vot1_chat_viz_mode', chatState.visualizationMode);
    });
    
    // Change AI model
    modelSelect?.addEventListener('change', (e) => {
        chatState.selectedModel = e.target.value;
        console.log('AI model changed to:', chatState.selectedModel);
        localStorage.setItem('vot1_chat_model', chatState.selectedModel);
    });
    
    // Change memory context level
    memoryContextSelect?.addEventListener('change', (e) => {
        chatState.memoryContextLevel = e.target.value;
        console.log('Memory context level changed to:', chatState.memoryContextLevel);
        localStorage.setItem('vot1_memory_context_level', chatState.memoryContextLevel);
    });
    
    // Toggle Composio integration
    composioToggle?.addEventListener('change', (e) => {
        chatState.composioEnabled = e.target.checked;
        console.log('Composio integration:', chatState.composioEnabled ? 'enabled' : 'disabled');
        localStorage.setItem('vot1_composio_enabled', chatState.composioEnabled ? 'true' : 'false');
    });
    
    // Toggle expanded view
    expandedView?.addEventListener('click', () => {
        toggleExpandedView();
    });
    
    // Load saved settings
    loadSavedSettings();
}

// Load saved user settings
function loadSavedSettings() {
    // Load visualization mode preference
    const savedVizMode = localStorage.getItem('vot1_chat_viz_mode');
    if (savedVizMode && visualizationModeSelect) {
        chatState.visualizationMode = savedVizMode;
        visualizationModeSelect.value = savedVizMode;
    }
    
    // Load model preference
    const savedModel = localStorage.getItem('vot1_chat_model');
    if (savedModel && modelSelect) {
        chatState.selectedModel = savedModel;
        modelSelect.value = savedModel;
    }
    
    // Load memory context level
    const savedMemoryLevel = localStorage.getItem('vot1_memory_context_level');
    if (savedMemoryLevel && memoryContextSelect) {
        chatState.memoryContextLevel = savedMemoryLevel;
        memoryContextSelect.value = savedMemoryLevel;
    }
    
    // Load Composio setting
    const composioEnabled = localStorage.getItem('vot1_composio_enabled');
    if (composioEnabled && composioToggle) {
        chatState.composioEnabled = composioEnabled === 'true';
        composioToggle.checked = chatState.composioEnabled;
    }
}

// Fetch available AI models from the server
async function fetchAvailableModels() {
    if (!modelSelect) return;
    
    try {
        const response = await fetch('/api/chat/available-models');
        if (response.ok) {
            const models = await response.json();
            
            // Clear existing options
            while (modelSelect.firstChild) {
                modelSelect.removeChild(modelSelect.firstChild);
            }
            
            // Add model options
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.name;
                modelSelect.appendChild(option);
            });
            
            // Set selected model
            modelSelect.value = chatState.selectedModel;
        }
    } catch (error) {
        console.error('Error fetching available models:', error);
    }
}

// Check Composio connection status
async function checkComposioConnection() {
    if (!composioToggle) return;
    
    try {
        const response = await fetch('/api/integrations/composio/status');
        if (response.ok) {
            const status = await response.json();
            
            if (status.connected) {
                composioToggle.disabled = false;
                document.getElementById('composio-status')?.classList.add('connected');
                document.getElementById('composio-status-text').textContent = 'Connected';
            } else {
                document.getElementById('composio-status-text').textContent = 'Disconnected';
                console.warn('Composio is not connected:', status.error);
            }
        }
    } catch (error) {
        console.error('Error checking Composio connection:', error);
    }
}

// Send a message to the API
async function sendMessage() {
    const message = chatInput.value.trim();
    
    // Don't send empty messages
    if (!message || chatState.isProcessing) {
        return;
    }
    
    // Update UI state
    chatState.isProcessing = true;
    sendButton.disabled = true;
    chatInput.disabled = true;
    
    // Add user message to UI
    addMessageToUI('user', message);
    
    // Clear input field
    chatInput.value = '';
    
    try {
        // Show typing indicator
        addTypingIndicator();
        
        // Prepare request data
        const requestData = {
            message: message,
            conversation_id: chatState.conversationId,
            include_memory_context: chatState.memoryContextLevel !== 'none',
            memory_context_level: chatState.memoryContextLevel,
            visualization_mode: chatState.visualizationMode,
            model: chatState.selectedModel,
            use_composio: chatState.composioEnabled
        };
        
        console.log('Sending chat message:', requestData);
        
        // Send to API
        const response = await fetch('/api/chat/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        // Remove typing indicator
        removeTypingIndicator();
        
        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Received chat response:', data);
        
        // Add assistant response to UI
        addMessageToUI('assistant', data.response, data.memory_references, data.tools_used);
        
        // Handle visualization update if present
        if (data.visualization_update && chatState.visualizationMode !== 'disabled') {
            handleVisualizationUpdate(data.visualization_update);
        }
        
        // Save to chat history
        saveChatHistory();
        
    } catch (error) {
        console.error('Error sending message:', error);
        removeTypingIndicator();
        
        // Add error message to UI
        addMessageToUI('system', 'An error occurred while processing your message. Please try again.');
    } finally {
        // Reset UI state
        chatState.isProcessing = false;
        sendButton.disabled = false;
        chatInput.disabled = false;
        chatInput.focus();
    }
}

// Add a message to the UI
function addMessageToUI(role, content, memoryReferences = [], toolsUsed = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}-message`;
    
    // Create message content
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Handle markdown formatting
    contentDiv.innerHTML = formatMessageContent(content);
    
    // Add role avatar/icon
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    
    if (role === 'user') {
        avatarDiv.innerHTML = '<i class="fas fa-user"></i>';
    } else if (role === 'assistant') {
        avatarDiv.innerHTML = '<i class="fas fa-robot"></i>';
    } else {
        avatarDiv.innerHTML = '<i class="fas fa-exclamation-circle"></i>';
    }
    
    // Add memory references if present
    if (memoryReferences && memoryReferences.length > 0) {
        const referencesDiv = document.createElement('div');
        referencesDiv.className = 'memory-references';
        referencesDiv.innerHTML = '<h4>Related Memories:</h4>';
        
        const referencesList = document.createElement('ul');
        memoryReferences.forEach(ref => {
            const item = document.createElement('li');
            item.innerHTML = `<span class="memory-id">${ref.id}</span>: ${ref.summary} <span class="relevance">(${Math.round(ref.relevance * 100)}% match)</span>`;
            item.addEventListener('click', () => {
                // Focus on this memory in the visualization
                handleVisualizationUpdate({
                    command: 'focus',
                    params: { id: ref.id }
                });
            });
            referencesList.appendChild(item);
        });
        
        referencesDiv.appendChild(referencesList);
        contentDiv.appendChild(referencesDiv);
    }
    
    // Add tools used if present (Composio integration, 2025 feature)
    if (toolsUsed && toolsUsed.length > 0) {
        const toolsDiv = document.createElement('div');
        toolsDiv.className = 'tools-used';
        toolsDiv.innerHTML = '<h4>External Tools Used:</h4>';
        
        const toolsList = document.createElement('ul');
        toolsUsed.forEach(tool => {
            const item = document.createElement('li');
            item.innerHTML = `<span class="tool-icon"><i class="fas fa-plug"></i></span> 
                              <span class="tool-name">${tool.name}</span>: 
                              <span class="tool-action">${tool.action}</span>`;
            toolsList.appendChild(item);
        });
        
        toolsDiv.appendChild(toolsList);
        contentDiv.appendChild(toolsDiv);
    }
    
    // Assemble the message
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    
    // Add timestamp
    const timestamp = document.createElement('div');
    timestamp.className = 'message-timestamp';
    timestamp.textContent = new Date().toLocaleTimeString();
    messageDiv.appendChild(timestamp);
    
    // Add to chat window
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Update chat state
    chatState.messageHistory.push({
        role: role,
        content: content,
        timestamp: new Date().toISOString(),
        memory_references: memoryReferences,
        tools_used: toolsUsed
    });
}

// Format message content (handle special formatting)
function formatMessageContent(content) {
    // Basic markdown-like formatting
    let formatted = content
        // Code blocks with language
        .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre class="code-block language-$1"><code>$2</code></pre>')
        // Inline code
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Bold
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        // Headers
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^# (.*$)/gm, '<h1>$1</h1>')
        // Lists
        .replace(/^\s*\- (.*$)/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>\n)+/g, '<ul>$&</ul>')
        // Links
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Replace newlines with <br> if not in a pre block
    formatted = formatted.replace(/\n(?!<\/(pre|ul|ol)>)/g, '<br>');
    
    return formatted;
}

// Add typing indicator while waiting for response
function addTypingIndicator() {
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'typing-indicator';
    indicatorDiv.id = 'typing-indicator';
    
    // Create dots
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('span');
        indicatorDiv.appendChild(dot);
    }
    
    chatMessages.appendChild(indicatorDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Remove typing indicator after response
function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Toggle chat panel visibility
function toggleChatPanel() {
    chatPanel.classList.toggle('chat-panel-hidden');
    
    // Update toggle button icon
    if (chatPanel.classList.contains('chat-panel-hidden')) {
        chatToggle.innerHTML = '<i class="fas fa-comment"></i>';
    } else {
        chatToggle.innerHTML = '<i class="fas fa-times"></i>';
        chatInput.focus();
    }
}

// Toggle expanded view (2025 feature)
function toggleExpandedView() {
    chatPanel.classList.toggle('chat-panel-expanded');
    
    // Update toggle button icon
    if (chatPanel.classList.contains('chat-panel-expanded')) {
        expandedView.innerHTML = '<i class="fas fa-compress-alt"></i>';
    } else {
        expandedView.innerHTML = '<i class="fas fa-expand-alt"></i>';
    }
}

// Clear chat history
function clearChat() {
    if (confirm('Are you sure you want to clear the chat history? This cannot be undone.')) {
        // Clear chat messages from UI
        while (chatMessages.firstChild) {
            chatMessages.removeChild(chatMessages.firstChild);
        }
        
        // Create a new conversation
        chatState.conversationId = 'conv-' + generateUUID();
        chatState.messageHistory = [];
        
        // Clear localStorage
        localStorage.removeItem('vot1_chat_history');
        
        // Add system message
        addMessageToUI('system', 'Chat history has been cleared. Starting a new conversation.');
        
        console.log('Chat cleared. New conversation ID:', chatState.conversationId);
    }
}

// Save chat history to localStorage
function saveChatHistory() {
    // Limit history to last 50 messages to avoid localStorage limits
    const historyToSave = {
        conversationId: chatState.conversationId,
        messages: chatState.messageHistory.slice(-50)
    };
    
    localStorage.setItem('vot1_chat_history', JSON.stringify(historyToSave));
}

// Load chat history from localStorage
function loadChatHistory() {
    const savedHistory = localStorage.getItem('vot1_chat_history');
    
    if (savedHistory) {
        try {
            const history = JSON.parse(savedHistory);
            
            // Restore conversation ID
            chatState.conversationId = history.conversationId;
            
            // Clear any existing messages
            while (chatMessages.firstChild) {
                chatMessages.removeChild(chatMessages.firstChild);
            }
            
            // Restore messages
            history.messages.forEach(msg => {
                addMessageToUI(
                    msg.role, 
                    msg.content, 
                    msg.memory_references || [], 
                    msg.tools_used || []
                );
            });
            
            console.log('Loaded chat history with conversation ID:', chatState.conversationId);
        } catch (error) {
            console.error('Error loading chat history:', error);
            localStorage.removeItem('vot1_chat_history');
        }
    }
}

// Handle visualization updates from chat
function handleVisualizationUpdate(updateCommand) {
    console.log('Handling visualization update:', updateCommand);
    
    // Only proceed if update is available and visualization mode isn't disabled
    if (!updateCommand || chatState.visualizationMode === 'disabled') return;
    
    // If visualization mode is manual, ask for confirmation
    if (chatState.visualizationMode === 'manual') {
        const confirmed = confirm(
            `Apply visualization update: ${updateCommand.command} ${JSON.stringify(updateCommand.params || {})}?`
        );
        
        if (!confirmed) return;
    }
    
    // Execute the command based on type
    try {
        const vizHandler = window.visualizationHandler;
        if (!vizHandler) {
            console.error('Visualization handler not found');
            return;
        }
        
        // Execute the command
        switch (updateCommand.command) {
            case 'focus':
                vizHandler.focusNode(updateCommand.params.id);
                break;
            case 'filter':
                vizHandler.filterNodes(updateCommand.params.criteria);
                break;
            case 'highlight':
                vizHandler.highlightNodes(updateCommand.params.ids || updateCommand.params.criteria);
                break;
            case 'search':
                vizHandler.searchAndHighlight(updateCommand.params.query);
                break;
            case 'layout':
                vizHandler.changeLayout(updateCommand.params.type);
                break;
            case 'reset':
                vizHandler.resetView();
                break;
            case 'custom':
                // Handle custom viz commands
                if (vizHandler.executeCustomCommand) {
                    vizHandler.executeCustomCommand(updateCommand.params);
                }
                break;
            default:
                console.warn('Unknown visualization command:', updateCommand.command);
        }
    } catch (error) {
        console.error('Error executing visualization command:', error);
    }
}

// Update system prompt for the current conversation
async function updateSystemPrompt(prompt) {
    if (!prompt || !chatState.conversationId) return;
    
    try {
        const response = await fetch('/api/chat/system-prompt', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                conversation_id: chatState.conversationId,
                prompt: prompt
            })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to update system prompt: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            chatState.systemPrompt = prompt;
            console.log('System prompt updated successfully');
            return true;
        } else {
            console.error('Failed to update system prompt:', result.error);
            return false;
        }
    } catch (error) {
        console.error('Error updating system prompt:', error);
        return false;
    }
}

// Search memories
async function searchMemories(query, limit = 5) {
    try {
        const response = await fetch(`/api/chat/memory-search?query=${encodeURIComponent(query)}&limit=${limit}`);
        
        if (!response.ok) {
            throw new Error(`Memory search failed: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error searching memories:', error);
        return { results: [] };
    }
}

// Generate a UUID for conversation IDs
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Initialize chat when document is ready
document.addEventListener('DOMContentLoaded', function() {
    initChat();
});

// Export functions for external use
window.vot1Chat = {
    sendMessage,
    clearChat,
    toggleChatPanel,
    updateSystemPrompt,
    searchMemories
}; 