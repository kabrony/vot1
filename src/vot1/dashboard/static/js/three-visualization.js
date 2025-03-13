/**
 * VOT1 THREE.js Memory Visualization
 * 
 * This module provides a 3D visualization of the VOT1 memory system using THREE.js.
 * It visualizes memory nodes and relationships in a 3D graph structure that can be
 * navigated and interacted with.
 */

// Global variables
let scene, camera, renderer, controls;
let graph = {nodes: [], links: []};
let nodeObjects = {};
let linkObjects = {};

// Configuration
const config = {
    nodeSizeBase: 5,
    nodeSizeVariation: 2,
    nodeColors: {
        conversation: 0x3366cc,
        semantic: 0x33cc33,
        swarm: 0xcc9933,
        feedback: 0xcc3366,
        default: 0x999999
    },
    highlightColor: 0xffffff,
    linkColor: 0x666666,
    highlightLinkColor: 0xffffff,
    backgroundColor: 0x111111
};

/**
 * Initialize the 3D visualization
 * @param {string} containerId - ID of the container element
 */
function initVisualization(containerId) {
    const container = document.getElementById(containerId);
    
    // Create scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(config.backgroundColor);
    
    // Create camera
    const width = container.clientWidth;
    const height = container.clientHeight;
    camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.z = 150;
    
    // Create renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);
    
    // Add orbit controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.25;
    
    // Add lights
    const ambientLight = new THREE.AmbientLight(0xcccccc, 0.5);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(1, 1, 1).normalize();
    scene.add(directionalLight);
    
    // Add event listeners
    window.addEventListener('resize', onWindowResize, false);
    renderer.domElement.addEventListener('mousemove', onMouseMove, false);
    
    // Start animation loop
    animate();
}

/**
 * Update the memory graph with new data
 * @param {Object} data - Graph data with nodes and links
 */
function updateMemoryGraph(data) {
    // Clear existing graph
    clearGraph();
    
    // Store new graph data
    graph = data;
    
    // Create nodes
    createNodes();
    
    // Create links
    createLinks();
    
    // Update layout
    updateLayout();
}

/**
 * Clear the current graph
 */
function clearGraph() {
    // Remove nodes
    Object.values(nodeObjects).forEach(obj => {
        scene.remove(obj);
    });
    nodeObjects = {};
    
    // Remove links
    Object.values(linkObjects).forEach(obj => {
        scene.remove(obj);
    });
    linkObjects = {};
}

/**
 * Create node objects in the scene
 */
function createNodes() {
    graph.nodes.forEach(node => {
        // Create geometry
        const geometry = new THREE.SphereGeometry(
            config.nodeSizeBase + node.size * config.nodeSizeVariation, 
            16, 16
        );
        
        // Create material with color based on node type
        const material = new THREE.MeshLambertMaterial({
            color: config.nodeColors[node.type] || config.nodeColors.default
        });
        
        // Create mesh
        const mesh = new THREE.Mesh(geometry, material);
        
        // Set position
        mesh.position.set(
            node.x || (Math.random() - 0.5) * 100,
            node.y || (Math.random() - 0.5) * 100,
            node.z || (Math.random() - 0.5) * 100
        );
        
        // Store node data
        mesh.userData = { node: node, material: material };
        
        // Add to scene and store reference
        scene.add(mesh);
        nodeObjects[node.id] = mesh;
    });
}

/**
 * Create link objects in the scene
 */
function createLinks() {
    graph.links.forEach(link => {
        // Get source and target nodes
        const sourceNode = nodeObjects[link.source];
        const targetNode = nodeObjects[link.target];
        
        if (!sourceNode || !targetNode) return;
        
        // Create geometry
        const points = [
            sourceNode.position.clone(),
            targetNode.position.clone()
        ];
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        
        // Create material
        const material = new THREE.LineBasicMaterial({
            color: config.linkColor,
            transparent: true,
            opacity: 0.6
        });
        
        // Create line
        const line = new THREE.Line(geometry, material);
        
        // Store link data
        line.userData = { 
            link: link, 
            material: material,
            source: sourceNode,
            target: targetNode
        };
        
        // Add to scene and store reference
        scene.add(line);
        linkObjects[link.source + '-' + link.target] = line;
    });
}

/**
 * Update the layout of the graph
 */
function updateLayout() {
    // In a real implementation, this would apply a force-directed
    // layout algorithm to position nodes. This is a simplified version.
    
    // For demonstration, just arrange nodes in a random sphere
    const radius = 100;
    graph.nodes.forEach(node => {
        const mesh = nodeObjects[node.id];
        if (!mesh) return;
        
        // Only update position if not already set
        if (!node.x || !node.y || !node.z) {
            const phi = Math.acos(-1 + 2 * Math.random());
            const theta = 2 * Math.PI * Math.random();
            
            mesh.position.x = radius * Math.sin(phi) * Math.cos(theta);
            mesh.position.y = radius * Math.sin(phi) * Math.sin(theta);
            mesh.position.z = radius * Math.cos(phi);
            
            // Update node data
            node.x = mesh.position.x;
            node.y = mesh.position.y;
            node.z = mesh.position.z;
        }
    });
    
    // Update links to follow nodes
    updateLinks();
}

/**
 * Update link positions to follow nodes
 */
function updateLinks() {
    Object.values(linkObjects).forEach(line => {
        const sourceNode = line.userData.source;
        const targetNode = line.userData.target;
        
        // Update line geometry to connect nodes
        const points = [
            sourceNode.position.clone(),
            targetNode.position.clone()
        ];
        
        // Update geometry
        line.geometry.dispose();
        line.geometry = new THREE.BufferGeometry().setFromPoints(points);
    });
}

/**
 * Handle window resize
 */
function onWindowResize() {
    const container = renderer.domElement.parentElement;
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    
    renderer.setSize(width, height);
}

/**
 * Handle mouse movement for interaction
 */
function onMouseMove(event) {
    // Get mouse position
    const rect = renderer.domElement.getBoundingClientRect();
    const mouseX = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    const mouseY = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    
    // Create raycaster
    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera({ x: mouseX, y: mouseY }, camera);
    
    // Find intersections with nodes
    const intersects = raycaster.intersectObjects(Object.values(nodeObjects));
    
    // Reset all nodes and links to default appearance
    Object.values(nodeObjects).forEach(node => {
        node.userData.material.color.setHex(
            config.nodeColors[node.userData.node.type] || config.nodeColors.default
        );
    });
    
    Object.values(linkObjects).forEach(link => {
        link.userData.material.color.setHex(config.linkColor);
        link.userData.material.opacity = 0.6;
    });
    
    // Highlight intersected node and its links
    if (intersects.length > 0) {
        const node = intersects[0].object;
        node.userData.material.color.setHex(config.highlightColor);
        
        // Highlight connected links
        const nodeId = node.userData.node.id;
        
        Object.values(linkObjects).forEach(link => {
            const linkData = link.userData.link;
            if (linkData.source === nodeId || linkData.target === nodeId) {
                link.userData.material.color.setHex(config.highlightLinkColor);
                link.userData.material.opacity = 1.0;
            }
        });
    }
}

/**
 * Animation loop
 */
function animate() {
    requestAnimationFrame(animate);
    
    // Update controls
    controls.update();
    
    // Render scene
    renderer.render(scene, camera);
}

// Export public API
export {
    initVisualization,
    updateMemoryGraph
};