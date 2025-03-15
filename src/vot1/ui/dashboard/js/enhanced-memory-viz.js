/**
 * VOTai TRILOGY BRAIN - Enhanced Memory Network Visualization
 * Modern THREE.js implementation with progressive loading, optimized for large memory networks
 * Integrates with Composio for advanced data processing
 */

class EnhancedMemoryVisualization {
  constructor(container, options = {}) {
    this.container = container;
    this.options = Object.assign({
      backgroundColor: 0x050019,
      cameraPosition: { x: 0, y: 0, z: 100 },
      nodeSize: 2,
      connectionOpacity: 0.3,
      maxNodes: 500,
      animationSpeed: 0.5,
      glowIntensity: 1,
      rotationSpeed: 0.0005,
      memoryViewDistance: 50,
      // Progressive loading options
      progressiveLevels: [
        { distance: 200, detail: 'low', maxNodes: 500 },
        { distance: 100, detail: 'medium', maxNodes: 1000 },
        { distance: 50, detail: 'high', maxNodes: 2000 }
      ],
      // Composio integration options
      useComposio: true,
      composioRefreshRate: 5000
    }, options);

    // Core state
    this.nodes = [];
    this.links = [];
    this.nodeGroups = {}; // Organize nodes by category
    this.hoveredNode = null;
    this.selectedNode = null;
    this.currentDetailLevel = 'low';
    this.currentLoadedNodes = 0;

    // THREE.js core components
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();
    this.clock = new THREE.Clock();

    // Material cache for different LOD (Level of Detail) levels
    this.materials = {
      low: {},
      medium: {},
      high: {}
    };

    // Memory classification
    this.memoryLevels = {
      'L1': { color: 0xff1a8c, size: 1.5 },  // Hot pink for L1 (recent memories)
      'L2': { color: 0x00ccff, size: 1.2 },  // Cyan for L2 (important but not recent)
      'L3': { color: 0x7c3aed, size: 1.0 }   // Purple for L3 (archived memories)
    };

    this.importanceColors = [
      0xffef40, // Yellow - very high importance
      0xff9f1a, // Orange - high importance
      0x00ccff, // Cyan - medium importance
      0x7c3aed, // Purple - low importance
      0x444444  // Grey - very low importance
    ];

    // Composio integration
    this.composioClient = null;
    this.lastComposioRefresh = 0;

    // Initialize visualization and create event listeners
    this.init();
    this.createEventListeners();
    this.initComposioIntegration();
    this.animate();
  }

  /**
   * Initialize THREE.js scene and core components
   */
  init() {
    // Create scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(this.options.backgroundColor);
    this.scene.fog = new THREE.FogExp2(this.options.backgroundColor, 0.001);

    // Create camera
    const { width, height } = this.container.getBoundingClientRect();
    this.camera = new THREE.PerspectiveCamera(60, width / height, 1, 1000);
    this.camera.position.set(
      this.options.cameraPosition.x,
      this.options.cameraPosition.y,
      this.options.cameraPosition.z
    );
    this.camera.lookAt(this.scene.position);

    // Create renderer with WebGL2 if available
    this.renderer = new THREE.WebGLRenderer({ 
      antialias: true, 
      alpha: true,
      powerPreference: "high-performance"
    });
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.setSize(width, height);
    this.container.appendChild(this.renderer.domElement);

    // Add orbit controls with damping for smooth camera movement
    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.1;
    this.controls.rotateSpeed = 0.5;
    this.controls.minDistance = 20;
    this.controls.maxDistance = 500;
    
    // Create node container for each level of detail
    this.nodeGroups = {
      low: new THREE.Group(),
      medium: new THREE.Group(),
      high: new THREE.Group()
    };
    
    // Initially only add the low-detail group
    this.scene.add(this.nodeGroups.low);
    
    // Create links container
    this.linksGroup = new THREE.Group();
    this.scene.add(this.linksGroup);

    // Add background particles
    this.createBackgroundParticles();
    
    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
    this.scene.add(ambientLight);
    
    // Add directional light
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
    directionalLight.position.set(1, 1, 1);
    this.scene.add(directionalLight);

    // Create composer for post-processing effects
    this.createComposer();
    
    // Initialize stats for performance monitoring if in dev mode
    if (this.options.showStats) {
      this.stats = new Stats();
      this.container.appendChild(this.stats.dom);
    }
  }

