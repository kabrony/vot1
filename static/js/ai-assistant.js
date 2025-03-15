/**
 * VOT1 AI Assistant
 * Chat interface with hybrid thinking visualization
 */

const AIAssistant = {
  // State
  messages: [],
  thinking: null,
  isThinking: false,
  isExpanded: false,
  socket: null,
  typingTimeout: null,
  typingSpeed: 20, // ms per character
  initialized: false,
  
  // Config
  config: {
    maxMessages: 50,
    defaultSystemMessage: {
      role: 'system',
      content: 'Hello! I\'m your AI assistant. How can I help you today?'
    },
    modelInfo: {
      name: 'Claude 3.7 Sonnet',
      version: '20250219',
      capabilities: [
        'Hybrid Reasoning Mode',
        'Memory Integration',
        'Code Generation',
        'Data Analysis'
      ]
    }
  },
  
  // Initialize AI assistant
  init(socket) {
    console.log('Initializing AI assistant...');
    
    // Set socket
    this.socket = socket;
    
    // Get container
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-message-btn');
    
    if (!chatMessages || !chatInput || !sendButton) {
      console.error('Chat elements not found');
      return false;
    }
    
    // Initialize only once
    if (!this.initialized) {
      // Add initial message
      if (this.messages.length === 0) {
        this.addMessage('system', this.config.defaultSystemMessage.content);
      }
      
      // Set up event handlers
      this.setupEventHandlers();
      
      this.initialized = true;
    }
    
    return true;
  },
  
  // Set up event handlers
  setupEventHandlers() {
    // Chat open/close controls
    document.getElementById('collapse-chat-btn')?.addEventListener('click', () => {
      this.collapseChat();
    });
    
    document.getElementById('expand-chat-btn')?.addEventListener('click', () => {
      this.expandChat();
    });
    
    // Send button
    document.getElementById('send-message-btn')?.addEventListener('click', () => {
      this.sendMessage();
    });
    
    // Enter key in textarea
    document.getElementById('chat-input')?.addEventListener('keydown', (event) => {
      // Check if Enter was pressed without Shift
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        this.sendMessage();
      }
    });
    
    // Register socket events if socket is available
    if (this.socket) {
      this.socket.on('chat_response', (data) => {
        this.handleResponse(data);
      });
      
      this.socket.on('thinking_update', (data) => {
        this.updateThinking(data);
      });
    }
  },
  
  // Open chat panel
  openChat() {
    document.getElementById('chat-panel').classList.remove('collapsed');
    
    // Focus input
    setTimeout(() => {
      document.getElementById('chat-input')?.focus();
    }, 300);
  },
  
  // Collapse chat panel
  collapseChat() {
    const chatPanel = document.getElementById('chat-panel');
    chatPanel.classList.remove('expanded');
    chatPanel.classList.add('collapsed');
    
    // Hide thinking panel
    document.querySelector('.chat-thinking')?.classList.add('hidden');
  },
  
  // Expand chat panel
  expandChat() {
    const chatPanel = document.getElementById('chat-panel');
    chatPanel.classList.remove('collapsed');
    chatPanel.classList.add('expanded');
    
    // Show thinking panel if there's thinking content
    if (this.thinking) {
      document.querySelector('.chat-thinking')?.classList.remove('hidden');
    }
    
    // Focus input
    setTimeout(() => {
      document.getElementById('chat-input')?.focus();
    }, 300);
  },
  
  // Send message
  sendMessage() {
    // Get input
    const chatInput = document.getElementById('chat-input');
    if (!chatInput) return;
    
    // Get message
    const message = chatInput.value.trim();
    
    // Skip if empty
    if (!message) return;
    
    // Add message to UI
    this.addMessage('user', message);
    
    // Clear input
    chatInput.value = '';
    
    // Set thinking state
    this.setThinking(true);
    
    // Add temporary response message
    const tempResponseId = 'temp-response-' + Date.now();
    const tempMessageElement = this.createMessageElement('assistant', '<div class="typing-indicator"><span></span><span></span><span></span></div>');
    tempMessageElement.id = tempResponseId;
    document.getElementById('chat-messages').appendChild(tempMessageElement);
    
    // Scroll to bottom
    this.scrollToBottom();
    
    // If socket is available, send message to server
    if (this.socket) {
      this.socket.emit('chat_message', {
        message,
        context: {
          panel: Dashboard.activePanel,
          hybridThinking: true,
          maxThinkingTokens: 8000
        }
      });
    } else {
      // Simulate response for demo
      setTimeout(() => {
        // Generate demo thinking
        this.thinking = `Analyzing request: "${message}"...\n\nStep 1: Understand the user query\n- User is asking about ${message.includes('?') ? 'a question' : 'a task'}\n- This appears to be related to ${this.guessIntent(message)}\n\nStep 2: Consider relevant context\n- Current panel: ${Dashboard.activePanel}\n- Available tools: file visualization, MCP, memory system\n\nStep 3: Generate appropriate response\n- Provide helpful information\n- Include relevant actions if needed`;
        
        this.updateThinking({ thinking: this.thinking });
        
        // Generate demo response
        const responseTime = Math.min(1000 + message.length * 10, 3000);
        setTimeout(() => {
          const demoResponse = this.generateDemoResponse(message);
          
          // Remove temporary message
          document.getElementById(tempResponseId)?.remove();
          
          // Add actual response
          this.addMessage('assistant', demoResponse);
          this.setThinking(false);
        }, responseTime);
      }, 800);
    }
  },
  
  // Handle response from server
  handleResponse(data) {
    // Remove any temporary response messages
    const tempMessages = document.querySelectorAll('.message.assistant .typing-indicator');
    tempMessages.forEach(elem => {
      const messageElem = elem.closest('.message');
      if (messageElem) {
        messageElem.remove();
      }
    });
    
    // Add message
    if (data.message) {
      this.addMessage('assistant', data.message);
    }
    
    // Update thinking
    if (data.thinking) {
      this.updateThinking({ thinking: data.thinking });
    }
    
    // Set thinking state
    this.setThinking(false);
  },
  
  // Add message to chat
  addMessage(role, content) {
    // Skip if empty
    if (!content) return;
    
    // Create message element
    const messageElement = this.createMessageElement(role, content);
    
    // Add to messages container
    const messagesContainer = document.getElementById('chat-messages');
    if (messagesContainer) {
      messagesContainer.appendChild(messageElement);
      
      // Limit the number of messages
      while (messagesContainer.children.length > this.config.maxMessages) {
        messagesContainer.removeChild(messagesContainer.firstChild);
      }
      
      // Scroll to bottom
      this.scrollToBottom();
    }
    
    // Store in messages array
    this.messages.push({ role, content });
  },
  
  // Create message element
  createMessageElement(role, content) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${role}`;
    
    const contentElement = document.createElement('div');
    contentElement.className = 'message-content';
    
    // Format content (convert markdown, etc.)
    if (role === 'assistant' && typeof content === 'string' && !content.includes('<div class="typing-indicator">')) {
      // For actual content, not the typing indicator
      contentElement.innerHTML = this.formatMessage(content);
    } else {
      contentElement.innerHTML = content;
    }
    
    messageElement.appendChild(contentElement);
    return messageElement;
  },
  
  // Set thinking state
  setThinking(isThinking) {
    this.isThinking = isThinking;
    
    // Update UI
    const chatPanel = document.getElementById('chat-panel');
    const thinkingPanel = document.querySelector('.chat-thinking');
    
    if (isThinking) {
      chatPanel?.classList.add('thinking');
      
      // Only show thinking panel if expanded and there's thinking content
      if (chatPanel?.classList.contains('expanded') && this.thinking) {
        thinkingPanel?.classList.remove('hidden');
      }
    } else {
      chatPanel?.classList.remove('thinking');
      
      // Hide thinking panel after a delay if not expanded
      if (!chatPanel?.classList.contains('expanded')) {
        thinkingPanel?.classList.add('hidden');
      }
    }
  },
  
  // Update thinking content
  updateThinking(data) {
    if (!data.thinking) return;
    
    this.thinking = data.thinking;
    
    // Update thinking content
    const thinkingContent = document.getElementById('thinking-content');
    if (thinkingContent) {
      thinkingContent.innerHTML = this.formatThinking(this.thinking);
    }
    
    // Show thinking panel if expanded
    if (document.getElementById('chat-panel')?.classList.contains('expanded')) {
      document.querySelector('.chat-thinking')?.classList.remove('hidden');
    }
  },
  
  // Format message (convert markdown to HTML)
  formatMessage(text) {
    if (!text) return '';
    
    // Replace URLs with links
    text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
    
    // Convert markdown-style code blocks to HTML
    text = text.replace(/```(\w*)([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>');
    
    // Convert markdown-style inline code to HTML
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Convert markdown-style bold to HTML
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Convert markdown-style italic to HTML
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Convert line breaks to <br>
    text = text.replace(/\n/g, '<br>');
    
    return text;
  },
  
  // Format thinking content
  formatThinking(text) {
    if (!text) return '';
    
    // Add syntax highlighting for thinking steps
    text = text.replace(/Step \d+:/g, '<strong class="thinking-step">$&</strong>');
    
    // Highlight thinking patterns
    text = text.replace(/Reasoning:/g, '<strong class="thinking-reasoning">$&</strong>');
    text = text.replace(/Analysis:/g, '<strong class="thinking-analysis">$&</strong>');
    text = text.replace(/Conclusion:/g, '<strong class="thinking-conclusion">$&</strong>');
    
    // Convert line breaks to <br>
    text = text.replace(/\n/g, '<br>');
    
    return text;
  },
  
  // Scroll chat to bottom
  scrollToBottom() {
    const messagesContainer = document.getElementById('chat-messages');
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  },
  
  // Demo functions for standalone testing
  
  // Guess intent for demo
  guessIntent(message) {
    message = message.toLowerCase();
    
    if (message.includes('file') || message.includes('structure') || message.includes('visual')) {
      return 'file visualization';
    } else if (message.includes('mcp') || message.includes('component') || message.includes('module')) {
      return 'MCP components';
    } else if (message.includes('memory') || message.includes('brain') || message.includes('remember')) {
      return 'memory system';
    } else if (message.includes('code') || message.includes('program') || message.includes('develop')) {
      return 'code development';
    } else {
      return 'general assistance';
    }
  },
  
  // Generate demo response for standalone testing
  generateDemoResponse(message) {
    message = message.toLowerCase();
    
    if (message.includes('hello') || message.includes('hi ') || message.includes('hey')) {
      return 'Hello! I\'m your AI assistant powered by Claude 3.7 Sonnet. How can I help you with the VOT1 system today?';
    } else if (message.includes('help')) {
      return 'I can help you with various aspects of the VOT1 system:\n\n- File structure visualization\n- MCP (Modular Component Platform) management\n- Memory system integration\n- Code development and suggestions\n\nJust let me know what you\'d like assistance with!';
    } else if (message.includes('file') || message.includes('structure') || message.includes('visual')) {
      return 'The file structure visualization uses THREE.js to create an interactive 3D visualization of your project. You can:\n\n- Change the depth of visualization in the settings\n- Click on nodes to see details\n- Use the mouse to rotate and zoom the view\n\nWould you like me to help you with a specific aspect of the visualization?';
    } else if (message.includes('mcp') || message.includes('component') || message.includes('module')) {
      return 'The MCP (Modular Component Platform) allows you to manage modular components and tools. Currently, there are integrations for GitHub, Perplexity AI, Figma, and Firecrawl. You can start/stop nodes and connect to various tools through the MCP panel.';
    } else if (message.includes('memory') || message.includes('brain') || message.includes('trilogy')) {
      return 'The TRILOGY BRAIN memory system is an advanced neural-symbolic memory architecture that allows for storing and retrieving various types of memories including facts, concepts, code snippets, conversations, and reflections. The memory graph visualization shows the relationships between different memory nodes.';
    } else if (message.includes('code') || message.includes('program') || message.includes('develop')) {
      return 'I can help with code development by generating suggestions, explaining code, or helping you implement new features. For the VOT1 project, the main components include:\n\n- Dashboard interface\n- THREE.js visualization\n- MCP integration\n- Memory system\n\nWhat specific coding task would you like help with?';
    } else {
      return 'I understand you\'re asking about ' + this.guessIntent(message) + '. Could you provide more specific details about what you\'d like to know or do? I\'m here to help with any aspect of the VOT1 system.';
    }
  }
};

// Register initialization on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  // Initialize AI assistant
  AIAssistant.init(Dashboard.socket);
}); 