/**
 * VOT1 THREE.js Memory Visualization
 * 
 * This module provides a 3D visualization of the VOT1 memory system using THREE.js.
 * It visualizes memory nodes and relationships in a 3D graph structure with a
 * cyberpunk aesthetic featuring neon colors, glow effects, and an immersive grid environment.
 */

// Global variables
let scene, camera, renderer, controls;
let graph = {nodes: [], links: []};
let nodeObjects = {};
let linkObjects = {};
let particles, grid; 
let raycaster, mouse;
let clock, elapsedTime = 0;
let selectedNode = null;

// Configuration
const config = {
    nodeSizeBase: 6,
    nodeSizeVariation: 3,
    nodeColors: {
        conversation: 0x00ffff, // Cyan
        semantic: 0xff00ff,     // Magenta
        swarm: 0x00ff8f,        // Neon green
        feedback: 0xffff00,     // Yellow
        default: 0x8844ff       // Purple
    },
    highlightColor: 0xffffff,    // White
    linkColor: 0x44bbff,         // Blue
    highlightLinkColor: 0xff44bb, // Pink
    backgroundColor: 0x080808,   // Almost black
    glowIntensity: 0.8,          // Glow strength
    glowSize: 2.0,               // Glow size multiplier
    particleCount: 1000,         // Background particles
    gridColor: 0x0088ff,         // Grid color
    gridOpacity: 0.15,           // Grid opacity
    cameraDistance: 150,         // Initial camera distance
    animationSpeed: 0.5          // Animation speed multiplier
};

// Core visualization variables
let container, nodes = [], connections = [];
let visualizationReady = false;
let isAnimating = true;
let nodeGroups = {};
let memoryData = null;
let stats;
let composer, effectFXAA, bloomPass;

/**
 * Initialize the 3D visualization
 * @param {string} containerId - ID of the container element
 */
function initVisualization(containerId) {
    const container = document.getElementById(containerId);
    
    // Initialize clock for animations
    clock = new THREE.Clock();
    
    // Create scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(config.backgroundColor);
    
    // Create camera
    const width = container.clientWidth;
    const height = container.clientHeight;
    camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.z = config.cameraDistance;
    
    // Create renderer with antialiasing and high precision
    renderer = new THREE.WebGLRenderer({ 
        antialias: true,
        alpha: true,
        logarithmicDepthBuffer: true
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);
    
    // Add orbit controls with damping
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.rotateSpeed = 0.7;
    controls.zoomSpeed = 1.2;
    
    // Setup raycaster for interaction
    raycaster = new THREE.Raycaster();
    mouse = new THREE.Vector2();
    
    // Add lights
    addLights();
    
    // Create cyberpunk environment
    createEnvironment();
    
    // Add event listeners
    setupEventListeners(container);
    
    // Start animation loop
    animate();
    
    // Log initialization
    console.log("VOT1 Memory Visualization initialized");
}

// Initialize post-processing effects
function initPostProcessing() {
    try {
        composer = new THREE.EffectComposer(renderer);
        const renderPass = new THREE.RenderPass(scene, camera);
        composer.addPass(renderPass);
        
        // Add FXAA for anti-aliasing
        if (config.fxaaEnabled) {
            effectFXAA = new THREE.ShaderPass(THREE.FXAAShader);
            effectFXAA.uniforms['resolution'].value.set(
                1 / (container.clientWidth * renderer.getPixelRatio()),
                1 / (container.clientHeight * renderer.getPixelRatio())
            );
            composer.addPass(effectFXAA);
        }
        
        // Add bloom effect
        bloomPass = new THREE.UnrealBloomPass(
            new THREE.Vector2(container.clientWidth, container.clientHeight),
            config.bloomStrength,
            config.bloomRadius,
            config.bloomThreshold
        );
        composer.addPass(bloomPass);
        
        console.log('Post-processing initialized');
    } catch (error) {
        console.warn('Post-processing initialization failed:', error);
        config.postProcessing = false;
    }
}

// Initialize node groups for different types of nodes
function initNodeGroups() {
    // Create groups for different node types
    const types = ['conversation', 'semantic', 'swarm', 'feedback'];
    
    types.forEach(type => {
        nodeGroups[type] = new THREE.Group();
        nodeGroups[type].name = `${type}-nodes`;
        scene.add(nodeGroups[type]);
    });

    // Create a group for connections
    nodeGroups['connections'] = new THREE.Group();
    nodeGroups['connections'].name = 'connections';
    scene.add(nodeGroups['connections']);
}

// Load memory data from API or use sample data
function loadMemoryData() {
    // Try to load from API first
    fetch('/api/memories/graph')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            memoryData = data;
            console.log('Loaded memory data from API:', data);
            createVisualizationFromData(data);
        })
        .catch(error => {
            console.warn('Failed to load data from API, using sample data instead:', error);
            // Use sample data
            memoryData = generateSampleData();
            createVisualizationFromData(memoryData);
        });
}

// Generate sample memory data for development/testing
function generateSampleData() {
    console.log('Generating sample memory data...');
    
    const types = ['conversation', 'semantic', 'swarm', 'feedback'];
    const sampleData = {
        nodes: [],
        connections: []
    };
    
    // Generate sample nodes
    const nodeCount = 100;
    for (let i = 0; i < nodeCount; i++) {
        const type = types[Math.floor(Math.random() * types.length)];
        const node = {
            id: `node-${i}`,
            type: type,
            label: `${type.charAt(0).toUpperCase() + type.slice(1)} ${i}`,
            importance: Math.random(),
            timestamp: new Date(Date.now() - Math.random() * 604800000).toISOString(),
            data: {
                content: `Sample content for ${type} ${i}`,
                embedding: Array.from({length: 3}, () => Math.random() * 2 - 1)
            }
        };
        sampleData.nodes.push(node);
    }
    
    // Generate sample connections (edges)
    const connectionCount = Math.min(nodeCount * 3, 200);
    for (let i = 0; i < connectionCount; i++) {
        const sourceIndex = Math.floor(Math.random() * nodeCount);
        let targetIndex;
        do {
            targetIndex = Math.floor(Math.random() * nodeCount);
        } while (targetIndex === sourceIndex);
        
        const connection = {
            id: `connection-${i}`,
            source: sampleData.nodes[sourceIndex].id,
            target: sampleData.nodes[targetIndex].id,
            strength: Math.random(),
            type: Math.random() > 0.5 ? 'semantic' : 'causal'
        };
        sampleData.connections.push(connection);
    }
    
    return sampleData;
}

// Create visualization from memory data
function createVisualizationFromData(data) {
    // Clear existing visualization
    clearVisualization();
    
    // Create nodes
    if (data.nodes && data.nodes.length > 0) {
        createNodes(data.nodes);
    }
    
    // Create connections
    if (data.connections && data.connections.length > 0) {
        createConnections(data.connections, data.nodes);
    }
    
    // Apply force-directed layout
    if (config.clusteringEnabled) {
        applyForceDirectedLayout();
    }
    
    // Update stats display
    updateStats(data);
}

// Clear existing visualization
function clearVisualization() {
    // Properly dispose of geometries and materials
    nodes.forEach(node => {
        if (node.geometry) node.geometry.dispose();
        if (node.material) {
            if (Array.isArray(node.material)) {
                node.material.forEach(mat => mat.dispose());
            } else {
                node.material.dispose();
            }
        }
        scene.remove(node);
    });
    nodes = [];
    
    // Dispose of connection geometries and materials
    connections.forEach(connection => {
        if (connection.geometry) connection.geometry.dispose();
        if (connection.material) connection.material.dispose();
        scene.remove(connection);
    });
    connections = [];
    
    // Clear node groups
    Object.values(nodeGroups).forEach(group => {
        while (group.children.length > 0) {
            const child = group.children[0];
            if (child.geometry) child.geometry.dispose();
            if (child.material) {
                if (Array.isArray(child.material)) {
                    child.material.forEach(mat => mat.dispose());
                } else {
                    child.material.dispose();
                }
            }
            group.remove(child);
        }
    });
    
    // Reset selected node
    selectedNode = null;
    
    // Force garbage collection
    if (renderer) renderer.info.reset();
}

