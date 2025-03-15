/**
 * VOT1 Dashboard
 * Main JavaScript for the unified dashboard interface
 */

// Main Dashboard Controller
const Dashboard = {
  // State
  components: {},
  settings: {
    theme: 'cyberpunk',
    refreshInterval: 30,
    enableVisualization: true,
    enableMemory: true,
    enableMcp: true,
    enableAi: true
  },
  activePanel: 'dashboard-panel',
  socketConnected: false,
  socket: null,
  refreshTimer: null,

  // Initialize the dashboard
  init() {
    console.log('Initializing VOT1 Dashboard...');
    
    // Initialize socket connection
    this.initSocket();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Load settings from localStorage
    this.loadSettings();
    
    // Apply current theme
    this.applyTheme(this.settings.theme);
    
    // Fetch components
    this.fetchComponents();
    
    // Start auto-refresh
    this.startAutoRefresh();
    
    console.log('Dashboard initialized');
  },
  
  // Initialize socket connection
  initSocket() {
    try {
      // Get the host and port from the current URL
      const host = window.location.hostname;
      const port = window.location.port;
      
      // Connect to the socket server
      this.socket = io(`http://${host}:${port}`);
      
      // Set up socket event listeners
      this.socket.on('connect', () => {
        console.log('Socket connected');
        this.socketConnected = true;
        this.showToast('Connected to server', 'success');
      });
      
      this.socket.on('disconnect', () => {
        console.log('Socket disconnected');
        this.socketConnected = false;
        this.showToast('Disconnected from server', 'error');
      });
      
      this.socket.on('component_updated', (data) => {
        console.log('Component updated:', data);
        this.updateComponentBlock(data.component_id, data.data);
      });
      
      this.socket.on('chat_response', (data) => {
        console.log('Chat response:', data);
        AIAssistant.handleResponse(data);
      });
      
      this.socket.on('error', (data) => {
        console.error('Socket error:', data);
        this.showToast(`Error: ${data.error}`, 'error');
      });
    } catch (error) {
      console.error('Error initializing socket:', error);
      this.showToast('Could not connect to server', 'error');
    }
  },
  
  // Set up event listeners
  setupEventListeners() {
    // Navigation links
    document.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const panelId = link.getAttribute('data-panel');
        this.switchPanel(panelId);
      });
    });
    
    // Global refresh button
    document.getElementById('refresh-btn').addEventListener('click', () => {
      this.fetchComponents();
    });
    
    // Settings form
    document.getElementById('save-settings-btn').addEventListener('click', () => {
      this.saveSettings();
    });
    
    // Theme selector in settings
    document.getElementById('ui-theme').addEventListener('change', (e) => {
      this.applyTheme(e.target.value);
    });
    
    // Chat panel controls
    document.getElementById('collapse-chat-btn').addEventListener('click', () => {
      AIAssistant.collapseChat();
    });
    
    document.getElementById('expand-chat-btn').addEventListener('click', () => {
      AIAssistant.expandChat();
    });
    
    // Send message button
    document.getElementById('send-message-btn').addEventListener('click', () => {
      AIAssistant.sendMessage();
    });
    
    // Chat input enter key
    document.getElementById('chat-input').addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        AIAssistant.sendMessage();
      }
    });
    
    // Close modal
    document.querySelector('.close-btn').addEventListener('click', () => {
      this.closeModal();
    });
    
    // Click outside modal to close
    document.getElementById('component-modal').addEventListener('click', (e) => {
      if (e.target.id === 'component-modal') {
        this.closeModal();
      }
    });
    
    // Visualization refresh button
    document.getElementById('refresh-vis-btn').addEventListener('click', () => {
      if (Visualizer) {
        Visualizer.refreshVisualization();
      }
    });
    
    // Visualization controls
    document.getElementById('depth-selector').addEventListener('change', (e) => {
      if (Visualizer) {
        Visualizer.setDepth(e.target.value);
      }
    });
    
    document.getElementById('theme-selector').addEventListener('change', (e) => {
      if (Visualizer) {
        Visualizer.setTheme(e.target.value);
      }
    });
    
    // MCP node actions
    document.getElementById('start-node-btn').addEventListener('click', () => {
      this.startNode();
    });
    
    document.getElementById('stop-node-btn').addEventListener('click', () => {
      this.stopNode();
    });
    
    document.getElementById('sync-memory-btn').addEventListener('click', () => {
      this.syncMemory();
    });
  },
  
  // Load settings from localStorage
  loadSettings() {
    const savedSettings = localStorage.getItem('vot1_dashboard_settings');
    if (savedSettings) {
      try {
        const parsedSettings = JSON.parse(savedSettings);
        this.settings = { ...this.settings, ...parsedSettings };
        
        // Apply settings to form
        document.getElementById('ui-theme').value = this.settings.theme;
        document.getElementById('refresh-interval').value = this.settings.refreshInterval;
        document.getElementById('enable-visualization').checked = this.settings.enableVisualization;
        document.getElementById('enable-memory').checked = this.settings.enableMemory;
        document.getElementById('enable-mcp').checked = this.settings.enableMcp;
        document.getElementById('enable-ai').checked = this.settings.enableAi;
        
        console.log('Settings loaded:', this.settings);
      } catch (error) {
        console.error('Error parsing settings:', error);
      }
    }
  },
  
  // Save settings to localStorage
  saveSettings() {
    // Get form values
    const theme = document.getElementById('ui-theme').value;
    const refreshInterval = parseInt(document.getElementById('refresh-interval').value);
    const enableVisualization = document.getElementById('enable-visualization').checked;
    const enableMemory = document.getElementById('enable-memory').checked;
    const enableMcp = document.getElementById('enable-mcp').checked;
    const enableAi = document.getElementById('enable-ai').checked;
    
    // Update settings
    this.settings = {
      theme,
      refreshInterval,
      enableVisualization,
      enableMemory,
      enableMcp,
      enableAi
    };
    
    // Save to localStorage
    localStorage.setItem('vot1_dashboard_settings', JSON.stringify(this.settings));
    
    // Apply theme
    this.applyTheme(theme);
    
    // Restart auto-refresh
    this.startAutoRefresh();
    
    this.showToast('Settings saved', 'success');
    console.log('Settings saved:', this.settings);
  },
  
  // Apply theme to the dashboard
  applyTheme(theme) {
    document.body.className = `theme-${theme}`;
  },
  
  // Switch active panel
  switchPanel(panelId) {
    // Hide all panels
    document.querySelectorAll('.content-panel').forEach(panel => {
      panel.classList.remove('active');
    });
    
    // Show selected panel
    document.getElementById(panelId).classList.add('active');
    
    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.remove('active');
    });
    
    document.querySelector(`.nav-link[data-panel="${panelId}"]`).classList.add('active');
    
    // Update active panel
    this.activePanel = panelId;
    
    // Initialize panel-specific features
    if (panelId === 'visualization-panel' && Visualizer) {
      Visualizer.initVisualization();
    } else if (panelId === 'memory-panel' && MemoryGraph) {
      MemoryGraph.initGraph();
    }
  },
  
  // Start auto-refresh timer
  startAutoRefresh() {
    // Clear existing timer
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }
    
    // Set new timer
    this.refreshTimer = setInterval(() => {
      this.fetchComponents();
    }, this.settings.refreshInterval * 1000);
    
    console.log(`Auto-refresh started (${this.settings.refreshInterval}s)`);
  },
  
  // Fetch components from API
  fetchComponents() {
    fetch('/api/components')
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          this.components = data.components;
          this.renderDashboardGrid();
          console.log('Components fetched:', this.components);
        } else {
          console.error('Error fetching components:', data.error);
          this.showToast(`Error: ${data.error}`, 'error');
        }
      })
      .catch(error => {
        console.error('Error fetching components:', error);
        this.showToast('Could not fetch components', 'error');
      });
  },
  
  // Render dashboard grid with component blocks
  renderDashboardGrid() {
    const grid = document.getElementById('dashboard-grid');
    
    // Clear existing components
    grid.innerHTML = '';
    
    // Create component blocks
    for (const [id, component] of Object.entries(this.components)) {
      // Skip disabled components
      if (
        (component.type === 'visualization' && !this.settings.enableVisualization) ||
        (component.type === 'memory' && !this.settings.enableMemory) ||
        (component.type === 'mcp' && !this.settings.enableMcp) ||
        (component.type === 'ai_assistant' && !this.settings.enableAi)
      ) {
        continue;
      }
      
      const block = this.createComponentBlock(id, component);
      grid.appendChild(block);
    }
    
    // Show empty message if no components
    if (grid.children.length === 0) {
      const emptyMessage = document.createElement('div');
      emptyMessage.className = 'empty-message';
      emptyMessage.innerHTML = '<p>No components available</p>';
      grid.appendChild(emptyMessage);
    }
  },
  
  // Create a component block
  createComponentBlock(id, component) {
    // Clone template
    const template = document.getElementById('component-block-template');
    const block = document.importNode(template.content, true).querySelector('.component-block');
    
    // Set component ID
    block.setAttribute('data-component-id', id);
    block.classList.add(`status-${component.status}`);
    
    // Set title
    block.querySelector('.component-title').textContent = component.name;
    
    // Set content based on component type
    const body = block.querySelector('.component-body');
    
    switch (component.type) {
      case 'visualization':
        body.innerHTML = this.createVisualizationContent(component);
        break;
      case 'memory':
        body.innerHTML = this.createMemoryContent(component);
        break;
      case 'mcp':
        body.innerHTML = this.createMcpContent(component);
        break;
      case 'ai_assistant':
        body.innerHTML = this.createAiContent(component);
        break;
      default:
        body.innerHTML = `<p>Unknown component type: ${component.type}</p>`;
    }
    
    // Set footer info
    block.querySelector('.component-status').textContent = component.status;
    block.querySelector('.component-timestamp').textContent = this.formatTimestamp(component.last_updated);
    
    // Add event listeners
    block.querySelector('.refresh-component-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      this.refreshComponent(id);
    });
    
    block.querySelector('.expand-component-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      this.showComponentDetails(id);
    });
    
    // Make the whole block clickable to expand
    block.addEventListener('click', () => {
      this.showComponentDetails(id);
    });
    
    return block;
  },
  
  // Create visualization content
  createVisualizationContent(component) {
    const data = component.data;
    
    if (data.error) {
      return `<p class="error-message">${data.error}</p>`;
    }
    
    if (!data.structure) {
      return '<p>No visualization data available</p>';
    }
    
    return `
      <div class="component-preview">
        <div class="preview-info">
          <p><strong>Files:</strong> ${data.structure?.items?.length || 0}</p>
          <p><strong>Directories:</strong> ${this.countDirectories(data.structure)}</p>
        </div>
        <div class="preview-action">
          <button class="btn btn-primary view-visualization-btn">
            <i class="fa-solid fa-project-diagram"></i> View Visualization
          </button>
        </div>
      </div>
    `;
  },
  
  // Create memory content
  createMemoryContent(component) {
    const data = component.data;
    
    if (data.error) {
      return `<p class="error-message">${data.error}</p>`;
    }
    
    const stats = data.stats || { memory_count: 0, type_distribution: {} };
    const memoryCount = stats.memory_count || 0;
    const memoryTypes = Object.keys(stats.type_distribution || {}).length;
    
    let recentMemories = '';
    if (data.recent_memories && data.recent_memories.length > 0) {
      const memories = data.recent_memories.slice(0, 2);
      recentMemories = memories.map(memory => `
        <div class="preview-memory">
          <span class="memory-type">${memory.type}</span>
          <p>${this.truncateText(memory.content, 100)}</p>
        </div>
      `).join('');
    } else {
      recentMemories = '<p>No recent memories</p>';
    }
    
    return `
      <div class="component-preview">
        <div class="preview-info">
          <p><strong>Memories:</strong> ${memoryCount}</p>
          <p><strong>Types:</strong> ${memoryTypes}</p>
        </div>
        <div class="preview-memories">
          <h4>Recent</h4>
          ${recentMemories}
        </div>
      </div>
    `;
  },
  
  // Create MCP content
  createMcpContent(component) {
    const data = component.data;
    
    if (data.error) {
      return `<p class="error-message">${data.error}</p>`;
    }
    
    const nodes = data.nodes || [];
    let nodesList = '';
    
    if (nodes.length > 0) {
      nodesList = nodes.slice(0, 2).map(node => `
        <div class="preview-node">
          <span class="node-id">${node.id}</span>
          <span class="node-status ${node.status}">${node.status}</span>
        </div>
      `).join('');
    } else {
      nodesList = '<p>No active nodes</p>';
    }
    
    return `
      <div class="component-preview">
        <div class="preview-info">
          <p><strong>Nodes:</strong> ${nodes.length}</p>
          <p><strong>Active:</strong> ${nodes.filter(n => n.status === 'active').length}</p>
        </div>
        <div class="preview-nodes">
          ${nodesList}
        </div>
      </div>
    `;
  },
  
  // Create AI assistant content
  createAiContent(component) {
    const data = component.data;
    
    if (data.error) {
      return `<p class="error-message">${data.error}</p>`;
    }
    
    const chatHistory = data.chat_history || [];
    const messageCount = chatHistory.length;
    
    let lastMessage = '';
    if (messageCount > 0) {
      const lastUserMessage = [...chatHistory].reverse().find(msg => msg.role === 'user');
      const lastAssistantMessage = [...chatHistory].reverse().find(msg => msg.role === 'assistant');
      
      lastMessage = `
        <div class="preview-message">
          ${lastUserMessage ? `<p><strong>You:</strong> ${this.truncateText(lastUserMessage.content, 50)}</p>` : ''}
          ${lastAssistantMessage ? `<p><strong>AI:</strong> ${this.truncateText(lastAssistantMessage.content, 50)}</p>` : ''}
        </div>
      `;
    } else {
      lastMessage = '<p>No messages yet</p>';
    }
    
    return `
      <div class="component-preview">
        <div class="preview-info">
          <p><strong>Messages:</strong> ${messageCount}</p>
        </div>
        <div class="preview-chat">
          ${lastMessage}
        </div>
        <div class="preview-action">
          <button class="btn btn-primary open-chat-btn">
            <i class="fa-solid fa-comments"></i> Open Chat
          </button>
        </div>
      </div>
    `;
  },
  
  // Update a component block with new data
  updateComponentBlock(componentId, data) {
    // Update component data
    if (this.components[componentId]) {
      this.components[componentId].data = data;
      this.components[componentId].last_updated = new Date().toISOString();
      
      // Find the component block
      const block = document.querySelector(`.component-block[data-component-id="${componentId}"]`);
      if (block) {
        // Update content based on component type
        const body = block.querySelector('.component-body');
        const component = this.components[componentId];
        
        switch (component.type) {
          case 'visualization':
            body.innerHTML = this.createVisualizationContent(component);
            break;
          case 'memory':
            body.innerHTML = this.createMemoryContent(component);
            break;
          case 'mcp':
            body.innerHTML = this.createMcpContent(component);
            break;
          case 'ai_assistant':
            body.innerHTML = this.createAiContent(component);
            break;
        }
        
        // Update timestamp
        block.querySelector('.component-timestamp').textContent = this.formatTimestamp(component.last_updated);
        
        // Re-attach event listeners
        const openChatBtn = block.querySelector('.open-chat-btn');
        if (openChatBtn) {
          openChatBtn.addEventListener('click', () => {
            AIAssistant.openChat();
          });
        }
        
        const viewVisualizationBtn = block.querySelector('.view-visualization-btn');
        if (viewVisualizationBtn) {
          viewVisualizationBtn.addEventListener('click', () => {
            this.switchPanel('visualization-panel');
            if (Visualizer) {
              Visualizer.initVisualization();
            }
          });
        }
      }
    }
  },
  
  // Refresh a component
  refreshComponent(componentId) {
    if (this.socketConnected) {
      this.socket.emit('update_component', { component_id: componentId });
      this.showToast(`Refreshing ${this.components[componentId].name}...`, 'info');
    } else {
      this.showToast('Not connected to server', 'error');
    }
  },
  
  // Show component details in modal
  showComponentDetails(componentId) {
    const component = this.components[componentId];
    if (!component) return;
    
    // Set modal title
    document.getElementById('modal-title').textContent = component.name;
    
    // Set modal content
    const modalBody = document.getElementById('modal-body');
    
    // Format data as JSON
    const jsonString = JSON.stringify(component, null, 2);
    
    modalBody.innerHTML = `
      <div class="component-details">
        <div class="details-section">
          <h4>Component Details</h4>
          <p><strong>ID:</strong> ${component.id}</p>
          <p><strong>Type:</strong> ${component.type}</p>
          <p><strong>Status:</strong> ${component.status}</p>
          <p><strong>Last Updated:</strong> ${this.formatTimestamp(component.last_updated)}</p>
        </div>
        
        <div class="details-section">
          <h4>Configuration</h4>
          <pre>${JSON.stringify(component.config, null, 2)}</pre>
        </div>
        
        <div class="details-section">
          <h4>Data</h4>
          <pre>${JSON.stringify(component.data, null, 2)}</pre>
        </div>
      </div>
    `;
    
    // Show modal
    document.getElementById('component-modal').classList.add('active');
  },
  
  // Close modal
  closeModal() {
    document.getElementById('component-modal').classList.remove('active');
  },
  
  // Show toast notification
  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'fa-info-circle';
    if (type === 'success') icon = 'fa-check-circle';
    if (type === 'error') icon = 'fa-exclamation-circle';
    if (type === 'warning') icon = 'fa-exclamation-triangle';
    
    toast.innerHTML = `
      <div class="toast-icon">
        <i class="fa-solid ${icon}"></i>
      </div>
      <div class="toast-content">
        <p>${message}</p>
      </div>
    `;
    
    document.getElementById('toast-container').appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => {
        toast.remove();
      }, 300);
    }, 3000);
  },
  
  // MCP actions
  startNode() {
    // Find selected node or create a new one
    const nodeName = prompt('Enter node name:', `node_${Date.now()}`);
    if (!nodeName) return;
    
    if (this.socketConnected) {
      this.socket.emit('mcp_action', { action: 'start_node', node_id: nodeName });
      this.showToast(`Starting node ${nodeName}...`, 'info');
    } else {
      this.showToast('Not connected to server', 'error');
    }
  },
  
  stopNode() {
    // Get selected node from UI
    const nodesList = document.getElementById('mcp-nodes-list');
    const selectedNode = nodesList.querySelector('.node-item.selected');
    
    if (!selectedNode) {
      this.showToast('No node selected', 'warning');
      return;
    }
    
    const nodeId = selectedNode.getAttribute('data-node-id');
    
    if (this.socketConnected) {
      this.socket.emit('mcp_action', { action: 'stop_node', node_id: nodeId });
      this.showToast(`Stopping node ${nodeId}...`, 'info');
    } else {
      this.showToast('Not connected to server', 'error');
    }
  },
  
  syncMemory() {
    if (this.socketConnected) {
      this.socket.emit('mcp_action', { action: 'sync_memory' });
      this.showToast('Syncing memory across nodes...', 'info');
    } else {
      this.showToast('Not connected to server', 'error');
    }
  },
  
  // Helper methods
  countDirectories(structure) {
    let count = 0;
    
    const countRecursive = (item) => {
      if (item.type === 'directory') {
        count++;
        if (item.children) {
          item.children.forEach(countRecursive);
        }
      }
    };
    
    if (structure && structure.items) {
      structure.items.forEach(countRecursive);
    }
    
    return count;
  },
  
  truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  },
  
  formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now - date;
      const diffSec = Math.floor(diffMs / 1000);
      
      if (diffSec < 60) return `${diffSec}s ago`;
      if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
      if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
      
      return date.toLocaleString();
    } catch (error) {
      return timestamp;
    }
  }
};

