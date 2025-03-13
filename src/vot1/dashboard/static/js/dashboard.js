/**
 * VOT1 Dashboard Interface
 * 
 * This module provides the main interface for the VOT1 dashboard,
 * integrating the THREE.js visualization with UI controls and data display.
 */

import { initVisualization, updateMemoryGraph } from './three-visualization.js';

// Dashboard state
let dashboardState = {
    selectedNode: null,
    memoryFilter: 'all',
    timeRange: {
        start: null,
        end: null
    },
    searchQuery: '',
    isLoading: false
};

// Cache for memory data
let memoryCache = {
    lastFetched: null,
    data: null
};

/**
 * Initialize the dashboard
 */
function initDashboard() {
    // Initialize visualization
    initVisualization('visualization-container');
    
    // Set up event listeners
    setupEventListeners();
    
    // Load initial data
    loadMemoryData();
}

/**
 * Set up event listeners for dashboard controls
 */
function setupEventListeners() {
    // Memory type filter
    document.getElementById('memory-type-filter').addEventListener('change', function(e) {
        dashboardState.memoryFilter = e.target.value;
        applyFilters();
    });
    
    // Search input
    document.getElementById('memory-search').addEventListener('input', function(e) {
        dashboardState.searchQuery = e.target.value;
        applyFilters();
    });
    
    // Time range controls
    document.getElementById('time-range-start').addEventListener('change', function(e) {
        dashboardState.timeRange.start = e.target.value ? new Date(e.target.value) : null;
        applyFilters();
    });
    
    document.getElementById('time-range-end').addEventListener('change', function(e) {
        dashboardState.timeRange.end = e.target.value ? new Date(e.target.value) : null;
        applyFilters();
    });
    
    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', function() {
        loadMemoryData(true);
    });
}

/**
 * Load memory data from the API
 * @param {boolean} forceRefresh - Whether to force a refresh even if data is cached
 */
function loadMemoryData(forceRefresh = false) {
    // Check cache first
    const now = new Date();
    if (!forceRefresh && 
        memoryCache.lastFetched && 
        (now - memoryCache.lastFetched) < 60000) {
        // Use cached data if less than a minute old
        processMemoryData(memoryCache.data);
        return;
    }
    
    // Show loading state
    setLoadingState(true);
    
    // Fetch data from API
    fetch('/api/memory/graph')
        .then(response => response.json())
        .then(data => {
            // Cache the data
            memoryCache.data = data;
            memoryCache.lastFetched = now;
            
            // Process and display data
            processMemoryData(data);
            
            // Hide loading state
            setLoadingState(false);
        })
        .catch(error => {
            console.error('Error fetching memory data:', error);
            setLoadingState(false);
            showError('Failed to load memory data. Please try again.');
        });
}

/**
 * Process memory data and prepare it for visualization
 * @param {Object} data - Raw memory data from API
 */
function processMemoryData(data) {
    // Convert API data to visualization format
    const graphData = {
        nodes: data.memories.map(memory => ({
            id: memory.id,
            type: memory.type,
            content: memory.content,
            timestamp: new Date(memory.timestamp),
            size: calculateNodeSize(memory),
            // Additional metadata
            metadata: memory.metadata || {}
        })),
        links: data.connections.map(connection => ({
            source: connection.from,
            target: connection.to,
            strength: connection.strength || 0.5,
            type: connection.type || 'default'
        }))
    };
    
    // Apply filters
    const filteredData = filterGraphData(graphData);
    
    // Update visualization
    updateMemoryGraph(filteredData);
    
    // Update stats display
    updateStatsDisplay(graphData);
}

/**
 * Calculate node size based on memory importance
 * @param {Object} memory - Memory data
 * @returns {number} - Size factor (0-1)
 */
function calculateNodeSize(memory) {
    // Base size
    let size = 0.5;
    
    // Adjust based on number of connections
    const connectionCount = memory.connectionCount || 0;
    size += Math.min(connectionCount * 0.1, 0.3);
    
    // Adjust based on recency
    const ageInDays = (Date.now() - new Date(memory.timestamp).getTime()) / (1000 * 60 * 60 * 24);
    size += Math.max(0, 0.2 - (ageInDays * 0.01));
    
    return size;
}

/**
 * Apply filters to the graph data
 * @param {Object} graphData - Complete graph data
 * @returns {Object} - Filtered graph data
 */