// Create 3D nodes from data
function createNodes(nodesData) {
    // Limit the number of nodes to prevent performance issues
    const nodesToRender = nodesData.slice(0, config.maxNodes);
    
    // Use instanced mesh for better performance if there are many nodes
    const useInstancing = nodesToRender.length > 50;
    let instancedMeshes = {};
    
    if (useInstancing) {
        // Setup instanced meshes for each type
        const types = ['conversation', 'semantic', 'swarm', 'feedback'];
        
        types.forEach(type => {
            // Create geometry
            const geometry = new THREE.SphereGeometry(1.0, 32, 32);
            
            // Create material with proper color space
            const material = new THREE.MeshStandardMaterial({
                color: config.nodeColors[type] || config.nodeColors.conversation,
                emissive: config.nodeColors[type] || config.nodeColors.conversation,
                emissiveIntensity: config.glowIntensity,
                metalness: 0.8,
                roughness: 0.2,
                toneMapped: true
            });
            
            // Create instanced mesh
            const count = nodesToRender.filter(node => (node.type || 'conversation') === type).length;
            if (count > 0) {
                const instancedMesh = new THREE.InstancedMesh(geometry, material, count);
                instancedMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
                instancedMesh.count = 0; // Start with 0 and increment as we add instances
                instancedMeshes[type] = instancedMesh;
                nodeGroups[type].add(instancedMesh);
            }
        });
    }
    
    // Create dummy for transformation matrix
    const dummy = new THREE.Object3D();
    
    nodesToRender.forEach((nodeData, index) => {
        // Determine node type and appearance
        const type = nodeData.type || 'conversation';
        const importance = nodeData.importance || Math.random();
        const size = config.nodeSizeBase + (config.nodeSizeVariation - config.nodeSizeBase) * importance;
        
        // Position node (will be adjusted by force-directed layout)
        const position = nodeData.data && nodeData.data.embedding ? 
            new THREE.Vector3(...nodeData.data.embedding.map(v => v * 50)) : 
            new THREE.Vector3(
                (Math.random() - 0.5) * 100,
                (Math.random() - 0.5) * 100,
                (Math.random() - 0.5) * 100
            );
        
        if (useInstancing && instancedMeshes[type]) {
            // Set position and scale in instanced mesh
            dummy.position.copy(position);
            dummy.scale.set(size, size, size);
            dummy.updateMatrix();
            
            const instancedMesh = instancedMeshes[type];
            const instanceId = instancedMesh.count;
            
            instancedMesh.setMatrixAt(instanceId, dummy.matrix);
            instancedMesh.count++;
            
            // Store node data
            if (!instancedMesh.userData.nodes) {
                instancedMesh.userData.nodes = [];
            }
            
            instancedMesh.userData.nodes.push({
                ...nodeData,
                originalPosition: position.clone(),
                index: instanceId,
                size: size,
                connections: 0
            });
            
            // Add to tracking array as a reference to the instanced mesh
            const nodeReference = {
                isInstancedReference: true,
                instancedMesh: instancedMesh,
                instanceId: instanceId,
                position: position.clone(),
                userData: {
                    ...nodeData,
                    originalPosition: position.clone(),
                    index: instanceId,
                    size: size,
                    connections: 0
                }
            };
            
            nodes.push(nodeReference);
            
        } else {
            // Create geometry
            const geometry = new THREE.SphereGeometry(size, 32, 32);
            
            // Create material with proper color encoding
            const material = new THREE.MeshStandardMaterial({
                color: config.nodeColors[type] || config.nodeColors.conversation,
                emissive: config.nodeColors[type] || config.nodeColors.conversation,
                emissiveIntensity: config.glowIntensity * importance,
                metalness: 0.8,
                roughness: 0.2,
                toneMapped: true
            });
            
            // Create mesh
            const node = new THREE.Mesh(geometry, material);
            node.position.copy(position);
            
            // Store node data
            node.userData = {
                ...nodeData,
                originalPosition: position.clone(),
                index: index,
                size: size,
                connections: 0
            };
            
            // Add to scene and tracking arrays
            nodeGroups[type].add(node);
            nodes.push(node);
        }
    });
    
    // Update instanced matrix if using instancing
    if (useInstancing) {
        Object.values(instancedMeshes).forEach(mesh => {
            if (mesh) mesh.instanceMatrix.needsUpdate = true;
        });
    }
    
    console.log(`Created ${nodes.length} nodes${useInstancing ? ' using instanced rendering' : ''}`);
}

// Create connections between nodes
function createConnections(connectionsData, nodesData) {
    // Create map of node IDs to indices
    const nodeMap = {};
    nodesData.forEach((node, index) => {
        nodeMap[node.id] = index;
    });
    
    // Use line segments for better performance with many connections
    const useLineSegments = connectionsData.length > 100;
    
    if (useLineSegments) {
        // Group connections by type for better batching
        const connectionsByType = {
            'semantic': [],
            'causal': []
        };
        
        // Process connections and group them
        connectionsData.slice(0, config.maxConnections).forEach(connectionData => {
            const sourceIndex = nodeMap[connectionData.source];
            const targetIndex = nodeMap[connectionData.target];
            
            // Skip if source or target node doesn't exist
            if (sourceIndex === undefined || targetIndex === undefined) return;
            if (sourceIndex >= nodes.length || targetIndex >= nodes.length) return;
            
            const sourceNode = nodes[sourceIndex];
            const targetNode = nodes[targetIndex];
            
            // Skip if source or target node is the same
            if (sourceNode === targetNode) return;
            
            // Update connection count
            sourceNode.userData.connections = (sourceNode.userData.connections || 0) + 1;
            targetNode.userData.connections = (targetNode.userData.connections || 0) + 1;
            
            // Get positions
            const sourcePosition = sourceNode.isInstancedReference ? 
                sourceNode.position : sourceNode.position.clone();
            
            const targetPosition = targetNode.isInstancedReference ? 
                targetNode.position : targetNode.position.clone();
            
            // Add to connection type group
            const type = connectionData.type || 'semantic';
            
            connectionsByType[type].push({
                sourcePosition,
                targetPosition,
                sourceNode,
                targetNode,
                userData: connectionData,
                strength: connectionData.strength || 0.5
            });
        });
        
        // Create line segments for each connection type
        Object.entries(connectionsByType).forEach(([type, connections]) => {
            if (connections.length === 0) return;
            
            // Create geometry for all connections of this type
            const positions = new Float32Array(connections.length * 6); // 2 points per connection, 3 coords per point
            const colors = new Float32Array(connections.length * 6); // 2 colors per connection, 3 values per color
            
            let color;
            if (type === 'semantic') {
                color = new THREE.Color(0x43e97b);
            } else {
                color = new THREE.Color(0xf83a3a);
            }
            
            // Fill position and color arrays
            connections.forEach((conn, i) => {
                const idx = i * 6;
                
                // Source position
                positions[idx] = conn.sourcePosition.x;
                positions[idx + 1] = conn.sourcePosition.y;
                positions[idx + 2] = conn.sourcePosition.z;
                
                // Target position
                positions[idx + 3] = conn.targetPosition.x;
                positions[idx + 4] = conn.targetPosition.y;
                positions[idx + 5] = conn.targetPosition.z;
                
                // Source color (with strength)
                colors[idx] = color.r;
                colors[idx + 1] = color.g;
                colors[idx + 2] = color.b;
                
                // Target color (with strength)
                colors[idx + 3] = color.r;
                colors[idx + 4] = color.g;
                colors[idx + 5] = color.b;
            });
            
            // Create buffer geometry with positions and colors
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
            
            // Create material with proper color encoding
            const material = new THREE.LineBasicMaterial({
                vertexColors: true,
                transparent: true,
                opacity: config.connectionOpacity,
                toneMapped: true
            });
            
            // Create line segments
            const lineSegments = new THREE.LineSegments(geometry, material);
            
            // Store connection data
            lineSegments.userData = {
                isConnectionGroup: true,
                type: type,
                connections: connections.map(conn => ({
                    sourceNode: conn.sourceNode,
                    targetNode: conn.targetNode,
                    userData: conn.userData
                }))
            };
            
            // Add to scene
            nodeGroups['connections'].add(lineSegments);
            
            // Add reference to each connection for tracking
            connections.forEach((conn, i) => {
                const connection = {
                    isConnectionReference: true,
                    lineSegments: lineSegments,
                    index: i,
                    sourceNode: conn.sourceNode,
                    targetNode: conn.targetNode,
                    userData: conn.userData
                };
                
                this.connections.push(connection);
            });
        });
        
        console.log(`Created connections using LineSegments for better performance`);
        
    } else {
        // Limit connections to prevent performance issues
        const connectionsToRender = connectionsData.slice(0, config.maxConnections);
        
        connectionsToRender.forEach(connectionData => {
            const sourceIndex = nodeMap[connectionData.source];
            const targetIndex = nodeMap[connectionData.target];
            
            // Skip if source or target node doesn't exist
            if (sourceIndex === undefined || targetIndex === undefined) return;
            if (sourceIndex >= nodes.length || targetIndex >= nodes.length) return;
            
            const sourceNode = nodes[sourceIndex];
            const targetNode = nodes[targetIndex];
            
            // Skip if source or target node is the same
            if (sourceNode === targetNode) return;
            
            // Update connection count
            sourceNode.userData.connections = (sourceNode.userData.connections || 0) + 1;
            targetNode.userData.connections = (targetNode.userData.connections || 0) + 1;
            
            // Get positions
            const sourcePosition = sourceNode.isInstancedReference ? 
                sourceNode.position : sourceNode.position;
                
            const targetPosition = targetNode.isInstancedReference ? 
                targetNode.position : targetNode.position;
            
            // Create geometry
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute([
                sourcePosition.x, sourcePosition.y, sourcePosition.z,
                targetPosition.x, targetPosition.y, targetPosition.z
            ], 3));
            
            // Determine color and width based on connection type and strength
            const strength = connectionData.strength || 0.5;
            const connectionType = connectionData.type || 'semantic';
            const color = connectionType === 'semantic' ? 0x43e97b : 0xf83a3a;
            const width = 0.1 + strength * 0.5;
            
            // Create material with proper color encoding
            const material = new THREE.LineBasicMaterial({
                color: color,
                transparent: true,
                opacity: config.connectionOpacity * strength,
                linewidth: width,
                toneMapped: true
            });
            
            // Create line
            const connection = new THREE.Line(geometry, material);
            
            // Store connection data
            connection.userData = {
                ...connectionData,
                sourceNode: sourceNode,
                targetNode: targetNode
            };
            
            // Add to scene and tracking arrays
            nodeGroups['connections'].add(connection);
            connections.push(connection);
        });
        
        console.log(`Created ${connections.length} connections`);
    }
}

