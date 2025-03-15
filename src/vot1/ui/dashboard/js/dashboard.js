/**
 * VOTai TRILOGY BRAIN - Dashboard Main
 * Main dashboard initialization and control
 */

class TrilogyDashboard {
  constructor() {
    // Dashboard components
    this.memoryVisualization = null;
    this.terminal = null; // Reference to terminal interface instance
    this.charts = null;   // Reference to charts instance
    
    // Dashboard state
    this.currentView = 'network';
    this.detailLevel = 3;
    this.isWalletConnected = false;
    
    // System state
    this.agents = [];
    this.memories = [];
    this.systemStats = {
      uptime: 0,
      memoryOperations: 0,
      activeNodes: 0,
      connectedAgents: 0
    };
    
    // UI Elements
    this.connectWalletBtn = null;
    this.toggleViewBtn = null;
    this.visMode = null;
    this.detailLevelSlider = null;
    
    // Tooltip element for memory previews
    this.tooltip = null;
    
    // Initialize when DOM is fully loaded
    document.addEventListener('DOMContentLoaded', this.init.bind(this));
  }
  
  init() {
    // Initialize UI references
    this.connectWalletBtn = document.getElementById('connect-wallet');
    this.toggleViewBtn = document.getElementById('toggle-view');
    this.visMode = document.getElementById('vis-mode');
    this.detailLevelSlider = document.getElementById('detail-level');
    
    // Initialize THREE.js visualization
    const container = document.getElementById('three-container');
    this.memoryVisualization = new MemoryNetworkVisualization(container);
    
    // Get references to other components
    this.terminal = window.terminalInterface;
    this.charts = window.dashboardCharts;
    
    // Create tooltip for memory previews
    this.createTooltip();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Initialize with demo data
    this.loadDemoData();
    
    // Start system monitoring
    this.startSystemMonitoring();
    
    // Log initialization complete
    console.log('VOTai TRILOGY BRAIN dashboard initialized');
    this.terminal.logSystem('Dashboard initialized. Welcome to VOTai TRILOGY BRAIN!');
  }
  
  createTooltip() {
    // Create tooltip element for memory previews
    this.tooltip = document.createElement('div');
    this.tooltip.className = 'memory-tooltip';
    this.tooltip.style.position = 'absolute';
    this.tooltip.style.display = 'none';
    this.tooltip.style.zIndex = '1000';
    this.tooltip.style.background = 'rgba(5, 0, 19, 0.9)';
    this.tooltip.style.border = '1px solid var(--secondary)';
    this.tooltip.style.borderRadius = '4px';
    this.tooltip.style.padding = '10px';
    this.tooltip.style.maxWidth = '300px';
    this.tooltip.style.boxShadow = '0 0 10px rgba(16, 165, 245, 0.5)';
    this.tooltip.style.backdropFilter = 'blur(5px)';
    this.tooltip.style.fontFamily = "'Share Tech Mono', monospace";
    this.tooltip.style.fontSize = '0.8rem';
    this.tooltip.style.color = 'var(--text-primary)';
    this.tooltip.style.pointerEvents = 'none'; // Allow mouse events to pass through
    
    document.body.appendChild(this.tooltip);
  }
  
  setupEventListeners() {
    // Connect wallet button
    this.connectWalletBtn.addEventListener('click', this.connectWallet.bind(this));
    
    // Toggle view button
    this.toggleViewBtn.addEventListener('click', this.toggleView.bind(this));
    
    // Visualization mode select
    this.visMode.addEventListener('change', this.changeVisualizationMode.bind(this));
    
    // Detail level slider
    this.detailLevelSlider.addEventListener('input', this.updateDetailLevel.bind(this));
    
    // Memory visualization events
    document.addEventListener('showMemoryPreview', this.showMemoryPreview.bind(this));
    document.addEventListener('hideMemoryPreview', this.hideMemoryPreview.bind(this));
    
    // Mouse move for tooltip positioning
    document.addEventListener('mousemove', (event) => {
      if (this.tooltip.style.display === 'block') {
        // Position tooltip to follow cursor
        const x = event.clientX + 15;
        const y = event.clientY + 15;
        
        // Keep tooltip within viewport
        const tooltipRect = this.tooltip.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Adjust position if tooltip would go beyond viewport edges
        const adjustedX = x + tooltipRect.width > viewportWidth ? x - tooltipRect.width - 30 : x;
        const adjustedY = y + tooltipRect.height > viewportHeight ? y - tooltipRect.height - 30 : y;
        
        this.tooltip.style.left = `${adjustedX}px`;
        this.tooltip.style.top = `${adjustedY}px`;
      }
    });
  }
  