  /**
   * Create post-processing effects
   */
  createComposer() {
    this.composer = new THREE.EffectComposer(this.renderer);
    const renderPass = new THREE.RenderPass(this.scene, this.camera);
    this.composer.addPass(renderPass);

    // Bloom effect for glow with optimized settings
    const bloomPass = new THREE.UnrealBloomPass(
      new THREE.Vector2(window.innerWidth, window.innerHeight),
      1.5,   // strength
      0.4,   // radius
      0.85   // threshold
    );
    bloomPass.strength = this.options.glowIntensity;
    this.composer.addPass(bloomPass);
    this.bloomPass = bloomPass;

    // Add film grain effect for cyberpunk aesthetic
    const filmPass = new THREE.FilmPass(
      0.35,   // noise intensity
      0.025,  // scanline intensity
      648,    // scanline count
      false   // grayscale
    );
    filmPass.renderToScreen = true;
    this.composer.addPass(filmPass);
    
    // Optimization: selective rendering for effects
    this.composer.setSize(window.innerWidth, window.innerHeight);
  }

  /**
   * Initialize Composio integration if available
   */
  initComposioIntegration() {
    if (!this.options.useComposio || !window.composioClient) {
      console.warn('Composio integration unavailable or disabled');
      return;
    }
    
    try {
      // Initialize Composio client from global scope
      this.composioClient = window.composioClient;
      console.log('Composio integration initialized for memory visualization');
      
      // Initial data fetch
      this.fetchMemoryDataFromComposio();
    } catch (error) {
      console.error('Failed to initialize Composio integration:', error);
    }
  }
  
  /**
   * Fetch memory data from Composio
   */
  async fetchMemoryDataFromComposio() {
    if (!this.composioClient) return;
    
    try {
      // Get current timestamp
      const now = Date.now();
      
      // Only refresh if enough time has passed
      if (now - this.lastComposioRefresh < this.options.composioRefreshRate) {
        return;
      }
      
      // Update timestamp
      this.lastComposioRefresh = now;
      
      // Execute Composio tool to get memory data
      const result = await this.composioClient.executeTool('getMemoryNetwork', {
        detail_level: this.currentDetailLevel,
        max_nodes: this.options.progressiveLevels.find(l => l.detail === this.currentDetailLevel).maxNodes
      });
      
      // Process the result if successful
      if (result && result.success && result.data) {
        this.updateMemoryVisualization(result.data);
      }
    } catch (error) {
      console.error('Error fetching memory data from Composio:', error);
    }
  }

  /**
   * Update the memory visualization with new data
   */
  updateMemoryVisualization(data) {
    // Clear existing nodes at current detail level
    this.clearDetailLevel(this.currentDetailLevel);
    
    // Process nodes
    if (data.nodes && Array.isArray(data.nodes)) {
      data.nodes.forEach(node => {
        this.addNode(node, this.currentDetailLevel);
      });
    }
    
    // Process links
    if (data.links && Array.isArray(data.links)) {
      data.links.forEach(link => {
        this.addLink(link);
      });
    }
    
    // Update node count
    this.currentLoadedNodes = data.nodes ? data.nodes.length : 0;
    
    // Update UI if available
    if (this.updateUI) {
      this.updateUI({
        nodeCount: this.currentLoadedNodes,
        detailLevel: this.currentDetailLevel,
        lastUpdate: new Date().toISOString()
      });
    }
  }

  /**
   * Clear nodes at a specific detail level
   */
  clearDetailLevel(level) {
    if (this.nodeGroups[level]) {
      // Dispose materials and geometries to prevent memory leaks
      this.nodeGroups[level].children.forEach(child => {
        if (child.geometry) child.geometry.dispose();
        if (child.material) {
          if (Array.isArray(child.material)) {
            child.material.forEach(mat => mat.dispose());
          } else {
            child.material.dispose();
          }
        }
      });
      
      // Clear the group
      while (this.nodeGroups[level].children.length > 0) {
        this.nodeGroups[level].remove(this.nodeGroups[level].children[0]);
      }
    }
    
    // Clear links
    while (this.linksGroup.children.length > 0) {
      const link = this.linksGroup.children[0];
      if (link.geometry) link.geometry.dispose();
      if (link.material) link.material.dispose();
      this.linksGroup.remove(link);
    }
  }

