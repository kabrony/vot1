/**
 * VOT1 File Structure Visualizer
 * 
 * A cyberpunk-themed Three.js component for visualizing project file structure in 3D.
 * Features interactive node exploration, color-coded file types, and orbit controls.
 * 
 * @version 1.0.0
 */

// Helper function to get Three.js - works in browser, Node.js and ES modules
function getThree() {
  try {
    if (typeof THREE !== 'undefined') {
      return THREE;
    } else if (typeof require === 'function') {
      return require('three');
    } else {
      console.warn('THREE.js not found. Make sure to include it before this script.');
      return null;
    }
  } catch (e) {
    console.error('Error loading THREE.js:', e);
    return null;
  }
}

const THREE = getThree();

class FileStructureVisualizer {
  /**
   * Create a new file structure visualizer.
   * 
   * @param {Object} options - Configuration options
   * @param {string|HTMLElement} options.container - Container element or selector
   * @param {Object} options.data - File structure data
   * @param {Object} options.theme - Visual theme options
   * @param {number} options.nodeSize - Size of nodes (default: 1)
   * @param {number} options.nodeSpacing - Spacing between nodes (default: 5)
   * @param {boolean} options.animate - Whether to animate the visualization (default: true)
   * @param {Function} options.onNodeClick - Callback for node clicks
   * @param {Function} options.onNodeHover - Callback for node hover
   * @param {number} options.maxNodesPerLevel - Max nodes to show per level (default: 500)
   */
  constructor(options = {}) {
    // Process options with defaults
    this.options = Object.assign({
      container: '#visualization',
      data: null,
      theme: {
        background: 0x000000,
        folderColor: 0x00ffff,
        fileColors: {
          // File extensions with their colors (cyberpunk theme)
          '.js': 0xff00ff,
          '.py': 0x00ffaa,
          '.html': 0xff8800,
          '.css': 0x0088ff,
          '.json': 0xffff00,
          '.md': 0x88ff00,
          '.txt': 0xffffff,
          '.jpg': 0xff0088,
          '.png': 0x00ff88,
          '.svg': 0x8800ff,
          // Default for other files
          'default': 0x7f7f7f
        },
        gridColor: 0x222222,
        particleColor: 0x0088ff,
        lightColor: 0xffffff,
        rimLightColor: 0xff00ff,
      },
      nodeSize: 1,
      nodeSpacing: 5,
      animate: true,
      showGrid: true,
      showParticles: true,
      maxNodesPerLevel: 500,
      lodDistanceThreshold: 50,
      onNodeClick: null,
      onNodeHover: null
    }, options);

    // Performance monitoring
    this.stats = {
      visibleNodes: 0,
      fps: 0,
      lastFrameTime: performance.now()
    };

    // Initialize scene
    this._initRenderer();
    this._initScene();
    this._initCamera();
    this._initLights();
    this._initControls();
    this._initGrid();
    this._initParticles();
    
    // Load data if provided
    if (this.options.data) {
      this.loadData(this.options.data);
    }

    // Start animation loop
    if (this.options.animate) {
      this._animate();
    }

    // Add resize listener
    window.addEventListener('resize', this._onWindowResize.bind(this));
  }

  /**
   * Initialize the Three.js renderer.
   * @private
   */
  _initRenderer() {
    // Get the container
    const container = typeof this.options.container === 'string' 
      ? document.querySelector(this.options.container) 
      : this.options.container;
    
    if (!container) {
      throw new Error(`Container not found: ${this.options.container}`);
    }
    
    this.container = container;
    
    // Create renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    this.renderer.shadowMap.enabled = true;
    this.renderer.outputEncoding = THREE.sRGBEncoding;
    
    container.appendChild(this.renderer.domElement);
    
    // Get container dimensions
    this.width = container.clientWidth;
    this.height = container.clientHeight;
  }

  /**
   * Initialize the Three.js scene.
   * @private
   */
  _initScene() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(this.options.theme.background);
    this.scene.fog = new THREE.FogExp2(this.options.theme.background, 0.002);
    