  connectWallet() {
    if (this.isWalletConnected) {
      // Disconnect wallet
      this.isWalletConnected = false;
      this.connectWalletBtn.querySelector('.cyber-button__text').textContent = 'CONNECT WALLET';
      this.terminal.logAgent('SYSTEM', 'Wallet disconnected.');
    } else {
      // Simulate wallet connection
      this.terminal.logAgent('SYSTEM', 'Connecting to wallet...');
      
      setTimeout(() => {
        this.isWalletConnected = true;
        this.connectWalletBtn.querySelector('.cyber-button__text').textContent = 'DISCONNECT WALLET';
        this.terminal.logAgent('SYSTEM', 'Wallet connected! Address: 0x71C...F3B2');
        
        // Update token stats
        document.querySelector('.system-status .status-item:nth-child(3) .value').textContent = '8,427';
      }, 1500);
    }
  }
  
  toggleView() {
    // Toggle between different dashboard layouts
    // For simplicity, just alert for now
    this.terminal.logAgent('SYSTEM', 'View switching is not implemented in the demo.');
  }
  
  changeVisualizationMode() {
    const mode = this.visMode.value;
    this.currentView = mode;
    
    this.terminal.logAgent('SYSTEM', `Visualization mode changed to: ${mode}`);
    
    // Adjust visualization based on mode
    switch (mode) {
      case 'network':
        // Default network view - no special settings
        break;
      case 'clusters':
        // Group by memory clusters
        break;
      case 'importance':
        // Heatmap by importance
        break;
      case 'temporal':
        // Arrange by time
        break;
    }
  }
  
  updateDetailLevel() {
    const level = parseInt(this.detailLevelSlider.value);
    this.detailLevel = level;
    
    this.terminal.logAgent('SYSTEM', `Detail level set to: ${level}`);
    
    // Adjust visualization detail level
    // For demo, adjust glow intensity and rotation speed
    if (this.memoryVisualization) {
      // Map detail level (1-5) to glow intensity (0.5-2.0)
      const glowIntensity = 0.5 + (level - 1) * 0.375;
      this.memoryVisualization.updateGlowIntensity(glowIntensity);
      
      // Map detail level (1-5) to rotation speed (10-50)
      const rotationSpeed = 10 + (level - 1) * 10;
      this.memoryVisualization.updateRotationSpeed(rotationSpeed);
    }
  }
  
  showMemoryPreview(event) {
    const memory = event.detail;
    if (!memory) return;
    
    // Format memory preview content
    const importance = Math.round(memory.importance * 100);
    const date = new Date(memory.timestamp || Date.now()).toLocaleString();
    
    let content = `
      <div style="margin-bottom: 5px; color: var(--secondary); font-weight: bold;">${memory.id}</div>
      <div style="margin-bottom: 5px; display: flex; justify-content: space-between;">
        <span style="color: var(--text-secondary);">Level: <span style="color: var(--primary);">${memory.level}</span></span>
        <span style="color: var(--text-secondary);">Importance: <span style="color: var(--accent);">${importance}%</span></span>
      </div>
      <hr style="border-color: var(--panel-border); margin: 5px 0;" />
      <div style="margin-bottom: 5px; color: var(--text-bright);">${memory.text}</div>
      <div style="font-size: 0.7rem; color: var(--text-secondary); text-align: right;">${date}</div>
    `;
    
    // Update and show tooltip
    this.tooltip.innerHTML = content;
    this.tooltip.style.display = 'block';
  }
  
  hideMemoryPreview() {
    this.tooltip.style.display = 'none';
  }
  
  loadDemoData() {
    // Generate sample memory data
    const memoryCount = 150; // Number of memories to generate
    const memories = this.generateDemoMemories(memoryCount);
    
    // Set data to visualization
    if (this.memoryVisualization) {
      this.memoryVisualization.setData({ memories });
    }
    
    this.memories = memories;
    this.terminal.logAgent('MEMORY', `Loaded ${memoryCount} memories into visualization.`);
  }
  