function filterGraphData(graphData) {
    // Filter nodes
    const filteredNodes = graphData.nodes.filter(node => {
        // Filter by memory type
        if (dashboardState.memoryFilter !== 'all' && 
            node.type !== dashboardState.memoryFilter) {
            return false;
        }
        
        // Filter by time range
        if (dashboardState.timeRange.start && 
            node.timestamp < dashboardState.timeRange.start) {
            return false;
        }
        
        if (dashboardState.timeRange.end && 
            node.timestamp > dashboardState.timeRange.end) {
            return false;
        }
        
        // Filter by search query
        if (dashboardState.searchQuery && 
            !node.content.toLowerCase().includes(dashboardState.searchQuery.toLowerCase())) {
            return false;
        }
        
        return true;
    });
    
    // Get IDs of filtered nodes
    const filteredNodeIds = new Set(filteredNodes.map(node => node.id));
    
    // Filter links to only include connections between filtered nodes
    const filteredLinks = graphData.links.filter(link => 
        filteredNodeIds.has(link.source) && filteredNodeIds.has(link.target)
    );
    
    return {
        nodes: filteredNodes,
        links: filteredLinks
    };
}

/**
 * Apply current filters and update visualization
 */
function applyFilters() {
    if (!memoryCache.data) return;
    
    // Apply filters to cached data
    const filteredData = filterGraphData(processMemoryData(memoryCache.data));
    
    // Update visualization
    updateMemoryGraph(filteredData);
}

/**
 * Update stats display with memory information
 * @param {Object} graphData - Complete graph data
 */
function updateStatsDisplay(graphData) {
    const statsEl = document.getElementById('memory-stats');
    
    // Calculate stats
    const totalMemories = graphData.nodes.length;
    const memoryTypes = {};
    graphData.nodes.forEach(node => {
        memoryTypes[node.type] = (memoryTypes[node.type] || 0) + 1;
    });
    
    const totalConnections = graphData.links.length;
    
    // Create stats HTML
    let statsHtml = `
        <div class="stat-item">
            <span class="stat-label">Total Memories:</span>
            <span class="stat-value">${totalMemories}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Total Connections:</span>
            <span class="stat-value">${totalConnections}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Memory Types:</span>
            <div class="memory-type-breakdown">
    `;
    
    // Add memory type breakdown
    Object.keys(memoryTypes).forEach(type => {
        const percentage = Math.round((memoryTypes[type] / totalMemories) * 100);
        statsHtml += `
            <div class="type-bar-container">
                <span class="type-label">${type}:</span>
                <div class="type-bar" style="width: ${percentage}%; background-color: var(--color-${type})"></div>
                <span class="type-count">${memoryTypes[type]}</span>
            </div>
        `;
    });
    
    statsHtml += `
            </div>
        </div>
    `;
    
    // Update stats container
    statsEl.innerHTML = statsHtml;
}

/**
 * Set loading state for the dashboard
 * @param {boolean} isLoading - Whether the dashboard is loading
 */
function setLoadingState(isLoading) {
    dashboardState.isLoading = isLoading;
    
    const loadingEl = document.getElementById('loading-indicator');
    if (isLoading) {
        loadingEl.style.display = 'block';
    } else {
        loadingEl.style.display = 'none';
    }
}

/**
 * Show error message
 * @param {string} message - Error message to display
 */
function showError(message) {
    const errorEl = document.getElementById('error-container');
    errorEl.textContent = message;
    errorEl.style.display = 'block';
    
    // Hide after 5 seconds
    setTimeout(() => {
        errorEl.style.display = 'none';
    }, 5000);
}

/**
 * Handle node selection event from visualization
 * @param {Object} node - Selected node data
 */
function handleNodeSelected(node) {
    dashboardState.selectedNode = node;
    
    // Update node details panel
    const detailsEl = document.getElementById('node-details');
    
    let detailsHtml = `
        <h3>${node.type} Memory</h3>
        <div class="detail-item">
            <span class="detail-label">ID:</span>
            <span class="detail-value">${node.id}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">Created:</span>
            <span class="detail-value">${node.timestamp.toLocaleString()}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">Content:</span>
            <div class="detail-content">${node.content}</div>
        </div>
    `;
    
    // Add metadata if available
    if (node.metadata && Object.keys(node.metadata).length > 0) {
        detailsHtml += `<h4>Metadata</h4>`;
        
        Object.entries(node.metadata).forEach(([key, value]) => {
            detailsHtml += `
                <div class="detail-item">
                    <span class="detail-label">${key}:</span>
                    <span class="detail-value">${typeof value === 'object' ? JSON.stringify(value) : value}</span>
                </div>
            `;
        });
    }
    
    detailsEl.innerHTML = detailsHtml;
    detailsEl.style.display = 'block';
}

// Export public API
export {
    initDashboard,
    loadMemoryData,
    handleNodeSelected
};