// Advanced force-directed layout for nodes
function applyForceDirectedLayout() {
    console.log('Applying advanced force-directed layout to nodes...');
    
    if (!nodes.length) return;
    
    // Track layout iterations
    const iterations = 300;
    const coolingFactor = 0.95;
    const initialTemperature = 100;
    
    // Layout parameters
    const params = {
        repulsionStrength: 200,
        attractionStrength: 0.1,
        centralGravity: 0.05,
        maxVelocity: 2.0,
        minDistance: 5,
        theta: 0.8,  // Barnes-Hut approximation threshold
        temperature: initialTemperature
    };
    
    // Create position and velocity arrays for efficient computation
    const positions = [];
    const velocities = [];
    const nodeTypes = [];
    
    // Initialize positions and velocities
    nodes.forEach((node, i) => {
        // Get position from node (handling instanced nodes)
        const pos = node.isInstancedReference ? 
            node.position.clone() : 
            node.position.clone();
        
        positions.push(pos);
        velocities.push(new THREE.Vector3(0, 0, 0));
        nodeTypes.push(node.userData.type || 'conversation');
    });
    
    // Perform simulation iterations
    for (let iter = 0; iter < iterations; iter++) {
        // Cool down the system
        params.temperature *= coolingFactor;
        
        // Calculate repulsive forces (node-node repulsion)
        for (let i = 0; i < nodes.length; i++) {
            const pos1 = positions[i];
            const importance1 = nodes[i].userData.importance || 0.5;
            
            for (let j = i + 1; j < nodes.length; j++) {
                const pos2 = positions[j];
                const importance2 = nodes[j].userData.importance || 0.5;
                
                // Same types have stronger repulsion
                const typeMultiplier = nodeTypes[i] === nodeTypes[j] ? 1.5 : 1.0;
                
                // Calculate distance vector
                const dx = pos1.x - pos2.x;
                const dy = pos1.y - pos2.y;
                const dz = pos1.z - pos2.z;
                
                // Avoid division by zero
                const distance = Math.sqrt(dx * dx + dy * dy + dz * dz) || 0.1;
                
                // Calculate repulsive force
                if (distance < params.minDistance * 10) {
                    const force = params.repulsionStrength * 
                        (importance1 + importance2) * 0.5 * 
                        typeMultiplier / (distance * distance);
                    
                    // Apply force to velocity
                    const fx = dx * force / distance;
                    const fy = dy * force / distance;
                    const fz = dz * force / distance;
                    
                    velocities[i].x += fx;
                    velocities[i].y += fy;
                    velocities[i].z += fz;
                    
                    velocities[j].x -= fx;
                    velocities[j].y -= fy;
                    velocities[j].z -= fz;
                }
            }
        }
        
        // Calculate attractive forces (connections)
        for (let i = 0; i < connections.length; i++) {
            const connection = connections[i];
            
            // Skip connection references (we'll handle them in the group)
            if (connection.isConnectionReference) continue;
            
            const sourceNode = connection.userData.sourceNode;
            const targetNode = connection.userData.targetNode;
            
            if (!sourceNode || !targetNode) continue;
            
            // Find indices
            const sourceIndex = nodes.indexOf(sourceNode);
            const targetIndex = nodes.indexOf(targetNode);
            
            if (sourceIndex < 0 || targetIndex < 0) continue;
            
            const pos1 = positions[sourceIndex];
            const pos2 = positions[targetIndex];
            
            // Calculate distance vector
            const dx = pos1.x - pos2.x;
            const dy = pos1.y - pos2.y;
            const dz = pos1.z - pos2.z;
            
            const distance = Math.sqrt(dx * dx + dy * dy + dz * dz) || 0.1;
            
            // Calculate attractive force
            const strength = connection.userData.strength || 0.5;
            const force = params.attractionStrength * distance * strength;
            
            // Apply force to velocity
            const fx = dx * force / distance;
            const fy = dy * force / distance;
            const fz = dz * force / distance;
            
            velocities[sourceIndex].x -= fx;
            velocities[sourceIndex].y -= fy;
            velocities[sourceIndex].z -= fz;
            
            velocities[targetIndex].x += fx;
            velocities[targetIndex].y += fy;
            velocities[targetIndex].z += fz;
        }
        
        // Apply central gravity
        for (let i = 0; i < nodes.length; i++) {
            const pos = positions[i];
            const importance = nodes[i].userData.importance || 0.5;
            
            // Calculate distance from center
            const distance = pos.length();
            if (distance > 0.1) {
                // Apply gravity force towards center
                const force = params.centralGravity * distance * importance;
                velocities[i].x -= pos.x * force / distance;
                velocities[i].y -= pos.y * force / distance;
                velocities[i].z -= pos.z * force / distance;
            }
        }
        
        // Apply velocity and temperature limits
        for (let i = 0; i < nodes.length; i++) {
            const vel = velocities[i];
            
            // Limit velocity
            const speed = vel.length();
            if (speed > params.maxVelocity) {
                vel.multiplyScalar(params.maxVelocity / speed);
            }
            
            // Apply temperature (maximum movement per iteration)
            if (speed > params.temperature) {
                vel.multiplyScalar(params.temperature / speed);
            }
            
            // Update position
            const pos = positions[i];
            pos.add(vel);
            
            // Apply position to node (different for instanced meshes)
            if (nodes[i].isInstancedReference) {
                nodes[i].position.copy(pos);
                
                // Update instanced mesh matrix
                const dummy = new THREE.Object3D();
                dummy.position.copy(pos);
                const size = nodes[i].userData.size || 1.0;
                dummy.scale.set(size, size, size);
                dummy.updateMatrix();
                
                nodes[i].instancedMesh.setMatrixAt(nodes[i].instanceId, dummy.matrix);
                nodes[i].instancedMesh.instanceMatrix.needsUpdate = true;
            } else {
                nodes[i].position.copy(pos);
            }
            
            // Dampen velocity for next iteration
            vel.multiplyScalar(0.9);
        }
    }
    
    // Update connections to follow nodes
    updateConnections();
    
    console.log('Force-directed layout completed');
}

// Add lighting to the scene
function addLights() {
    // Ambient light for base illumination
    const ambientLight = new THREE.AmbientLight(0x222222, 0.5);
    scene.add(ambientLight);
    
    // Main directional light
    const mainLight = new THREE.DirectionalLight(0xffffff, 0.7);
    mainLight.position.set(1, 1, 1).normalize();
    scene.add(mainLight);
    
    // Colored point lights for cyberpunk effect
    const colors = [0x00ffff, 0xff00ff, 0x00ff8f];
    const positions = [
        new THREE.Vector3(100, 50, 50),
        new THREE.Vector3(-100, -50, 50),
        new THREE.Vector3(0, 100, -50)
    ];
    
    positions.forEach((position, i) => {
        const light = new THREE.PointLight(colors[i], 0.5, 200);
        light.position.copy(position);
        scene.add(light);
    });
}

/**
 * Create the cyberpunk environment with grid and particles
 */
function createEnvironment() {
    // Create grid
    createGrid();
    
    // Create particle system
    createParticleSystem();
}

/**
 * Create cyberpunk grid
 */
function createGrid() {
    // Create grid helper
    const size = 200;
    const divisions = 20;
    
    // Create custom grid material
    const gridMaterial = new THREE.LineBasicMaterial({
        color: config.gridColor,
        transparent: true,
        opacity: config.gridOpacity,
        fog: true
    });
    
    // Create horizontal grid
    const horizontalGrid = new THREE.GridHelper(size, divisions, config.gridColor, config.gridColor);
    horizontalGrid.material = gridMaterial;
    scene.add(horizontalGrid);
    
    // Create vertical grids
    const verticalGrid1 = new THREE.GridHelper(size, divisions, config.gridColor, config.gridColor);
    verticalGrid1.rotation.x = Math.PI / 2;
    verticalGrid1.material = gridMaterial.clone();
    verticalGrid1.material.opacity = config.gridOpacity * 0.5;
    scene.add(verticalGrid1);
    
    const verticalGrid2 = new THREE.GridHelper(size, divisions, config.gridColor, config.gridColor);
    verticalGrid2.rotation.z = Math.PI / 2;
    verticalGrid2.material = gridMaterial.clone();
    verticalGrid2.material.opacity = config.gridOpacity * 0.5;
    scene.add(verticalGrid2);
    
    // Store reference
    grid = {
        horizontal: horizontalGrid,
        vertical1: verticalGrid1,
        vertical2: verticalGrid2
    };
}

/**
 * Create particle system for cyberpunk atmosphere
 */