  /**
   * Create background particles effect
   */
  createBackgroundParticles() {
    const particleCount = 1000;
    const particles = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    
    const color = new THREE.Color();
    
    for (let i = 0; i < positions.length; i += 3) {
      // Position particles in a spherical volume for better distribution
      const radius = 200 + Math.random() * 800;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI;
      
      positions[i]     = radius * Math.sin(phi) * Math.cos(theta);
      positions[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i + 2] = radius * Math.cos(phi);
      
      // Color with improved visual effect - gradient based on distance
      const distanceNormalized = radius / 1000;
      const baseColor = new THREE.Color(this.importanceColors[Math.floor(Math.random() * this.importanceColors.length)]);
      const mix = Math.random() * 0.3 * (1 - distanceNormalized * 0.5); // Dimmer with distance
      color.set(this.options.backgroundColor).lerp(baseColor, mix);
      
      colors[i]     = color.r;
      colors[i + 1] = color.g;
      colors[i + 2] = color.b;
    }
    
    particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particles.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    
    // Use point sprites with custom shaders for better performance
    const material = new THREE.PointsMaterial({
      size: 0.5,
      vertexColors: true,
      opacity: 0.7,
      transparent: true,
      sizeAttenuation: true
    });
    
    this.particleSystem = new THREE.Points(particles, material);
    this.scene.add(this.particleSystem);
    
    // Add subtle animation to particles
    this.particleSystem.userData.animationSpeed = 0.01;
  }

  /**
   * Create event listeners for user interaction
   */
  createEventListeners() {
    window.addEventListener('resize', this.onWindowResize.bind(this));
    this.renderer.domElement.addEventListener('mousemove', this.onMouseMove.bind(this));
    this.renderer.domElement.addEventListener('click', this.onMouseClick.bind(this));
    
    // Add zoom event listener to handle detail level changes
    this.controls.addEventListener('change', this.onCameraMove.bind(this));
  }
  
  /**
   * Handle camera movement to update detail level
   */
  onCameraMove() {
    const distance = this.camera.position.length();
    
    // Find appropriate detail level based on camera distance
    let newDetailLevel = 'low';
    for (const level of this.options.progressiveLevels) {
      if (distance < level.distance) {
        newDetailLevel = level.detail;
      }
    }
    
    // Only update if detail level has changed
    if (newDetailLevel !== this.currentDetailLevel) {
      console.log(`Changing detail level from ${this.currentDetailLevel} to ${newDetailLevel}`);
      
      // Remove current detail level group and add new one
      this.scene.remove(this.nodeGroups[this.currentDetailLevel]);
      this.scene.add(this.nodeGroups[newDetailLevel]);
      
      // Update current detail level
      this.currentDetailLevel = newDetailLevel;
      
      // Fetch new data at appropriate detail level
      this.fetchMemoryDataFromComposio();
    }
  }

  /**
   * Handle window resize events
   */
  onWindowResize() {
    const { width, height } = this.container.getBoundingClientRect();
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
    this.composer.setSize(width, height);
  }

  /**
   * Handle mouse move events for node hovering
   */
  onMouseMove(event) {
    // Calculate mouse position in normalized device coordinates
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    // Update the raycaster with the mouse position and camera
    this.raycaster.setFromCamera(this.mouse, this.camera);

    // Find intersections with nodes in the current detail level group
    const intersects = this.raycaster.intersectObjects(this.nodeGroups[this.currentDetailLevel].children);
    
    // Restore previous hovered node appearance
    if (this.hoveredNode && (!intersects.length || intersects[0].object !== this.hoveredNode)) {
      this.restoreNodeAppearance(this.hoveredNode);
      this.hoveredNode = null;
      document.body.style.cursor = 'default';
      this.hideMemoryPreview();
    }
    
    // Handle new hover
    if (intersects.length > 0) {
      const object = intersects[0].object;
      if (object !== this.hoveredNode) {
        this.hoveredNode = object;
        document.body.style.cursor = 'pointer';
        
        // Scale up hovered node
        const originalScale = object.userData.originalScale || { x: 1, y: 1, z: 1 };
        object.scale.set(originalScale.x * 1.5, originalScale.y * 1.5, originalScale.z * 1.5);
        
        // Show memory preview
        if (object.userData.memory) {
          this.showMemoryPreview(object.userData.memory);
        }
      }
    }
  }

