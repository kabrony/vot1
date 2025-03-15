/**
 * VOTai TRILOGY BRAIN - Composio Memory Adapter
 * 
 * This module connects the THREE.js visualization with the Composio toolbox,
 * enabling dynamic data retrieval and cognitive thinking capabilities for
 * the memory visualization system.
 */

class ComposioMemoryAdapter {
  constructor(options = {}) {
    this.options = Object.assign({
      useLocalCache: true,
      cacheTTL: 60000,  // 1 minute
      batchSize: 50,    // Process memory in batches to avoid overloading
      maxRequests: 5,   // Maximum concurrent requests
      debugMode: false
    }, options);

    // State tracking
    this.initialized = false;
    this.activeRequests = 0;
    this.requestQueue = [];
    this.memoryCache = new Map();
    
    // Reference to visualization
    this.visualization = null;
    
    // Statistics
    this.stats = {
      requestsTotal: 0,
      requestsSuccess: 0,
      requestsFailed: 0,
      cacheHits: 0,
      cacheMisses: 0,
      lastRefresh: null
    };
    
    // Initialize if Composio is available
    this._init();
  }
  
  /**
   * Initialize the adapter
   * @private
   */
  _init() {
    if (typeof window.composioClient === 'undefined') {
      if (this.options.debugMode) {
        console.warn('Composio client not available. Memory adapter will use mock data.');
      }
      this._initMockMode();
      return;
    }
    
    try {
      this.composioClient = window.composioClient;
      this.initialized = true;
      
      if (this.options.debugMode) {
        console.log('ComposioMemoryAdapter initialized successfully');
      }
      
      // Clean cache periodically
      if (this.options.useLocalCache) {
        setInterval(() => this._cleanCache(), this.options.cacheTTL * 2);
      }
    } catch (error) {
      console.error('Failed to initialize ComposioMemoryAdapter:', error);
      this._initMockMode();
    }
  }
  
  /**
   * Initialize mock mode for development/testing
   * @private
   */
  _initMockMode() {
    this.useMockData = true;
    this.initialized = true;
    
    if (this.options.debugMode) {
      console.log('ComposioMemoryAdapter initialized in mock mode');
    }
  }
  
  /**
   * Connect to a visualization instance
   * @param {EnhancedMemoryVisualization} visualization - The visualization instance
   */
  connectVisualization(visualization) {
    this.visualization = visualization;
    
    if (this.visualization) {
      // Replace the visualization's fetchMemoryDataFromComposio method
      const originalFetch = this.visualization.fetchMemoryDataFromComposio.bind(this.visualization);
      this.visualization.fetchMemoryDataFromComposio = async () => {
        // Use our method instead
        const result = await this.getMemoryNetwork(
          this.visualization.currentDetailLevel,
          this.visualization.options.progressiveLevels.find(
            l => l.detail === this.visualization.currentDetailLevel
          ).maxNodes
        );
        
        // Update the visualization with the result
        if (result && result.success) {
          this.visualization.updateMemoryVisualization(result.data);
        }
      };
      
      // Also replace the memory details fetching
      const originalFetchDetails = this.visualization.fetchMemoryDetailsFromComposio.bind(this.visualization);
      this.visualization.fetchMemoryDetailsFromComposio = async (memoryId) => {
        const result = await this.getMemoryDetails(memoryId);
        
        if (result && result.success) {
          this.visualization.showDetailedMemoryInTerminal(result.data);
        }
      };
      
      if (this.options.debugMode) {
        console.log('ComposioMemoryAdapter connected to visualization');
      }
    }
  }
  
  /**
   * Clean expired items from cache
   * @private
   */
  _cleanCache() {
    if (!this.options.useLocalCache) return;
    
    const now = Date.now();
    const expiredKeys = [];
    
    this.memoryCache.forEach((value, key) => {
      if (now - value.timestamp > this.options.cacheTTL) {
        expiredKeys.push(key);
      }
    });
    
    expiredKeys.forEach(key => this.memoryCache.delete(key));
    
    if (this.options.debugMode && expiredKeys.length > 0) {
      console.log(`Cleaned ${expiredKeys.length} items from cache`);
    }
  }
  