function createParticleSystem() {
    const particleCount = config.particleCount;
    const particleGeometry = new THREE.BufferGeometry();
    
    // Create arrays for particle attributes
    const positions = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);
    const colors = new Float32Array(particleCount * 3);
    
    // Generate random particles
    for (let i = 0; i < particleCount; i++) {
        // Position (random in a sphere)
        const radius = 150 + Math.random() * 50;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos((Math.random() * 2) - 1);
        
        positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
        positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
        positions[i * 3 + 2] = radius * Math.cos(phi);
        
        // Size (random)
        sizes[i] = Math.random() * 1.5 + 0.5;
        
        // Color (choose from cyberpunk palette)
        const colorChoice = Math.floor(Math.random() * 3);
        if (colorChoice === 0) {
            // Cyan
            colors[i * 3] = 0.0;
            colors[i * 3 + 1] = 0.8 + Math.random() * 0.2;
            colors[i * 3 + 2] = 0.8 + Math.random() * 0.2;
        } else if (colorChoice === 1) {
            // Magenta
            colors[i * 3] = 0.8 + Math.random() * 0.2;
            colors[i * 3 + 1] = 0.0;
            colors[i * 3 + 2] = 0.8 + Math.random() * 0.2;
        } else {
            // Green
            colors[i * 3] = 0.0;
            colors[i * 3 + 1] = 0.8 + Math.random() * 0.2;
            colors[i * 3 + 2] = 0.4 * Math.random();
        }
    }
    
    // Add attributes to geometry
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleGeometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    particleGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    
    // Create point sprite texture
    const textureLoader = new THREE.TextureLoader();
    const particleTexture = textureLoader.load('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAhGVYSWZNTQAqAAAACAAGAQYAAwAAAAEAAgAAARIAAwAAAAEAAQAAARoABQAAAAEAAABWARsABQAAAAEAAABeASgAAwAAAAEAAgAAh2kABAAAAAEAAABmAAAAAAAAAEgAAAABAAAASAAAAAEAAqACAAQAAAABAAAAIKADAAQAAAABAAAAIAAAAAAQdIdCAAAACXBIWXMAAAsTAAALEwEAmpwYAAACZmlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iWE1QIENvcmUgNS40LjAiPgogICA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogICAgICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIgogICAgICAgICAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyIKICAgICAgICAgICAgeG1sbnM6ZXhpZj0iaHR0cDovL25zLmFkb2JlLmNvbS9leGlmLzEuMC8iPgogICAgICAgICA8dGlmZjpPcmllbnRhdGlvbj4xPC90aWZmOk9yaWVudGF0aW9uPgogICAgICAgICA8dGlmZjpSZXNvbHV0aW9uVW5pdD4yPC90aWZmOlJlc29sdXRpb25Vbml0PgogICAgICAgICA8ZXhpZjpDb2xvclNwYWNlPjE8L2V4aWY6Q29sb3JTcGFjZT4KICAgICAgICAgPGV4aWY6UGl4ZWxYRGltZW5zaW9uPjMyPC9leGlmOlBpeGVsWERpbWVuc2lvbj4KICAgICAgICAgPGV4aWY6UGl4ZWxZRGltZW5zaW9uPjMyPC9leGlmOlBpeGVsWURpbWVuc2lvbj4KICAgICAgPC9yZGY6RGVzY3JpcHRpb24+CiAgIDwvcmRmOlJERj4KPC94OnhtcG1ldGE+Ck0aSxoAAAXFSURBVFgJrVdbiBtVGP7PJJNsdjfJZrM+VF+0im5LUbE+iEIF8QJCC4JUwbaCyAoi4iIIfRJRQcGHhSKCWHwUUVAEfRAUKVLri0+uLEWh7SbZ3SS72U0mM+Pvm8xOZiezKTgHDjPn8l/+/3znP3OmhkssvvduP0OzFS5GV8MOH9dE9hCd0I7S8zSxzzIo8rPzRZrZ+TbETq4npYgrdJv+VGSH6D+VUejIx6F0WBbdstBmkPCqxw6jrWkiyYAl6BG3ALNIQ1ixzHZLZP13DMRAX64pAjD3ptFvzWRywfFKpXLUNM05y7LqnueVOzo6rsxms0OpVOoRRVF2KYoi0OLbRYtBqIEfURQGKHFNRVGcDjKwsLCwv1wuf1cqlU52dnbOA2wumUyeqlarB3Rd/7RQKLyhaVoPlHRhT4PeiLjcENCAH4FdJIbPANhgMNDn5+cP8fVSb2/vccDOmaY50NXVNV4oFHbDyTtLS0uvYpVnI2qzKKAEAC54dIEYDp+BOJ/n1etarXbUMIxfsYK/U6nUONTX2EnCMIyllZWV0XQ6fdB13fMLCwuPwMwz6XQ6j7hWoRkMoQZBKGqDYwLRxAADkNXV1ec9zzuGEx7u6OiYwO7W1taW4egtPp9MJqO2t7f/hQxiyM5CoTDc09PzHjJyHz5GsaNZGIIaQ4bLnvr40ZsyEBsHHMd5BvBfocPfLi0tFUOlzZoxMfTMzs7eYhjGq6urq3tgaJfnece5EfA6cgn0NnQITZHgqjY4DLgKuCLc/h66vmPb9jOYiI2Lg5oaOByGYWyr1+s74Ow+7Gcb7nNmJgF3rrEydL0pAwDYV6vVirquP4S2h2lMXOrFNQwbsb+amZnpNk3z8Ww2m62YNUECqvDhR7fE27GzBQ8wsCvw9+MQ2bPUV3R4oRfa1HJiYmI7MnOkr69v2KkYZCJ7UhNvH4ZZhAC2t7e3F1D5FVwfRz9t+w2noU5OTt4OM/ch7sfWK1bwI1oiQgcGCO4MQMQHlO8G9L0fwLvqdvKY78/jPUOWZd3red5uy7a1TKdG+PACEHw5WwYAHkJB7gTAdrjiN1v8Ft8+BM0jCPHRycnJvWtra4YGcMmRURXAfhz40cWL74IBdtbMVMxDt4wZmwZzrchDUJUFKVogzS8PXGctCuTLFkxJCNXGTx5mQ8sD1Ow4GKMvIkVCYgshRFADYYLDQcvfgnjx0IpdL5QFYP7XRNSD9wDFgA5bUMHrJ8NJIdqE8lm7CZMMAYATgjTEH4N4cQRsyUA4Hl2PjY31oUN2QKPkByGuYTK4RvV7AVVR1yvVTf8xYeJpAb/Q+NmfKa7iR7cFBgT45sRtcjwEVJ7K5XIv4l4/go7e3t/f/wHSNMrjQRb4lLwLyXG/M7R/G3m84fC8pqFt5OInLJ5eU0aBHqKoUiAiCIGVTCazHZA34OY2vBifx8CxXC5XBMwewP2F9P2CU31mdna2CrAYVv8b9H2dn58fqNfrL/X39z+JdA5GpoQQOJGh+BaivbAgwNidZkY5x2h0iqYfzDYE50xDfBPyWUTHuxjvR9AevDGX0Lc+OTm5Bxl4d3h4+HI8WF9CsJeRvl8rlYqH/yVBhgA6hdIJvcjyMsD1DF/EfJb8Z1QoYnySPxphpXgRQ3QEsNebdBjPygfIQx4r/hP9RdR7IPoDDM84jmNHGEJYb28Z8MPHW+z6GG+8aziZR2amMGrxFl9KfHFQNxVmZWxsLMHjGP1uQoaGcHAP4rTH0PSHYRhV27Ybj2Yfx8+Av4IG4oQgMiC4xnFzJAxHqeUNuPIx2AuNSGWZmpq6BU/FHcjkdogHVjfgbzwfwVeYVPgZ4TH4T7i1hgFm3BemJUOCD/7f0Ng2Q2FYS/hy4SdaGTnlWOEBiJ9Af9RDFgz9sFjUxQSgdLDPwWQr8nUzGkS9GLy/4v+FXIBT1xoD11tRyN/3CcwKz8MR4BIxEPtmjCnN43g+9y8QUWdSXBRGHQAAAABJRU5ErkJggg==');
    
    // Create shader material for particles
    const particleMaterial = new THREE.ShaderMaterial({
        uniforms: {
            pointTexture: { value: particleTexture },
            time: { value: 0.0 }
        },
        vertexShader: `
            attribute float size;
            attribute vec3 color;
            varying vec3 vColor;
            uniform float time;
            
            void main() {
                vColor = color;
                
                // Animate particles
                vec3 pos = position;
                float offset = position.x + position.y + position.z;
                pos.y += sin(time * 0.2 + offset * 0.05) * 2.0;
                pos.x += cos(time * 0.3 + offset * 0.04) * 2.0;
                pos.z += sin(time * 0.1 + offset * 0.03) * 2.0;
                
                vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
                gl_PointSize = size * (300.0 / -mvPosition.z);
                gl_Position = projectionMatrix * mvPosition;
            }
        `,
        fragmentShader: `
            uniform sampler2D pointTexture;
            varying vec3 vColor;
            
            void main() {
                gl_FragColor = vec4(vColor, 1.0) * texture2D(pointTexture, gl_PointCoord);
                if (gl_FragColor.a < 0.1) discard;
            }
        `,
        blending: THREE.AdditiveBlending,
        depthTest: false,
        transparent: true
    });
    
    // Create particle system
    particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);
}

// Handle window resize
function onWindowResize() {
    if (!container) return;
    
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
    
    // Update post-processing sizes
    if (config.postProcessing && composer) {
        composer.setSize(container.clientWidth, container.clientHeight);
        
        // Update FXAA resolution
        if (effectFXAA) {
            effectFXAA.uniforms['resolution'].value.set(
                1 / (container.clientWidth * renderer.getPixelRatio()),
                1 / (container.clientHeight * renderer.getPixelRatio())
            );
        }
    }
}

/**
 * Set up event listeners
 * @param {HTMLElement} container - The container element
 */
function setupEventListeners(container) {
    // Window resize
    window.addEventListener('resize', () => {
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        
        renderer.setSize(width, height);
    });
    
    // Mouse move for node hovering
    container.addEventListener('mousemove', (event) => {
        // Calculate mouse position in normalized device coordinates
        const rect = renderer.domElement.getBoundingClientRect();
        mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    });
    
    // Mouse click for node selection
    container.addEventListener('click', (event) => {
        // Use raycaster to find intersected objects
        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObjects(Object.values(nodeObjects));
        
        if (intersects.length > 0) {
            const node = intersects[0].object;
            
            // Clear previous selection
            if (selectedNode && selectedNode !== node) {
                resetNodeHighlight(selectedNode);
            }
            
            // Set new selection
            selectedNode = node;
            highlightNode(node);
            
            // Trigger custom event for node selection
            const nodeData = node.userData.node;
            const event = new CustomEvent('memory-selected', { 
                detail: nodeData 
            });
            document.dispatchEvent(event);
        } else {
            // Deselect if clicking empty space
            if (selectedNode) {
                resetNodeHighlight(selectedNode);
                selectedNode = null;
            }
        }
    });
}

/**
 * Animation loop
 */
function animate() {
    requestAnimationFrame(animate);
    
    // Get elapsed time since last frame
    const delta = clock.getDelta();
    elapsedTime += delta;
    
    // Update controls
    controls.update();
    
    // Update particle system
    if (particles) {
        particles.material.uniforms.time.value = elapsedTime;
    }
    
    // Update raycaster for interactive elements
    if (mouse) {
        raycaster.setFromCamera(mouse, camera);
        
        // Check for intersections with nodes
        const intersects = raycaster.intersectObjects(Object.values(nodeObjects));
        
        // Handle hover effects
        if (intersects.length > 0) {
            if (intersects[0].object !== selectedNode) {
                document.body.style.cursor = 'pointer';
            }
        } else {
            document.body.style.cursor = 'default';
        }
    }
    
    // Update links
    updateLinks();
    
    // Render scene
    renderer.render(scene, camera);
}

