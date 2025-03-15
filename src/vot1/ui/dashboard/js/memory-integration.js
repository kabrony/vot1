/**
 * VOTai TRILOGY BRAIN - Memory System Integration
 * This script integrates the dashboard UI with the memory subsystem
 */

class MemoryIntegration {
  constructor() {
    this.memoryAPI = null;
    this.ipfsConnected = false;
    this.zkEnabled = false;
    this.tokenBalance = 0;
    this.agentRegistry = {};
    this.currentMemoryNodes = [];
    
    // Operation stats
    this.stats = {
      totalMemories: 0,
      retrievalCount: 0,
      storageCount: 0,
      verificationCount: 0,
      successRate: 0
    };
    
    // Connect to local memory system or mock if not available
    this.initializeAPI();
    
    // Set up periodic updates
    this.startMonitoring();
  }
  
  async initializeAPI() {
    try {
      // First try to load the real memory system
      if (window.ComposioMemoryBridge) {
        console.log('Using ComposioMemoryBridge for memory operations');
        this.memoryAPI = window.ComposioMemoryBridge;
        
        // Check connection
        const status = await this.memoryAPI.getStatus();
        this.updateConnectionStatus(status);
      } else {
        console.log('Memory system not found, using mock implementation');
        this.initializeMockAPI();
      }
      
      // Register with terminal
      if (window.terminalInterface) {
        window.terminalInterface.addAgent('MEMORY', {
          color: '#00ccff',
          icon: '🧠',
          name: 'Memory Manager'
        });
        
        window.terminalInterface.logAgent('MEMORY', 'Memory integration initialized');
      }
      
      // Load initial memory data
      await this.loadInitialData();
    } catch (error) {
      console.error('Error initializing memory API:', error);
      this.initializeMockAPI();
    }
  }
  
  initializeMockAPI() {
    // Create a mock API for development/testing
    this.memoryAPI = {
      // Mock memory storage
      memories: [],
      
      // Store a memory
      storeMemory: async (content, type, metadata) => {
        const memoryId = 'mem-' + Math.random().toString(36).substring(2, 15);
        const memory = {
          id: memoryId,
          content,
          type,
          metadata: {
            ...metadata,
            timestamp: Date.now(),
            importance: Math.random()
          }
        };
        
        // Add to mock storage
        this.memoryAPI.memories.push(memory);
        this.stats.storageCount++;
        
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 300));
        
        return memoryId;
      },
      
