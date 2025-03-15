/**
 * VOTai TRILOGY BRAIN - Memory Network Visualization
 * THREE.js implementation for memory network visualization
 */

class MemoryNetworkVisualization {
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
      memoryViewDistance: 50
    }, options);

    this.nodes = [];
    this.links = [];
    this.hoveredNode = null;
    this.selectedNode = null;
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();
    this.clock = new THREE.Clock();

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

    this.init();
    this.createEventListeners();
    this.animate();
  }

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

    // Create renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.setSize(width, height);
    this.container.appendChild(this.renderer.domElement);

    // Add orbit controls
    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.1;
    this.controls.rotateSpeed = 0.5;
    
    // Create node container
    this.nodesGroup = new THREE.Group();
    this.scene.add(this.nodesGroup);
    
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
  }

  createComposer() {
    this.composer = new THREE.EffectComposer(this.renderer);
    const renderPass = new THREE.RenderPass(this.scene, this.camera);
    this.composer.addPass(renderPass);

    // Bloom effect for glow
    const bloomPass = new THREE.UnrealBloomPass(
      new THREE.Vector2(window.innerWidth, window.innerHeight),
      1.5,   // strength
      0.4,   // radius
      0.85   // threshold
    );
    bloomPass.strength = this.options.glowIntensity;
    this.composer.addPass(bloomPass);
    this.bloomPass = bloomPass;

    // Add film grain effect
    const filmPass = new THREE.FilmPass(
      0.35,   // noise intensity
      0.025,  // scanline intensity
      648,    // scanline count
      false   // grayscale
    );
    filmPass.renderToScreen = true;
    this.composer.addPass(filmPass);
  }

  createBackgroundParticles() {
    const particleCount = 1000;
    const particles = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    
    const color = new THREE.Color();
    
    for (let i = 0; i < positions.length; i += 3) {
      // Position
      positions[i]     = (Math.random() - 0.5) * 1000;
      positions[i + 1] = (Math.random() - 0.5) * 1000;
      positions[i + 2] = (Math.random() - 0.5) * 1000;
      
      // Color
      const baseColor = new THREE.Color(this.importanceColors[Math.floor(Math.random() * this.importanceColors.length)]);
      const mix = Math.random() * 0.3; // Dim the colors
      color.set(this.options.backgroundColor).lerp(baseColor, mix);
      
      colors[i]     = color.r;
      colors[i + 1] = color.g;
      colors[i + 2] = color.b;
    }
    
    particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particles.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    
    const material = new THREE.PointsMaterial({
      size: 0.5,
      vertexColors: true,
      opacity: 0.7,
      transparent: true
    });
    
    this.particleSystem = new THREE.Points(particles, material);
    this.scene.add(this.particleSystem);
  }

  createEventListeners() {
    window.addEventListener('resize', this.onWindowResize.bind(this));
    this.renderer.domElement.addEventListener('mousemove', this.onMouseMove.bind(this));
    this.renderer.domElement.addEventListener('click', this.onMouseClick.bind(this));
  }

  onWindowResize() {
    const { width, height } = this.container.getBoundingClientRect();
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
    this.composer.setSize(width, height);
  }

  onMouseMove(event) {
    // Calculate mouse position in normalized device coordinates
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    // Update the raycaster with the mouse position and camera
    this.raycaster.setFromCamera(this.mouse, this.camera);

    // Find intersections with nodes
    const intersects = this.raycaster.intersectObjects(this.nodesGroup.children);
    
    // Restore previous hovered node appearance
    if (this.hoveredNode && (!intersects.length || intersects[0].object !== this.hoveredNode)) {
      this.restoreNodeAppearance(this.hoveredNode);
      this.hoveredNode = null;
      document.body.style.cursor = 'default';
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
    } else {
      // Hide memory preview when not hovering over a node
      this.hideMemoryPreview();
    }
  }

  onMouseClick(event) {
    // Calculate mouse position in normalized device coordinates
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    // Update the raycaster with the mouse position and camera
    this.raycaster.setFromCamera(this.mouse, this.camera);

    // Find intersections with nodes
    const intersects = this.raycaster.intersectObjects(this.nodesGroup.children);
    
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
      }
    }
  }

  restoreNodeAppearance(node) {
    // Restore original scale
    if (node.userData.originalScale) {
      node.scale.copy(node.userData.originalScale);
    }
    
    // Restore original color
    if (node.material && node.userData.originalColor) {
      node.material.color.set(node.userData.originalColor);
      node.material.emissive.set(node.userData.originalEmissive || 0x000000);
      node.material.emissiveIntensity = node.userData.originalEmissiveIntensity || 0.2;
    }
  }

  showMemoryPreview(memory) {
    // Implementation for showing memory preview (tooltip)
    // This would be handled by a tooltip system not included in this file
    document.dispatchEvent(new CustomEvent('showMemoryPreview', { 
      detail: memory 
    }));
  }

  hideMemoryPreview() {
    // Implementation for hiding memory preview
    document.dispatchEvent(new CustomEvent('hideMemoryPreview'));
  }

  showMemoryInTerminal(memory) {
    // Dispatch event to show memory in terminal
    document.dispatchEvent(new CustomEvent('showMemoryInTerminal', { 
      detail: memory 
    }));
  }

  highlightConnections(node) {
    // Reset all links to default appearance
    this.linksGroup.children.forEach(link => {
      link.material.opacity = this.options.connectionOpacity;
      link.material.linewidth = 1;
    });
    
    // Highlight links connected to the selected node
    const nodeId = node.userData.id;
    
    this.linksGroup.children.forEach(link => {
      if (link.userData.sourceId === nodeId || link.userData.targetId === nodeId) {
        link.material.opacity = 1.0;
        link.material.linewidth = 2;
      }
    });
  }

  animate() {
    requestAnimationFrame(this.animate.bind(this));
    
    const delta = this.clock.getDelta();
    const elapsedTime = this.clock.getElapsedTime();
    
    // Rotate background particles
    if (this.particleSystem) {
      this.particleSystem.rotation.y += this.options.rotationSpeed;
      this.particleSystem.rotation.x += this.options.rotationSpeed * 0.5;
    }
    
    // Update controls
    this.controls.update();
    
    // Pulse effect for nodes
    this.nodesGroup.children.forEach(node => {
      // Skip selected node
      if (node === this.selectedNode || node === this.hoveredNode) return;
      
      // Get original scale or set default
      if (!node.userData.originalScale) {
        node.userData.originalScale = {
          x: node.scale.x,
          y: node.scale.y,
          z: node.scale.z
        };
      }
      
      // Subtle pulse effect based on sin wave
      const pulse = 1 + Math.sin(elapsedTime * 2 + node.userData.id) * 0.05;
      node.scale.set(
        node.userData.originalScale.x * pulse,
        node.userData.originalScale.y * pulse,
        node.userData.originalScale.z * pulse
      );
    });
    
    // Render scene with post-processing
    this.composer.render();
  }

  // API methods to update visualization with memory data
  
  setData(memoryData) {
    // Clear existing nodes and links
    this.clearVisualization();
    
    // Process memory data
    this.processMemoryData(memoryData);
    
    // Layout the network
    this.applyForceLayout();
  }
  
  processMemoryData(memoryData) {
    const nodes = [];
    const links = [];
    
    // Process nodes
    memoryData.memories.forEach((memory, index) => {
      // Create node
      const node = {
        id: memory.id || index,
        level: memory.cacheLevel || 'L1',
        importance: memory.importance || 0.5,
        timestamp: memory.timestamp || Date.now(),
        text: memory.text || '',
        tokenCount: memory.tokenCount || 0,
        x: (Math.random() - 0.5) * 100,
        y: (Math.random() - 0.5) * 100,
        z: (Math.random() - 0.5) * 100
      };
      
      nodes.push(node);
      
      // Process links
      if (memory.connections) {
        memory.connections.forEach(connection => {
          links.push({
            source: node.id,
            target: connection.targetId,
            strength: connection.strength || 0.5
          });
        });
      }
    });
    
    // Limit number of nodes if needed
    if (nodes.length > this.options.maxNodes) {
      nodes.sort((a, b) => b.importance - a.importance);
      nodes.splice(this.options.maxNodes);
      
      // Filter links to only include existing nodes
      const nodeIds = nodes.map(n => n.id);
      links = links.filter(link => 
        nodeIds.includes(link.source) && nodeIds.includes(link.target)
      );
    }
    
    this.nodes = nodes;
    this.links = links;
    
    // Create visualization elements
    this.createVisualizationElements();
  }
  
  clearVisualization() {
    // Remove all nodes
    while (this.nodesGroup.children.length > 0) {
      const node = this.nodesGroup.children[0];
      if (node.material) node.material.dispose();
      if (node.geometry) node.geometry.dispose();
      this.nodesGroup.remove(node);
    }
    
    // Remove all links
    while (this.linksGroup.children.length > 0) {
      const link = this.linksGroup.children[0];
      if (link.material) link.material.dispose();
      if (link.geometry) link.geometry.dispose();
      this.linksGroup.remove(link);
    }
    
    this.nodes = [];
    this.links = [];
    this.hoveredNode = null;
    this.selectedNode = null;
  }
  
  createVisualizationElements() {
    // Create node meshes
    this.nodes.forEach(node => {
      // Determine node appearance based on level and importance
      const levelConfig = this.memoryLevels[node.level] || this.memoryLevels.L3;
      
      // Determine color based on importance
      const importanceIndex = Math.min(
        Math.floor(node.importance * this.importanceColors.length),
        this.importanceColors.length - 1
      );
      const nodeColor = this.importanceColors[importanceIndex];
      
      // Create geometry
      const geometry = new THREE.SphereGeometry(
        this.options.nodeSize * levelConfig.size, 
        16, 
        16
      );
      
      // Create material
      const material = new THREE.MeshStandardMaterial({
        color: nodeColor,
        emissive: nodeColor,
        emissiveIntensity: 0.2,
        roughness: 0.3,
        metalness: 0.8
      });
      
      // Create mesh
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(node.x, node.y, node.z);
      
      // Store original appearance
      mesh.userData = {
        id: node.id,
        memory: node,
        originalColor: nodeColor,
        originalEmissive: nodeColor,
        originalEmissiveIntensity: 0.2
      };
      
      // Add to group
      this.nodesGroup.add(mesh);
    });
    
    // Create link lines
    this.links.forEach(link => {
      // Find source and target nodes
      const sourceNode = this.nodes.find(n => n.id === link.source);
      const targetNode = this.nodes.find(n => n.id === link.target);
      
      if (!sourceNode || !targetNode) return;
      
      // Create line geometry
      const geometry = new THREE.BufferGeometry();
      const positions = new Float32Array([
        sourceNode.x, sourceNode.y, sourceNode.z,
        targetNode.x, targetNode.y, targetNode.z
      ]);
      geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      
      // Determine color based on source node level
      const levelConfig = this.memoryLevels[sourceNode.level] || this.memoryLevels.L3;
      
      // Create line material
      const material = new THREE.LineBasicMaterial({
        color: levelConfig.color,
        opacity: this.options.connectionOpacity * link.strength,
        transparent: true
      });
      
      // Create line
      const line = new THREE.Line(geometry, material);
      
      // Store link data
      line.userData = {
        sourceId: sourceNode.id,
        targetId: targetNode.id,
        strength: link.strength
      };
      
      // Add to group
      this.linksGroup.add(line);
    });
  }
  
  applyForceLayout() {
    // Simple force-directed layout
    // In a real implementation, you would use a more sophisticated algorithm
    // like D3's force layout or a custom WebWorker implementation
    
    // Create node lookup for faster access
    const nodeLookup = {};
    this.nodes.forEach((node, i) => {
      nodeLookup[node.id] = {
        node,
        index: i,
        mesh: this.nodesGroup.children[i]
      };
    });
    
    // Run force simulation for a fixed number of iterations
    const iterations = 100;
    const repulsionStrength = 5;
    const attractionStrength = 0.01;
    const centeringStrength = 0.03;
    
    for (let iteration = 0; iteration < iterations; iteration++) {
      // Calculate repulsion forces between all nodes
      this.nodes.forEach((nodeA, i) => {
        let forceX = 0;
        let forceY = 0;
        let forceZ = 0;
        
        // Repulsion from other nodes
        this.nodes.forEach((nodeB, j) => {
          if (i === j) return;
          
          const dx = nodeA.x - nodeB.x;
          const dy = nodeA.y - nodeB.y;
          const dz = nodeA.z - nodeB.z;
          const distance = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
          
          // Avoid division by very small numbers
          const normalizedDistance = Math.max(distance, 0.1);
          
          // Repulsion force
          const force = repulsionStrength / (normalizedDistance * normalizedDistance);
          
          forceX += dx * force / normalizedDistance;
          forceY += dy * force / normalizedDistance;
          forceZ += dz * force / normalizedDistance;
        });
        
        // Attraction along links
        this.links.forEach(link => {
          if (link.source === nodeA.id) {
            const targetData = nodeLookup[link.target];
            if (targetData) {
              const nodeB = targetData.node;
              const dx = nodeB.x - nodeA.x;
              const dy = nodeB.y - nodeA.y;
              const dz = nodeB.z - nodeA.z;
              const distance = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
              
              forceX += dx * attractionStrength * link.strength;
              forceY += dy * attractionStrength * link.strength;
              forceZ += dz * attractionStrength * link.strength;
            }
          } else if (link.target === nodeA.id) {
            const sourceData = nodeLookup[link.source];
            if (sourceData) {
              const nodeB = sourceData.node;
              const dx = nodeB.x - nodeA.x;
              const dy = nodeB.y - nodeA.y;
              const dz = nodeB.z - nodeA.z;
              const distance = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
              
              forceX += dx * attractionStrength * link.strength;
              forceY += dy * attractionStrength * link.strength;
              forceZ += dz * attractionStrength * link.strength;
            }
          }
        });
        
        // Centering force
        forceX -= nodeA.x * centeringStrength;
        forceY -= nodeA.y * centeringStrength;
        forceZ -= nodeA.z * centeringStrength;
        
        // Apply forces
        nodeA.x += forceX;
        nodeA.y += forceY;
        nodeA.z += forceZ;
      });
    }
    
    // Update mesh positions based on new node positions
    this.nodes.forEach((node, i) => {
      const mesh = this.nodesGroup.children[i];
      mesh.position.set(node.x, node.y, node.z);
    });
    
    // Update link positions
    this.links.forEach((link, i) => {
      const sourceData = nodeLookup[link.source];
      const targetData = nodeLookup[link.target];
      
      if (sourceData && targetData) {
        const line = this.linksGroup.children[i];
        const positions = line.geometry.attributes.position.array;
        
        positions[0] = sourceData.node.x;
        positions[1] = sourceData.node.y;
        positions[2] = sourceData.node.z;
        positions[3] = targetData.node.x;
        positions[4] = targetData.node.y;
        positions[5] = targetData.node.z;
        
        line.geometry.attributes.position.needsUpdate = true;
      }
    });
  }
  
  // Methods to update options
  
  updateGlowIntensity(intensity) {
    this.options.glowIntensity = intensity;
    if (this.bloomPass) {
      this.bloomPass.strength = intensity;
    }
  }
  
  updateAnimationSpeed(speed) {
    this.options.animationSpeed = speed;
  }
  
  updateRotationSpeed(speed) {
    this.options.rotationSpeed = speed * 0.001;
  }
  
  // Add a single memory node to the visualization
  addMemoryNode(memory) {
    // Create node data
    const node = {
      id: memory.id || this.nodes.length,
      level: memory.cacheLevel || 'L1',
      importance: memory.importance || 0.5,
      timestamp: memory.timestamp || Date.now(),
      text: memory.text || '',
      tokenCount: memory.tokenCount || 0,
      x: (Math.random() - 0.5) * 100,
      y: (Math.random() - 0.5) * 100,
      z: (Math.random() - 0.5) * 100
    };
    
    // Add to nodes array
    this.nodes.push(node);
    
    // Determine node appearance
    const levelConfig = this.memoryLevels[node.level] || this.memoryLevels.L3;
    
    // Determine color based on importance
    const importanceIndex = Math.min(
      Math.floor(node.importance * this.importanceColors.length),
      this.importanceColors.length - 1
    );
    const nodeColor = this.importanceColors[importanceIndex];
    
    // Create geometry
    const geometry = new THREE.SphereGeometry(
      this.options.nodeSize * levelConfig.size, 
      16, 
      16
    );
    
    // Create material
    const material = new THREE.MeshStandardMaterial({
      color: nodeColor,
      emissive: nodeColor,
      emissiveIntensity: 0.2,
      roughness: 0.3,
      metalness: 0.8
    });
    
    // Create mesh
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(node.x, node.y, node.z);
    
    // Store original appearance
    mesh.userData = {
      id: node.id,
      memory: node,
      originalColor: nodeColor,
      originalEmissive: nodeColor,
      originalEmissiveIntensity: 0.2
    };
    
    // Add to group
    this.nodesGroup.add(mesh);
    
    // Process any connections
    if (memory.connections) {
      memory.connections.forEach(connection => {
        this.addMemoryLink(node.id, connection.targetId, connection.strength || 0.5);
      });
    }
    
    return node;
  }
  
  // Add a link between memory nodes
  addMemoryLink(sourceId, targetId, strength = 0.5) {
    // Find source and target nodes
    const sourceNode = this.nodes.find(n => n.id === sourceId);
    const targetNode = this.nodes.find(n => n.id === targetId);
    
    if (!sourceNode || !targetNode) return null;
    
    // Add to links array
    const link = {
      source: sourceId,
      target: targetId,
      strength: strength
    };
    
    this.links.push(link);
    
    // Create line geometry
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array([
      sourceNode.x, sourceNode.y, sourceNode.z,
      targetNode.x, targetNode.y, targetNode.z
    ]);
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    // Determine color based on source node level
    const levelConfig = this.memoryLevels[sourceNode.level] || this.memoryLevels.L3;
    
    // Create line material
    const material = new THREE.LineBasicMaterial({
      color: levelConfig.color,
      opacity: this.options.connectionOpacity * strength,
      transparent: true
    });
    
    // Create line
    const line = new THREE.Line(geometry, material);
    
    // Store link data
    line.userData = {
      sourceId: sourceId,
      targetId: targetId,
      strength: strength
    };
    
    // Add to group
    this.linksGroup.add(line);
    
    return link;
  }
  
  // Method to focus camera on a specific node
  focusOnNode(nodeId) {
    const node = this.nodes.find(n => n.id === nodeId);
    if (!node) return;
    
    // Find corresponding mesh
    const meshIndex = this.nodes.findIndex(n => n.id === nodeId);
    const mesh = this.nodesGroup.children[meshIndex];
    
    if (mesh) {
      // Move camera to focus on the node
      const targetPosition = new THREE.Vector3(
        mesh.position.x,
        mesh.position.y,
        mesh.position.z + this.options.memoryViewDistance
      );
      
      // Animate camera movement
      gsap.to(this.camera.position, {
        x: targetPosition.x,
        y: targetPosition.y,
        z: targetPosition.z,
        duration: 1.5,
        ease: "power2.inOut",
        onUpdate: () => {
          this.camera.lookAt(mesh.position);
        }
      });
      
      // Select the node
      if (this.selectedNode && this.selectedNode !== mesh) {
        this.restoreNodeAppearance(this.selectedNode);
      }
      
      this.selectedNode = mesh;
      this.highlightConnections(mesh);
    }
  }
}

// Export the class
window.MemoryNetworkVisualization = MemoryNetworkVisualization; 