  generateDemoMemories(count) {
    const memories = [];
    const topics = [
      'User query about TRILOGY BRAIN architecture',
      'Discussion of memory cascade operations',
      'Zero-knowledge proofs for memory verification',
      'IPFS decentralized storage implementation',
      'Tokenomics model for memory services',
      'Integration with Claude 3.7 API',
      'Dashboard visualization development',
      'Cyberpunk interface design principles',
      'Memory benchmarking methodology',
      'Context window optimization techniques'
    ];
    
    // Cache levels and their distributions
    const cacheLevels = {
      'L1': 0.35, // 35% in L1
      'L2': 0.45, // 45% in L2
      'L3': 0.20  // 20% in L3
    };
    
    // Generate memories
    for (let i = 0; i < count; i++) {
      // Determine cache level based on distribution
      const levelRoll = Math.random();
      let cacheLevel = 'L3';
      let cumulativeProbability = 0;
      
      for (const [level, probability] of Object.entries(cacheLevels)) {
        cumulativeProbability += probability;
        if (levelRoll < cumulativeProbability) {
          cacheLevel = level;
          break;
        }
      }
      
      // Random importance based on cache level
      let importanceBase;
      switch (cacheLevel) {
        case 'L1': importanceBase = 0.7; break; // L1: 0.7-1.0
        case 'L2': importanceBase = 0.4; break; // L2: 0.4-0.7
        case 'L3': importanceBase = 0.0; break; // L3: 0.0-0.4
      }
      
      const importance = importanceBase + Math.random() * 0.3;
      
      // Generate timestamp (more recent for higher levels)
      const now = Date.now();
      const maxAge = cacheLevel === 'L1' ? 2 : (cacheLevel === 'L2' ? 7 : 30); // days
      const timestamp = now - Math.random() * maxAge * 24 * 60 * 60 * 1000;
      
      // Select a random topic
      const topicIndex = Math.floor(Math.random() * topics.length);
      
      // Create memory
      const memory = {
        id: `mem-${i.toString().padStart(3, '0')}`,
        text: topics[topicIndex],
        cacheLevel: cacheLevel,
        importance: importance,
        timestamp: timestamp,
        tokenCount: 20 + Math.floor(Math.random() * 80)
      };
      
      // Add connections (more for important memories)
      const connectionCount = Math.floor(importance * 5); // 0-5 connections
      if (connectionCount > 0) {
        memory.connections = [];
        
        // Create connections to random existing memories
        for (let j = 0; j < connectionCount; j++) {
          if (memories.length > 0) {
            const targetIndex = Math.floor(Math.random() * memories.length);
            memory.connections.push({
              targetId: memories[targetIndex].id,
              strength: 0.3 + Math.random() * 0.7 // 0.3-1.0 strength
            });
          }
        }
      }
      
      memories.push(memory);
    }
    
    return memories;
  }
  
  startSystemMonitoring() {
    // Update system stats periodically
    setInterval(() => {
      // Update uptime
      this.systemStats.uptime += 1; // Add 1 minute
      const days = Math.floor(this.systemStats.uptime / (60 * 24));
      const hours = Math.floor((this.systemStats.uptime % (60 * 24)) / 60);
      const minutes = this.systemStats.uptime % 60;
      
      const uptimeString = `${days}d ${hours}h ${minutes}m`;
      document.querySelector('.footer-stat:nth-child(1) .value').textContent = uptimeString;
      
      // Random fluctuations in other stats
      this.systemStats.memoryOperations += Math.floor(Math.random() * 100);
      document.querySelector('.footer-stat:nth-child(2) .value').textContent = 
        (this.systemStats.memoryOperations / 1000).toFixed(1) + 'K';
      
      // Random active nodes between 15-20 out of 24
      this.systemStats.activeNodes = 15 + Math.floor(Math.random() * 6);
      document.querySelector('.footer-stat:nth-child(3) .value').textContent = 
        `${this.systemStats.activeNodes}/24`;
      
      // Simulate occasional memory cascade operations
      if (Math.random() < 0.1) { // 10% chance each minute
        this.terminal.logAgent('MEMORY', 'Memory cascade operation triggered automatically.');
        this.terminal.logAgent('MEMORY', 'Processing memories for cascade...');
        
        setTimeout(() => {
          const cascadeCount = Math.floor(Math.random() * 30) + 10;
          this.terminal.logAgent('MEMORY', `Cascade complete: ${cascadeCount} memories processed.`);
        }, 2000);
      }
      
      // Occasionally simulate agent connections/disconnections
      if (Math.random() < 0.15) { // 15% chance each minute
        const isConnection = Math.random() < 0.6; // 60% connection, 40% disconnection
        
        if (isConnection && this.systemStats.connectedAgents < 16) {
          this.systemStats.connectedAgents++;
          this.terminal.logAgent('SYSTEM', `New agent connected. Total agents: ${this.systemStats.connectedAgents}`);
        } else if (!isConnection && this.systemStats.connectedAgents > 8) {
          this.systemStats.connectedAgents--;
          this.terminal.logAgent('SYSTEM', `Agent disconnected. Total agents: ${this.systemStats.connectedAgents}`);
        }
        
        document.querySelector('.system-status .status-item:nth-child(2) .value').textContent = 
          this.systemStats.connectedAgents;
      }
    }, 60000); // Update every minute
    
    // Initial values
    this.systemStats.uptime = 212 * 60 + 47; // 3d 12h 47m in minutes
    this.systemStats.memoryOperations = 87500;
    this.systemStats.activeNodes = 18;
    this.systemStats.connectedAgents = 12;
  }
}

// Initialize dashboard
const dashboard = new TrilogyDashboard(); 