      // Retrieve memories
      retrieveMemories: async (query, limit = 10) => {
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 500));
        
        this.stats.retrievalCount++;
        
        // Filter memories (very basic mock implementation)
        return this.memoryAPI.memories
          .filter(memory => !query || memory.content.includes(query))
          .slice(0, limit);
      },
      
      // Get memory by ID
      getMemory: async (id) => {
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 200));
        
        return this.memoryAPI.memories.find(memory => memory.id === id) || null;
      },
      
      // Delete memory
      deleteMemory: async (id) => {
        const initialLength = this.memoryAPI.memories.length;
        this.memoryAPI.memories = this.memoryAPI.memories.filter(memory => memory.id !== id);
        
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 200));
        
        return initialLength !== this.memoryAPI.memories.length;
      },
      
      // Get relationships
      getMemoryRelationships: async (id) => {
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // Generate random relationships
        const relationships = [];
        const memory = this.memoryAPI.memories.find(memory => memory.id === id);
        
        if (memory) {
          const relatedCount = Math.floor(Math.random() * 5) + 1;
          
          for (let i = 0; i < relatedCount; i++) {
            // Pick a random memory that's not the source
            const targetOptions = this.memoryAPI.memories.filter(m => m.id !== id);
            if (targetOptions.length === 0) continue;
            
            const targetMemory = targetOptions[Math.floor(Math.random() * targetOptions.length)];
            
            relationships.push({
              sourceId: id,
              targetId: targetMemory.id,
              type: ['related_to', 'precedes', 'follows', 'references'][Math.floor(Math.random() * 4)],
              strength: Math.random() * 0.7 + 0.3,
              metadata: {
                createdAt: Date.now()
              }
            });
          }
        }
        
        return relationships;
      },
      
      // Mock IPFS operations
      getIPFSStatus: async () => {
        await new Promise(resolve => setTimeout(resolve, 200));
        
        return {
          connected: Math.random() > 0.2, // 80% chance of being connected
          peers: Math.floor(Math.random() * 50) + 5,
          storedMemories: this.memoryAPI.memories.length,
          pinned: Math.floor(this.memoryAPI.memories.length * 0.8)
        };
      },
      
      // Mock ZK operations
      verifyMemory: async (id) => {
        await new Promise(resolve => setTimeout(resolve, 400));
        
        this.stats.verificationCount++;
        const success = Math.random() > 0.1; // 90% success rate
        
        if (success) {
          this.stats.successRate = (this.stats.successRate * (this.stats.verificationCount - 1) + 100) / this.stats.verificationCount;
        } else {
          this.stats.successRate = (this.stats.successRate * (this.stats.verificationCount - 1)) / this.stats.verificationCount;
        }
        
        return {
          verified: success,
          proof: success ? 'mock-zk-proof-' + Math.random().toString(36).substring(2, 15) : null,
          timestamp: Date.now()
        };
      },
      
      // Mock status
      getStatus: async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
        
        return {
          operational: true,
          memoryCount: this.memoryAPI.memories.length,
          ipfsConnected: Math.random() > 0.2,
          zkEnabled: Math.random() > 0.3,
          tokenBalance: Math.floor(Math.random() * 1000)
        };
      }
    };
  }
  
  async loadInitialData() {
    if (!window.dashboard) {
      console.warn('Dashboard not initialized, cannot load initial data');
      return;
    }
    
    try {
      // Get overall stats
      const status = await this.memoryAPI.getStatus();
      this.updateConnectionStatus(status);
      
      // Generate or load memories
      if (this.stats.totalMemories === 0) {
        await this.generateDemoMemories(50);
      }
      
      // Update 3D visualization
      await this.updateVisualization();
      
      console.log('Initial memory data loaded');
    } catch (error) {
      console.error('Error loading initial memory data:', error);
    }
  }
  
  async updateConnectionStatus(status) {
    this.ipfsConnected = status.ipfsConnected;
    this.zkEnabled = status.zkEnabled;
    this.tokenBalance = status.tokenBalance;
    this.stats.totalMemories = status.memoryCount;
    
    // Update UI
    this.updateStatusUI();
  }
  
  updateStatusUI() {
    // Update token balance
    const tokenBalanceEl = document.querySelector('.right-sidebar .status-item:nth-child(3) .value');
    if (tokenBalanceEl) {
      tokenBalanceEl.textContent = this.tokenBalance;
    }
    
    // Update IPFS status
    const ipfsStatusEl = document.querySelector('.ipfs-status .status-item:nth-child(3) .value');
    if (ipfsStatusEl) {
      ipfsStatusEl.className = 'value ' + (this.ipfsConnected ? 'status-online' : 'status-error');
      ipfsStatusEl.textContent = this.ipfsConnected ? 'ONLINE' : 'OFFLINE';
    }
    
    // Update stored memories
    const storedMemoriesEl = document.querySelector('.ipfs-status .status-item:nth-child(2) .value');
    if (storedMemoriesEl) {
      storedMemoriesEl.textContent = this.formatNumber(this.stats.totalMemories);
    }
    
    // Update ZK verifications chart if available
    if (window.dashboardCharts) {
      window.dashboardCharts.updateZKVerification(this.stats.successRate);
    }
  }
  
  async generateDemoMemories(count) {
    if (!this.memoryAPI) {
      console.error('Memory API not initialized');
      return;
    }
    
    if (window.terminalInterface) {
      window.terminalInterface.logAgent('MEMORY', `Generating ${count} demo memories...`);
    }
    
    // Memory content templates
    const templates = [
      "Analysis of {topic} shows correlation with {related_topic}",
      "User query about {topic} processed. Response generated with context from {related_topic}",
      "Long-term memory storage for {topic} concepts initiated",
      "Connection established between {topic} and {related_topic} with confidence {confidence}%",
      "Episodic memory of user interaction with {topic} saved",
      "System reflection on {topic} completed, insights documented",
      "Metadata for {topic} updated with new relevance score"
    ];
    
    // Topics for templates
    const topics = [
      "TRILOGY BRAIN", "neural networks", "memory storage", "knowledge graphs", 
      "tokenomics", "zero-knowledge proofs", "IPFS", "decentralized systems",
      "memory cascade", "temporal reasoning", "agent coordination", "semantic indexing"
    ];
    
    // Generate random memories
    const memoryPromises = [];
    for (let i = 0; i < count; i++) {
      // Select random template and topics
      const template = templates[Math.floor(Math.random() * templates.length)];
      const mainTopic = topics[Math.floor(Math.random() * topics.length)];
      const relatedTopic = topics[Math.floor(Math.random() * topics.length)];
      const confidence = Math.floor(Math.random() * 60) + 40; // 40-99%
      
      // Create content from template
      const content = template
        .replace('{topic}', mainTopic)
        .replace('{related_topic}', relatedTopic)
        .replace('{confidence}', confidence);
      
      // Determine memory type
      const types = ["general", "conversation", "concept", "reasoning", "procedure"];
      const type = types[Math.floor(Math.random() * types.length)];
      
      // Generate metadata
      const metadata = {
        importance: Math.random() * 0.7 + 0.3, // 0.3-1.0
        timestamp: Date.now() - Math.floor(Math.random() * 86400000 * 7), // Up to 7 days old
        topics: [mainTopic, relatedTopic],
        confidence: confidence / 100,
        tokenCount: Math.floor(Math.random() * 100) + 20
      };
      
      // Store memory
      const promise = this.memoryAPI.storeMemory(content, type, metadata);
      memoryPromises.push(promise);
    }
    
    // Wait for all memories to be stored
    await Promise.all(memoryPromises);
    
    if (window.terminalInterface) {
      window.terminalInterface.logAgent('MEMORY', `Generated ${count} demo memories successfully`);
    }
    
    // Update total count
    this.stats.totalMemories += count;
    this.updateStatusUI();
  }
  
  async updateVisualization() {
    if (!window.dashboard || !window.dashboard.memoryVisualization) {
      console.warn('Memory visualization not initialized, cannot update');
      return;
    }
    
    try {
      // Get recent memories
      const memories = await this.memoryAPI.retrieveMemories('', 50);
      this.currentMemoryNodes = [];
      
      // Convert to visualization format
      const memoryNodes = memories.map(memory => {
        // Determine cache level based on importance and age
        let cacheLevel = 'L3';
        const importance = memory.metadata?.importance || 0.5;
        const timestamp = memory.metadata?.timestamp || Date.now();
        const age = Date.now() - timestamp;
        
        if (importance > 0.7 || age < 86400000) { // High importance or less than 1 day old
          cacheLevel = 'L1';
        } else if (importance > 0.4 || age < 3 * 86400000) { // Medium importance or less than 3 days old
          cacheLevel = 'L2';
        }
        
        const node = {
          id: memory.id,
          text: memory.content,
          cacheLevel,
          importance,
          timestamp,
          tokenCount: memory.metadata?.tokenCount || 0
        };
        
        this.currentMemoryNodes.push(node);
        return node;
      });
      
      // Get relationships for selected memories
      const relationshipPromises = memories.slice(0, 10).map(memory => 
        this.memoryAPI.getMemoryRelationships(memory.id)
      );
      
      const allRelationships = await Promise.all(relationshipPromises);
      
      // Convert relationships to connections format for visualization
      const connections = [];
      
      allRelationships.forEach(relationships => {
        relationships.forEach(rel => {
          const connection = {
            sourceId: rel.sourceId,
            targetId: rel.targetId,
            strength: rel.strength
          };
          
          // Only add if both source and target are in our current nodes
          const sourceExists = memoryNodes.find(node => node.id === rel.sourceId);
          const targetExists = memoryNodes.find(node => node.id === rel.targetId);
          
          if (sourceExists && targetExists) {
            connections.push(connection);
          }
        });
      });
      
      // Add connections to memory nodes
      memoryNodes.forEach(node => {
        node.connections = connections.filter(conn => conn.sourceId === node.id);
      });
      
      // Update visualization
      window.dashboard.memoryVisualization.setData({ memories: memoryNodes });
      
      console.log(`Updated visualization with ${memoryNodes.length} nodes and ${connections.length} connections`);
    } catch (error) {
      console.error('Error updating visualization:', error);
    }
  }
  
  startMonitoring() {
    // Update visualization every 30 seconds
    setInterval(() => this.updateVisualization(), 30000);
    
    // Update status every 10 seconds
    setInterval(async () => {
      try {
        const status = await this.memoryAPI.getStatus();
        this.updateConnectionStatus(status);
      } catch (error) {
        console.error('Error updating status:', error);
      }
    }, 10000);
    
    // Simulate memory cascade operations
    setInterval(() => this.simulateMemoryOperations(), 5000);
  }
  
  async simulateMemoryOperations() {
    if (!window.terminalInterface) return;
    
    // 20% chance of a memory operation each interval
    if (Math.random() > 0.2) return;
    
    const operations = [
      'store',  // Store new memory
      'retrieve', // Retrieve existing memory
      'verify',  // ZK verification
      'consolidate' // Memory consolidation
    ];
    
    const operation = operations[Math.floor(Math.random() * operations.length)];
    
    try {
      switch (operation) {
        case 'store':
          // Store a new memory
          const content = `New observation recorded at ${new Date().toLocaleTimeString()}`;
          const memoryId = await this.memoryAPI.storeMemory(content, 'general', { importance: Math.random() });
          window.terminalInterface.logAgent('MEMORY', `Memory stored: ${memoryId}`);
          
          // Update stats
          this.stats.totalMemories++;
          this.updateStatusUI();
          
          // Update visualization on occasion
          if (Math.random() > 0.7) {
            this.updateVisualization();
          }
          break;
          
        case 'retrieve':
          // Retrieve a random memory
          if (this.currentMemoryNodes.length > 0) {
            const randomNode = this.currentMemoryNodes[Math.floor(Math.random() * this.currentMemoryNodes.length)];
            const memory = await this.memoryAPI.getMemory(randomNode.id);
            window.terminalInterface.logAgent('MEMORY', `Memory retrieved: ${randomNode.id}`);
            window.terminalInterface.logAgent('MEMORY', `Content: ${memory.content.substring(0, 50)}...`);
          }
          break;
          
        case 'verify':
          // ZK verification
          if (this.currentMemoryNodes.length > 0 && this.zkEnabled) {
            const randomNode = this.currentMemoryNodes[Math.floor(Math.random() * this.currentMemoryNodes.length)];
            const verification = await this.memoryAPI.verifyMemory(randomNode.id);
            
            if (verification.verified) {
              window.terminalInterface.logAgent('MEMORY', `ZK verification successful for memory: ${randomNode.id}`);
            } else {
              window.terminalInterface.logAgent('MEMORY', `ZK verification failed for memory: ${randomNode.id}`, 'error');
            }
          }
          break;
          
        case 'consolidate':
          // Memory consolidation
          window.terminalInterface.logAgent('MEMORY', 'Initiating memory consolidation process...');
          
          // Simulate consolidation time
          await new Promise(resolve => setTimeout(resolve, 1500));
          
          const consolidatedCount = Math.floor(Math.random() * 5) + 1;
          window.terminalInterface.logAgent('MEMORY', `Consolidated ${consolidatedCount} memories successfully`);
          break;
      }
    } catch (error) {
      console.error(`Error in memory operation ${operation}:`, error);
      window.terminalInterface.logAgent('MEMORY', `Error during ${operation} operation: ${error.message}`, 'error');
    }
  }
  
  // Helper to format numbers with K/M suffixes
  formatNumber(num) {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  }
  
  // Get a memory by ID (for external use)
  async getMemory(id) {
    if (!this.memoryAPI) return null;
    
    try {
      return await this.memoryAPI.getMemory(id);
    } catch (error) {
      console.error('Error retrieving memory:', error);
      return null;
    }
  }
  
  // Store a new memory (for external use)
  async storeMemory(content, type, metadata) {
    if (!this.memoryAPI) return null;
    
    try {
      const memoryId = await this.memoryAPI.storeMemory(content, type, metadata);
      this.stats.totalMemories++;
      this.stats.storageCount++;
      this.updateStatusUI();
      
      // Update visualization occasionally
      if (Math.random() > 0.7) {
        this.updateVisualization();
      }
      
      return memoryId;
    } catch (error) {
      console.error('Error storing memory:', error);
      return null;
    }
  }
  
  // Search memories (for external use)
  async searchMemories(query, limit = 10) {
    if (!this.memoryAPI) return [];
    
    try {
      const memories = await this.memoryAPI.retrieveMemories(query, limit);
      this.stats.retrievalCount++;
      return memories;
    } catch (error) {
      console.error('Error searching memories:', error);
      return [];
    }
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    window.memoryIntegration = new MemoryIntegration();
    console.log('Memory integration initialized');
    
    // Register memory commands with terminal if available
    if (window.terminalInterface) {
      window.terminalInterface.registerHandler('memory', (args) => {
        if (!args.length) {
          window.terminalInterface.logSystem('Memory command requires arguments. Try: memory help');
          return;
        }
        
        const subCommand = args[0];
        
        switch(subCommand) {
          case 'help':
            window.terminalInterface.logSystem('Memory Commands:');
            window.terminalInterface.logSystem('  memory status - Show memory system status');
            window.terminalInterface.logSystem('  memory search <query> - Search memories');
            window.terminalInterface.logSystem('  memory generate <count> - Generate demo memories');
            window.terminalInterface.logSystem('  memory refresh - Refresh visualization');
            window.terminalInterface.logSystem('  memory zk <id> - Verify memory with ZK proof');
            break;
            
          case 'status':
            window.terminalInterface.logAgent('MEMORY', `Total memories: ${window.memoryIntegration.stats.totalMemories}`);
            window.terminalInterface.logAgent('MEMORY', `IPFS connected: ${window.memoryIntegration.ipfsConnected ? 'Yes' : 'No'}`);
            window.terminalInterface.logAgent('MEMORY', `ZK enabled: ${window.memoryIntegration.zkEnabled ? 'Yes' : 'No'}`);
            window.terminalInterface.logAgent('MEMORY', `Token balance: ${window.memoryIntegration.tokenBalance}`);
            break;
            
          case 'search':
            const query = args.slice(1).join(' ');
            window.terminalInterface.logSystem(`Searching for: ${query}...`);
            
            window.memoryIntegration.searchMemories(query, 5)
              .then(results => {
                window.terminalInterface.logSystem(`Found ${results.length} results:`);
                results.forEach((memory, index) => {
                  window.terminalInterface.logAgent('MEMORY', `[${index+1}] ${memory.content.substring(0, 100)}...`);
                });
              });
            break;
            
          case 'generate':
            const count = parseInt(args[1]) || 10;
            window.terminalInterface.logSystem(`Generating ${count} memories...`);
            
            window.memoryIntegration.generateDemoMemories(count)
              .then(() => {
                window.terminalInterface.logSystem(`Generated ${count} memories successfully`);
              });
            break;
            
          case 'refresh':
            window.terminalInterface.logSystem('Refreshing memory visualization...');
            window.memoryIntegration.updateVisualization();
            break;
            
          case 'zk':
            const memoryId = args[1];
            if (!memoryId) {
              window.terminalInterface.logSystem('Please provide a memory ID');
              break;
            }
            
            window.terminalInterface.logSystem(`Verifying memory ${memoryId} with ZK proof...`);
            
            if (window.memoryIntegration.memoryAPI) {
              window.memoryIntegration.memoryAPI.verifyMemory(memoryId)
                .then(result => {
                  if (result.verified) {
                    window.terminalInterface.logAgent('MEMORY', `✓ Memory ${memoryId} verified successfully`);
                    window.terminalInterface.logAgent('MEMORY', `Proof: ${result.proof}`);
                  } else {
                    window.terminalInterface.logAgent('MEMORY', `✗ Memory ${memoryId} verification failed`, 'error');
                  }
                });
            }
            break;
            
          default:
            window.terminalInterface.logSystem(`Unknown memory command: ${subCommand}`);
            window.terminalInterface.logSystem('Try "memory help" for available commands');
        }
      });
    }
  }, 1000); // Give time for other components to initialize
}); 