    // Create group for file structure
    this.fileStructureGroup = new THREE.Group();
    this.scene.add(this.fileStructureGroup);
    
    // Shared geometries and materials for better performance
    this.sharedGeometries = {
      folder: new THREE.BoxGeometry(1, 1, 1),
      file: new THREE.SphereGeometry(0.5, 16, 16)
    };
    
    this.sharedMaterials = {
      folder: new THREE.MeshPhongMaterial({ 
        color: this.options.theme.folderColor,
        shininess: 100,
        emissive: this.options.theme.folderColor,
        emissiveIntensity: 0.2
      })
    };
    
    // Create materials for file types
    this.sharedMaterials.files = {};
    Object.entries(this.options.theme.fileColors).forEach(([ext, color]) => {
      this.sharedMaterials.files[ext] = new THREE.MeshPhongMaterial({ 
        color: color,
        shininess: 100,
        emissive: color,
        emissiveIntensity: 0.1
      });
    });
  }

  /**
   * Initialize the camera.
   * @private
   */
  _initCamera() {
    const aspect = this.width / this.height;
    this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 2000);
    this.camera.position.set(20, 20, 20);
    this.camera.lookAt(0, 0, 0);
  }

  /**
   * Initialize scene lighting.
   * @private
   */
  _initLights() {
    // Main directional light
    this.directionalLight = new THREE.DirectionalLight(this.options.theme.lightColor, 1);
    this.directionalLight.position.set(1, 1, 1);
    this.scene.add(this.directionalLight);
    
    // Ambient light for base illumination
    this.ambientLight = new THREE.AmbientLight(this.options.theme.lightColor, 0.4);
    this.scene.add(this.ambientLight);
    
    // Rim light for cyberpunk effect
    this.rimLight = new THREE.DirectionalLight(this.options.theme.rimLightColor, 0.5);
    this.rimLight.position.set(-1, 0, -1);
    this.scene.add(this.rimLight);
    
    // Point light at center
    this.centerLight = new THREE.PointLight(this.options.theme.lightColor, 0.5, 50);
    this.centerLight.position.set(0, 5, 0);
    this.scene.add(this.centerLight);
  }

  /**
   * Initialize orbit controls.
   * @private
   */
  _initControls() {
    if (typeof THREE.OrbitControls !== 'undefined') {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.1;
      this.controls.rotateSpeed = 0.5;
      this.controls.minDistance = 10;
      this.controls.maxDistance = 500;
    } else {
      console.warn('THREE.OrbitControls not found. Interactive controls disabled.');
    }
  }

  /**
   * Initialize grid for visual reference.
   * @private
   */
  _initGrid() {
    if (this.options.showGrid) {
      const gridHelper = new THREE.GridHelper(200, 50, this.options.theme.gridColor, this.options.theme.gridColor);
      gridHelper.position.y = -10;
      this.scene.add(gridHelper);
      this.grid = gridHelper;
    }
  }
  
  /**
   * Initialize particle system for atmosphere.
   * @private
   */
  _initParticles() {
    if (!this.options.showParticles) return;
    
    const particleCount = 2000;
    const particleGeometry = new THREE.BufferGeometry();
    const particleMaterial = new THREE.PointsMaterial({
      color: this.options.theme.particleColor,
      size: 0.5,
      transparent: true,
      opacity: 0.5,
      map: this._createParticleTexture(),
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });
    
    // Create random positions for particles in a large cube around the scene
    const positions = new Float32Array(particleCount * 3);
    const size = 100;
    
    for (let i = 0; i < particleCount; i++) {
      const i3 = i * 3;
      positions[i3] = (Math.random() - 0.5) * size * 2;
      positions[i3 + 1] = (Math.random() - 0.5) * size * 2;
      positions[i3 + 2] = (Math.random() - 0.5) * size * 2;
    }
    
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    this.particles = new THREE.Points(particleGeometry, particleMaterial);
    this.scene.add(this.particles);
    
    // Store original positions
    this.particlePositions = positions.slice();
  }
  
  /**
   * Create a particle texture for better-looking points.
   * @private
   * @returns {THREE.Texture} The particle texture
   */
  _createParticleTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 16;
    canvas.height = 16;
    
    const context = canvas.getContext('2d');
    const gradient = context.createRadialGradient(8, 8, 0, 8, 8, 8);
    gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
    
    context.fillStyle = gradient;
    context.fillRect(0, 0, 16, 16);
    
    const texture = new THREE.Texture(canvas);
    texture.needsUpdate = true;
    return texture;
  }

  /**
   * Handle window resize events.
   * @private
   */
  _onWindowResize() {
    this.width = this.container.clientWidth;
    this.height = this.container.clientHeight;
    
    this.camera.aspect = this.width / this.height;
    this.camera.updateProjectionMatrix();
    
    this.renderer.setSize(this.width, this.height);
  }

  /**
   * Animation loop.
   * @private
   */
  _animate() {
    requestAnimationFrame(this._animate.bind(this));
    
    // Calculate FPS
    const now = performance.now();
    const delta = now - this.stats.lastFrameTime;
    this.stats.lastFrameTime = now;
    this.stats.fps = 1000 / delta;
    
    // Update controls if available
    if (this.controls) {
      this.controls.update();
    }
    
    // Animate particles
    if (this.particles) {
      const positions = this.particles.geometry.attributes.position.array;
      
      for (let i = 0; i < positions.length; i += 3) {
        // Simple sine wave animation on y-axis
        positions[i + 1] = this.particlePositions[i + 1] + Math.sin(now * 0.001 + i) * 0.5;
      }
      
      this.particles.geometry.attributes.position.needsUpdate = true;
      this.particles.rotation.y = now * 0.00005;
    }
    
    // Update object visibility based on camera distance (LOD)
    if (this.fileNodes) {
      this._updateNodeVisibility();
    }
    
    // Render scene
    this.renderer.render(this.scene, this.camera);
  }
  
  /**
   * Update node visibility based on distance from camera (Level of Detail).
   * @private
   */
  _updateNodeVisibility() {
    let visibleCount = 0;
    const threshold = this.options.lodDistanceThreshold;
    
    this.fileNodes.forEach(node => {
      const distance = this.camera.position.distanceTo(node.position);
      
      // Skip nodes that are too far away
      if (node.userData.depth > 1 && distance > threshold * node.userData.depth) {
        node.visible = false;
      } else {
        node.visible = true;
        visibleCount++;
      }
    });
    
    this.stats.visibleNodes = visibleCount;
  }

  /**
   * Load and visualize file structure data.
   * 
   * @param {Object|Array} data - File structure data
   * @returns {Promise} Promise that resolves when visualization is complete
   */
  loadData(data) {
    // Clear existing visualization
    while (this.fileStructureGroup.children.length > 0) {
      const child = this.fileStructureGroup.children[0];
      this.fileStructureGroup.remove(child);
      
      if (child.geometry) {
        child.geometry.dispose();
      }
      
      if (child.material) {
        if (Array.isArray(child.material)) {
          child.material.forEach(m => m.dispose());
        } else {
          child.material.dispose();
        }
      }
    }
    
    this.fileNodes = [];
    
    // Process the file structure data
    if (Array.isArray(data)) {
      // Process root-level array
      this._createNodesFromItems(data, this.fileStructureGroup, new THREE.Vector3(0, 0, 0), 0);
    } else if (data && typeof data === 'object') {
      // Process single root object
      this._createNodeFromItem(data, this.fileStructureGroup, new THREE.Vector3(0, 0, 0), 0);
    } else {
      console.error('Invalid data format for visualization', data);
      return Promise.reject(new Error('Invalid data format'));
    }
    
    // Center the camera on the structure
    this.resetCamera();
    
    return Promise.resolve();
  }
  
  /**
   * Create 3D nodes from array of items.
   * 
   * @private
   * @param {Array} items - Array of file/folder items
   * @param {THREE.Object3D} parent - Parent 3D object
   * @param {THREE.Vector3} position - Base position for this level
   * @param {number} depth - Current depth level
   * @returns {Array} Array of created nodes
   */
  _createNodesFromItems(items, parent, position, depth) {
    const nodes = [];
    const nodeSize = this.options.nodeSize;
    const nodeSpacing = this.options.nodeSpacing;
    
    // If we have too many nodes, only show a subset
    const itemsToProcess = items.length > this.options.maxNodesPerLevel 
      ? items.slice(0, this.options.maxNodesPerLevel)
      : items;
    
    // Calculate the total width needed for this level
    const totalWidth = itemsToProcess.length * nodeSpacing;
    const startX = position.x - totalWidth / 2;
    
    // Create nodes for each item
    itemsToProcess.forEach((item, index) => {
      const itemPosition = new THREE.Vector3(
        startX + index * nodeSpacing,
        position.y,
        position.z
      );
      
      const node = this._createNodeFromItem(item, parent, itemPosition, depth);
      nodes.push(node);
    });
    
    return nodes;
  }

  /**
   * Create a 3D node from a single item.
   * 
   * @private
   * @param {Object} item - File/folder item
   * @param {THREE.Object3D} parent - Parent 3D object
   * @param {THREE.Vector3} position - Position for this node
   * @param {number} depth - Current depth level
   * @returns {THREE.Object3D} Created node
   */
  _createNodeFromItem(item, parent, position, depth) {
    const nodeSize = this.options.nodeSize;
    let node;
    
    if (item.type === 'folder' && item.children) {
      // Create folder node
      node = new THREE.Mesh(
        this.sharedGeometries.folder,
        this.sharedMaterials.folder
      );
      
      // Scale based on number of children
      const scale = 0.5 + Math.min(1.5, Math.log(item.children.length + 1) / Math.log(10));
      node.scale.set(scale, scale, scale);
      
      // Add children if depth is not too deep
      if (depth < this.options.maxDepth) {
        const childPosition = new THREE.Vector3(
          position.x,
          position.y - nodeSize * 3,
          position.z + nodeSize * 5
        );
        
        this._createNodesFromItems(item.children, node, childPosition, depth + 1);
      }
    } else {
      // Create file node - get color based on extension
      const ext = this._getFileExtension(item.name);
      const material = this.sharedMaterials.files[ext] || 
                      this.sharedMaterials.files['default'];
      
      node = new THREE.Mesh(
        this.sharedGeometries.file,
        material
      );
      
      // Scale based on file size
      const size = item.size || 0;
      const scale = 0.5 + Math.min(1.5, Math.log(size + 1) / Math.log(10) / 2);
      node.scale.set(scale, scale, scale);
    }
    
    // Set position
    node.position.copy(position);
    
    // Store item data
    node.userData = { 
      item: item,
      depth: depth,
      type: item.type
    };
    
    // Add to parent
    parent.add(node);
    
    // Store for later reference
    this.fileNodes.push(node);
    
    // Add event handlers
    this._addNodeInteractivity(node);
    
    return node;
  }
  
  /**
   * Add interactivity to a node.
   * 
   * @private
   * @param {THREE.Object3D} node - The node to make interactive
   */
  _addNodeInteractivity(node) {
    // We'll use a raycaster in the main class rather than adding listeners
    // to each individual node, for better performance
    const onClick = this.options.onNodeClick;
    const onHover = this.options.onNodeHover;
    
    if (onClick || onHover) {
      this._initRaycaster();
      
      // Set up mouse position tracking if not already done
      if (!this.mouse) {
        this.mouse = new THREE.Vector2();
        
        this.container.addEventListener('mousemove', (event) => {
          // Calculate mouse position in normalized device coordinates
          const rect = this.renderer.domElement.getBoundingClientRect();
          this.mouse.x = ((event.clientX - rect.left) / this.width) * 2 - 1;
          this.mouse.y = -((event.clientY - rect.top) / this.height) * 2 + 1;
          
          this._checkHover();
        });
        
        this.container.addEventListener('click', () => {
          this._checkClick();
        });
      }
    }
  }
  
  /**
   * Initialize raycaster for node interaction.
   * @private
   */
  _initRaycaster() {
    if (!this.raycaster) {
      this.raycaster = new THREE.Raycaster();
      this.selectedNode = null;
      this.hoveredNode = null;
    }
  }
  
  /**
   * Check for hover interactions.
   * @private
   */
  _checkHover() {
    if (!this.raycaster || !this.options.onNodeHover) return;
    
    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(this.fileNodes);
    
    if (intersects.length > 0) {
      const node = intersects[0].object;
      
      // Only trigger if it's a new hover
      if (this.hoveredNode !== node) {
        this.hoveredNode = node;
        this.options.onNodeHover(node.userData.item, node);
      }
    } else if (this.hoveredNode) {
      // Clear hover when no intersection
      const lastHovered = this.hoveredNode;
      this.hoveredNode = null;
      this.options.onNodeHover(null, lastHovered);
    }
  }
  
  /**
   * Check for click interactions.
   * @private
   */
  _checkClick() {
    if (!this.raycaster || !this.options.onNodeClick) return;
    
    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(this.fileNodes);
    
    if (intersects.length > 0) {
      const node = intersects[0].object;
      this.selectedNode = node;
      this.options.onNodeClick(node.userData.item, node);
    }
  }
  
  /**
   * Get file extension from filename.
   * 
   * @private
   * @param {string} filename - File name
   * @returns {string} File extension
   */
  _getFileExtension(filename) {
    const match = filename.match(/\.[0-9a-z]+$/i);
    return match ? match[0].toLowerCase() : 'default';
  }
  
  /**
   * Reset camera to view the entire structure.
   */
  resetCamera() {
    this.camera.position.set(20, 20, 20);
    this.camera.lookAt(0, 0, 0);
    
    if (this.controls) {
      this.controls.reset();
    }
  }
  
  /**
   * Toggle grid visibility.
   * 
   * @param {boolean} visible - Whether the grid should be visible
   */
  toggleGrid(visible) {
    if (this.grid) {
      this.grid.visible = visible;
    }
  }
  
  /**
   * Toggle particles visibility.
   * 
   * @param {boolean} visible - Whether particles should be visible
   */
  toggleParticles(visible) {
    if (this.particles) {
      this.particles.visible = visible;
    }
  }
  
  /**
   * Get current performance statistics.
   * 
   * @returns {Object} Performance statistics
   */
  getStats() {
    return {
      fps: Math.round(this.stats.fps),
      visibleNodes: this.stats.visibleNodes,
      totalNodes: this.fileNodes ? this.fileNodes.length : 0
    };
  }
  
  /**
   * Dispose of all Three.js resources.
   */
  dispose() {
    // Stop animation
    if (this._animationFrame) {
      cancelAnimationFrame(this._animationFrame);
    }
    
    // Remove event listeners
    window.removeEventListener('resize', this._onWindowResize);
    
    // Dispose of geometries and materials
    Object.values(this.sharedGeometries).forEach(g => g.dispose());
    
    Object.values(this.sharedMaterials).forEach(m => {
      if (typeof m === 'object' && m !== null) {
        if (m.dispose) m.dispose();
        if (typeof m === 'object') {
          Object.values(m).forEach(sm => {
            if (sm && sm.dispose) sm.dispose();
          });
        }
      }
    });
    
    // Remove everything from the scene
    while (this.scene.children.length > 0) {
      const object = this.scene.children[0];
      this.scene.remove(object);
    }
    
    // Dispose of renderer
    this.renderer.dispose();
    
    // Remove canvas from DOM
    if (this.renderer.domElement.parentElement) {
      this.renderer.domElement.parentElement.removeChild(this.renderer.domElement);
    }
  }
}

// Export for both ES modules and script tag usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = FileStructureVisualizer;
} else if (typeof define === 'function' && define.amd) {
  define([], function() { return FileStructureVisualizer; });
} else {
  window.FileStructureVisualizer = FileStructureVisualizer;
} 