/**
 * VOT1 Memory Graph Visualization
 * Force-directed graph visualization for TRILOGY BRAIN memory system
 */

const MemoryGraph = {
  // State
  graph: null,
  nodes: [],
  links: [],
  simulation: null,
  svg: null,
  zoom: null,
  width: 0,
  height: 0,
  nodeElements: null,
  linkElements: null,
  textElements: null,
  tooltipTimeout: null,
  initialized: false,
  
  // Config
  config: {
    nodeRadius: 10,
    linkDistance: 100,
    chargeStrength: -300,
    memoryColors: {
      'fact': '#00afff',
      'concept': '#ff00af',
      'code': '#00ff7f',
      'conversation': '#ffaa00',
      'reflection': '#9966ff',
      'default': '#7f7f7f'
    },
    tooltipDelay: 300
  },
  
  // Initialize memory graph
  async init() {
    console.log('Initializing memory graph...');
    
    // Get container
    const container = document.getElementById('memory-graph');
    if (!container) {
      console.error('Memory graph container not found');
      return false;
    }
    
    // Display loading state
    container.innerHTML = '<div class="loading-indicator"><div class="loading-spinner"></div><p>Loading memory graph...</p></div>';
    
    try {
      // Get container dimensions
      this.width = container.clientWidth;
      this.height = container.clientHeight || 400;
      
      // Create SVG if not already initialized
      if (!this.initialized) {
        // Create SVG element
        this.svg = d3.select('#memory-graph')
          .append('svg')
          .attr('width', this.width)
          .attr('height', this.height)
          .attr('class', 'memory-graph-svg');
        
        // Create zoom behavior
        this.zoom = d3.zoom()
          .scaleExtent([0.1, 4])
          .on('zoom', (event) => {
            this.svg.select('g').attr('transform', event.transform);
          });
        
        // Apply zoom to SVG
        this.svg.call(this.zoom);
        
        // Create main group for graph elements
        this.graph = this.svg.append('g');
        
        // Create arrow marker for directed links
        this.svg.append('defs').append('marker')
          .attr('id', 'arrowhead')
          .attr('viewBox', '-0 -5 10 10')
          .attr('refX', 20)
          .attr('refY', 0)
          .attr('orient', 'auto')
          .attr('markerWidth', 6)
          .attr('markerHeight', 6)
          .attr('xoverflow', 'visible')
          .append('svg:path')
          .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
          .attr('fill', '#999')
          .style('stroke', 'none');
        
        // Create tooltip
        if (!document.getElementById('graph-tooltip')) {
          const tooltip = document.createElement('div');
          tooltip.id = 'graph-tooltip';
          tooltip.className = 'graph-tooltip';
          document.body.appendChild(tooltip);
        }
        
        this.initialized = true;
      }
      
      // Fetch memory data
      await this.fetchMemoryData();
      
      return true;
    } catch (error) {
      console.error('Error initializing memory graph:', error);
      container.innerHTML = '<div class="error-message"><i class="fas fa-exclamation-triangle"></i> Failed to load memory graph</div>';
      return false;
    }
  },
  
  // Fetch memory data from API
  async fetchMemoryData() {
    try {
      const response = await fetch('/api/memory/graph');
      const data = await response.json();
      
      if (data.status === 'success') {
        this.processMemoryData(data.memory_graph);
      } else {
        console.error('Error fetching memory data:', data.error);
        Dashboard.showToast(`Error fetching memory data: ${data.error}`, 'error');
        throw new Error(data.error);
      }
    } catch (error) {
      console.error('Error fetching memory data:', error);
      Dashboard.showToast('Could not fetch memory data', 'error');
      
      // Use sample data for demonstration if fetching fails
      this.useSampleData();
    }
  },
  
  // Process memory data and create graph
  processMemoryData(data) {
    if (!data || !data.nodes || !data.links) {
      console.error('Invalid memory data format');
      this.useSampleData();
      return;
    }
    
    // Process nodes
    this.nodes = data.nodes.map(node => ({
      id: node.id,
      label: node.label || node.id,
      type: node.type || 'default',
      content: node.content || '',
      timestamp: node.timestamp,
      importance: node.importance || 1
    }));
    
    // Process links
    this.links = data.links.map(link => ({
      source: link.source,
      target: link.target,
      type: link.type || 'default',
      strength: link.strength || 1
    }));
    
    // Create visualization
    this.createVisualization();
  },
  
  // Use sample data for demonstration
  useSampleData() {
    // Sample nodes
    this.nodes = [
      { id: '1', label: 'Project Structure', type: 'concept', content: 'The overall structure of the VOT1 project', importance: 1.5 },
      { id: '2', label: 'File Visualization', type: 'fact', content: 'Component for visualizing file structure in 3D', importance: 1.2 },
      { id: '3', label: 'Dashboard', type: 'concept', content: 'Unified dashboard for all components', importance: 1.8 },
      { id: '4', label: 'MCP Integration', type: 'code', content: 'Integration with Modular Component Platform', importance: 1.3 },
      { id: '5', label: 'TRILOGY BRAIN', type: 'concept', content: 'Advanced memory system for AI', importance: 1.6 },
      { id: '6', label: 'User Requirements', type: 'conversation', content: 'Discussion about user requirements', importance: 1.1 },
      { id: '7', label: 'Component Design', type: 'reflection', content: 'Thoughts on component design', importance: 1.2 }
    ];
    
    // Sample links
    this.links = [
      { source: '1', target: '2', type: 'contains', strength: 1.2 },
      { source: '1', target: '3', type: 'contains', strength: 1.5 },
      { source: '1', target: '4', type: 'contains', strength: 1.1 },
      { source: '3', target: '2', type: 'uses', strength: 0.8 },
      { source: '3', target: '4', type: 'uses', strength: 0.9 },
      { source: '3', target: '5', type: 'integrates', strength: 1.3 },
      { source: '5', target: '7', type: 'contains', strength: 0.7 },
      { source: '6', target: '3', type: 'influences', strength: 0.6 },
      { source: '6', target: '7', type: 'influences', strength: 0.5 }
    ];
    
    // Create visualization
    this.createVisualization();
  },
  
  // Create force-directed graph visualization
  createVisualization() {
    // Clear existing elements
    this.graph.selectAll('*').remove();
    
    // Create force simulation
    this.simulation = d3.forceSimulation(this.nodes)
      .force('link', d3.forceLink(this.links).id(d => d.id).distance(d => this.config.linkDistance / (d.strength || 1)))
      .force('charge', d3.forceManyBody().strength(this.config.chargeStrength))
      .force('center', d3.forceCenter(this.width / 2, this.height / 2))
      .force('collision', d3.forceCollide().radius(d => this.config.nodeRadius * (d.importance || 1) + 5));
    
    // Create links
    this.linkElements = this.graph.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(this.links)
      .enter().append('line')
      .attr('class', 'link')
      .attr('stroke-width', d => Math.sqrt(d.strength || 1) * 2)
      .attr('marker-end', 'url(#arrowhead)');
    
    // Create nodes
    this.nodeElements = this.graph.append('g')
      .attr('class', 'nodes')
      .selectAll('circle')
      .data(this.nodes)
      .enter().append('circle')
      .attr('class', 'node')
      .attr('r', d => this.config.nodeRadius * (d.importance || 1))
      .attr('fill', d => this.getNodeColor(d.type))
      .call(this.dragBehavior())
      .on('mouseover', this.handleNodeMouseOver.bind(this))
      .on('mouseout', this.handleNodeMouseOut.bind(this))
      .on('click', this.handleNodeClick.bind(this));
    
    // Create node labels
    this.textElements = this.graph.append('g')
      .attr('class', 'labels')
      .selectAll('text')
      .data(this.nodes)
      .enter().append('text')
      .text(d => d.label)
      .attr('class', 'node-label')
      .attr('dx', 15)
      .attr('dy', 4);
    
    // Set up tick function
    this.simulation.on('tick', () => {
      this.linkElements
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      
      this.nodeElements
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);
      
      this.textElements
        .attr('x', d => d.x)
        .attr('y', d => d.y);
    });
    
    // Center and fit graph
    this.centerGraph();
  },
  
  // Create drag behavior for nodes
  dragBehavior() {
    return d3.drag()
      .on('start', (event, d) => {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });
  },
  
  // Get color for node based on type
  getNodeColor(type) {
    return this.config.memoryColors[type] || this.config.memoryColors.default;
  },
  
  // Handle node mouse over
  handleNodeMouseOver(event, d) {
    // Clear any existing timeout
    if (this.tooltipTimeout) {
      clearTimeout(this.tooltipTimeout);
    }
    
    // Set timeout for tooltip
    this.tooltipTimeout = setTimeout(() => {
      const tooltip = d3.select('#graph-tooltip');
      
      // Format content
      const formattedContent = d.content.length > 150 
        ? d.content.substring(0, 150) + '...' 
        : d.content;
      
      // Set tooltip content
      tooltip.html(`
        <div class="tooltip-header">
          <span class="tooltip-title">${d.label}</span>
          <span class="tooltip-type ${d.type}">${d.type}</span>
        </div>
        <div class="tooltip-content">${formattedContent}</div>
        ${d.timestamp ? `<div class="tooltip-footer">Created: ${new Date(d.timestamp).toLocaleString()}</div>` : ''}
      `)
      .style('left', (event.pageX + 10) + 'px')
      .style('top', (event.pageY - 28) + 'px')
      .style('opacity', 1)
      .style('display', 'block');
      
      // Highlight connected nodes and links
      this.highlightConnections(d.id);
    }, this.config.tooltipDelay);
  },
  
  // Handle node mouse out
  handleNodeMouseOut() {
    // Clear timeout
    if (this.tooltipTimeout) {
      clearTimeout(this.tooltipTimeout);
      this.tooltipTimeout = null;
    }
    
    // Hide tooltip
    d3.select('#graph-tooltip')
      .style('opacity', 0)
      .style('display', 'none');
    
    // Reset highlights
    this.resetHighlights();
  },
  
  // Handle node click
  handleNodeClick(event, d) {
    // Show memory details
    this.showMemoryDetails(d);
    
    // Prevent event from propagating
    event.stopPropagation();
  },
  
  // Highlight connections for a node
  highlightConnections(nodeId) {
    // Dim all nodes and links
    this.nodeElements.attr('opacity', 0.3);
    this.linkElements.attr('opacity', 0.1);
    this.textElements.attr('opacity', 0.3);
    
    // Get connected links
    const connectedLinks = this.links.filter(link => 
      link.source.id === nodeId || link.target.id === nodeId
    );
    
    // Get connected nodes
    const connectedNodeIds = new Set([nodeId]);
    connectedLinks.forEach(link => {
      connectedNodeIds.add(link.source.id);
      connectedNodeIds.add(link.target.id);
    });
    
    // Highlight connected nodes
    this.nodeElements
      .filter(d => connectedNodeIds.has(d.id))
      .attr('opacity', 1);
    
    // Highlight connected links
    this.linkElements
      .filter(d => d.source.id === nodeId || d.target.id === nodeId)
      .attr('opacity', 1);
    
    // Highlight connected labels
    this.textElements
      .filter(d => connectedNodeIds.has(d.id))
      .attr('opacity', 1);
  },
  
  // Reset highlights
  resetHighlights() {
    this.nodeElements.attr('opacity', 1);
    this.linkElements.attr('opacity', 1);
    this.textElements.attr('opacity', 1);
  },
  
  // Show memory details
  showMemoryDetails(memory) {
    // Get recent memories container
    const memoryContainer = document.getElementById('recent-memories');
    if (!memoryContainer) return;
    
    // Add memory item
    const memoryItem = document.createElement('div');
    memoryItem.className = 'memory-item';
    memoryItem.innerHTML = `
      <div class="memory-item-header">
        <span class="memory-item-type ${memory.type}">${memory.type}</span>
        <span class="memory-item-time">${memory.timestamp ? new Date(memory.timestamp).toLocaleString() : 'Unknown'}</span>
      </div>
      <div class="memory-item-content">
        <h4>${memory.label}</h4>
        <p>${memory.content}</p>
      </div>
    `;
    
    // Insert at top
    if (memoryContainer.firstChild) {
      memoryContainer.insertBefore(memoryItem, memoryContainer.firstChild);
    } else {
      memoryContainer.appendChild(memoryItem);
    }
    
    // Limit to 5 memories
    while (memoryContainer.children.length > 5) {
      memoryContainer.removeChild(memoryContainer.lastChild);
    }
    
    // Highlight item
    memoryItem.classList.add('highlight');
    setTimeout(() => {
      memoryItem.classList.remove('highlight');
    }, 2000);
  },
  
  // Center and fit graph
  centerGraph() {
    if (!this.svg || !this.graph) return;
    
    // Reset zoom
    this.svg.transition()
      .duration(750)
      .call(this.zoom.transform, d3.zoomIdentity);
  },
  
  // Resize graph
  resize() {
    // Get container
    const container = document.getElementById('memory-graph');
    if (!container || !this.svg) return;
    
    // Get new dimensions
    this.width = container.clientWidth;
    this.height = container.clientHeight;
    
    // Update SVG dimensions
    this.svg
      .attr('width', this.width)
      .attr('height', this.height);
    
    // Update simulation
    if (this.simulation) {
      this.simulation
        .force('center', d3.forceCenter(this.width / 2, this.height / 2))
        .restart();
    }
  }
};

// Register initialization on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  // Initialize only when dashboard or memory panel is active
  if (Dashboard && (Dashboard.activePanel === 'dashboard-panel' || Dashboard.activePanel === 'memory-panel')) {
    MemoryGraph.init();
  }
  
  // Add resize listener
  window.addEventListener('resize', () => {
    MemoryGraph.resize();
  });
}); 