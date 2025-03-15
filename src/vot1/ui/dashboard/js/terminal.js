/**
 * VOTai TRILOGY BRAIN - Terminal Component
 * Terminal interface for system messaging and agent interactions
 */

class TerminalInterface {
  constructor(options = {}) {
    this.options = Object.assign({
      maxLines: 100,            // Maximum number of lines to keep in history
      typewriterSpeed: 20,      // Speed of typewriter effect in ms
      commandHistory: 10,       // Number of commands to keep in history
      agentResponseDelay: 500,  // Delay before agent response in ms
      promptText: 'VOTai@TRILOGY:~$'
    }, options);
    
    // DOM elements
    this.terminal = document.getElementById('system-console');
    this.input = document.getElementById('terminal-command');
    this.clearButton = document.getElementById('clear-console');
    this.toggleButton = document.getElementById('toggle-console');
    
    // Terminal state
    this.isHidden = false;
    this.history = [];
    this.historyIndex = -1;
    this.commandHistory = [];
    this.agents = {};
    this.processingCommand = false;
    
    // Command handlers
    this.commands = {
      'help': this.showHelp.bind(this),
      'clear': this.clearTerminal.bind(this),
      'stats': this.showStats.bind(this),
      'agent': this.agentCommand.bind(this),
      'memory': this.memoryCommand.bind(this),
      'ipfs': this.ipfsCommand.bind(this),
      'benchmark': this.runBenchmark.bind(this),
      'cascade': this.triggerCascade.bind(this),
      'token': this.tokenCommand.bind(this),
      'status': this.showStatus.bind(this)
    };
    
    this.init();
  }
  
  init() {
    // Set up event listeners
    this.input.addEventListener('keydown', this.handleKeyDown.bind(this));
    this.clearButton.addEventListener('click', this.clearTerminal.bind(this));
    this.toggleButton.addEventListener('click', this.toggleTerminal.bind(this));
    
    // Listen for memory visualization events
    document.addEventListener('showMemoryInTerminal', this.handleMemorySelection.bind(this));
    
    // Register default agents
    this.registerAgent('SYSTEM', {
      color: 'var(--text-primary)',
      icon: '🔄',
      name: 'SYSTEM'
    });
    
    this.registerAgent('ERROR', {
      color: 'var(--status-error)',
      icon: '⚠️',
      name: 'ERROR'
    });
    
    this.registerAgent('CLAUDE', {
      color: 'var(--primary)',
      icon: '🧠',
      name: 'CLAUDE 3.7'
    });
    
    this.registerAgent('MEMORY', {
      color: 'var(--secondary)',
      icon: '💾',
      name: 'MEMORY MANAGER'
    });
    
    this.registerAgent('IPFS', {
      color: '#11A380',
      icon: '📦',
      name: 'IPFS STORAGE'
    });
    
    this.registerAgent('ZK', {
      color: 'var(--accent)',
      icon: '🔐',
      name: 'ZK VERIFICATION'
    });
    
    // Initial message
    this.logAgent('SYSTEM', 'Terminal initialized. Type "help" for available commands.');
  }
  