  /**
   * Handle mouse click events for node selection
   */
  onMouseClick(event) {
    // Calculate mouse position in normalized device coordinates
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    // Update the raycaster with the mouse position and camera
    this.raycaster.setFromCamera(this.mouse, this.camera);

    // Find intersections with nodes
    const intersects = this.raycaster.intersectObjects(this.nodeGroups[this.currentDetailLevel].children);
    
    if (intersects.length > 0) {
      const object = intersects[0].object;
      
      // Restore previous selected node appearance
      if (this.selectedNode && this.selectedNode !== object) {
        this.restoreNodeAppearance(this.selectedNode);
      }
      
      // Update selected node
      this.selectedNode = object;
      
      // Highlight connections for the selected node
      this.highlightConnections(object);
      
      // Show memory details in the terminal
      if (object.userData.memory) {
        this.showMemoryInTerminal(object.userData.memory);
        
        // If we're using Composio, fetch additional memory details
        if (this.composioClient && object.userData.memory.id) {
          this.fetchMemoryDetailsFromComposio(object.userData.memory.id);
        }
      }
    }
  }
  
  /**
   * Fetch detailed memory information from Composio
   */
  async fetchMemoryDetailsFromComposio(memoryId) {
    if (!this.composioClient) return;
    
    try {
      const result = await this.composioClient.executeTool('getMemoryDetails', {
        memory_id: memoryId
      });
      
      if (result && result.success && result.data) {
        // Update the terminal with detailed memory information
        this.showDetailedMemoryInTerminal(result.data);
      }
    } catch (error) {
      console.error('Error fetching memory details from Composio:', error);
    }
  }

  /**
   * Show memory preview on hover
   */
  showMemoryPreview(memory) {
    // Create or update preview element
    if (!this.previewElement) {
      this.previewElement = document.createElement('div');
      this.previewElement.className = 'memory-preview';
      this.previewElement.style.position = 'absolute';
      this.previewElement.style.zIndex = '100';
      this.previewElement.style.padding = '10px';
      this.previewElement.style.background = 'rgba(0, 0, 0, 0.8)';
      this.previewElement.style.border = '1px solid #00ccff';
      this.previewElement.style.borderRadius = '5px';
      this.previewElement.style.color = '#ffffff';
      this.previewElement.style.fontSize = '12px';
      this.previewElement.style.pointerEvents = 'none';
      this.previewElement.style.boxShadow = '0 0 10px rgba(0, 204, 255, 0.5)';
      document.body.appendChild(this.previewElement);
    }
    
    // Update content
    let content = '';
    if (memory.type) content += `<div class="preview-type">${memory.type}</div>`;
    if (memory.title) content += `<div class="preview-title">${memory.title}</div>`;
    if (memory.snippet) content += `<div class="preview-snippet">${memory.snippet}</div>`;
    if (memory.created) {
      const date = new Date(memory.created);
      content += `<div class="preview-date">${date.toLocaleDateString()} ${date.toLocaleTimeString()}</div>`;
    }
    
    this.previewElement.innerHTML = content;
    
    // Position next to cursor
    const mouseMoveListener = (e) => {
      this.previewElement.style.left = `${e.clientX + 15}px`;
      this.previewElement.style.top = `${e.clientY + 15}px`;
    };
    
    document.addEventListener('mousemove', mouseMoveListener);
    this.previewMouseMoveListener = mouseMoveListener;
    
    // Show preview
    this.previewElement.style.display = 'block';
  }

