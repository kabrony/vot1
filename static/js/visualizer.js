/**
 * VOT1 File Structure Visualizer
 * THREE.js visualization for project file structure
 */

const Visualizer = {
  // State
  scene: null,
  camera: null,
  renderer: null,
  controls: null,
  nodes: {},
  lines: [],
  raycaster: new THREE.Raycaster(),
  mouse: new THREE.Vector2(),
  depth: 10,
  theme: 'cyberpunk',
  initialized: false,
  
  // Config
  config: {
    nodeSize: {
      directory: 5,
      file: 3
    },
    nodeMaterial: {
      directory: null,
      file: null
    },
    nodeGeometry: {
      directory: null,
      file: null
    },
    colors: {
      cyberpunk: {
        background: 0x080215,
        directory: 0x00ffff,
        file: 0xff00cc,
        highlight: 0x00ff00,
        line: 0x00ffff
      },
      dark: {
        background: 0x121212,
        directory: 0x007bff,
        file: 0x6c757d,
        highlight: 0x28a745,
        line: 0x007bff
      },
      light: {
        background: 0xf0f0f0,
        directory: 0x007bff,
        file: 0x6c757d,
        highlight: 0x28a745,
        line: 0x007bff
      }
    }
  },
  
  // Initialize visualization
  initVisualization() {
    console.log('Initializing visualization...');
    
    // Get container
    const container = document.getElementById('visualization-3d');
    if (!container) {
      console.error('Visualization container not found');
      return;
    }
    
    // Clear container
    container.innerHTML = '';
    
    // Initialize only once
    if (!this.initialized) {
      // Set up scene
      this.scene = new THREE.Scene();
      this.scene.background = new THREE.Color(this.config.colors[this.theme].background);
      
      // Set up camera
      this.camera = new THREE.PerspectiveCamera(
        75,
        container.clientWidth / container.clientHeight,
        0.1,
        1000
      );
      this.camera.position.z = 100;
      
      // Set up renderer
      this.renderer = new THREE.WebGLRenderer({ antialias: true });
      this.renderer.setSize(container.clientWidth, container.clientHeight);
      container.appendChild(this.renderer.domElement);
      
      // Set up controls
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.25;
      this.controls.screenSpacePanning = true;
      
      // Add event listeners
      window.addEventListener('resize', this.onWindowResize.bind(this));
      this.renderer.domElement.addEventListener('mousemove', this.onMouseMove.bind(this));
      this.renderer.domElement.addEventListener('click', this.onClick.bind(this));
      
      // Create materials and geometries
      this.createMaterials();
      
      this.initialized = true;
    }
    
    // Create grid
    this.createGrid();
    
    // Fetch and render structure
    this.fetchStructure();
    
    // Start animation loop
    this.animate();
  },
  
  // Create reusable materials and geometries
  createMaterials() {
    // Directory geometry (larger sphere)
    this.config.nodeGeometry.directory = new THREE.SphereGeometry(
      this.config.nodeSize.directory,
      16,
      16
    );
    
    // File geometry (smaller sphere)
    this.config.nodeGeometry.file = new THREE.SphereGeometry(
      this.config.nodeSize.file,
      12,
      12
    );
    
    // Directory material
    this.config.nodeMaterial.directory = new THREE.MeshPhongMaterial({
      color: this.config.colors[this.theme].directory,
      emissive: this.config.colors[this.theme].directory,
      emissiveIntensity: 0.5,
      shininess: 50
    });
    
    // File material
    this.config.nodeMaterial.file = new THREE.MeshPhongMaterial({
      color: this.config.colors[this.theme].file,
      emissive: this.config.colors[this.theme].file,
      emissiveIntensity: 0.3,
      shininess: 30
    });
  },
  
  // Create background grid
  createGrid() {
    // Remove existing grid
    const existingGrid = this.scene.getObjectByName('grid');
    if (existingGrid) {
      this.scene.remove(existingGrid);
    }
    
    // Create new grid
    const gridHelper = new THREE.GridHelper(
      500,
      50,
      new THREE.Color(this.config.colors[this.theme].line),
      new THREE.Color(this.config.colors[this.theme].line)
    );
    gridHelper.name = 'grid';
    gridHelper.material.opacity = 0.2;
    gridHelper.material.transparent = true;
    this.scene.add(gridHelper);
    
    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    this.scene.add(ambientLight);
    
    // Add directional light
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(0, 20, 20);
    this.scene.add(directionalLight);
    
    // Add point lights for cyberpunk effect
    const pointLight1 = new THREE.PointLight(
      this.config.colors[this.theme].directory,
      1,
      150
    );
    pointLight1.position.set(50, 50, 50);
    this.scene.add(pointLight1);
    
    const pointLight2 = new THREE.PointLight(
      this.config.colors[this.theme].file,
      1,
      150
    );
    pointLight2.position.set(-50, -50, 50);
    this.scene.add(pointLight2);
  },
  
  // Fetch structure data from API
  fetchStructure() {
    // Show loading indicator
    this.showLoading(true);
    
    // Fetch data
    fetch(`/api/file-structure?max_depth=${this.depth}`)
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          // Render structure
          this.renderStructure(data.structure);
          
          // Hide loading indicator
          this.showLoading(false);
        } else {
          console.error('Error fetching structure:', data.error);
          Dashboard.showToast(`Error: ${data.error}`, 'error');
          this.showLoading(false);
        }
      })
      .catch(error => {
        console.error('Error fetching structure:', error);
        Dashboard.showToast('Could not fetch structure data', 'error');
        this.showLoading(false);
      });
  },
  
  // Render structure from data
  renderStructure(data) {
    // Clear existing nodes and lines
    this.clearStructure();
    
    // Root position
    const rootPosition = new THREE.Vector3(0, 0, 0);
    
    // Create root node
    const rootNode = {
      name: data.name || 'root',
      path: data.path || '/',
      type: 'directory',
      object: this.createNode('directory', rootPosition)
    };
    
    // Add to scene
    this.scene.add(rootNode.object);
    
    // Store in nodes
    this.nodes[rootNode.path] = rootNode;
    
    // Recursively create children
    if (data.items && data.items.length > 0) {
      this.createChildren(data.items, rootNode, 0, Math.PI * 2, 20);
    }
    
    // Add label to root node
    this.addLabel(rootNode);
  },
  
  // Recursively create children nodes
  createChildren(items, parent, startAngle, endAngle, distance) {
    // Skip if no items
    if (!items || items.length === 0) return;
    
    // Calculate angle step
    const angleStep = (endAngle - startAngle) / items.length;
    
    // Create nodes for each item
    items.forEach((item, index) => {
      // Calculate position
      const angle = startAngle + angleStep * index;
      const x = Math.cos(angle) * distance;
      const z = Math.sin(angle) * distance;
      const y = parent.object.position.y - (item.type === 'directory' ? 15 : 10);
      
      const position = new THREE.Vector3(x, y, z);
      
      // Create node
      const node = {
        name: item.name,
        path: item.path,
        type: item.type,
        object: this.createNode(item.type, position)
      };
      
      // Add to scene
      this.scene.add(node.object);
      
      // Store in nodes
      this.nodes[node.path] = node;
      
      // Create line connecting to parent
      this.createLine(parent.object.position, node.object.position);
      
      // Recursively create children if this is a directory
      if (item.type === 'directory' && item.children && item.children.length > 0) {
        // Only create children if within depth limit
        const depth = node.path.split('/').length - 1;
        if (depth < this.depth) {
          this.createChildren(
            item.children,
            node,
            angle - angleStep / 2,
            angle + angleStep / 2,
            distance * 0.8
          );
        }
      }
      
      // Add label
      this.addLabel(node);
    });
  },
  
  // Create a node
  createNode(type, position) {
    // Create mesh
    const geometry = this.config.nodeGeometry[type];
    const material = this.config.nodeMaterial[type].clone();
    
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.copy(position);
    
    return mesh;
  },
  
  // Create a line connecting two positions
  createLine(start, end) {
    // Create geometry
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      'position',
      new THREE.Float32BufferAttribute([
        start.x, start.y, start.z,
        end.x, end.y, end.z
      ], 3)
    );
    
    // Create material
    const material = new THREE.LineBasicMaterial({
      color: this.config.colors[this.theme].line,
      opacity: 0.6,
      transparent: true
    });
    
    // Create line
    const line = new THREE.Line(geometry, material);
    
    // Add to scene
    this.scene.add(line);
    
    // Store in lines
    this.lines.push(line);
    
    return line;
  },
  
  // Add text label to node
  addLabel(node) {
    // Skip if no object
    if (!node.object) return;
    
    // Create canvas
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 256;
    canvas.height = 64;
    
    // Set canvas background (transparent)
    context.fillStyle = 'rgba(0, 0, 0, 0)';
    context.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw text
    context.font = 'Bold 24px Arial';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    
    // Set text color based on theme
    if (this.theme === 'light') {
      context.fillStyle = '#000000';
    } else {
      context.fillStyle = '#ffffff';
    }
    
    // Draw text
    context.fillText(node.name, canvas.width / 2, canvas.height / 2);
    
    // Create texture
    const texture = new THREE.CanvasTexture(canvas);
    
    // Create material
    const material = new THREE.SpriteMaterial({
      map: texture,
      transparent: true
    });
    
    // Create sprite
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(10, 2.5, 1);
    
    // Position sprite above node
    sprite.position.set(
      node.object.position.x,
      node.object.position.y + (node.type === 'directory' ? 7 : 5),
      node.object.position.z
    );
    
    // Add to scene
    this.scene.add(sprite);
  },
  
  // Clear structure (remove nodes and lines)
  clearStructure() {
    // Remove nodes
    Object.values(this.nodes).forEach(node => {
      if (node.object) {
        this.scene.remove(node.object);
      }
    });
    
    // Remove lines
    this.lines.forEach(line => {
      this.scene.remove(line);
    });
    
    // Reset arrays
    this.nodes = {};
    this.lines = [];
  },
  
  // Show/hide loading indicator
  showLoading(show) {
    const container = document.getElementById('visualization-3d');
    
    if (show) {
      // Create and show loading indicator
      let loading = container.querySelector('.loading-indicator');
      
      if (!loading) {
        loading = document.createElement('div');
        loading.className = 'loading-indicator';
        loading.innerHTML = `
          <div class="loading-spinner"></div>
          <p>Loading visualization...</p>
        `;
        container.appendChild(loading);
      }
      
      loading.style.display = 'flex';
    } else {
      // Hide loading indicator
      const loading = container.querySelector('.loading-indicator');
      if (loading) {
        loading.style.display = 'none';
      }
    }
  },
  
  // Window resize handler
  onWindowResize() {
    const container = document.getElementById('visualization-3d');
    if (!container || !this.camera || !this.renderer) return;
    
    // Update camera
    this.camera.aspect = container.clientWidth / container.clientHeight;
    this.camera.updateProjectionMatrix();
    
    // Update renderer
    this.renderer.setSize(container.clientWidth, container.clientHeight);
  },
  
  // Mouse move handler
  onMouseMove(event) {
    // Skip if not initialized
    if (!this.initialized) return;
    
    // Calculate mouse position
    const container = document.getElementById('visualization-3d');
    const rect = container.getBoundingClientRect();
    
    this.mouse.x = ((event.clientX - rect.left) / container.clientWidth) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / container.clientHeight) * 2 + 1;
    
    // Check intersections
    this.checkIntersections();
  },
  
  // Click handler
  onClick() {
    // Skip if not initialized
    if (!this.initialized) return;
    
    // Check intersections
    const intersectedNode = this.checkIntersections();
    
    // Show details if node is clicked
    if (intersectedNode) {
      this.showNodeDetails(intersectedNode);
    }
  },
  
  // Check for intersections with mouse
  checkIntersections() {
    // Skip if not initialized
    if (!this.scene || !this.camera) return null;
    
    // Update raycaster
    this.raycaster.setFromCamera(this.mouse, this.camera);
    
    // Get all meshes in the scene
    const meshes = [];
    this.scene.traverse(object => {
      if (object instanceof THREE.Mesh) {
        meshes.push(object);
      }
    });
    
    // Check intersections
    const intersects = this.raycaster.intersectObjects(meshes);
    
    // Reset all node colors
    Object.values(this.nodes).forEach(node => {
      if (node.object && node.object.material) {
        node.object.material.emissiveIntensity = node.type === 'directory' ? 0.5 : 0.3;
      }
    });
    
    // Highlight intersected node
    if (intersects.length > 0) {
      const object = intersects[0].object;
      
      // Find node
      const node = Object.values(this.nodes).find(n => n.object === object);
      
      if (node) {
        // Highlight node
        node.object.material.emissiveIntensity = 1;
        
        return node;
      }
    }
    
    return null;
  },
  
  // Show node details
  showNodeDetails(node) {
    // Get details container
    const detailsContainer = document.getElementById('node-details');
    if (!detailsContainer) return;
    
    // Set details
    detailsContainer.innerHTML = `
      <p><strong>Name:</strong> ${node.name}</p>
      <p><strong>Type:</strong> ${node.type}</p>
      <p><strong>Path:</strong> ${node.path}</p>
    `;
  },
  
  // Animation loop
  animate() {
    requestAnimationFrame(this.animate.bind(this));
    
    // Skip if not initialized
    if (!this.initialized) return;
    
    // Update controls
    if (this.controls) {
      this.controls.update();
    }
    
    // Render scene
    if (this.scene && this.camera && this.renderer) {
      this.renderer.render(this.scene, this.camera);
    }
  },
  
  // Set visualization depth
  setDepth(depth) {
    this.depth = parseInt(depth);
    this.refreshVisualization();
  },
  
  // Set visualization theme
  setTheme(theme) {
    this.theme = theme;
    
    // Update colors
    if (this.config.nodeMaterial.directory) {
      this.config.nodeMaterial.directory.color.setHex(this.config.colors[theme].directory);
      this.config.nodeMaterial.directory.emissive.setHex(this.config.colors[theme].directory);
    }
    
    if (this.config.nodeMaterial.file) {
      this.config.nodeMaterial.file.color.setHex(this.config.colors[theme].file);
      this.config.nodeMaterial.file.emissive.setHex(this.config.colors[theme].file);
    }
    
    // Update background
    if (this.scene) {
      this.scene.background.setHex(this.config.colors[theme].background);
    }
    
    // Update grid
    this.createGrid();
    
    // Refresh visualization
    this.refreshVisualization();
  },
  
  // Refresh visualization
  refreshVisualization() {
    // Skip if not initialized
    if (!this.initialized) return;
    
    // Fetch structure
    this.fetchStructure();
  }
};

// Register initialization on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  // Initialize only when dashboard is active
  if (Dashboard && Dashboard.activePanel === 'visualization-panel') {
    Visualizer.initVisualization();
  }
}); 