  handleKeyDown(event) {
    // Handle command history navigation (up/down arrows)
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      this.navigateHistory(-1);
    } else if (event.key === 'ArrowDown') {
      event.preventDefault();
      this.navigateHistory(1);
    } else if (event.key === 'Enter') {
      event.preventDefault();
      this.executeCommand();
    } else if (event.key === 'Tab') {
      event.preventDefault();
      this.autocompleteCommand();
    }
  }
  
  navigateHistory(direction) {
    if (this.commandHistory.length === 0) return;
    
    this.historyIndex += direction;
    
    // Constrain history index
    if (this.historyIndex < 0) this.historyIndex = 0;
    if (this.historyIndex >= this.commandHistory.length) {
      this.historyIndex = this.commandHistory.length - 1;
      // Allow going one step beyond the end to clear the input
      if (direction > 0 && this.input.value === this.commandHistory[this.historyIndex]) {
        this.input.value = '';
        this.historyIndex = this.commandHistory.length;
        return;
      }
    }
    
    this.input.value = this.commandHistory[this.historyIndex];
    
    // Move cursor to end of input
    setTimeout(() => {
      this.input.selectionStart = this.input.selectionEnd = this.input.value.length;
    }, 0);
  }
  
  autocompleteCommand() {
    const input = this.input.value.trim();
    if (!input) return;
    
    // Find matching commands
    const matches = Object.keys(this.commands).filter(cmd => cmd.startsWith(input));
    
    if (matches.length === 1) {
      // Single match - complete the command
      this.input.value = matches[0] + ' ';
    } else if (matches.length > 1) {
      // Multiple matches - display them
      this.logSystem(`Matching commands: ${matches.join(', ')}`);
    }
  }
  
  executeCommand() {
    const command = this.input.value.trim();
    if (!command) return;
    
    // Add to history
    this.addToCommandHistory(command);
    
    // Log the command
    this.logCommand(command);
    
    // Clear input
    this.input.value = '';
    
    // Process command
    this.processCommand(command);
  }
  
  addToCommandHistory(command) {
    // Don't add duplicate consecutive commands
    if (this.commandHistory.length > 0 && this.commandHistory[this.commandHistory.length - 1] === command) {
      this.historyIndex = this.commandHistory.length;
      return;
    }
    
    this.commandHistory.push(command);
    
    // Keep history under limit
    if (this.commandHistory.length > this.options.commandHistory) {
      this.commandHistory.shift();
    }
    
    // Reset history index to point to end of history
    this.historyIndex = this.commandHistory.length;
  }
  
  processCommand(command) {
    if (this.processingCommand) return;
    
    this.processingCommand = true;
    
    // Split the command into parts
    const parts = command.split(' ');
    const cmd = parts[0].toLowerCase();
    const args = parts.slice(1);
    
    // Execute the command
    if (cmd in this.commands) {
      try {
        this.commands[cmd](args);
      } catch (error) {
        this.logError(`Error executing command: ${error.message}`);
      }
    } else {
      this.logError(`Unknown command: ${cmd}. Type "help" for available commands.`);
    }
    
    this.processingCommand = false;
  }
  
  // Command Handlers
  
  showHelp() {
    const commands = [
      { cmd: 'help', desc: 'Show available commands' },
      { cmd: 'clear', desc: 'Clear the terminal' },
      { cmd: 'stats', desc: 'Show system statistics' },
      { cmd: 'agent list', desc: 'List all registered agents' },
      { cmd: 'agent <name> <message>', desc: 'Send message as agent' },
      { cmd: 'memory list', desc: 'List memories in cache' },
      { cmd: 'memory search <query>', desc: 'Search memories' },
      { cmd: 'memory stats', desc: 'Show memory statistics' },
      { cmd: 'ipfs status', desc: 'Show IPFS connection status' },
      { cmd: 'ipfs sync', desc: 'Synchronize with IPFS network' },
      { cmd: 'benchmark run', desc: 'Run memory benchmark' },
      { cmd: 'cascade force', desc: 'Force memory cascade operation' },
      { cmd: 'token balance', desc: 'Show token balance' },
      { cmd: 'token transactions', desc: 'Show recent transactions' },
      { cmd: 'status', desc: 'Show system status' }
    ];
    
    this.logSystem('Available commands:');
    commands.forEach(({ cmd, desc }) => {
      this.terminal.innerHTML += `<div class="terminal-line"><span class="terminal-command-help">${cmd.padEnd(25)}</span><span class="terminal-help-desc">${desc}</span></div>`;
    });
    
    this.scrollToBottom();
  }
  
  clearTerminal() {
    this.terminal.innerHTML = '';
    this.logSystem('Terminal cleared');
  }
  
  toggleTerminal() {
    const container = this.terminal.parentElement;
    
    if (this.isHidden) {
      container.style.height = '200px';
      this.toggleButton.textContent = 'HIDE';
    } else {
      container.style.height = '32px'; // Just enough for the header
      this.toggleButton.textContent = 'SHOW';
    }
    
    this.isHidden = !this.isHidden;
  }
  
  showStats() {
    this.logSystem('System Statistics:');
    
    const stats = [
      { name: 'Uptime', value: '3d 12h 47m' },
      { name: 'Memory Usage', value: '67%' },
      { name: 'Active Agents', value: '12/24' },
      { name: 'Memory Operations', value: '87.5K' },
      { name: 'Token Processing', value: '1.2K/s' },
      { name: 'Cache Hit Rate', value: '89%' },
      { name: 'VOTai Tokens', value: '8,427' }
    ];
    
    stats.forEach(({ name, value }) => {
      this.terminal.innerHTML += `<div class="terminal-line"><span class="terminal-stat-name">${name.padEnd(20)}</span><span class="terminal-stat-value">${value}</span></div>`;
    });
    
    this.scrollToBottom();
  }
  
  agentCommand(args) {
    if (!args.length) {
      this.logError('Invalid agent command. Usage: agent list | agent <name> <message>');
      return;
    }
    
    if (args[0] === 'list') {
      // List all registered agents
      this.logSystem('Registered Agents:');
      
      Object.values(this.agents).forEach(agent => {
        this.terminal.innerHTML += `<div class="terminal-line"><span style="color: ${agent.color}">${agent.icon} ${agent.name}</span></div>`;
      });
    } else {
      // Send message as agent
      const agentName = args[0].toUpperCase();
      const message = args.slice(1).join(' ');
      
      if (!message) {
        this.logError('Missing message. Usage: agent <name> <message>');
        return;
      }
      
      if (agentName in this.agents) {
        this.logAgent(agentName, message);
      } else {
        this.logError(`Unknown agent: ${agentName}. Use "agent list" to see available agents.`);
      }
    }
  }
  
  memoryCommand(args) {
    if (!args.length) {
      this.logError('Invalid memory command. Usage: memory list | memory search <query> | memory stats');
      return;
    }
    
    const subcommand = args[0];
    
    if (subcommand === 'list') {
      // Simulate fetching memories from the cache
      this.logAgent('MEMORY', 'Fetching memories from cache...');
      
      setTimeout(() => {
        // This would normally come from the actual memory system
        const memories = [
          { id: 'mem-001', text: 'User asked about token economics', level: 'L1', importance: 0.85 },
          { id: 'mem-002', text: 'Discussed integration with Claude 3.7', level: 'L1', importance: 0.92 },
          { id: 'mem-003', text: 'User concerned about IPFS decentralization', level: 'L2', importance: 0.73 },
          { id: 'mem-004', text: 'Explained ZK verification process', level: 'L2', importance: 0.68 },
          { id: 'mem-005', text: 'User mentioned VillageOfThousands.io', level: 'L1', importance: 0.89 }
        ];
        
        this.logAgent('MEMORY', `Found ${memories.length} memories in cache:`);
        
        memories.forEach(mem => {
          const importance = (mem.importance * 100).toFixed(0) + '%';
          this.terminal.innerHTML += `<div class="terminal-line"><span class="memory-id">${mem.id}</span> <span class="memory-level">[${mem.level}]</span> <span class="memory-importance">${importance}</span> ${mem.text}</div>`;
        });
        
        this.scrollToBottom();
      }, 800);
    } else if (subcommand === 'search') {
      const query = args.slice(1).join(' ');
      
      if (!query) {
        this.logError('Missing search query. Usage: memory search <query>');
        return;
      }
      
      this.logAgent('MEMORY', `Searching memories for: "${query}"...`);
      
      setTimeout(() => {
        // This would normally be a real search through the memory system
        const results = [
          { id: 'mem-002', text: 'Discussed integration with Claude 3.7', level: 'L1', importance: 0.92, relevance: 0.87 }
        ];
        
        if (results.length) {
          this.logAgent('MEMORY', `Found ${results.length} results:`);
          
          results.forEach(mem => {
            const relevance = (mem.relevance * 100).toFixed(0) + '%';
            this.terminal.innerHTML += `<div class="terminal-line"><span class="memory-id">${mem.id}</span> <span class="memory-level">[${mem.level}]</span> <span class="memory-relevance">${relevance}</span> ${mem.text}</div>`;
          });
        } else {
          this.logAgent('MEMORY', `No results found for: "${query}"`);
        }
        
        this.scrollToBottom();
      }, 1000);
    } else if (subcommand === 'stats') {
      this.logAgent('MEMORY', 'Memory System Statistics:');
      
      const stats = [
        { name: 'L1 Cache Utilization', value: '67%' },
        { name: 'L2 Cache Utilization', value: '41%' },
        { name: 'L3 Cache Utilization', value: '23%' },
        { name: 'Total Memories', value: '842' },
        { name: 'Avg. Importance', value: '0.72' },
        { name: 'Last Cascade', value: '47 min ago' }
      ];
      
      stats.forEach(({ name, value }) => {
        this.terminal.innerHTML += `<div class="terminal-line"><span class="terminal-stat-name">${name.padEnd(25)}</span><span class="terminal-stat-value">${value}</span></div>`;
      });
      
      this.scrollToBottom();
    } else {
      this.logError(`Unknown memory subcommand: ${subcommand}. Valid: list, search, stats`);
    }
  }
  
  ipfsCommand(args) {
    if (!args.length) {
      this.logError('Invalid IPFS command. Usage: ipfs status | ipfs sync');
      return;
    }
    
    const subcommand = args[0];
    
    if (subcommand === 'status') {
      this.logAgent('IPFS', 'IPFS Connection Status:');
      
      const stats = [
        { name: 'Connected Peers', value: '32' },
        { name: 'Stored Memories', value: '2.4K' },
        { name: 'Total Storage', value: '128 MB' },
        { name: 'Gateway Status', value: 'Online' },
        { name: 'Network Latency', value: '215ms' }
      ];
      
      stats.forEach(({ name, value }) => {
        this.terminal.innerHTML += `<div class="terminal-line"><span class="terminal-stat-name">${name.padEnd(20)}</span><span class="terminal-stat-value">${value}</span></div>`;
      });
      
      this.scrollToBottom();
    } else if (subcommand === 'sync') {
      this.logAgent('IPFS', 'Syncing with IPFS network...');
      
      // Simulate a few progress updates
      setTimeout(() => this.logAgent('IPFS', 'Connecting to peers...'), 500);
      setTimeout(() => this.logAgent('IPFS', 'Indexing content...'), 1500);
      setTimeout(() => this.logAgent('IPFS', 'Verifying memory hashes...'), 2500);
      setTimeout(() => this.logAgent('IPFS', 'Sync complete: 128 memories synced.'), 3500);
    } else {
      this.logError(`Unknown IPFS subcommand: ${subcommand}. Valid: status, sync`);
    }
  }
  
  runBenchmark(args) {
    const type = args[0] || 'memory';
    
    this.logAgent('SYSTEM', `Starting ${type} benchmark...`);
    
    // Simulate benchmark progress
    setTimeout(() => this.logAgent('SYSTEM', 'Initializing benchmark environment...'), 500);
    setTimeout(() => this.logAgent('SYSTEM', 'Generating test data...'), 1500);
    setTimeout(() => this.logAgent('SYSTEM', 'Running memory operations...'), 2500);
    
    setTimeout(() => {
      this.logAgent('SYSTEM', 'Benchmark complete. Results:');
      
      const results = [
        { name: 'Memory Storage (1 item)', value: '0.8 ms' },
        { name: 'Memory Storage (10 items)', value: '7.2 ms' },
        { name: 'Memory Storage (100 items)', value: '68.5 ms' },
        { name: 'Memory Retrieval (exact)', value: '1.2 ms' },
        { name: 'Memory Retrieval (semantic)', value: '12.7 ms' },
        { name: 'Context Building', value: '18.3 ms' }
      ];
      
      results.forEach(({ name, value }) => {
        this.terminal.innerHTML += `<div class="terminal-line"><span class="terminal-stat-name">${name.padEnd(30)}</span><span class="terminal-stat-value">${value}</span></div>`;
      });
      
      this.scrollToBottom();
    }, 4000);
  }
  
  triggerCascade(args) {
    const force = args[0] === 'force';
    
    if (force) {
      this.logAgent('MEMORY', 'Forcing memory cascade operation...');
    } else {
      this.logAgent('MEMORY', 'Checking if cascade is needed...');
      setTimeout(() => {
        this.logAgent('MEMORY', 'L1 cache at 67% capacity. No cascade required yet.');
        return;
      }, 500);
      return;
    }
    
    // Simulate cascade process
    setTimeout(() => this.logAgent('MEMORY', 'Analyzing memory importance...'), 800);
    setTimeout(() => this.logAgent('MEMORY', 'Processing L1 cache (842 memories)...'), 1600);
    setTimeout(() => this.logAgent('MEMORY', 'Identified 156 memories for cascade...'), 2400);
    setTimeout(() => this.logAgent('MEMORY', 'Compressing memories for L2 storage...'), 3200);
    
    setTimeout(() => {
      this.logAgent('MEMORY', 'Cascade complete: 156 memories processed.');
      this.logAgent('MEMORY', 'L1: 686 memories, L2: 423 memories, L3: 255 memories');
    }, 4000);
  }
  
  tokenCommand(args) {
    if (!args.length) {
      this.logError('Invalid token command. Usage: token balance | token transactions');
      return;
    }
    
    const subcommand = args[0];
    
    if (subcommand === 'balance') {
      this.logAgent('SYSTEM', 'Token Balance:');
      
      const balances = [
        { token: 'VOTai', balance: '8,427.00', value: '$16,854.00' },
        { token: 'ETH', balance: '1.25', value: '$3,750.00' }
      ];
      
      balances.forEach(({ token, balance, value }) => {
        this.terminal.innerHTML += `<div class="terminal-line"><span class="token-name">${token.padEnd(10)}</span><span class="token-balance">${balance.padEnd(15)}</span><span class="token-value">${value}</span></div>`;
      });
      
      this.scrollToBottom();
    } else if (subcommand === 'transactions') {
      this.logAgent('SYSTEM', 'Recent Token Transactions:');
      
      const txns = [
        { type: 'REWARD', amount: '+42.50 VOT', timestamp: '10:27:15', desc: 'Memory provider reward' },
        { type: 'SPEND', amount: '-15.00 VOT', timestamp: '09:42:08', desc: 'AI processing fee' },
        { type: 'REWARD', amount: '+35.75 VOT', timestamp: '08:15:22', desc: 'Memory provider reward' }
      ];
      
      txns.forEach(({ type, amount, timestamp, desc }) => {
        const cls = type === 'REWARD' ? 'token-reward' : 'token-spend';
        this.terminal.innerHTML += `<div class="terminal-line"><span class="token-time">[${timestamp}]</span><span class="${cls}">${amount.padEnd(15)}</span>${desc}</div>`;
      });
      
      this.scrollToBottom();
    } else {
      this.logError(`Unknown token subcommand: ${subcommand}. Valid: balance, transactions`);
    }
  }
  
  showStatus() {
    this.logSystem('System Status:');
    
    const componentsStatus = [
      { name: 'CascadingMemoryCache', status: 'ONLINE', desc: '3 levels, 67% capacity' },
      { name: 'EpisodicMemoryManager', status: 'ONLINE', desc: '842 memories stored' },
      { name: 'IPFS Storage', status: 'ONLINE', desc: '32 peers connected' },
      { name: 'ZK Verification', status: 'ONLINE', desc: '42 verifications/min' },
      { name: 'Claude 3.7 API', status: 'ONLINE', desc: '200K context window' },
      { name: 'Web3 Provider', status: 'ONLINE', desc: 'Connected to Mainnet' }
    ];
    
    componentsStatus.forEach(({ name, status, desc }) => {
      const statusClass = status === 'ONLINE' ? 'status-online' : 'status-offline';
      this.terminal.innerHTML += `<div class="terminal-line"><span class="component-name">${name.padEnd(25)}</span><span class="${statusClass}">${status.padEnd(10)}</span>${desc}</div>`;
    });
    
    this.scrollToBottom();
  }
  
  // Memory selection event handler
  handleMemorySelection(event) {
    const memory = event.detail;
    
    if (!memory) return;
    
    this.logAgent('MEMORY', `Displaying memory ${memory.id}:`);
    
    // Create a formatted display of the memory
    const formattedMemory = [
      `ID: ${memory.id}`,
      `Level: ${memory.level}`,
      `Importance: ${(memory.importance * 100).toFixed(0)}%`,
      `Tokens: ${memory.tokenCount}`,
      `Timestamp: ${new Date(memory.timestamp).toLocaleString()}`,
      `Text: ${memory.text}`
    ];
    
    formattedMemory.forEach(line => {
      this.terminal.innerHTML += `<div class="terminal-line memory-detail">${line}</div>`;
    });
    
    this.scrollToBottom();
  }
  
  // Logging methods
  
  logCommand(command) {
    const timestamp = this.getTimestamp();
    this.terminal.innerHTML += `<div class="terminal-line"><span class="terminal-prompt">${this.options.promptText}</span> <span class="terminal-user-command">${command}</span></div>`;
    this.scrollToBottom();
  }
  
  logSystem(message) {
    this.logMessage('SYSTEM', message);
  }
  
  logError(message) {
    this.logMessage('ERROR', message);
  }
  
  logAgent(agentName, message) {
    this.logMessage(agentName, message);
  }
  
  logMessage(agentName, message) {
    const agent = this.agents[agentName] || this.agents.SYSTEM;
    const timestamp = this.getTimestamp();
    
    this.terminal.innerHTML += `<div class="terminal-line">
      <span class="terminal-time">[${timestamp}]</span> 
      <span class="terminal-agent" style="color: ${agent.color}">${agent.icon} ${agent.name}:</span> 
      <span class="terminal-message">${message}</span>
    </div>`;
    
    this.scrollToBottom();
  }
  
  // Helper methods
  
  getTimestamp() {
    const now = new Date();
    return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
  }
  
  scrollToBottom() {
    this.terminal.scrollTop = this.terminal.scrollHeight;
  }
  
  registerAgent(id, config) {
    this.agents[id] = config;
  }
  
  // Public API
  
  /**
   * Add a message from an agent to the terminal
   * @param {string} agentId - The ID of the agent
   * @param {string} message - The message to display
   */
  addAgentMessage(agentId, message) {
    if (agentId in this.agents) {
      this.logAgent(agentId, message);
      return true;
    }
    return false;
  }
  
  /**
   * Register a new agent with the terminal
   * @param {string} id - Unique identifier for the agent
   * @param {object} config - Agent configuration {name, color, icon}
   */
  addAgent(id, config) {
    this.registerAgent(id, config);
    return true;
  }
  
  /**
   * Clear the terminal
   */
  clear() {
    this.clearTerminal();
  }
  
  /**
   * Get all registered agents
   * @returns {Array} - Array of agent IDs
   */
  getAgents() {
    return Object.keys(this.agents);
  }
}

