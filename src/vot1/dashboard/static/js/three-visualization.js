/**
 * Three.js Memory Visualization
 * 
 * This file creates an interactive 3D visualization of memory nodes using Three.js.
 * Each node represents a memory item, with different colors for different types.
 */

class MemoryVisualization {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        
        // Memory node data
        this.nodes = [];
        this.links = [];
        
        // Colors from our palette
        this.colors = {
            conversation: 0x3c1f3c, // Deep Purple
            semantic: 0x005966,     // Teal
            user: 0x999999,         // Medium Gray
            assistant: 0xac202d,    // Red
            selected: 0xffd700,     // Gold
            background: 0x222222,   // Dark background
            ambient: 0x444444       // Ambient light color
        };
        
        // Initialize the visualization
        this.init();
        
        // Start the animation loop
        this.animate();
        
        // Handle window resize
        window.addEventListener('resize', this.onWindowResize.bind(this));
    }
    
    init() {
        // Set up renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setClearColor(this.colors.background);
        this.container.appendChild(this.renderer.domElement);
        
        // Set up scene
        this.scene = new THREE.Scene();
        
        // Set up camera
        this.camera = new THREE.PerspectiveCamera(
            60, 
            this.container.clientWidth / this.container.clientHeight, 
            0.1, 
            1000
        );
        this.camera.position.z = 100;
        
        // Set up lights
        const ambientLight = new THREE.AmbientLight(this.colors.ambient);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(1, 1, 1).normalize();
        this.scene.add(directionalLight);
        
        // Set up controls
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.25;
        this.controls.screenSpacePanning = false;
        this.controls.minDistance = 30;
        this.controls.maxDistance = 200;
        
        // Create a group to hold all nodes
        this.nodesGroup = new THREE.Group();
        this.scene.add(this.nodesGroup);
        
        // Set up raycaster for interactivity
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        this.container.addEventListener('mousemove', this.onMouseMove.bind(this), false);
        this.container.addEventListener('click', this.onMouseClick.bind(this), false);
        
        // Add some placeholder geometry to represent the memory structure
        this.addCenterSphere();
    }
    
    addCenterSphere() {
        // Create a central sphere to represent the system
        const geometry = new THREE.SphereGeometry(5, 32, 32);
        const material = new THREE.MeshPhongMaterial({
            color: this.colors.conversation,
            emissive: this.colors.conversation,
            emissiveIntensity: 0.3,
            shininess: 50
        });
        this.centerSphere = new THREE.Mesh(geometry, material);
        this.nodesGroup.add(this.centerSphere);
        
        // Add some particle effects around the center sphere
        this.addParticles();
    }
    
    addParticles() {
        const particleCount = 300;
        const particles = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        
        for (let i = 0; i < particleCount * 3; i += 3) {
            // Create a sphere of particles
            const radius = 50;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(Math.random() * 2 - 1);
            
            positions[i] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
            positions[i + 2] = radius * Math.cos(phi);
        }
        
        particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        
        const particleMaterial = new THREE.PointsMaterial({
            color: 0xffffff,
            size: 0.5,
            transparent: true,
            opacity: 0.5
        });
        
        this.particleSystem = new THREE.Points(particles, particleMaterial);
        this.scene.add(this.particleSystem);
    }
    
    updateMemoryNodes(memoryData) {
        // Clear existing nodes
        while (this.nodesGroup.children.length > 1) { // Keep the center sphere
            this.nodesGroup.remove(this.nodesGroup.children[this.nodesGroup.children.length - 1]);
        }
        
        // Reset nodes array
        this.nodes = [];
        
        // Process conversation memory
        if (memoryData.conversation) {
            memoryData.conversation.forEach((item, index) => {
                this.addMemoryNode(item, 'conversation', index);
            });
        }
        
        // Process semantic memory
        if (memoryData.semantic) {
            memoryData.semantic.forEach((item, index) => {
                this.addMemoryNode(item, 'semantic', index + (memoryData.conversation ? memoryData.conversation.length : 0));
            });
        }
        
        // Add links between related nodes
        this.addLinks();
    }
    
    addMemoryNode(item, type, index) {
        const nodeRadius = 2;
        const geometry = new THREE.SphereGeometry(nodeRadius, 16, 16);
        
        // Determine color based on memory type and role
        let nodeColor = this.colors[type];
        if (item.role) {
            nodeColor = this.colors[item.role] || nodeColor;
        }
        
        const material = new THREE.MeshPhongMaterial({
            color: nodeColor,
            emissive: nodeColor,
            emissiveIntensity: 0.2,
            shininess: 30
        });
        
        const node = new THREE.Mesh(geometry, material);
        
        // Position nodes in a spiral pattern around the center
        const spiralRadius = 20 + (index * 0.5);
        const angle = index * 0.4;
        const height = (index % 5) - 2;
        
        node.position.set(
            spiralRadius * Math.cos(angle),
            height * 4,
            spiralRadius * Math.sin(angle)
        );
        
        // Store the original color for hover effects
        node.userData = {
            originalColor: nodeColor,
            type: type,
            item: item,
            index: index
        };
        
        this.nodesGroup.add(node);
        this.nodes.push(node);
        
        // Add a pulsing effect for newer nodes
        if (index < 5) {
            this.addNodePulse(node);
        }
    }
    
    addNodePulse(node) {
        // Add a pulsing ring around the node
        const ringGeometry = new THREE.RingGeometry(3, 3.5, 32);
        const ringMaterial = new THREE.MeshBasicMaterial({
            color: node.userData.originalColor,
            transparent: true,
            opacity: 0.5,
            side: THREE.DoubleSide
        });
        
        const ring = new THREE.Mesh(ringGeometry, ringMaterial);
        ring.position.copy(node.position);
        ring.lookAt(this.camera.position);
        ring.userData = { pulse: true, scale: 1, opacity: 0.5 };
        
        this.nodesGroup.add(ring);
    }
    
    addLinks() {
        // Add links between related nodes based on metadata
        // This is a simplified demonstration
        for (let i = 0; i < this.nodes.length; i++) {
            const node = this.nodes[i];
            const item = node.userData.item;
            
            // Connect assistant responses to user messages
            if (item.role === 'assistant' && item.metadata && item.metadata.in_response_to) {
                const sourceId = item.metadata.in_response_to;
                const sourceNode = this.findNodeById(sourceId);
                
                if (sourceNode) {
                    this.createLink(sourceNode, node);
                }
            }
        }
    }
    
    findNodeById(id) {
        for (const node of this.nodes) {
            if (node.userData.item.id === id) {
                return node;
            }
        }
        return null;
    }
    
    createLink(sourceNode, targetNode) {
        const points = [];
        points.push(sourceNode.position);
        points.push(targetNode.position);
        
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const material = new THREE.LineBasicMaterial({
            color: 0x888888,
            transparent: true,
            opacity: 0.3,
            linewidth: 1
        });
        
        const line = new THREE.Line(geometry, material);
        this.nodesGroup.add(line);
        this.links.push(line);
    }
    
    onMouseMove(event) {
        // Calculate mouse position in normalized device coordinates
        const rect = this.container.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / this.container.clientWidth) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / this.container.clientHeight) * 2 + 1;
    }
    
    onMouseClick(event) {
        // Cast a ray and check for intersections with memory nodes
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.nodes);
        
        if (intersects.length > 0) {
            const node = intersects[0].object;
            const item = node.userData.item;
            
            // Display memory details in a popup or sidebar
            console.log('Clicked memory node:', item);
            
            // Change color to indicate selection
            this.nodes.forEach(n => {
                if (n.material) {
                    n.material.color.setHex(n.userData.originalColor);
                    n.material.emissive.setHex(n.userData.originalColor);
                }
            });
            
            node.material.color.setHex(this.colors.selected);
            node.material.emissive.setHex(this.colors.selected);
            
            // Trigger custom event with memory details
            const event = new CustomEvent('memory-selected', { detail: item });
            document.dispatchEvent(event);
        }
    }
    
    animate() {
        requestAnimationFrame(this.animate.bind(this));
        this.render();
    }
    
    render() {
        // Update particle system rotation
        if (this.particleSystem) {
            this.particleSystem.rotation.y += 0.0005;
        }
        
        // Update pulsing rings
        this.nodesGroup.children.forEach(child => {
            if (child.userData && child.userData.pulse) {
                // Increase scale and decrease opacity
                child.userData.scale += 0.01;
                child.userData.opacity -= 0.005;
                
                child.scale.set(child.userData.scale, child.userData.scale, child.userData.scale);
                child.material.opacity = child.userData.opacity;
                
                // Reset when it gets too big or transparent
                if (child.userData.scale > 2 || child.userData.opacity <= 0) {
                    child.userData.scale = 1;
                    child.userData.opacity = 0.5;
                }
                
                // Always look at the camera
                child.lookAt(this.camera.position);
            }
        });
        
        // Update controls
        this.controls.update();
        
        // Render the scene
        this.renderer.render(this.scene, this.camera);
    }
    
    onWindowResize() {
        // Update camera and renderer when window is resized
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }
}

// Create the visualization when the page is loaded
document.addEventListener('DOMContentLoaded', () => {
    const visualization = new MemoryVisualization('memory-visualization');
    
    // Add some demo data
    const demoData = {
        conversation: [
            { id: '1', role: 'user', content: 'Hello, how are you?', timestamp: new Date().toISOString() },
            { id: '2', role: 'assistant', content: 'I\'m doing well, thank you!', metadata: { in_response_to: '1' }, timestamp: new Date().toISOString() },
            { id: '3', role: 'user', content: 'Tell me about VOT1', timestamp: new Date().toISOString() },
            { id: '4', role: 'assistant', content: 'VOT1 is an enhanced Claude integration system...', metadata: { in_response_to: '3' }, timestamp: new Date().toISOString() }
        ],
        semantic: [
            { id: '5', content: 'VOT1 is a powerful integration system for Anthropic\'s Claude AI models', timestamp: new Date().toISOString() },
            { id: '6', content: 'Claude 3.7 Sonnet was released in June 2024', timestamp: new Date().toISOString() }
        ]
    };
    
    visualization.updateMemoryNodes(demoData);
    
    // Expose visualization to global scope for API updates
    window.memoryVisualization = visualization;
}); 