// Update connections positions based on node positions
function updateConnections() {
    connections.forEach(connection => {
        const sourceNode = connection.userData.sourceNode;
        const targetNode = connection.userData.targetNode;
        
        if (!sourceNode || !targetNode) return;
        
        const positions = connection.geometry.attributes.position.array;
        
        // Update source position
        positions[0] = sourceNode.position.x;
        positions[1] = sourceNode.position.y;
        positions[2] = sourceNode.position.z;
        
        // Update target position
        positions[3] = targetNode.position.x;
        positions[4] = targetNode.position.y;
        positions[5] = targetNode.position.z;
        
        connection.geometry.attributes.position.needsUpdate = true;
    });
}

// Animate nodes (pulse effect)
function animateNodes(elapsedTime) {
    const time = elapsedTime * 0.001;
    
    nodes.forEach((node, index) => {
        // Skip selected nodes
        if (node === selectedNode) return;
        
        // Pulse effect based on importance
        const importance = node.userData.importance || 0.5;
        const pulse = Math.sin(time + index * 0.1) * 0.1 * importance;
        
        // Apply pulse to emissive intensity
        const type = node.userData.type || 'conversation';
        const baseIntensity = config.glowIntensity * importance;
        
        if (node.material) {
            node.material.emissiveIntensity = baseIntensity + pulse;
        }
        
        // Slight movement
        if (!node.userData.isHighlighted && node !== intersectedObject) {
            node.position.x += Math.sin(time * 0.5 + index) * 0.01;
            node.position.y += Math.cos(time * 0.5 + index * 0.5) * 0.01;
            node.position.z += Math.sin(time * 0.3 + index * 0.2) * 0.01;
        }
    });
}

// Setup UI controls
function setupUIControls() {
    // Toggle animation button
    const toggleAnimationBtn = document.getElementById('toggle-animation');
    if (toggleAnimationBtn) {
        toggleAnimationBtn.addEventListener('click', () => {
            isAnimating = !isAnimating;
            controls.autoRotate = isAnimating;
            toggleAnimationBtn.textContent = isAnimating ? 'Pause Animation' : 'Resume Animation';
        });
    }
    
    // Reset camera button
    const resetCameraBtn = document.getElementById('reset-camera');
    if (resetCameraBtn) {
        resetCameraBtn.addEventListener('click', () => {
            controls.reset();
            camera.position.set(0, 0, config.cameraDistance);
            camera.lookAt(0, 0, 0);
        });
    }
    
    // Filter buttons
    const nodeTypes = ['conversation', 'semantic', 'swarm', 'feedback'];
    nodeTypes.forEach(type => {
        const filterBtn = document.getElementById(`filter-${type}`);
        if (filterBtn) {
            filterBtn.addEventListener('click', () => {
                toggleNodeTypeVisibility(type);
            });
        }
    });
    
    // Refresh data button
    const refreshBtn = document.getElementById('refresh-data');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadMemoryData();
        });
    }
}

// Toggle visibility of a node type
function toggleNodeTypeVisibility(type) {
    if (!nodeGroups[type]) return;
    
    nodeGroups[type].visible = !nodeGroups[type].visible;
    
    // Update button state
    const filterBtn = document.getElementById(`filter-${type}`);
    if (filterBtn) {
        if (nodeGroups[type].visible) {
            filterBtn.classList.add('active');
        } else {
            filterBtn.classList.remove('active');
        }
    }
}

// Show info about a node
function showNodeInfo(nodeData) {
    const nodeInfo = document.getElementById('node-info');
    if (!nodeInfo || !nodeData) return;
    
    nodeInfo.innerHTML = `
        <h3>${nodeData.label || 'Memory Node'}</h3>
        <p><strong>Type:</strong> ${nodeData.type || 'Unknown'}</p>
        <p><strong>Connections:</strong> ${nodeData.connections || 0}</p>
        <p><strong>Created:</strong> ${new Date(nodeData.timestamp).toLocaleString() || 'Unknown'}</p>
    `;
    
    nodeInfo.style.display = 'block';
}

// Hide node info
function hideNodeInfo() {
    const nodeInfo = document.getElementById('node-info');
    if (!nodeInfo) return;
    
    nodeInfo.style.display = 'none';
}

// Show detailed info about a node
function showDetailedNodeInfo(nodeData) {
    const detailPanel = document.getElementById('node-detail-panel');
    if (!detailPanel || !nodeData) return;
    
    // Format node content
    const content = nodeData.data && nodeData.data.content 
        ? nodeData.data.content 
        : 'No content available';
    
    // Build connected nodes list
    let connectedNodesList = '<p>No connections found</p>';
    if (memoryData && memoryData.connections) {
        const connectedNodes = memoryData.connections.filter(conn => 
            conn.source === nodeData.id || conn.target === nodeData.id
        );
        
        if (connectedNodes.length > 0) {
            connectedNodesList = '<ul class="connected-nodes-list">';
            connectedNodes.forEach(conn => {
                const connectedId = conn.source === nodeData.id ? conn.target : conn.source;
                const connectedNode = memoryData.nodes.find(n => n.id === connectedId);
                if (connectedNode) {
                    connectedNodesList += `
                        <li>
                            <span class="node-type-indicator ${connectedNode.type}"></span>
                            ${connectedNode.label} 
                            <span class="connection-type">(${conn.type})</span>
                        </li>
                    `;
                }
            });
            connectedNodesList += '</ul>';
        }
    }
    
    // Populate detail panel
    detailPanel.innerHTML = `
        <div class="detail-header">
            <h2>${nodeData.label || 'Memory Node'}</h2>
            <span class="node-type ${nodeData.type}">${nodeData.type || 'unknown'}</span>
            <button id="close-detail-panel" class="close-button">×</button>
        </div>
        <div class="detail-content">
            <div class="detail-section">
                <h3>Content</h3>
                <div class="content-box">${content}</div>
            </div>
            <div class="detail-section">
                <h3>Metadata</h3>
                <table class="metadata-table">
                    <tr>
                        <td>ID:</td>
                        <td>${nodeData.id}</td>
                    </tr>
                    <tr>
                        <td>Created:</td>
                        <td>${new Date(nodeData.timestamp).toLocaleString()}</td>
                    </tr>
                    <tr>
                        <td>Importance:</td>
                        <td>${(nodeData.importance * 100).toFixed(0)}%</td>
                    </tr>
                    <tr>
                        <td>Connections:</td>
                        <td>${nodeData.connections || 0}</td>
                    </tr>
                </table>
            </div>
            <div class="detail-section">
                <h3>Connected Nodes</h3>
                <div class="connected-nodes">
                    ${connectedNodesList}
                </div>
            </div>
        </div>
        <div class="detail-actions">
            <button id="analyze-node" class="action-button">Analyze with Claude</button>
            <button id="research-node" class="action-button">Research with Perplexity</button>
            <button id="visualize-node" class="action-button">Focus Visualization</button>
        </div>
    `;
    
    // Show the panel
    detailPanel.style.display = 'block';
    
    // Add event listeners
    const closeBtn = document.getElementById('close-detail-panel');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            detailPanel.style.display = 'none';
        });
    }
    
    // Node analysis with Claude (will be implemented in Batch 4)
    const analyzeBtn = document.getElementById('analyze-node');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', () => {
            console.log('Analyze with Claude clicked for node:', nodeData);
            // Analysis function will be implemented in Batch 4
        });
    }
    
    // Research with Perplexity (will be implemented in Batch 4)
    const researchBtn = document.getElementById('research-node');
    if (researchBtn) {
        researchBtn.addEventListener('click', () => {
            console.log('Research with Perplexity clicked for node:', nodeData);
            // Research function will be implemented in Batch 4
        });
    }
    
    // Focus visualization
    const visualizeBtn = document.getElementById('visualize-node');
    if (visualizeBtn) {
        visualizeBtn.addEventListener('click', () => {
            focusOnNode(nodeData.id);
        });
    }
}

// Focus camera on a specific node
function focusOnNode(nodeId) {
    const node = nodes.find(n => n.userData.id === nodeId);
    if (!node) return;
    
    // Animate camera to focus on node
    const targetPosition = node.position.clone();
    const distance = 20;
    
    // Calculate camera position
    const cameraTargetPosition = targetPosition.clone().add(
        new THREE.Vector3(distance, distance, distance)
    );
    
    // Animate camera movement
    const startPosition = camera.position.clone();
    const duration = 1000; // ms
    const startTime = Date.now();
    
    function animateCamera() {
        const elapsedTime = Date.now() - startTime;
        const progress = Math.min(elapsedTime / duration, 1);
        
        // Easing function
        const easeProgress = 1 - Math.pow(1 - progress, 3);
        
        // Interpolate position
        camera.position.lerpVectors(startPosition, cameraTargetPosition, easeProgress);
        
        // Look at target
        camera.lookAt(targetPosition);
        
        // Continue animation if not complete
        if (progress < 1) {
            requestAnimationFrame(animateCamera);
        }
    }
    
    // Start animation
    animateCamera();
}

// Update stats display
function updateStats(data) {
    const stats = {
        totalNodes: data.nodes.length,
        totalConnections: data.connections.length,
        nodesByType: {}
    };
    
    // Count nodes by type
    data.nodes.forEach(node => {
        const type = node.type || 'unknown';
        stats.nodesByType[type] = (stats.nodesByType[type] || 0) + 1;
    });
    
    // Update DOM elements
    const totalNodesEl = document.getElementById('total-memories');
    if (totalNodesEl) totalNodesEl.textContent = stats.totalNodes;
    
    // Update other stats elements if they exist
    Object.entries(stats.nodesByType).forEach(([type, count]) => {
        const el = document.getElementById(`${type}-memories`);
        if (el) el.textContent = count;
    });
    
    console.log('Memory stats updated:', stats);
}