  /**
   * Hide memory preview when not hovering
   */
  hideMemoryPreview() {
    if (this.previewElement) {
      this.previewElement.style.display = 'none';
    }
    
    if (this.previewMouseMoveListener) {
      document.removeEventListener('mousemove', this.previewMouseMoveListener);
      this.previewMouseMoveListener = null;
    }
  }

  /**
   * Display memory details in terminal UI
   */
  showMemoryInTerminal(memory) {
    // Check if terminal element exists
    const terminal = document.getElementById('system-console');
    if (!terminal) return;
    
    // Format memory for display
    const timestamp = memory.created ? new Date(memory.created).toLocaleTimeString() : new Date().toLocaleTimeString();
    
    const lines = [
      `<div class="terminal-line"><span class="terminal-time">[${timestamp}]</span> <span class="terminal-success">Memory selected:</span></div>`,
      `<div class="terminal-line"><span class="terminal-label">ID:</span> <span class="terminal-value">${memory.id || 'unknown'}</span></div>`,
      `<div class="terminal-line"><span class="terminal-label">Type:</span> <span class="terminal-value">${memory.type || 'unknown'}</span></div>`
    ];
    
    if (memory.title) {
      lines.push(`<div class="terminal-line"><span class="terminal-label">Title:</span> <span class="terminal-value">${memory.title}</span></div>`);
    }
    
    if (memory.content) {
      // Truncate content if too long
      const truncatedContent = memory.content.length > 200 ? memory.content.substring(0, 200) + '...' : memory.content;
      lines.push(`<div class="terminal-line"><span class="terminal-label">Content:</span> <span class="terminal-value">${truncatedContent}</span></div>`);
    }
    
    if (memory.importance) {
      lines.push(`<div class="terminal-line"><span class="terminal-label">Importance:</span> <span class="terminal-value">${memory.importance}</span></div>`);
    }
    
    // Add a line showing "Loading detailed information..." if using Composio
    if (this.composioClient && memory.id) {
      lines.push(`<div class="terminal-line"><span class="terminal-info">Loading detailed information...</span></div>`);
    }
    
    // Add lines to terminal
    terminal.innerHTML += lines.join('');
    
    // Scroll to bottom
    terminal.scrollTop = terminal.scrollHeight;
  }
  
  /**
   * Show detailed memory information in terminal
   */
  showDetailedMemoryInTerminal(memoryDetails) {
    // Check if terminal element exists
    const terminal = document.getElementById('system-console');
    if (!terminal) return;
    
    // Format memory details for display
    const timestamp = new Date().toLocaleTimeString();
    
    const lines = [
      `<div class="terminal-line"><span class="terminal-time">[${timestamp}]</span> <span class="terminal-success">Detailed memory information:</span></div>`
    ];
    
    // Add relationships if available
    if (memoryDetails.relationships && memoryDetails.relationships.length > 0) {
      lines.push(`<div class="terminal-line"><span class="terminal-label">Relationships:</span></div>`);
      
      memoryDetails.relationships.forEach(rel => {
        lines.push(`<div class="terminal-line">  <span class="terminal-info">${rel.type}:</span> <span class="terminal-value">${rel.targetId}</span> (${rel.strength})</div>`);
      });
    }
    
    // Add embeddings visualization if available
    if (memoryDetails.embedding_visualization) {
      lines.push(`<div class="terminal-line"><span class="terminal-label">Embedding Visualization:</span> <span class="terminal-value">${memoryDetails.embedding_visualization}</span></div>`);
    }
    
    // Add metadata if available
    if (memoryDetails.metadata) {
      lines.push(`<div class="terminal-line"><span class="terminal-label">Metadata:</span></div>`);
      
      for (const [key, value] of Object.entries(memoryDetails.metadata)) {
        lines.push(`<div class="terminal-line">  <span class="terminal-info">${key}:</span> <span class="terminal-value">${value}</span></div>`);
      }
    }
    
    // Add lines to terminal
    terminal.innerHTML += lines.join('');
    
    // Scroll to bottom
    terminal.scrollTop = terminal.scrollHeight;
  }