// AI Assistant Controller
const AIAssistant = {
  // State
  chatHistory: [],
  isExpanded: false,
  isThinking: false,
  
  // Initialize
  init() {
    console.log('Initializing AI Assistant...');
  },
  
  // Open chat panel
  openChat() {
    const chatPanel = document.getElementById('chat-panel');
    chatPanel.classList.remove('collapsed');
    this.isExpanded = true;
  },
  
  // Collapse chat panel
  collapseChat() {
    const chatPanel = document.getElementById('chat-panel');
    chatPanel.classList.remove('expanded');
    chatPanel.classList.add('collapsed');
    this.isExpanded = false;
  },
  
  // Expand chat panel
  expandChat() {
    const chatPanel = document.getElementById('chat-panel');
    chatPanel.classList.remove('collapsed');
    chatPanel.classList.add('expanded');
    this.isExpanded = true;
  },
  
  // Send message
  sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Clear input
    input.value = '';
    
    // Add message to chat
    this.addMessage('user', message);
    
    // Add loading indicator
    this.setThinking(true);
    
    // Send to server
    if (Dashboard.socketConnected) {
      Dashboard.socket.emit('chat_message', {
        message,
        context: {
          activePanel: Dashboard.activePanel
        }
      });
    } else {
      setTimeout(() => {
        this.handleResponse({
          response: 'Sorry, I am not connected to the server right now. Please try again later.',
          thinking: null,
          timestamp: new Date().toISOString()
        });
      }, 1000);
    }
  },
  
  // Handle response from server
  handleResponse(data) {
    // Remove loading indicator
    this.setThinking(false);
    
    // Add response to chat
    this.addMessage('assistant', data.response);
    
    // Add thinking process if available
    if (data.thinking) {
      this.showThinking(data.thinking);
    }
  },
  
  // Add message to chat
  addMessage(role, content) {
    // Create message element
    const message = document.createElement('div');
    message.className = `message ${role}`;
    
    message.innerHTML = `
      <div class="message-content">
        <p>${this.formatMessage(content)}</p>
      </div>
    `;
    
    // Add to chat
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.appendChild(message);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Add to history
    this.chatHistory.push({
      role,
      content,
      timestamp: new Date().toISOString()
    });
  },
  
  // Set thinking state
  setThinking(isThinking) {
    this.isThinking = isThinking;
    
    if (isThinking) {
      // Add loading message
      const message = document.createElement('div');
      message.className = 'message assistant thinking';
      message.innerHTML = `
        <div class="message-content">
          <p><i class="fa-solid fa-spinner fa-spin"></i> Thinking...</p>
        </div>
      `;
      
      // Add to chat
      const messagesContainer = document.getElementById('chat-messages');
      messagesContainer.appendChild(message);
      
      // Scroll to bottom
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } else {
      // Remove loading message
      const thinkingMessage = document.querySelector('.message.thinking');
      if (thinkingMessage) {
        thinkingMessage.remove();
      }
    }
  },
  
  // Show thinking process
  showThinking(thinking) {
    if (!thinking) return;
    
    // Show thinking section
    const thinkingSection = document.querySelector('.chat-thinking');
    thinkingSection.classList.remove('hidden');
    
    // Set thinking content
    document.getElementById('thinking-content').textContent = thinking;
  },
  
  // Format message with Markdown-like syntax
  formatMessage(text) {
    if (!text) return '';
    
    // Replace URLs with links
    text = text.replace(
      /(https?:\/\/[^\s]+)/g,
      '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
    );
    
    // Replace *text* with <strong>text</strong>
    text = text.replace(/\*([^*]+)\*/g, '<strong>$1</strong>');
    
    // Replace _text_ with <em>text</em>
    text = text.replace(/_([^_]+)_/g, '<em>$1</em>');
    
    // Replace `code` with <code>code</code>
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Replace new lines with <br>
    text = text.replace(/\n/g, '<br>');
    
    return text;
  }
};

// Register initialization on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  Dashboard.init();
  AIAssistant.init();
}); 