// Initialize terminal when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Create and export the terminal instance
  window.terminalInterface = new TerminalInterface();
});

// Terminal CSS Styles (for reference)
/*
.terminal-line {
  margin-bottom: 4px;
  white-space: pre-wrap;
  word-break: break-word;
}

.terminal-time {
  color: var(--text-secondary);
  margin-right: 8px;
}

.terminal-agent {
  font-weight: bold;
  margin-right: 8px;
}

.terminal-message {
  color: var(--text-primary);
}

.terminal-user-command {
  color: var(--secondary);
  font-weight: bold;
}

.terminal-prompt {
  color: var(--secondary);
  margin-right: 5px;
}

.terminal-command-help {
  color: var(--secondary);
  font-weight: bold;
}

.terminal-help-desc {
  color: var(--text-secondary);
}

.terminal-stat-name {
  color: var(--text-secondary);
}

.terminal-stat-value {
  color: var(--text-bright);
  font-weight: bold;
}

.memory-id {
  color: var(--primary);
  font-weight: bold;
  margin-right: 5px;
}

.memory-level {
  color: var(--secondary);
  margin-right: 5px;
}

.memory-importance, .memory-relevance {
  color: var(--accent);
  margin-right: 5px;
}

.memory-detail {
  color: var(--text-secondary);
  margin-left: 15px;
}

.token-reward {
  color: var(--status-success);
  font-weight: bold;
}

.token-spend {
  color: var(--status-error);
  font-weight: bold;
}

.token-time {
  color: var(--text-secondary);
  margin-right: 8px;
}

.component-name {
  color: var(--text-secondary);
}

.status-online {
  color: var(--status-success);
  font-weight: bold;
}

.status-offline {
  color: var(--status-error);
  font-weight: bold;
}

.terminal-info {
  color: var(--status-info);
}

.terminal-success {
  color: var(--status-success);
}

.terminal-warning {
  color: var(--status-warning);
}

.terminal-error {
  color: var(--status-error);
}
*/ 