  /**
   * Highlight connections for selected node
   */
  highlightConnections(node) {
    // Reset all links
    this.linksGroup.children.forEach(link => {
      link.material.opacity = this.options.connectionOpacity / 2;
      link.material.color.set(0x444444);
    });
    
    // Get node ID
    const nodeId = node.userData.id;
    if (!nodeId) return;
    
    // Highlight connected links
    this.linksGroup.children.forEach(link => {
      if (link.userData.source === nodeId || link.userData.target === nodeId) {
        link.material.opacity = 1.0;
        
        // Color based on relationship type
        const relType = link.userData.type || 'default';
        const colors = {
          'semantic': 0x00ccff,
          'causal': 0xff9f1a,
          'temporal': 0x7c3aed,
          'hierarchical': 0xffef40,
          'default': 0xffffff
        };
        
        link.material.color.set(colors[relType]);
      }
    });
    
    // Highlight connected nodes
    const connectedNodeIds = new Set();
    this.linksGroup.children.forEach(link => {
      if (link.userData.source === nodeId) {
        connectedNodeIds.add(link.userData.target);
      } else if (link.userData.target === nodeId) {
        connectedNodeIds.add(link.userData.source);
      }
    });
    
    // Update appearance of connected nodes
    this.nodeGroups[this.currentDetailLevel].children.forEach(otherNode => {
      if (connectedNodeIds.has(otherNode.userData.id)) {
        // Scale up connected nodes
        const scale = 1.3;
        otherNode.scale.set(scale, scale, scale);
        
        // Add pulsing effect
        otherNode.userData.pulsing = true;
        otherNode.userData.pulseTime = 0;
      } else if (otherNode !== node) {
        // Dim non-connected nodes
        this.restoreNodeAppearance(otherNode);
        otherNode.material.opacity = 0.3;
      }
    });
  }

  /**
   * Restore node appearance
   */
  restoreNodeAppearance(node) {
    if (!node) return;
    
    // Reset scale
    const originalScale = node.userData.originalScale || { x: 1, y: 1, z: 1 };
    node.scale.set(originalScale.x, originalScale.y, originalScale.z);
    
    // Reset material
    if (node.material) {
      node.material.opacity = 1.0;
    }
    
    // Reset animation state
    node.userData.pulsing = false;
  }

  /**
   * Main animation loop
   */
  animate() {
    requestAnimationFrame(this.animate.bind(this));
    
    const delta = this.clock.getDelta();
    const elapsedTime = this.clock.getElapsedTime();
    
    // Update controls
    this.controls.update();
    
    // Rotate particle system
    if (this.particleSystem) {
      this.particleSystem.rotation.y += 0.0005;
    }
    
    // Update pulsing effect for selected nodes
    this.nodeGroups[this.currentDetailLevel].children.forEach(node => {
      if (node.userData.pulsing) {
        node.userData.pulseTime = (node.userData.pulseTime || 0) + delta;
        const scale = 1.2 + Math.sin(node.userData.pulseTime * 5) * 0.1;
        node.scale.set(scale, scale, scale);
      }
    });
    
    // Check for Composio data refresh
    if (this.options.useComposio && this.composioClient) {
      const now = Date.now();
      if (now - this.lastComposioRefresh > this.options.composioRefreshRate) {
        this.fetchMemoryDataFromComposio();
      }
    }
    
    // Handle progressive loading based on camera distance
    this.checkProgressiveLoading();
    
    // Render scene with post-processing
    this.composer.render();
    
    // Update stats if available
    if (this.stats) {
      this.stats.update();
    }
  }
  
  /**
   * Check and update progressive loading based on camera distance
   */
  checkProgressiveLoading() {
    const distance = this.camera.position.length();
    
    // Find appropriate detail level based on camera distance
    let newDetailLevel = 'low';
    for (const level of this.options.progressiveLevels) {
      if (distance < level.distance) {
        newDetailLevel = level.detail;
      }
    }
    
    // Only update if detail level has changed
    if (newDetailLevel !== this.currentDetailLevel) {
      // Remove current detail level group and add new one
      this.scene.remove(this.nodeGroups[this.currentDetailLevel]);
      this.scene.add(this.nodeGroups[newDetailLevel]);
      
      // Update current detail level
      this.currentDetailLevel = newDetailLevel;
      
      // Fetch new data at appropriate detail level
      this.fetchMemoryDataFromComposio();
    }
  }