  /**
   * Get a memory network for visualization
   * @param {string} detailLevel - Level of detail (low, medium, high)
   * @param {number} maxNodes - Maximum number of nodes to retrieve
   * @returns {Promise<Object>} - Result with success flag and data
   */
  async getMemoryNetwork(detailLevel = 'low', maxNodes = 500) {
    const cacheKey = `network_${detailLevel}_${maxNodes}`;
    
    // Check cache first
    if (this.options.useLocalCache && this.memoryCache.has(cacheKey)) {
      const cached = this.memoryCache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.options.cacheTTL) {
        this.stats.cacheHits++;
        return {
          success: true,
          data: cached.data,
          fromCache: true
        };
      }
    }
    
    this.stats.cacheMisses++;
    
    if (!this.initialized) {
      return { success: false, error: 'Adapter not initialized' };
    }
    
    if (this.useMockData) {
      return this._getMockMemoryNetwork(detailLevel, maxNodes);
    }
    
    // Enforce concurrent request limit
    if (this.activeRequests >= this.options.maxRequests) {
      return new Promise((resolve) => {
        this.requestQueue.push(() => {
          this._getMemoryNetworkFromComposio(detailLevel, maxNodes).then(resolve);
        });
      });
    }
    
    return this._getMemoryNetworkFromComposio(detailLevel, maxNodes);
  }
  
  /**
   * Get memory network data from Composio
   * @private
   */
  async _getMemoryNetworkFromComposio(detailLevel, maxNodes) {
    this.activeRequests++;
    this.stats.requestsTotal++;
    
    try {
      const params = {
        detail_level: detailLevel,
        max_nodes: maxNodes,
        use_cognitive_thinking: true, // Enable enhanced cognitive reasoning
        batch_size: this.options.batchSize
      };
      
      const result = await this.composioClient.executeTool('getMemoryNetwork', params);
      
      if (result && result.success) {
        this.stats.requestsSuccess++;
        
        // Cache the result
        if (this.options.useLocalCache) {
          this.memoryCache.set(`network_${detailLevel}_${maxNodes}`, {
            timestamp: Date.now(),
            data: result.data
          });
        }
        
        this.stats.lastRefresh = new Date().toISOString();
        
        return {
          success: true,
          data: result.data
        };
      } else {
        this.stats.requestsFailed++;
        return {
          success: false,
          error: result?.error || 'Unknown error'
        };
      }
    } catch (error) {
      this.stats.requestsFailed++;
      console.error('Error getting memory network from Composio:', error);
      return {
        success: false,
        error: error.message || 'Error getting memory network'
      };
    } finally {
      this.activeRequests--;
      
      // Process next request in queue
      if (this.requestQueue.length > 0 && this.activeRequests < this.options.maxRequests) {
        const nextRequest = this.requestQueue.shift();
        nextRequest();
      }
    }
  }
  
  /**
   * Get detailed information about a specific memory
   * @param {string} memoryId - ID of the memory
   * @returns {Promise<Object>} - Result with success flag and data
   */
  async getMemoryDetails(memoryId) {
    const cacheKey = `details_${memoryId}`;
    
    // Check cache first
    if (this.options.useLocalCache && this.memoryCache.has(cacheKey)) {
      const cached = this.memoryCache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.options.cacheTTL) {
        this.stats.cacheHits++;
        return {
          success: true,
          data: cached.data,
          fromCache: true
        };
      }
    }
    
    this.stats.cacheMisses++;
    
    if (!this.initialized) {
      return { success: false, error: 'Adapter not initialized' };
    }
    
    if (this.useMockData) {
      return this._getMockMemoryDetails(memoryId);
    }
    
    // Enforce concurrent request limit
    if (this.activeRequests >= this.options.maxRequests) {
      return new Promise((resolve) => {
        this.requestQueue.push(() => {
          this._getMemoryDetailsFromComposio(memoryId).then(resolve);
        });
      });
    }
    
    return this._getMemoryDetailsFromComposio(memoryId);
  }
  
  /**
   * Get memory details from Composio
   * @private
   */
  async _getMemoryDetailsFromComposio(memoryId) {
    this.activeRequests++;
    this.stats.requestsTotal++;
    
    try {
      const params = {
        memory_id: memoryId,
        include_relationships: true,
        include_embeddings: true,
        use_cognitive_reasoning: true // Enable deep thinking for this memory
      };
      
      const result = await this.composioClient.executeTool('getMemoryDetails', params);
      
      if (result && result.success) {
        this.stats.requestsSuccess++;
        
        // Cache the result
        if (this.options.useLocalCache) {
          this.memoryCache.set(`details_${memoryId}`, {
            timestamp: Date.now(),
            data: result.data
          });
        }
        
        return {
          success: true,
          data: result.data
        };
      } else {
        this.stats.requestsFailed++;
        return {
          success: false,
          error: result?.error || 'Unknown error'
        };
      }
    } catch (error) {
      this.stats.requestsFailed++;
      console.error('Error getting memory details from Composio:', error);
      return {
        success: false,
        error: error.message || 'Error getting memory details'
      };
    } finally {
      this.activeRequests--;
      
      // Process next request in queue
      if (this.requestQueue.length > 0 && this.activeRequests < this.options.maxRequests) {
        const nextRequest = this.requestQueue.shift();
        nextRequest();
      }
    }
  }
  
  /**
   * Perform cognitive thinking analysis on a memory
   * This uses Claude 3.7 Sonnet's hybrid thinking to analyze and enhance memory
   * @param {string} memoryId - ID of the memory
   * @param {string} analysisType - Type of analysis (standard, technical, creative, predictive)
   * @returns {Promise<Object>} - Result with success flag and analysis data
   */
  async performCognitiveThinking(memoryId, analysisType = 'standard') {
    if (!this.initialized) {
      return { success: false, error: 'Adapter not initialized' };
    }
    
    if (this.useMockData) {
      return this._getMockCognitiveThinking(memoryId, analysisType);
    }
    
    // Enforce concurrent request limit
    if (this.activeRequests >= this.options.maxRequests) {
      return new Promise((resolve) => {
        this.requestQueue.push(() => {
          this._performCognitiveThinkingViaComposio(memoryId, analysisType).then(resolve);
        });
      });
    }
    
    return this._performCognitiveThinkingViaComposio(memoryId, analysisType);
  }
  
  /**
   * Perform cognitive thinking analysis via Composio
   * @private
   */
  async _performCognitiveThinkingViaComposio(memoryId, analysisType) {
    this.activeRequests++;
    this.stats.requestsTotal++;
    
    try {
      const params = {
        memory_id: memoryId,
        analysis_type: analysisType,
        max_thinking_tokens: 8192, // Generous token limit for deep thinking
        include_related_memories: true
      };
      
      const result = await this.composioClient.executeTool('performCognitiveThinking', params);
      
      if (result && result.success) {
        this.stats.requestsSuccess++;
        return {
          success: true,
          data: result.data
        };
      } else {
        this.stats.requestsFailed++;
        return {
          success: false,
          error: result?.error || 'Unknown error'
        };
      }
    } catch (error) {
      this.stats.requestsFailed++;
      console.error('Error performing cognitive thinking via Composio:', error);
      return {
        success: false,
        error: error.message || 'Error performing cognitive thinking'
      };
    } finally {
      this.activeRequests--;
      
      // Process next request in queue
      if (this.requestQueue.length > 0 && this.activeRequests < this.options.maxRequests) {
        const nextRequest = this.requestQueue.shift();
        nextRequest();
      }
    }
  }
  
  /**
   * Get statistics about adapter usage
   * @returns {Object} - Statistics object
   */
  getStats() {
    return {
      ...this.stats,
      cacheSize: this.memoryCache.size,
      activeRequests: this.activeRequests,
      queueLength: this.requestQueue.length,
      initialized: this.initialized,
      useMockData: this.useMockData
    };
  }
  
  /**
   * Generate mock memory network data
   * @private
   */
  _getMockMemoryNetwork(detailLevel, maxNodes) {
    const nodeCount = Math.min(maxNodes, 100);
    const nodes = [];
    const links = [];
    
    // Generate nodes
    for (let i = 0; i < nodeCount; i++) {
      const id = `memory_${i}`;
      nodes.push({
        id,
        type: ['research', 'code', 'concept', 'reference', 'hybrid_thinking'][Math.floor(Math.random() * 5)],
        level: ['L1', 'L2', 'L3'][Math.floor(Math.random() * 3)],
        importance: Math.random(),
        title: `Mock Memory ${i}`,
        snippet: `This is a mock memory for testing the visualization with detail level ${detailLevel}`,
        created: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
        position: {
          x: (Math.random() - 0.5) * 200,
          y: (Math.random() - 0.5) * 200,
          z: (Math.random() - 0.5) * 200
        }
      });
    }
    
    // Generate links (connections between nodes)
    // Each node will have 1-3 connections
    for (let i = 0; i < nodeCount; i++) {
      const sourceId = `memory_${i}`;
      const linkCount = 1 + Math.floor(Math.random() * 3);
      
      for (let j = 0; j < linkCount; j++) {
        // Select a random target node that isn't the source
        let targetIndex;
        do {
          targetIndex = Math.floor(Math.random() * nodeCount);
        } while (targetIndex === i);
        
        const targetId = `memory_${targetIndex}`;
        
        links.push({
          source: sourceId,
          target: targetId,
          type: ['semantic', 'causal', 'temporal', 'hierarchical'][Math.floor(Math.random() * 4)],
          strength: Math.random()
        });
      }
    }
    
    return {
      success: true,
      data: {
        nodes,
        links
      }
    };
  }
  
  /**
   * Generate mock memory details
   * @private
   */
  _getMockMemoryDetails(memoryId) {
    // Extract index from memory ID if possible
    let index = 0;
    if (typeof memoryId === 'string') {
      const match = memoryId.match(/\d+/);
      if (match) {
        index = parseInt(match[0], 10);
      }
    }
    
    const memoryTypes = ['research', 'code', 'concept', 'reference', 'hybrid_thinking'];
    const memoryType = memoryTypes[index % memoryTypes.length];
    
    // Generate relationships
    const relationships = [];
    const relationshipCount = 2 + Math.floor(Math.random() * 4);
    
    for (let i = 0; i < relationshipCount; i++) {
      relationships.push({
        type: ['semantic', 'causal', 'temporal', 'hierarchical'][Math.floor(Math.random() * 4)],
        targetId: `memory_${Math.floor(Math.random() * 100)}`,
        strength: Math.random().toFixed(2)
      });
    }
    
    // Generate metadata based on memory type
    let metadata = {};
    
    switch (memoryType) {
      case 'research':
        metadata = {
          source: ['web', 'academic', 'internal'][Math.floor(Math.random() * 3)],
          confidence: (0.7 + Math.random() * 0.3).toFixed(2),
          keywords: ['ai', 'memory', 'visualization', 'cognitive', 'thinking'].slice(0, 2 + Math.floor(Math.random() * 3)).join(', ')
        };
        break;
      case 'code':
        metadata = {
          language: ['javascript', 'python', 'rust', 'typescript'][Math.floor(Math.random() * 4)],
          lines: 10 + Math.floor(Math.random() * 100),
          repository: 'github.com/vot1/trilogy-brain'
        };
        break;
      case 'concept':
        metadata = {
          domain: ['ai', 'visualization', 'memory', 'cognitive'][Math.floor(Math.random() * 4)],
          abstractness: (Math.random()).toFixed(2),
          connections: 5 + Math.floor(Math.random() * 20)
        };
        break;
      default:
        metadata = {
          category: ['general', 'technical', 'creative', 'analytical'][Math.floor(Math.random() * 4)],
          timestamp: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString()
        };
    }
    
    return {
      success: true,
      data: {
        id: memoryId,
        type: memoryType,
        title: `Detailed Memory ${index}`,
        content: `This is a detailed view of memory ${memoryId}. It contains more comprehensive information that would be displayed when a user clicks on a memory node in the visualization.`,
        created: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
        importance: (0.5 + Math.random() * 0.5).toFixed(2),
        level: ['L1', 'L2', 'L3'][Math.floor(Math.random() * 3)],
        relationships,
        metadata,
        embedding_visualization: '◉━━━━━━━━━━━━●━━━━━━━━━━━━◉'
      }
    };
  }
  
  /**
   * Generate mock cognitive thinking results
   * @private
   */
  _getMockCognitiveThinking(memoryId, analysisType) {
    const thinkingOutput = `Performing ${analysisType} analysis on memory ${memoryId}...
    
I need to consider multiple aspects of this memory to gain deeper insights.

First, let's consider the context in which this memory was formed. This appears to be a ${['research finding', 'code snippet', 'conceptual framework', 'reference material'][Math.floor(Math.random() * 4)]} related to memory visualization systems.

The implications of this memory are significant because:
1. It connects to our understanding of cognitive architectures
2. It demonstrates how information is represented in neural systems
3. It suggests new approaches for visualizing complex relationships

When we look at related memories, we see patterns of ${['hierarchical organization', 'temporal sequencing', 'semantic clustering', 'causal chains'][Math.floor(Math.random() * 4)]} which suggests that this memory is part of a broader knowledge structure.

The uncertainty in this analysis primarily stems from limited context about how this memory was formed and its relationship to external systems.`;

    const analysisOutput = `## ${analysisType.charAt(0).toUpperCase() + analysisType.slice(1)} Analysis of Memory ${memoryId}

This memory represents a key node in our understanding of ${['memory visualization', 'cognitive architectures', 'knowledge representation', 'information processing'][Math.floor(Math.random() * 4)]}.

**Key Insights:**
- The memory demonstrates ${['strong semantic connections', 'temporal coherence', 'hierarchical structure', 'causal relationships'][Math.floor(Math.random() * 4)]} with related concepts
- Its importance score of ${(0.5 + Math.random() * 0.5).toFixed(2)} indicates it has significant value in the knowledge graph
- The memory's creation timestamp suggests it ${Math.random() > 0.5 ? 'predates' : 'follows'} related memories, indicating a ${Math.random() > 0.5 ? 'foundational' : 'derivative'} role

**Potential Applications:**
- Enhancing visualization algorithms by incorporating these relationship patterns
- Improving memory recall by strengthening semantic connections
- Developing more nuanced importance metrics based on relationship types

**Recommendations:**
- Consider connecting this memory to ${['recent research findings', 'code implementations', 'conceptual frameworks', 'external references'][Math.floor(Math.random() * 4)]}
- Explore the ${['spatial', 'temporal', 'hierarchical', 'semantic'][Math.floor(Math.random() * 4)]} dimensions of this memory in greater detail
- Use this memory as a seed for generating related hypotheses`;

    return {
      success: true,
      data: {
        memoryId,
        analysisType,
        thinking: thinkingOutput,
        analysis: analysisOutput,
        timestamp: new Date().toISOString(),
        duration_ms: 500 + Math.floor(Math.random() * 2000)
      }
    };
  }
}

// Add to global scope
window.ComposioMemoryAdapter = ComposioMemoryAdapter; 