/**
 * VOT1 MCP Integration
 * Manages Modular Component Platform nodes and tools
 */

const MCP = {
  // State
  nodes: [],
  activeNode: null,
  tools: {},
  initialized: false,
  nodeStatus: {},
  requestQueue: [],
  socket: null,
  connectionInProgress: false,
  
  // Config
  config: {
    autoRefresh: true,
    refreshInterval: 5000, // 5 seconds
    maxRequestAttempts: 3,
    defaultAvatars: {
      github: 'fab fa-github',
      perplexity: 'fas fa-brain',
      figma: 'fab fa-figma',
      firecrawl: 'fas fa-spider',
      default: 'fas fa-cube'
    },
    toolDescriptions: {
      github: 'GitHub integration for repository access and management',
      perplexity: 'Enhanced search with AI-powered reasoning',
      figma: 'Design file access and collaboration',
      firecrawl: 'Web crawling and data extraction'
    }
  },
  
  // Initialize MCP component
  async init(socket) {
    console.log('Initializing MCP component...');
    
    // Set socket
    this.socket = socket;
    
    // Get container
    const container = document.getElementById('mcp-nodes-list');
    if (!container) {
      console.error('MCP container not found');
      return false;
    }
    
    // Display loading state
    container.innerHTML = '<div class="loading-indicator"><div class="loading-spinner"></div><p>Loading MCP nodes...</p></div>';
    
    // Initialize only once
    if (!this.initialized) {
      // Set up event handlers
      this.setupEventHandlers();
      
      this.initialized = true;
    }
    
    try {
      // Fetch nodes
      await this.fetchNodes();
      
      // Fetch tools
      await this.fetchTools();
      
      // Start auto-refresh if enabled
      this.startAutoRefresh();
      
      return true;
    } catch (error) {
      console.error('Error initializing MCP:', error);
      container.innerHTML = '<div class="error-message"><i class="fas fa-exclamation-triangle"></i> Failed to load MCP data</div>';
      Dashboard.showToast('Failed to initialize MCP component', 'error');
      return false;
    }
  },
  
  // Set up event handlers
  setupEventHandlers() {
    // Node operations
    document.addEventListener('click', (event) => {
      const startBtn = event.target.closest('.start-node-btn');
      const stopBtn = event.target.closest('.stop-node-btn');
      const detailsNodeBtn = event.target.closest('.node-details-btn');
      
      if (startBtn) {
        const nodeId = startBtn.dataset.nodeid;
        if (nodeId) {
          this.startNode(nodeId);
        }
      } else if (stopBtn) {
        const nodeId = stopBtn.dataset.nodeid;
        if (nodeId) {
          this.stopNode(nodeId);
        }
      } else if (detailsNodeBtn) {
        const nodeId = detailsNodeBtn.dataset.nodeid;
        if (nodeId) {
          const node = this.nodes.find(n => n.id === nodeId);
          if (node) {
            this.showNodeDetails(node);
          }
        }
      }
    });
    
    // Tool operations
    document.addEventListener('click', (event) => {
      const connectBtn = event.target.closest('.connect-tool-btn');
      const actionBtn = event.target.closest('.tool-action-btn');
      const detailsToolBtn = event.target.closest('.tool-details-btn');
      
      if (connectBtn) {
        const toolName = connectBtn.dataset.tool;
        if (toolName) {
          this.connectTool(toolName);
        }
      } else if (actionBtn) {
        const toolName = actionBtn.dataset.tool;
        const action = actionBtn.dataset.action;
        if (toolName && action) {
          this.executeToolAction(toolName, action);
        }
      } else if (detailsToolBtn) {
        const toolName = detailsToolBtn.dataset.tool;
        if (toolName) {
          this.showToolDetails(toolName, this.tools[toolName]);
        }
      }
    });
    
    // Global MCP buttons
    document.getElementById('sync-memory-btn')?.addEventListener('click', () => {
      this.syncMemory();
    });
    
    // Register socket events if socket is available
    if (this.socket) {
      this.socket.on('mcp_node_status', (data) => {
        this.updateNodeStatus(data.node_id, data.status);
      });
      
      this.socket.on('mcp_tool_status', (data) => {
        this.updateToolStatus(data.tool, data.status);
      });
      
      this.socket.on('mcp_logs', (data) => {
        this.updateNodeLogs(data.node_id, data.logs);
      });
    }
  },
  
  // Fetch nodes from API
  async fetchNodes() {
    try {
      const response = await fetch('/api/mcp/nodes');
      const data = await response.json();
      
      if (data.status === 'success') {
        this.nodes = data.nodes || [];
        this.renderNodes();
        return this.nodes;
      } else {
        console.error('Error fetching MCP nodes:', data.error);
        Dashboard.showToast(`Error fetching MCP nodes: ${data.error}`, 'error');
        throw new Error(data.error);
      }
    } catch (error) {
      console.error('Error fetching MCP nodes:', error);
      Dashboard.showToast('Could not fetch MCP nodes', 'error');
      throw error;
    }
  },
  
  // Fetch tools from API
  async fetchTools() {
    try {
      const response = await fetch('/api/mcp/tools');
      const data = await response.json();
      
      if (data.status === 'success') {
        this.tools = data.tools || {};
        
        // Add default tools if not present in response
        const defaultTools = ['github', 'perplexity', 'figma', 'firecrawl'];
        defaultTools.forEach(tool => {
          if (!this.tools[tool]) {
            this.tools[tool] = {
              display_name: tool.charAt(0).toUpperCase() + tool.slice(1),
              description: this.config.toolDescriptions[tool] || `${tool} integration`,
              connected: false,
              actions: []
            };
          }
        });
        
        this.renderTools();
        return this.tools;
      } else {
        console.error('Error fetching MCP tools:', data.error);
        Dashboard.showToast(`Error fetching MCP tools: ${data.error}`, 'error');
        throw new Error(data.error);
      }
    } catch (error) {
      console.error('Error fetching MCP tools:', error);
      Dashboard.showToast('Could not fetch MCP tools', 'error');
      throw error;
    }
  },
  
  // Check if a tool is connected
  async checkToolConnection(toolName) {
    try {
      const response = await fetch(`/api/mcp/tool/${toolName}/connection`);
      const data = await response.json();
      
      if (data.status === 'success') {
        this.updateToolStatus(toolName, { connected: data.connected });
        return data.connected;
      }
      return false;
    } catch (error) {
      console.error(`Error checking ${toolName} connection:`, error);
      return false;
    }
  },
  
  // Render nodes in container
  renderNodes() {
    const container = document.getElementById('mcp-nodes-list');
    if (!container) return;
    
    // Clear container
    container.innerHTML = '';
    
    if (this.nodes.length === 0) {
      container.innerHTML = '<p>No MCP nodes available</p>';
      return;
    }
    
    // Create nodes list
    const nodesList = document.createElement('div');
    nodesList.className = 'nodes-list';
    container.appendChild(nodesList);
    
    // Add nodes to list
    this.nodes.forEach(node => {
      const nodeElement = this.createNodeElement(node);
      nodesList.appendChild(nodeElement);
    });
  },
  
  // Create node element
  createNodeElement(node) {
    const nodeElement = document.createElement('div');
    nodeElement.className = 'node-item';
    nodeElement.dataset.nodeid = node.id;
    
    // Get node status
    const status = this.nodeStatus[node.id] || 'offline';
    
    // Create node item content
    nodeElement.innerHTML = `
      <div class="node-info">
        <span class="node-id">${node.name}</span>
        <span class="node-status ${status}">${status}</span>
      </div>
      <div class="node-actions">
        ${status === 'online' 
          ? `<button class="btn btn-sm btn-danger stop-node-btn" data-nodeid="${node.id}">
               <i class="fas fa-stop"></i>
             </button>`
          : `<button class="btn btn-sm btn-success start-node-btn" data-nodeid="${node.id}">
               <i class="fas fa-play"></i>
             </button>`
        }
        <button class="btn btn-sm btn-primary node-details-btn" data-nodeid="${node.id}">
          <i class="fas fa-info-circle"></i>
        </button>
      </div>
    `;
    
    return nodeElement;
  },
  
  // Render tools in container
  renderTools() {
    const container = document.getElementById('mcp-tools-container');
    if (!container) {
      // Create tools container if it doesn't exist
      const mpcPanel = document.getElementById('mcp-panel');
      if (!mpcPanel) return;
      
      const toolsContainer = document.createElement('div');
      toolsContainer.id = 'mcp-tools-container';
      toolsContainer.className = 'mcp-tools';
      toolsContainer.innerHTML = '<h3>Available Tools</h3>';
      
      mpcPanel.querySelector('.panel-content').appendChild(toolsContainer);
    }
    
    const toolsContainer = document.getElementById('mcp-tools-container');
    
    // Clear existing content
    toolsContainer.innerHTML = '<h3>Available Tools</h3>';
    
    // Create tools grid
    const toolGrid = document.createElement('div');
    toolGrid.className = 'tools-grid';
    toolsContainer.appendChild(toolGrid);
    
    // Add tools to grid
    Object.entries(this.tools).forEach(([toolName, tool]) => {
      const toolElement = this.createToolElement(toolName, tool);
      toolGrid.appendChild(toolElement);
    });
  },
  
  // Create tool element
  createToolElement(toolName, tool) {
    const toolElement = document.createElement('div');
    toolElement.className = 'tool-item';
    toolElement.dataset.tool = toolName;
    
    // Get connection status
    const isConnected = tool.connected || false;
    
    // Get icon
    const iconClass = this.config.defaultAvatars[toolName.toLowerCase()] || this.config.defaultAvatars.default;
    
    // Create tool item content
    toolElement.innerHTML = `
      <div class="tool-icon">
        <i class="${iconClass}"></i>
      </div>
      <div class="tool-info">
        <span class="tool-name">${tool.display_name || toolName}</span>
        <span class="tool-status ${isConnected ? 'connected' : 'disconnected'}">${isConnected ? 'Connected' : 'Disconnected'}</span>
      </div>
      <div class="tool-actions">
        ${isConnected
          ? `<button class="btn btn-sm btn-secondary tool-details-btn" data-tool="${toolName}">
               <i class="fas fa-info-circle"></i>
             </button>`
          : `<button class="btn btn-sm btn-primary connect-tool-btn" data-tool="${toolName}">
               <i class="fas fa-plug"></i>
             </button>
             <button class="btn btn-sm btn-secondary tool-details-btn" data-tool="${toolName}">
               <i class="fas fa-info-circle"></i>
             </button>`
        }
      </div>
    `;
    
    return toolElement;
  },
  
  // Update logs container
  updateNodeLogs(nodeId, logs) {
    const logsContainer = document.getElementById('mcp-logs-container');
    if (!logsContainer) return;
    
    // Only update if this is the active node
    if (this.activeNode !== nodeId) return;
    
    // Format and update logs
    const formattedLogs = Array.isArray(logs) 
      ? logs.map(log => `<div class="log-entry ${log.level.toLowerCase()}">[${log.timestamp}] ${log.message}</div>`).join('') 
      : `<div class="log-entry">${logs}</div>`;
    
    logsContainer.innerHTML = formattedLogs || '<p>No logs available</p>';
    
    // Scroll to bottom
    logsContainer.scrollTop = logsContainer.scrollHeight;
  },
  
  // Start auto-refresh
  startAutoRefresh() {
    if (this.config.autoRefresh) {
      this.stopAutoRefresh(); // Stop any existing refresh
      
      this.refreshTimer = setInterval(() => {
        if (Dashboard.activePanel === 'mcp-panel') {
          this.fetchNodes();
          this.fetchTools();
        }
      }, this.config.refreshInterval);
    }
  },
  
  // Stop auto-refresh
  stopAutoRefresh() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
  },
  
  // Start a node
  async startNode(nodeId) {
    try {
      Dashboard.showToast(`Starting node ${nodeId}...`, 'info');
      
      const response = await fetch(`/api/mcp/node/${nodeId}/start`, {
        method: 'POST'
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        this.updateNodeStatus(nodeId, 'starting');
        Dashboard.showToast(`Node ${nodeId} starting...`, 'success');
      } else {
        console.error('Error starting node:', data.error);
        Dashboard.showToast(`Error starting node: ${data.error}`, 'error');
      }
    } catch (error) {
      console.error('Error starting node:', error);
      Dashboard.showToast('Could not start node', 'error');
    }
  },
  
  // Stop a node
  async stopNode(nodeId) {
    try {
      Dashboard.showToast(`Stopping node ${nodeId}...`, 'info');
      
      const response = await fetch(`/api/mcp/node/${nodeId}/stop`, {
        method: 'POST'
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        this.updateNodeStatus(nodeId, 'stopping');
        Dashboard.showToast(`Node ${nodeId} stopping...`, 'success');
      } else {
        console.error('Error stopping node:', data.error);
        Dashboard.showToast(`Error stopping node: ${data.error}`, 'error');
      }
    } catch (error) {
      console.error('Error stopping node:', error);
      Dashboard.showToast('Could not stop node', 'error');
    }
  },
  
  // Connect a tool
  async connectTool(toolName) {
    if (this.connectionInProgress) {
      Dashboard.showToast('Another connection is in progress', 'warning');
      return;
    }
    
    this.connectionInProgress = true;
    
    try {
      Dashboard.showToast(`Connecting to ${toolName}...`, 'info');
      
      // Get tool parameters
      const response = await fetch(`/api/mcp/tool/${toolName}/parameters`);
      const data = await response.json();
      
      if (data.status === 'success') {
        // Show connection modal
        this.showConnectionModal(toolName, data.parameters);
      } else {
        console.error('Error getting tool parameters:', data.error);
        Dashboard.showToast(`Error getting tool parameters: ${data.error}`, 'error');
      }
    } catch (error) {
      console.error('Error connecting tool:', error);
      Dashboard.showToast('Could not connect tool', 'error');
    } finally {
      this.connectionInProgress = false;
    }
  },
  
  // Show connection modal
  showConnectionModal(toolName, parameters) {
    // Create the modal if it doesn't exist
    if (!document.getElementById('connection-modal')) {
      const modalHTML = `
        <div id="connection-modal" class="modal">
          <div class="modal-content">
            <div class="modal-header">
              <h3 id="connection-modal-title">Connect Tool</h3>
              <button id="connection-modal-close" class="close-btn">&times;</button>
            </div>
            <div class="modal-body" id="connection-modal-content">
              <!-- Form will be inserted here -->
            </div>
            <div class="modal-footer">
              <button id="connection-modal-submit" class="btn btn-primary">Connect</button>
            </div>
          </div>
        </div>
      `;
      
      const modalContainer = document.createElement('div');
      modalContainer.innerHTML = modalHTML;
      document.body.appendChild(modalContainer.firstElementChild);
    }
    
    // Get modal elements
    const modal = document.getElementById('connection-modal');
    const modalTitle = document.getElementById('connection-modal-title');
    const modalContent = document.getElementById('connection-modal-content');
    const modalClose = document.getElementById('connection-modal-close');
    const modalSubmit = document.getElementById('connection-modal-submit');
    
    // Set modal title
    modalTitle.textContent = `Connect to ${toolName}`;
    
    // Clear modal content
    modalContent.innerHTML = '';
    
    // Add parameters to modal
    if (parameters && Object.keys(parameters).length > 0) {
      // Create form
      const form = document.createElement('form');
      form.id = 'connection-form';
      
      // Add parameters to form
      Object.entries(parameters).forEach(([key, value]) => {
        const formGroup = document.createElement('div');
        formGroup.className = 'form-group';
        
        const label = document.createElement('label');
        label.htmlFor = `param-${key}`;
        label.textContent = key;
        
        const input = document.createElement('input');
        input.type = key.toLowerCase().includes('password') || key.toLowerCase().includes('key') || key.toLowerCase().includes('token') ? 'password' : 'text';
        input.id = `param-${key}`;
        input.name = key;
        input.value = value || '';
        input.className = 'form-control';
        
        formGroup.appendChild(label);
        formGroup.appendChild(input);
        form.appendChild(formGroup);
      });
      
      modalContent.appendChild(form);
    } else {
      // No parameters needed
      const message = document.createElement('p');
      message.textContent = 'No parameters needed for this tool. Click connect to proceed.';
      modalContent.appendChild(message);
    }
    
    // Set up submit button
    modalSubmit.textContent = 'Connect';
    modalSubmit.onclick = () => {
      // Get form data
      const form = document.getElementById('connection-form');
      const params = {};
      
      if (form) {
        const formData = new FormData(form);
        for (const [key, value] of formData.entries()) {
          params[key] = value;
        }
      }
      
      // Submit connection
      this.submitConnection(toolName, params);
      
      // Close modal
      modal.style.display = 'none';
    };
    
    // Set up close button
    modalClose.onclick = () => {
      modal.style.display = 'none';
    };
    
    // Close when clicking outside
    window.onclick = (event) => {
      if (event.target === modal) {
        modal.style.display = 'none';
      }
    };
    
    // Show modal
    modal.style.display = 'block';
  },
  
  // Submit connection
  async submitConnection(toolName, parameters) {
    try {
      Dashboard.showToast(`Connecting to ${toolName}...`, 'info');
      
      // Disable submission during API call
      this.connectionInProgress = true;
      
      const response = await fetch(`/api/mcp/tool/${toolName}/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ parameters })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        // Update tool status
        this.updateToolStatus(toolName, { connected: true });
        Dashboard.showToast(`Connected to ${toolName}`, 'success');
        
        // Refresh tools
        this.fetchTools();
      } else {
        console.error('Error connecting to tool:', data.error);
        Dashboard.showToast(`Error connecting to ${toolName}: ${data.error}`, 'error');
      }
    } catch (error) {
      console.error('Error connecting to tool:', error);
      Dashboard.showToast(`Could not connect to ${toolName}`, 'error');
    } finally {
      this.connectionInProgress = false;
    }
  },
  
  // Execute tool action
  async executeToolAction(toolName, action) {
    try {
      Dashboard.showToast(`Executing ${action} on ${toolName}...`, 'info');
      
      const response = await fetch(`/api/mcp/tool/${toolName}/action/${action}`, {
        method: 'POST'
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        Dashboard.showToast(`Action ${action} executed on ${toolName}`, 'success');
        
        // Update result in details modal if open
        const resultContainer = document.getElementById('tool-action-result');
        if (resultContainer) {
          resultContainer.style.display = 'block';
          resultContainer.innerHTML = `
            <h4>Result:</h4>
            <pre>${JSON.stringify(data.result, null, 2)}</pre>
          `;
        }
      } else {
        console.error('Error executing tool action:', data.error);
        Dashboard.showToast(`Error executing ${action} on ${toolName}: ${data.error}`, 'error');
      }
    } catch (error) {
      console.error('Error executing tool action:', error);
      Dashboard.showToast(`Could not execute ${action} on ${toolName}`, 'error');
    }
  },
  
  // Update node status
  updateNodeStatus(nodeId, status) {
    // Update status in state
    this.nodeStatus[nodeId] = status;
    
    // Update node element in UI
    const nodeElement = document.querySelector(`.node-item[data-nodeid="${nodeId}"]`);
    if (nodeElement) {
      // Update status indicator
      const statusIndicator = nodeElement.querySelector('.node-status');
      if (statusIndicator) {
        statusIndicator.className = `node-status ${status}`;
        statusIndicator.textContent = status;
      }
      
      // Update actions
      const actionsContainer = nodeElement.querySelector('.node-actions');
      if (actionsContainer) {
        if (status === 'online') {
          actionsContainer.innerHTML = `
            <button class="btn btn-sm btn-danger stop-node-btn" data-nodeid="${nodeId}">
              <i class="fas fa-stop"></i>
            </button>
            <button class="btn btn-sm btn-primary node-details-btn" data-nodeid="${nodeId}">
              <i class="fas fa-info-circle"></i>
            </button>
          `;
        } else if (status === 'offline') {
          actionsContainer.innerHTML = `
            <button class="btn btn-sm btn-success start-node-btn" data-nodeid="${nodeId}">
              <i class="fas fa-play"></i>
            </button>
            <button class="btn btn-sm btn-primary node-details-btn" data-nodeid="${nodeId}">
              <i class="fas fa-info-circle"></i>
            </button>
          `;
        } else {
          // For starting/stopping states
          actionsContainer.innerHTML = `
            <span class="status-badge ${status}">${status}</span>
            <button class="btn btn-sm btn-primary node-details-btn" data-nodeid="${nodeId}">
              <i class="fas fa-info-circle"></i>
            </button>
          `;
        }
      }
    }
  },
  
  // Update tool status
  updateToolStatus(toolName, status) {
    // Update tool in state
    if (this.tools[toolName]) {
      this.tools[toolName] = { ...this.tools[toolName], ...status };
    }
    
    // Update tool element in UI
    const toolElement = document.querySelector(`.tool-item[data-tool="${toolName}"]`);
    if (toolElement) {
      // Update status indicator
      const statusIndicator = toolElement.querySelector('.tool-status');
      if (statusIndicator) {
        statusIndicator.className = `tool-status ${status.connected ? 'connected' : 'disconnected'}`;
        statusIndicator.textContent = status.connected ? 'Connected' : 'Disconnected';
      }
      
      // Update actions
      const actionsContainer = toolElement.querySelector('.tool-actions');
      if (actionsContainer) {
        if (status.connected) {
          // Update to show connected state
          actionsContainer.innerHTML = `
            <button class="btn btn-sm btn-secondary tool-details-btn" data-tool="${toolName}">
              <i class="fas fa-info-circle"></i>
            </button>
          `;
        } else {
          // Update to show connect button
          actionsContainer.innerHTML = `
            <button class="btn btn-sm btn-primary connect-tool-btn" data-tool="${toolName}">
              <i class="fas fa-plug"></i>
            </button>
            <button class="btn btn-sm btn-secondary tool-details-btn" data-tool="${toolName}">
              <i class="fas fa-info-circle"></i>
            </button>
          `;
        }
      }
    }
  },
  
  // Show node details
  showNodeDetails(node) {
    // Set active node for logs
    this.activeNode = node.id;
    
    // Get or create modal
    if (!document.getElementById('component-modal')) {
      Dashboard.showToast('Component modal not found', 'error');
      return;
    }
    
    // Get modal elements
    const modal = document.getElementById('component-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    
    // Set modal title
    modalTitle.textContent = `Node: ${node.name}`;
    
    // Set modal content
    modalBody.innerHTML = `
      <div class="modal-details">
        <div class="details-row">
          <span class="details-label">ID:</span>
          <span class="details-value">${node.id}</span>
        </div>
        <div class="details-row">
          <span class="details-label">Type:</span>
          <span class="details-value">${node.type}</span>
        </div>
        <div class="details-row">
          <span class="details-label">Status:</span>
          <span class="details-value status-badge ${this.nodeStatus[node.id] || 'offline'}">${this.nodeStatus[node.id] || 'offline'}</span>
        </div>
        <div class="details-row">
          <span class="details-label">Description:</span>
          <span class="details-value">${node.description || 'No description'}</span>
        </div>
        <div class="details-row">
          <span class="details-label">Memory:</span>
          <span class="details-value">${node.memory || 'N/A'}</span>
        </div>
      </div>
      
      <div class="modal-section">
        <h4>Tools</h4>
        <div class="tools-list">
          ${node.tools && node.tools.length > 0
            ? node.tools.map(tool => `
                <div class="tool-item">
                  <i class="${this.config.defaultAvatars[tool.toLowerCase()] || this.config.defaultAvatars.default}"></i>
                  <span>${tool}</span>
                </div>
              `).join('')
            : '<p>No tools available</p>'
          }
        </div>
      </div>
      
      <div class="modal-section">
        <h4>Logs</h4>
        <div class="logs-container modal-logs">
          <p>Loading logs...</p>
        </div>
      </div>
      
      <div class="modal-section">
        <h4>Actions</h4>
        <div class="modal-actions">
          ${this.nodeStatus[node.id] === 'online' 
            ? `<button class="btn btn-danger stop-node-btn" data-nodeid="${node.id}">
                 <i class="fas fa-stop"></i> Stop Node
               </button>`
            : `<button class="btn btn-success start-node-btn" data-nodeid="${node.id}">
                 <i class="fas fa-play"></i> Start Node
               </button>`
          }
        </div>
      </div>
    `;
    
    // Fetch logs for this node
    this.fetchNodeLogs(node.id);
    
    // Show modal
    modal.style.display = 'block';
  },
  
  // Fetch logs for a node
  async fetchNodeLogs(nodeId) {
    try {
      const response = await fetch(`/api/mcp/node/${nodeId}/logs`);
      const data = await response.json();
      
      if (data.status === 'success') {
        // Update logs in modal
        const logsContainer = document.querySelector('.modal-logs');
        if (logsContainer) {
          if (data.logs && data.logs.length > 0) {
            const logsHTML = data.logs.map(log => 
              `<div class="log-entry ${log.level?.toLowerCase() || 'info'}">[${log.timestamp || new Date().toISOString()}] ${log.message}</div>`
            ).join('');
            logsContainer.innerHTML = logsHTML;
          } else {
            logsContainer.innerHTML = '<p>No logs available</p>';
          }
        }
      } else {
        console.error('Error fetching logs:', data.error);
      }
    } catch (error) {
      console.error('Error fetching logs:', error);
      const logsContainer = document.querySelector('.modal-logs');
      if (logsContainer) {
        logsContainer.innerHTML = '<p>Error loading logs</p>';
      }
    }
  },
  
  // Show tool details
  showToolDetails(toolName, tool) {
    // Get or create modal
    if (!document.getElementById('component-modal')) {
      Dashboard.showToast('Component modal not found', 'error');
      return;
    }
    
    // Get modal elements
    const modal = document.getElementById('component-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    
    // Set modal title
    modalTitle.textContent = `Tool: ${tool.display_name || toolName}`;
    
    // Set modal content
    modalBody.innerHTML = `
      <div class="modal-details">
        <div class="details-row">
          <span class="details-label">Name:</span>
          <span class="details-value">${toolName}</span>
        </div>
        <div class="details-row">
          <span class="details-label">Status:</span>
          <span class="details-value status-badge ${tool.connected ? 'connected' : 'disconnected'}">${tool.connected ? 'Connected' : 'Disconnected'}</span>
        </div>
        <div class="details-row">
          <span class="details-label">Description:</span>
          <span class="details-value">${tool.description || 'No description'}</span>
        </div>
      </div>
      
      <div class="modal-section">
        <h4>Actions</h4>
        <div class="modal-actions">
          ${tool.connected 
            ? `<div class="tool-actions-list">
                 ${tool.actions && tool.actions.length > 0 
                   ? tool.actions.map(action => `
                       <button class="btn btn-primary tool-action-btn" data-tool="${toolName}" data-action="${action.name || action}">
                         <i class="fas fa-bolt"></i> ${action.display_name || action.name || action}
                       </button>
                     `).join('')
                   : '<p>No actions available</p>'
                 }
               </div>`
            : `<button class="btn btn-primary connect-tool-btn" data-tool="${toolName}">
                 <i class="fas fa-plug"></i> Connect
               </button>`
          }
        </div>
      </div>
      
      <div class="modal-section" id="tool-action-result" style="display: none;"></div>
    `;
    
    // Show modal
    modal.style.display = 'block';
  },
  
  // Sync memory across nodes
  async syncMemory() {
    try {
      Dashboard.showToast('Syncing memory across nodes...', 'info');
      
      const response = await fetch('/api/mcp/memory/sync', {
        method: 'POST'
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        Dashboard.showToast('Memory synchronized successfully', 'success');
      } else {
        console.error('Error syncing memory:', data.error);
        Dashboard.showToast(`Error syncing memory: ${data.error}`, 'error');
      }
    } catch (error) {
      console.error('Error syncing memory:', error);
      Dashboard.showToast('Could not sync memory', 'error');
    }
  }
};

// Register initialization on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  // Initialize only when dashboard is active
  if (Dashboard && Dashboard.activePanel === 'mcp-panel') {
    MCP.init(Dashboard.socket);
  }
}); 