// Handle mouse movement
function onMouseMove(event) {
    // Calculate mouse position in normalized device coordinates
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    
    // Update raycaster
    raycaster.setFromCamera(mouse, camera);
    
    // Check for intersections with nodes
    const intersects = raycaster.intersectObjects(nodes);
    
    if (intersects.length > 0) {
        if (intersectedObject !== intersects[0].object) {
            // Reset previous intersected object
            if (intersectedObject) {
                intersectedObject.material.emissive.setHex(intersectedObject.currentHex);
            }
            
            // Set new intersected object
            intersectedObject = intersects[0].object;
            intersectedObject.currentHex = intersectedObject.material.emissive.getHex();
            intersectedObject.material.emissive.setHex(0xffff00);
            
            // Show node info
            showNodeInfo(intersectedObject.userData);
            
            // Set cursor to pointer
            container.style.cursor = 'pointer';
        }
    } else {
        // Reset intersected object
        if (intersectedObject) {
            intersectedObject.material.emissive.setHex(intersectedObject.currentHex);
            intersectedObject = null;
            
            // Hide node info
            hideNodeInfo();
            
            // Reset cursor
            container.style.cursor = 'auto';
        }
    }
}

// Handle mouse click
function onMouseClick(event) {
    if (intersectedObject) {
        // Show detailed info about the selected node
        showDetailedNodeInfo(intersectedObject.userData);
        
        // Highlight connections
        highlightNodeConnections(intersectedObject);
        
        // Store as selected node
        selectedNode = intersectedObject;
    } else {
        // Reset highlighted connections
        resetHighlightedConnections();
        
        // Clear selected node
        selectedNode = null;
    }
}

// Highlight connections for a selected node
function highlightNodeConnections(node) {
    // Reset previous highlighted connections
    resetHighlightedConnections();
    
    // Find all connections for this node
    const nodeConnections = connections.filter(connection => 
        connection.userData.sourceNode === node ||
        connection.userData.targetNode === node
    );
    
    // Highlight connections
    nodeConnections.forEach(connection => {
        connection.material.color.setHex(0xffff00);
        connection.material.opacity = 1.0;
        connection.material.linewidth = 2;
        
        // Store original values
        connection.userData.originalColor = connection.material.color.getHex();
        connection.userData.originalOpacity = connection.material.opacity;
        
        // Also highlight connected nodes
        const connectedNode = connection.userData.sourceNode === node ?
            connection.userData.targetNode : connection.userData.sourceNode;
        
        if (connectedNode) {
            connectedNode.material.emissive.setHex(0x88ff88);
            connectedNode.userData.isHighlighted = true;
        }
    });
}

// Reset highlighted connections
function resetHighlightedConnections() {
    connections.forEach(connection => {
        if (connection.userData.originalColor) {
            connection.material.color.setHex(connection.userData.originalColor);
            connection.material.opacity = connection.userData.originalOpacity;
            connection.userData.originalColor = null;
            connection.userData.originalOpacity = null;
        }
    });
    
    // Reset highlighted nodes
    nodes.forEach(node => {
        if (node.userData.isHighlighted) {
            const type = node.userData.type || 'conversation';
            node.material.emissive.setHex(config.nodeColors[type]);
            node.userData.isHighlighted = false;
        }
    });
}

// Setup real-time data updates
function setupRealTimeUpdates() {
    // Update interval in milliseconds
    const updateInterval = 10000; // 10 seconds
    
    console.log('Setting up real-time data updates every', updateInterval/1000, 'seconds');
    
    // Set up periodic fetching
    setInterval(() => {
        if (!visualizationReady || !isAnimating) return;
        
        // Fetch new data from API
        fetch('/api/memories/graph?timestamp=' + Date.now())
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Check if data is different from current
                if (hasDataChanged(data)) {
                    console.log('Memory data updated:', data);
                    
                    // Update visualization with new data
                    updateVisualizationWithNewData(data);
                } else {
                    console.log('No changes in memory data');
                }
            })
            .catch(error => {
                console.warn('Failed to fetch real-time updates:', error);
            });
    }, updateInterval);
    
    // Also setup WebSocket connection if available
    setupWebSocketConnection();
}

// Check if new data is different from current data
function hasDataChanged(newData) {
    if (!memoryData) return true;
    
    // Compare node counts
    if (newData.nodes.length !== memoryData.nodes.length) return true;
    
    // Compare connection counts
    if (newData.connections.length !== memoryData.connections.length) return true;
    
    // Check for any new nodes
    const currentNodeIds = new Set(memoryData.nodes.map(node => node.id));
    for (const node of newData.nodes) {
        if (!currentNodeIds.has(node.id)) return true;
    }
    
    return false;
}

// Update visualization with new data without full reset
function updateVisualizationWithNewData(newData) {
    // Store current camera position and orientation
    const cameraPosition = camera.position.clone();
    const cameraTarget = controls.target.clone();
    
    // Map current nodes by ID for quick lookup
    const currentNodesMap = {};
    memoryData.nodes.forEach(node => {
        currentNodesMap[node.id] = node;
    });
    
    // Find nodes to add, update, or remove
    const nodesToAdd = [];
    const nodesToUpdate = [];
    const nodeIdsToKeep = new Set();
    
    newData.nodes.forEach(newNode => {
        nodeIdsToKeep.add(newNode.id);
        
        if (currentNodesMap[newNode.id]) {
            // Node exists - check if needs update
            const currentNode = currentNodesMap[newNode.id];
            if (JSON.stringify(currentNode) !== JSON.stringify(newNode)) {
                nodesToUpdate.push(newNode);
            }
        } else {
            // New node to add
            nodesToAdd.push(newNode);
        }
    });
    
    // Find nodes to remove
    const nodeIdsToRemove = memoryData.nodes
        .filter(node => !nodeIdsToKeep.has(node.id))
        .map(node => node.id);
    
    // Same process for connections
    const currentConnectionsMap = {};
    memoryData.connections.forEach(conn => {
        currentConnectionsMap[conn.id] = conn;
    });
    
    const connectionsToAdd = [];
    const connectionsToUpdate = [];
    const connectionIdsToKeep = new Set();
    
    newData.connections.forEach(newConn => {
        connectionIdsToKeep.add(newConn.id);
        
        if (currentConnectionsMap[newConn.id]) {
            // Connection exists - check if needs update
            const currentConn = currentConnectionsMap[newConn.id];
            if (JSON.stringify(currentConn) !== JSON.stringify(newConn)) {
                connectionsToUpdate.push(newConn);
            }
        } else {
            // New connection to add
            connectionsToAdd.push(newConn);
        }
    });
    
    // Find connections to remove
    const connectionIdsToRemove = memoryData.connections
        .filter(conn => !connectionIdsToKeep.has(conn.id))
        .map(conn => conn.id);
    
    // Log changes
    console.log(`Changes detected: +${nodesToAdd.length} nodes, ~${nodesToUpdate.length} nodes, -${nodeIdsToRemove.length} nodes`);
    console.log(`Changes detected: +${connectionsToAdd.length} connections, ~${connectionsToUpdate.length} connections, -${connectionIdsToRemove.length} connections`);
    
    // Apply changes
    if (nodesToAdd.length > 0 || connectionsToAdd.length > 0 || 
        nodeIdsToRemove.length > 0 || connectionIdsToRemove.length > 0) {
        
        // If many changes, perform a full reset
        if (nodesToAdd.length + nodeIdsToRemove.length > 20 || 
            connectionsToAdd.length + connectionIdsToRemove.length > 50) {
            console.log('Many changes detected, performing full visualization reset');
            
            // Update memory data
            memoryData = newData;
            
            // Recreate visualization
            createVisualizationFromData(newData);
        } else {
            // Apply incremental updates
            console.log('Applying incremental updates to visualization');
            
            // Remove nodes
            removeNodesById(nodeIdsToRemove);
            
            // Remove connections
            removeConnectionsById(connectionIdsToRemove);
            
            // Add new nodes
            if (nodesToAdd.length > 0) {
                createNodes(nodesToAdd);
            }
            
            // Add new connections
            if (connectionsToAdd.length > 0) {
                createConnections(connectionsToAdd, newData.nodes);
            }
            
            // Update data
            memoryData = newData;
            
            // Apply layout
            applyForceDirectedLayout();
        }
    } else if (nodesToUpdate.length > 0 || connectionsToUpdate.length > 0) {
        // Only node/connection properties changed, not structure
        // Update properties without recreating
        updateNodeProperties(nodesToUpdate);
        updateConnectionProperties(connectionsToUpdate);
        
        // Update data
        memoryData = newData;
    }
    
    // Update stats display
    updateStats(newData);
    
    // Restore camera position
    camera.position.copy(cameraPosition);
    controls.target.copy(cameraTarget);
}

// WebSocket connection for real-time updates
function setupWebSocketConnection() {
    try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(`${protocol}//${window.location.host}/api/memories/stream`);
        
        ws.onopen = function(event) {
            console.log('WebSocket connection established for real-time memory updates');
        };
        
        ws.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'memory_update') {
                    console.log('Received memory update via WebSocket');
                    updateVisualizationWithNewData(data.payload);
                } else if (data.type === 'memory_created') {
                    // Add single new memory node
                    const newNode = data.payload;
                    console.log('New memory node created:', newNode);
                    
                    // Add node to memoryData
                    memoryData.nodes.push(newNode);
                    
                    // Add node to visualization with animation
                    createNodesWithAnimation([newNode]);
                } else if (data.type === 'memory_deleted') {
                    // Remove a memory node
                    const nodeId = data.payload.id;
                    console.log('Memory node deleted:', nodeId);
                    
                    // Remove from memoryData
                    memoryData.nodes = memoryData.nodes.filter(node => node.id !== nodeId);
                    memoryData.connections = memoryData.connections.filter(
                        conn => conn.source !== nodeId && conn.target !== nodeId
                    );
                    
                    // Remove from visualization
                    removeNodesById([nodeId]);
                }
            } catch (error) {
                console.error('Error processing WebSocket message:', error);
            }
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
        
        ws.onclose = function(event) {
            console.log('WebSocket connection closed, code:', event.code);
            
            // Attempt to reconnect after 5 seconds
            setTimeout(setupWebSocketConnection, 5000);
        };
        
        // Store WebSocket reference
        window.memoryWebSocket = ws;
        
    } catch (error) {
        console.warn('WebSocket connection failed:', error);
        console.log('Falling back to polling for updates');
    }
}