  /**
   * Add a node to the visualization
   */
  addNode(nodeData, detailLevel = 'low') {
    // Create geometry based on detail level
    let geometry;
    if (detailLevel === 'high') {
      // Higher detail geometry for close-up views
      geometry = new THREE.SphereGeometry(nodeData.size || this.options.nodeSize, 16, 12);
    } else if (detailLevel === 'medium') {
      geometry = new THREE.SphereGeometry(nodeData.size || this.options.nodeSize, 10, 8);
    } else {
      // Low poly for distant views
      geometry = new THREE.SphereGeometry(nodeData.size || this.options.nodeSize, 6, 4);
    }
    
    // Create material with glow effect
    const color = new THREE.Color(nodeData.color || this.getColorForNode(nodeData));
    const material = new THREE.MeshPhongMaterial({
      color: color,
      emissive: color,
      emissiveIntensity: 0.5,
      specular: 0xffffff,
      shininess: 100,
      transparent: true,
      opacity: 0.9
    });
    
    // Create mesh
    const mesh = new THREE.Mesh(geometry, material);
    
    // Set position
    mesh.position.set(
      nodeData.position.x || (Math.random() - 0.5) * 200,
      nodeData.position.y || (Math.random() - 0.5) * 200,
      nodeData.position.z || (Math.random() - 0.5) * 200
    );
    
    // Store node data
    mesh.userData = {
      id: nodeData.id,
      memory: nodeData,
      originalScale: { x: 1, y: 1, z: 1 },
      detailLevel: detailLevel
    };
    
    // Add to appropriate group
    this.nodeGroups[detailLevel].add(mesh);
    
    return mesh;
  }

  /**
   * Add a link between nodes
   */
  addLink(linkData) {
    // Find source and target nodes
    let sourceNode, targetNode;
    
    // Search in all detail levels
    for (const level of Object.keys(this.nodeGroups)) {
      this.nodeGroups[level].children.forEach(node => {
        if (node.userData.id === linkData.source) sourceNode = node;
        if (node.userData.id === linkData.target) targetNode = node;
      });
    }
    
    if (!sourceNode || !targetNode) {
      console.warn('Cannot create link - missing source or target node');
      return null;
    }
    
    // Create geometry
    const points = [
      sourceNode.position.clone(),
      targetNode.position.clone()
    ];
    
    const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
    
    // Determine color based on relationship type
    const colorMap = {
      'semantic': 0x00ccff,
      'causal': 0xff9f1a,
      'temporal': 0x7c3aed,
      'hierarchical': 0xffef40,
      'default': 0x666666
    };
    
    const color = colorMap[linkData.type] || colorMap.default;
    
    // Create material
    const lineMaterial = new THREE.LineBasicMaterial({
      color: color,
      transparent: true,
      opacity: this.options.connectionOpacity,
      linewidth: 1
    });
    
    // Create line
    const line = new THREE.Line(lineGeometry, lineMaterial);
    
    // Store link data
    line.userData = {
      source: linkData.source,
      target: linkData.target,
      type: linkData.type,
      strength: linkData.strength
    };
    
    // Add to links group
    this.linksGroup.add(line);
    
    return line;
  }

  /**
   * Get color for node based on data
   */
  getColorForNode(nodeData) {
    // Memory level takes precedence
    if (nodeData.level && this.memoryLevels[nodeData.level]) {
      return this.memoryLevels[nodeData.level].color;
    }
    
    // Then check importance
    if (nodeData.importance !== undefined) {
      const importanceIndex = Math.min(
        Math.floor(nodeData.importance * this.importanceColors.length),
        this.importanceColors.length - 1
      );
      
      return this.importanceColors[importanceIndex];
    }
    
    // Default to type-based colors
    const typeColors = {
      'research': 0x00ccff,
      'code': 0xff9f1a,
      'concept': 0xffef40,
      'reference': 0x7c3aed,
      'hybrid_thinking': 0xff1a8c,
      'default': 0x999999
    };
    
    return typeColors[nodeData.type] || typeColors.default;
  }
}

// Add to global scope
window.EnhancedMemoryVisualization = EnhancedMemoryVisualization; 