// Create nodes with animation
function createNodesWithAnimation(nodesData) {
    // Create nodes normally
    createNodes(nodesData);
    
    // Add animation effect
    const newNodeMeshes = nodes.slice(-nodesData.length);
    
    newNodeMeshes.forEach(node => {
        if (node.isInstancedReference) return; // Skip instanced references
        
        // Store original scale
        node.userData.originalScale = node.scale.clone();
        
        // Start with zero scale
        node.scale.set(0, 0, 0);
        
        // Animate to full scale
        const duration = 1000; // ms
        const startTime = Date.now();
        
        function animateScale() {
            const elapsedTime = Date.now() - startTime;
            const progress = Math.min(elapsedTime / duration, 1);
            
            // Elastic easing function
            const easeElastic = function(t) {
                return t === 0 ? 0 : t === 1 ? 1 :
                    Math.pow(2, -10 * t) * Math.sin((t - 0.1) * 5 * Math.PI) + 1;
            };
            
            const scaleValue = easeElastic(progress);
            
            // Set scale based on original scale
            node.scale.set(
                node.userData.originalScale.x * scaleValue,
                node.userData.originalScale.y * scaleValue,
                node.userData.originalScale.z * scaleValue
            );
            
            // Continue animation if not complete
            if (progress < 1) {
                requestAnimationFrame(animateScale);
            }
        }
        
        // Start animation
        animateScale();
    });
}

// Remove nodes by ID
function removeNodesById(nodeIds) {
    if (!nodeIds.length) return;
    
    const nodeIdsSet = new Set(nodeIds);
    const nodesToRemove = [];
    
    // Find nodes to remove
    nodes.forEach(node => {
        if (nodeIdsSet.has(node.userData.id)) {
            nodesToRemove.push(node);
        }
    });
    
    // Remove nodes with fade-out animation
    nodesToRemove.forEach(node => {
        removeNodeWithAnimation(node);
    });
    
    // Also remove any connections to/from these nodes
    connections = connections.filter(connection => {
        const source = connection.userData.sourceNode;
        const target = connection.userData.targetNode;
        
        if (!source || !target) return false;
        
        const sourceId = source.userData.id;
        const targetId = target.userData.id;
        
        if (nodeIdsSet.has(sourceId) || nodeIdsSet.has(targetId)) {
            // Remove connection from scene
            if (connection.parent) {
                connection.parent.remove(connection);
            }
            return false;
        }
        
        return true;
    });
}

// Remove a node with animation
function removeNodeWithAnimation(node) {
    if (node.isInstancedReference) {
        // Instanced meshes are harder to animate individually
        const index = nodes.indexOf(node);
        if (index !== -1) {
            nodes.splice(index, 1);
        }
        return;
    }
    
    // Start with normal scale
    const originalScale = node.scale.clone();
    const originalOpacity = node.material.opacity;
    
    // Make material transparent
    node.material.transparent = true;
    
    // Animate to zero scale and opacity
    const duration = 800; // ms
    const startTime = Date.now();
    
    function animateRemoval() {
        const elapsedTime = Date.now() - startTime;
        const progress = Math.min(elapsedTime / duration, 1);
        
        // Ease out cubic
        const easeOutCubic = function(t) {
            return 1 - Math.pow(1 - t, 3);
        };
        
        const scaleValue = 1 - easeOutCubic(progress);
        const opacityValue = 1 - easeOutCubic(progress);
        
        // Set scale
        node.scale.set(
            originalScale.x * scaleValue,
            originalScale.y * scaleValue,
            originalScale.z * scaleValue
        );
        
        // Set opacity
        node.material.opacity = originalOpacity * opacityValue;
        
        // Continue animation if not complete
        if (progress < 1) {
            requestAnimationFrame(animateRemoval);
        } else {
            // Remove from scene
            if (node.parent) {
                node.parent.remove(node);
            }
            
            // Remove from nodes array
            const index = nodes.indexOf(node);
            if (index !== -1) {
                nodes.splice(index, 1);
            }
            
            // Dispose resources
            if (node.geometry) node.geometry.dispose();
            if (node.material) {
                if (Array.isArray(node.material)) {
                    node.material.forEach(mat => mat.dispose());
                } else {
                    node.material.dispose();
                }
            }
        }
    }
    
    // Start animation
    animateRemoval();
}

// Remove connections by ID
function removeConnectionsById(connectionIds) {
    if (!connectionIds.length) return;
    
    const connectionIdsSet = new Set(connectionIds);
    const connectionsToRemove = [];
    
    // Find connections to remove
    connections.forEach(connection => {
        if (connectionIdsSet.has(connection.userData.id)) {
            connectionsToRemove.push(connection);
        }
    });
    
    // Remove connections with animation
    connectionsToRemove.forEach(connection => {
        removeConnectionWithAnimation(connection);
    });
}

// Remove a connection with animation
function removeConnectionWithAnimation(connection) {
    if (connection.isConnectionReference) {
        // Connection references are harder to animate individually
        const index = connections.indexOf(connection);
        if (index !== -1) {
            connections.splice(index, 1);
        }
        return;
    }
    
    // Store original opacity
    const originalOpacity = connection.material.opacity;
    
    // Make sure material is transparent
    connection.material.transparent = true;
    
    // Animate to zero opacity
    const duration = 500; // ms
    const startTime = Date.now();
    
    function animateRemoval() {
        const elapsedTime = Date.now() - startTime;
        const progress = Math.min(elapsedTime / duration, 1);
        
        // Linear fade
        connection.material.opacity = originalOpacity * (1 - progress);
        
        // Continue animation if not complete
        if (progress < 1) {
            requestAnimationFrame(animateRemoval);
        } else {
            // Remove from scene
            if (connection.parent) {
                connection.parent.remove(connection);
            }
            
            // Remove from connections array
            const index = connections.indexOf(connection);
            if (index !== -1) {
                connections.splice(index, 1);
            }
            
            // Dispose resources
            if (connection.geometry) connection.geometry.dispose();
            if (connection.material) connection.material.dispose();
        }
    }
    
    // Start animation
    animateRemoval();
}

// Update node properties
function updateNodeProperties(nodesToUpdate) {
    // Map nodes by ID for quick lookup
    const nodesMap = {};
    nodes.forEach(node => {
        nodesMap[node.userData.id] = node;
    });
    
    // Update node properties
    nodesToUpdate.forEach(nodeData => {
        const node = nodesMap[nodeData.id];
        if (!node) return;
        
        // Update userData
        node.userData = {
            ...node.userData,
            ...nodeData,
            originalPosition: node.userData.originalPosition, // Keep original position
            index: node.userData.index // Keep index
        };
        
        // Update visual properties if needed
        const type = nodeData.type || 'conversation';
        const importance = nodeData.importance || 0.5;
        
        if (!node.isInstancedReference && node.material) {
            // Update color
            node.material.color.setHex(config.nodeColors[type] || config.nodeColors.conversation);
            node.material.emissive.setHex(config.nodeColors[type] || config.nodeColors.conversation);
            node.material.emissiveIntensity = config.glowIntensity * importance;
            
            // Update size
            const size = config.nodeSizeBase + 
                (config.nodeSizeVariation - config.nodeSizeBase) * importance;
            
            // Only update geometry if size has changed significantly
            if (Math.abs(node.geometry.parameters.radius - size) > 0.2) {
                const oldGeometry = node.geometry;
                node.geometry = new THREE.SphereGeometry(size, 32, 32);
                oldGeometry.dispose();
            }
        }
    });
}

// Update connection properties
function updateConnectionProperties(connectionsToUpdate) {
    // Map connections by ID for quick lookup
    const connectionsMap = {};
    connections.forEach(connection => {
        connectionsMap[connection.userData.id] = connection;
    });
    
    // Update connection properties
    connectionsToUpdate.forEach(connectionData => {
        const connection = connectionsMap[connectionData.id];
        if (!connection || connection.isConnectionReference) return;
        
        // Update userData
        connection.userData = {
            ...connection.userData,
            ...connectionData,
            sourceNode: connection.userData.sourceNode, // Keep references
            targetNode: connection.userData.targetNode
        };
        
        // Update visual properties if needed
        const strength = connectionData.strength || 0.5;
        const connectionType = connectionData.type || 'semantic';
        const color = connectionType === 'semantic' ? 0x43e97b : 0xf83a3a;
        
        // Update color
        connection.material.color.setHex(color);
        
        // Update opacity
        connection.material.opacity = config.connectionOpacity * strength;
    });
}

// Initialize visualization on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing THREE.js Memory Visualization with r173...');
    
    // Check if all required scripts are loaded
    if (typeof THREE === 'undefined') {
        console.error('THREE.js library not loaded');
        const errorMessage = document.createElement('div');
        errorMessage.className = 'error-message';
        errorMessage.textContent = 'THREE.js library not loaded. Please check console for details.';
        document.getElementById('memory-visualization').appendChild(errorMessage);
        return;
    }
    
    // Log THREE.js version
    console.log(`Using THREE.js version: ${THREE.REVISION}`);
    
    initVisualization();
    
    // Set up real-time updates after initialization
    setTimeout(() => {
        setupRealTimeUpdates();
    }, 2000);
});

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
        // Create group to hold the node and its glow
        const group = new THREE.Group();
        
        // Get color based on node type
        const color = config.nodeColors[node.type] || config.nodeColors.default;
        
        // Create core geometry
        const coreGeometry = new THREE.SphereGeometry(
            config.nodeSizeBase + (node.size || 0.5) * config.nodeSizeVariation, 
            16, 16
        );
        
        // Create core material
        const coreMaterial = new THREE.MeshPhongMaterial({
            color: color,
            emissive: color,
            emissiveIntensity: 0.2,
            shininess: 30
        });
        
        // Create core mesh
        const coreMesh = new THREE.Mesh(coreGeometry, coreMaterial);
        group.add(coreMesh);
        
        // Create glow geometry (larger than core)
        const glowSize = (config.nodeSizeBase + (node.size || 0.5) * config.nodeSizeVariation) * config.glowSize;
        const glowGeometry = new THREE.SphereGeometry(glowSize, 16, 16);
        
        // Create glow material
        const glowMaterial = new THREE.ShaderMaterial({
            uniforms: {
                glowColor: { value: new THREE.Color(color) },
                viewVector: { value: new THREE.Vector3(0, 0, 0) },
                c: { value: 0.2 },
                p: { value: 4.5 },
                time: { value: 0.0 }
            },
            vertexShader: `
                uniform vec3 viewVector;
                uniform float c;
                uniform float p;
                uniform float time;
                varying float intensity;
                
                void main() {
                    vec3 vNormal = normalize(normalMatrix * normal);
                    vec3 vNormel = normalize(normalMatrix * viewVector);
                    intensity = pow(abs(c - dot(vNormal, vNormel)), p);
                    
                    // Add slight animation to glow
                    float offset = position.x + position.y + position.z;
                    float pulseIntensity = sin(time * 0.5 + offset * 0.05) * 0.05 + 0.95;
                    intensity *= pulseIntensity;
                    
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                uniform vec3 glowColor;
                varying float intensity;
                
                void main() {
                    vec3 glow = glowColor * intensity;
                    gl_FragColor = vec4(glow, 1.0);
                }
            `,
            side: THREE.BackSide,
            blending: THREE.AdditiveBlending,
            transparent: true,
            depthWrite: false
        });
        
        // Create glow mesh
        const glowMesh = new THREE.Mesh(glowGeometry, glowMaterial);
        group.add(glowMesh);
        
        // Set position
        group.position.set(
            node.x || (Math.random() - 0.5) * 100,
            node.y || (Math.random() - 0.5) * 100,
            node.z || (Math.random() - 0.5) * 100
        );
        
        // Store node data and references to materials
        group.userData = { 
            node: node,
            coreMaterial: coreMaterial,
            glowMaterial: glowMaterial,
            originalColor: color,
            originalSize: config.nodeSizeBase + (node.size || 0.5) * config.nodeSizeVariation
        };
        
        // Add to scene and store reference
        scene.add(group);
        nodeObjects[node.id] = group;
    });
}

/**
 * Create links between nodes
 */
function createLinks() {
    graph.links.forEach(link => {
        // Get source and target nodes
        const sourceNode = nodeObjects[link.source];
        const targetNode = nodeObjects[link.target];
        
        if (!sourceNode || !targetNode) return;
        
        // Create link material
        const linkMaterial = new THREE.LineBasicMaterial({
            color: config.linkColor,
            transparent: true,
            opacity: 0.6,
            linewidth: 1
        });
        
        // Create link geometry
        const linkGeometry = new THREE.BufferGeometry();
        
        // Set positions (will be updated in animation loop)
        const positions = new Float32Array(6); // 2 points * 3 coordinates
        linkGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        
        // Create line
        const linkLine = new THREE.Line(linkGeometry, linkMaterial);
        
        // Store link data
        linkLine.userData = {
            link: link,
            source: sourceNode,
            target: targetNode,
            material: linkMaterial,
            strength: link.strength || 0.5,
            originalColor: config.linkColor
        };
        
        // Add to scene and store reference
        scene.add(linkLine);
        linkObjects[link.source + '-' + link.target] = linkLine;
    });
}

/**
 * Create data flow particles on links
 * @param {Object} link - Link object
 * @param {Object} sourceNode - Source node
 * @param {Object} targetNode - Target node
 */
function createDataFlowParticles(link, sourceNode, targetNode) {
    // TODO: Implement data flow particles on links
    // This could be done by creating a particle system that follows the link path
}

/**
 * Update links to follow connected nodes
 */
function updateLinks() {
    Object.values(linkObjects).forEach(link => {
        const sourcePos = link.userData.source.position;
        const targetPos = link.userData.target.position;
        
        // Update line geometry positions
        const positions = link.geometry.attributes.position.array;
        
        // Set positions for start and end points
        positions[0] = sourcePos.x;
        positions[1] = sourcePos.y;
        positions[2] = sourcePos.z;
        
        positions[3] = targetPos.x;
        positions[4] = targetPos.y;
        positions[5] = targetPos.z;
        
        // Mark position attribute for update
        link.geometry.attributes.position.needsUpdate = true;
    });
}

/**
 * Highlight a node when selected
 * @param {Object} node - Node to highlight
 */
function highlightNode(node) {
    if (!node.userData) return;
    
    // Scale up the node
    gsap.to(node.scale, {
        x: 1.3,
        y: 1.3,
        z: 1.3,
        duration: 0.5,
        ease: "elastic.out(1, 0.5)"
    });
    
    // Change node color to highlight color
    node.userData.coreMaterial.color.setHex(config.highlightColor);
    node.userData.coreMaterial.emissive.setHex(config.highlightColor);
    node.userData.coreMaterial.emissiveIntensity = 0.5;
    
    // Change glow color
    node.userData.glowMaterial.uniforms.glowColor.value.setHex(config.highlightColor);
    
    // Highlight connected links
    highlightConnectedLinks(node);
}

/**
 * Reset node highlight
 * @param {Object} node - Node to reset
 */
function resetNodeHighlight(node) {
    if (!node.userData) return;
    
    // Reset node scale
    gsap.to(node.scale, {
        x: 1.0,
        y: 1.0,
        z: 1.0,
        duration: 0.5,
        ease: "elastic.out(1, 0.5)"
    });
    
    // Reset node color
    const originalColor = node.userData.originalColor;
    node.userData.coreMaterial.color.setHex(originalColor);
    node.userData.coreMaterial.emissive.setHex(originalColor);
    node.userData.coreMaterial.emissiveIntensity = 0.2;
    
    // Reset glow color
    node.userData.glowMaterial.uniforms.glowColor.value.setHex(originalColor);
    
    // Reset connected links
    resetConnectedLinks(node);
}

/**
 * Highlight links connected to a node
 * @param {Object} node - Node to highlight links for
 */
function highlightConnectedLinks(node) {
    const nodeId = node.userData.node.id;
    
    Object.values(linkObjects).forEach(link => {
        const linkData = link.userData.link;
        if (linkData.source === nodeId || linkData.target === nodeId) {
            // Brighten the link
            link.userData.material.color.setHex(config.highlightLinkColor);
            link.userData.material.opacity = 1.0;
            link.userData.material.linewidth = 2;
        }
    });
}

/**
 * Reset highlighting for links connected to a node
 * @param {Object} node - Node to reset links for
 */
function resetConnectedLinks(node) {
    const nodeId = node.userData.node.id;
    
    Object.values(linkObjects).forEach(link => {
        const linkData = link.userData.link;
        if (linkData.source === nodeId || linkData.target === nodeId) {
            // Reset link color and opacity
            link.userData.material.color.setHex(link.userData.originalColor);
            link.userData.material.opacity = 0.6;
            link.userData.material.linewidth = 1;
        }
    });
}

/**
 * Update node and link positions
 */
function updateLayout() {
    // In a real implementation, this would use a force-directed layout algorithm
    // For this demo, just arrange nodes in a sphere
    
    // Parameters for layout
    const radius = 80; // Sphere radius
    const nodes = Object.values(nodeObjects);
    
    // Arrange nodes in a sphere
    nodes.forEach((node, i) => {
        // Only update position if not already set
        if (!node.userData.node.x || !node.userData.node.y || !node.userData.node.z) {
            // Calculate position on sphere using golden spiral distribution
            const phi = Math.acos(-1 + (2 * i) / nodes.length);
            const theta = Math.sqrt(nodes.length * Math.PI) * phi;
            
            // Set position
            const x = radius * Math.sin(phi) * Math.cos(theta);
            const y = radius * Math.sin(phi) * Math.sin(theta);
            const z = radius * Math.cos(phi);
            
            // Update node position with animation
            gsap.to(node.position, {
                x: x,
                y: y,
                z: z,
                duration: 2,
                ease: "power2.out",
                delay: i * 0.05
            });
            
            // Store position in node data
            node.userData.node.x = x;
            node.userData.node.y = y;
            node.userData.node.z = z;
        }
    });
    
    // Update links to follow nodes
    updateLinks();
}

// Export the key functions for external use
window.MemoryVisualization = {
    init: initVisualization,
    updateGraph: updateMemoryGraph
};

// Initialize automatically if a specific div exists
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('memory-visualization-container');
    if (container) {
        initVisualization('memory-visualization-container');
        
        // Generate and display sample data for demonstration
        const sampleData = {
            nodes: [
                { id: '1', type: 'conversation', label: 'User Query', size: 1.0 },
                { id: '2', type: 'semantic', label: 'Semantic Link', size: 0.8 },
                { id: '3', type: 'swarm', label: 'Agent Task', size: 0.9 },
                { id: '4', type: 'feedback', label: 'System Response', size: 0.7 },
                { id: '5', type: 'default', label: 'Unknown Type', size: 0.5 }
            ],
            links: [
                { source: '1', target: '2', strength: 0.8 },
                { source: '1', target: '3', strength: 0.5 },
                { source: '2', target: '4', strength: 0.7 },
                { source: '3', target: '4', strength: 0.9 },
                { source: '4', target: '5', strength: 0.3 }
            ]
        };
        
        // Update the visualization after a delay for better UX
        setTimeout(() => {
            updateMemoryGraph(sampleData);
        }, 1000);
    }
});