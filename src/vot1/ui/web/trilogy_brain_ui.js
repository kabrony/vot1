/**
 * TRILOGY BRAIN UI - 3D Memory Network Visualization
 * 
 * This module provides an interactive 3D visualization of the TRILOGY BRAIN
 * distributed memory system using Three.js. It creates an immersive representation
 * of memory nodes, compute nodes, and the connections between them.
 * 
 * Features:
 * - Real-time visualization of network topology
 * - Interactive node exploration
 * - Memory flow visualization
 * - Network health monitoring
 * - 3D spatial representation of the memory architecture
 * 
 * The visualization is designed to be both informative and visually appealing,
 * with smooth animations and interactive elements that make it easy to understand
 * the system's state at a glance.
 * 
 * @module trilogy_brain_ui
 * @version 1.0.0
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { TWEEN } from 'three/addons/libs/tween.module.min.js';

// Node types and their corresponding colors
const NODE_TYPES = {
    MEMORY: {
        color: 0x3498db,
        glowColor: 0x6cb4f0,
        size: 1.0
    },
    COMPUTE: {
        color: 0x2ecc71,
        glowColor: 0x7fff9b,
        size: 0.8
    },
    VALIDATOR: {
        color: 0xe74c3c,
        glowColor: 0xff7675,
        size: 0.7
    },
    COORDINATOR: {
        color: 0xf39c12,
        glowColor: 0xffc04d,
        size: 1.2
    },
    GATEWAY: {
        color: 0x9b59b6,
        glowColor: 0xd6a2e8,
        size: 0.9
    }
};

// Connection types
const CONNECTION_TYPES = {
    STANDARD: {
        color: 0x6c7ae0,
        width: 0.1
    },
    HIGH_TRAFFIC: {
        color: 0xf39c12,
        width: 0.2
    },
    ERROR: {
        color: 0xe74c3c,
        width: 0.15
    },
    SECURE: {
        color: 0x2ecc71,
        width: 0.12
    }
};

/**
 * Main class for the TRILOGY BRAIN 3D visualization
 */
export default class TrilogyBrainUI {
    /**
     * Create a new TRILOGY BRAIN UI instance
     * @param {Object} options - Configuration options
     * @param {string} options.containerId - ID of the container element
     * @param {string} options.apiUrl - Base URL for the API
     * @param {boolean} options.enableEffects - Whether to enable post-processing effects
     * @param {boolean} options.autoRotate - Whether to auto-rotate the camera
     */
    constructor(options) {
        this.container = document.getElementById(options.containerId);
        this.apiUrl = options.apiUrl;
        this.enableEffects = options.enableEffects !== undefined ? options.enableEffects : true;
        this.autoRotate = options.autoRotate !== undefined ? options.autoRotate : false;
        
        // State
        this.nodes = new Map();
        this.selectedNode = null;
        this.isInitialized = false;
        this.lastUpdateTime = 0;
        this.updateInterval = 5000; // 5 seconds
        
        // Initialize 3D scene
        this._initScene();
        this._initRenderer();
        this._initCamera();
        this._initControls();
        this._initEffects();
        this._initLights();
        this._initEventListeners();
        
        // Start the render loop
        this._animate();
        
        // Mark as initialized
        this.isInitialized = true;
        console.log('TRILOGY BRAIN UI initialized');
        
        // Fetch initial data
        this._fetchNetworkData();
    }
    
    /**
     * Initialize the 3D scene
     * @private
     */
    _initScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0f0f1a);
        
        // Add a subtle grid for reference
        const gridHelper = new THREE.GridHelper(100, 50, 0x111133, 0x111133);
        gridHelper.position.y = -5;
        this.scene.add(gridHelper);
        
        // Add a particle background for a space-like effect
        this.addParticleBackground();
        
        // Object groups
        this.nodesGroup = new THREE.Group();
        this.linksGroup = new THREE.Group();
        this.labelsGroup = new THREE.Group();
        
        this.scene.add(this.nodesGroup);
        this.scene.add(this.linksGroup);
        this.scene.add(this.labelsGroup);
    }
    
    /**
     * Initialize the renderer
     * @private
     */
    _initRenderer() {
        // Main WebGL renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.0;
        this.container.appendChild(this.renderer.domElement);
        
        // Label renderer (CSS2D)
        this.labelRenderer = new CSS2DRenderer();
        this.labelRenderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.labelRenderer.domElement.style.position = 'absolute';
        this.labelRenderer.domElement.style.top = '0';
        this.labelRenderer.domElement.style.pointerEvents = 'none';
        this.container.appendChild(this.labelRenderer.domElement);
    }
    
    /**
     * Initialize the camera
     * @private
     */
    _initCamera() {
        const aspectRatio = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(60, aspectRatio, 0.1, 1000);
        this.camera.position.set(0, 10, 30);
        this.camera.lookAt(0, 0, 0);
    }
    
    /**
     * Initialize camera controls
     * @private
     */
    _initControls() {
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.rotateSpeed = 0.5;
        this.controls.autoRotate = this.autoRotate;
        this.controls.autoRotateSpeed = 0.5;
        this.controls.minDistance = 10;
        this.controls.maxDistance = 100;
        this.controls.enablePan = true;
    }
    
    /**
     * Initialize post-processing effects
     * @private
     */
    _initEffects() {
        if (!this.enableEffects) return;
        
        this.composer = new EffectComposer(this.renderer);
        
        const renderPass = new RenderPass(this.scene, this.camera);
        this.composer.addPass(renderPass);
        
        // Bloom effect for glow
        const bloomPass = new UnrealBloomPass(
            new THREE.Vector2(this.container.clientWidth, this.container.clientHeight),
            0.8,  // strength
            0.3,  // radius
            0.7   // threshold
        );
        this.composer.addPass(bloomPass);
        
        // Output pass
        const outputPass = new OutputPass();
        this.composer.addPass(outputPass);
    }
    
    /**
     * Initialize scene lighting
     * @private
     */
    _initLights() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
        this.scene.add(ambientLight);
        
        // Directional light (sun-like)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.7);
        directionalLight.position.set(5, 15, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 50;
        directionalLight.shadow.camera.left = -20;
        directionalLight.shadow.camera.right = 20;
        directionalLight.shadow.camera.top = 20;
        directionalLight.shadow.camera.bottom = -20;
        this.scene.add(directionalLight);
        
        // Add some colored point lights for atmosphere
        const pointLight1 = new THREE.PointLight(0x3498db, 2, 20);
        pointLight1.position.set(-15, 5, -10);
        this.scene.add(pointLight1);
        
        const pointLight2 = new THREE.PointLight(0x2ecc71, 2, 20);
        pointLight2.position.set(15, 5, -10);
        this.scene.add(pointLight2);
        
        const pointLight3 = new THREE.PointLight(0xe74c3c, 2, 20);
        pointLight3.position.set(0, 5, 15);
        this.scene.add(pointLight3);
    }
    
    /**
     * Initialize event listeners
     * @private
     */
    _initEventListeners() {
        // Resize handler
        window.addEventListener('resize', () => {
            this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
            this.labelRenderer.setSize(this.container.clientWidth, this.container.clientHeight);
            
            if (this.composer) {
                this.composer.setSize(this.container.clientWidth, this.container.clientHeight);
            }
        });
        
        // Mouse click handler for node selection
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        
        this.renderer.domElement.addEventListener('click', (event) => {
            // Calculate mouse position in normalized device coordinates
            const rect = this.renderer.domElement.getBoundingClientRect();
            mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
            
            // Update the raycaster
            raycaster.setFromCamera(mouse, this.camera);
            
            // Find intersections with nodes
            const intersects = raycaster.intersectObjects(this.nodesGroup.children);
            
            if (intersects.length > 0) {
                const nodeObject = intersects[0].object;
                this._selectNode(nodeObject.userData.nodeId);
            } else {
                this._deselectNode();
            }
        });
    }
    
    /**
     * Animation loop
     * @private
     */
    _animate() {
        requestAnimationFrame(this._animate.bind(this));
        
        // Update controls
        this.controls.update();
        
        // Update tweens
        TWEEN.update();
        
        // Check if we need to update data
        const currentTime = Date.now();
        if (currentTime - this.lastUpdateTime > this.updateInterval) {
            this._fetchNetworkData();
            this.lastUpdateTime = currentTime;
        }
        
        // Render
        if (this.enableEffects && this.composer) {
            this.composer.render();
        } else {
            this.renderer.render(this.scene, this.camera);
        }
        
        // Render labels
        this.labelRenderer.render(this.scene, this.camera);
    }
    
    /**
     * Fetch network data from the API
     * @private
     */
    _fetchNetworkData() {
        // TODO: Replace with actual API call
        // For now, simulate with mock data
        const mockData = this._generateMockData();
        this.updateNetwork(mockData);
        
        // In a real implementation, we would use:
        // fetch(`${this.apiUrl}/network/stats`)
        //     .then(response => response.json())
        //     .then(data => this.updateNetwork(data))
        //     .catch(error => console.error('Error fetching network data:', error));
    }
    
    /**
     * Generate mock data for demonstration
     * @private
     * @returns {Object} Mock network data
     */
    _generateMockData() {
        const nodeTypes = ['memory', 'compute', 'coordinator', 'validator', 'gateway'];
        const nodeStatuses = ['initializing', 'online', 'offline', 'error', 'syncing', 'backup'];
        
        const nodes = [];
        const nodeCount = 15;
        
        for (let i = 0; i < nodeCount; i++) {
            const nodeType = nodeTypes[Math.floor(Math.random() * nodeTypes.length)];
            const status = Math.random() > 0.3 ? 'online' : nodeStatuses[Math.floor(Math.random() * nodeStatuses.length)];
            
            nodes.push({
                node_id: `node_${i}`,
                node_type: nodeType,
                host: 'localhost',
                port: 8000 + i,
                status: status,
                capabilities: ['store', 'retrieve', 'sync'],
                resources: {
                    cpu: Math.random() * 100,
                    memory: Math.random() * 100,
                    storage: Math.random() * 100
                },
                last_heartbeat: new Date().toISOString(),
                error_count: Math.floor(Math.random() * 5)
            });
        }
        
        // Generate connections
        const connections = [];
        for (let i = 0; i < nodes.length; i++) {
            const connectionCount = Math.floor(Math.random() * 3) + 1;
            for (let j = 0; j < connectionCount; j++) {
                const targetIdx = Math.floor(Math.random() * nodes.length);
                if (targetIdx !== i) {
                    connections.push({
                        source: nodes[i].node_id,
                        target: nodes[targetIdx].node_id,
                        strength: Math.random()
                    });
                }
            }
        }
        
        return {
            nodes: nodes,
            connections: connections,
            network_health: Math.random(),
            timestamp: new Date().toISOString()
        };
    }
    
    /**
     * Update the network visualization
     * 
     * @param {Object} data - Network data from API
     */
    updateNetwork(data) {
        if (!data || !data.nodes) return;
        
        const existingNodeIds = new Set(this.nodes.keys());
        const newNodeIds = new Set();
        
        // Update or create nodes
        data.nodes.forEach((nodeData) => {
            const nodeId = nodeData.node_id;
            newNodeIds.add(nodeId);
            
            if (this.nodes.has(nodeId)) {
                // Update existing node
                this._updateNode(nodeId, nodeData);
            } else {
                // Create new node
                this._createNode(nodeData);
            }
        });
        
        // Remove nodes that no longer exist
        existingNodeIds.forEach((nodeId) => {
            if (!newNodeIds.has(nodeId)) {
                this._removeNode(nodeId);
            }
        });
        
        // Update connections
        this._updateConnections(data.connections || []);
        
        // Layout nodes in a nice formation
        this._layoutNodes();
    }
    
    /**
     * Create a new node visualization
     * 
     * @param {Object} nodeData - Node data from API
     * @private
     */
    _createNode(nodeData) {
        const nodeId = nodeData.node_id;
        const nodeType = nodeData.node_type;
        const status = nodeData.status;
        
        // Create node mesh
        const typeConfig = NODE_TYPES[nodeType] || NODE_TYPES.MEMORY;
        const geometry = new THREE.SphereGeometry(typeConfig.size, 32, 32);
        const material = new THREE.MeshStandardMaterial({
            color: typeConfig.color,
            emissive: typeConfig.glowColor,
            emissiveIntensity: 0.7,
            metalness: 0.3,
            roughness: 0.4
        });
        
        const mesh = new THREE.Mesh(geometry, material);
        mesh.userData = { nodeId, nodeType, status };
        
        // Random position initially
        const radius = 10 + Math.random() * 10;
        const angle = Math.random() * Math.PI * 2;
        mesh.position.set(
            Math.cos(angle) * radius,
            (Math.random() - 0.5) * 5,
            Math.sin(angle) * radius
        );
        
        // Store original position for animation
        const originalPosition = mesh.position.clone();
        
        // Add to scene
        this.nodesGroup.add(mesh);
        
        // Create label
        const labelDiv = document.createElement('div');
        labelDiv.className = 'node-label';
        labelDiv.textContent = `${nodeId} (${nodeType})`;
        labelDiv.style.color = '#ffffff';
        labelDiv.style.fontSize = '12px';
        labelDiv.style.padding = '2px';
        labelDiv.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        labelDiv.style.borderRadius = '4px';
        
        const label = new CSS2DObject(labelDiv);
        label.position.set(0, 1.5, 0);
        mesh.add(label);
        
        // Store node data
        this.nodes.set(nodeId, {
            data: nodeData,
            mesh: mesh,
            label: label,
            originalPosition,
            type: nodeType,
            status: status,
            connections: new Set()
        });
    }
    
    /**
     * Update an existing node visualization
     * 
     * @param {string} nodeId - Node ID
     * @param {Object} nodeData - Node data from API
     * @private
     */
    _updateNode(nodeId, nodeData) {
        const node = this.nodes.get(nodeId);
        if (!node) return;
        
        // Update node data
        node.data = nodeData;
        
        // Update visual properties
        const typeConfig = NODE_TYPES[nodeData.node_type] || NODE_TYPES.MEMORY;
        node.mesh.material.color.setHex(typeConfig.color);
        node.mesh.material.emissive.setHex(typeConfig.glowColor);
        
        // Update label
        const labelDiv = node.label.element;
        labelDiv.textContent = `${nodeId} (${nodeData.node_type})`;
        
        // Update user data
        node.mesh.userData.nodeType = nodeData.node_type;
        node.mesh.userData.status = nodeData.status;
    }
    
    /**
     * Remove a node from the visualization
     * 
     * @param {string} nodeId - Node ID
     * @private
     */
    _removeNode(nodeId) {
        const node = this.nodes.get(nodeId);
        if (!node) return;
        
        // Remove mesh from scene
        this.nodesGroup.remove(node.mesh);
        
        // Remove connections
        node.connections.forEach(connectionId => {
            const connection = this.linksGroup.getObjectByName(connectionId);
            if (connection) {
                this.linksGroup.remove(connection);
            }
        });
        
        // Remove from nodes map
        this.nodes.delete(nodeId);
        
        // If this was the selected node, deselect it
        if (this.selectedNode === nodeId) {
            this._deselectNode();
        }
    }
    
    /**
     * Update connections between nodes
     * 
     * @param {Array} connections - Connection data from API
     * @private
     */
    _updateConnections(connections) {
        // Clear existing connections
        while (this.linksGroup.children.length > 0) {
            this.linksGroup.remove(this.linksGroup.children[0]);
        }
        
        // Clear connection records
        this.nodes.forEach(node => {
            node.connections.clear();
        });
        
        // Create new connections
        connections.forEach(connection => {
            const sourceNode = this.nodes.get(connection.source);
            const targetNode = this.nodes.get(connection.target);
            
            if (!sourceNode || !targetNode) return;
            
            // Create line material
            const typeConfig = CONNECTION_TYPES[connection.type] || CONNECTION_TYPES.STANDARD;
            const material = new THREE.LineBasicMaterial({
                color: typeConfig.color,
                transparent: true,
                opacity: connection.strength || 0.3,
                linewidth: typeConfig.width
            });
            
            // Create line geometry
            const geometry = new THREE.BufferGeometry().setFromPoints([
                sourceNode.mesh.position,
                targetNode.mesh.position
            ]);
            
            // Create line
            const line = new THREE.Line(geometry, material);
            const connectionId = `connection_${connection.source}_${connection.target}`;
            line.name = connectionId;
            
            // Add to scene
            this.linksGroup.add(line);
            
            // Record connection
            sourceNode.connections.add(connectionId);
            targetNode.connections.add(connectionId);
        });
    }
    
    /**
     * Layout nodes in a visually appealing formation
     * @private
     */
    _layoutNodes() {
        const nodeCount = this.nodes.size;
        if (nodeCount === 0) return;
        
        // Use a spherical layout
        const radius = Math.min(20, Math.max(10, nodeCount * 1.5));
        
        // Group nodes by type
        const nodesByType = {};
        this.nodes.forEach((node, nodeId) => {
            const type = node.data.node_type;
            if (!nodesByType[type]) {
                nodesByType[type] = [];
            }
            nodesByType[type].push({ id: nodeId, node });
        });
        
        // Position each type in its own area
        const typeCount = Object.keys(nodesByType).length;
        Object.entries(nodesByType).forEach(([type, nodes], typeIndex) => {
            const phi = (typeIndex / typeCount) * Math.PI * 2;
            const groupRadius = radius * 0.8;
            const groupCenter = new THREE.Vector3(
                Math.cos(phi) * groupRadius,
                Math.sin(phi) * groupRadius,
                0
            );
            
            // Position nodes in a circle around the group center
            nodes.forEach((nodeEntry, nodeIndex) => {
                const node = nodeEntry.node;
                const angle = (nodeIndex / nodes.length) * Math.PI * 2;
                const distance = 5 + Math.random() * 3;
                
                const targetPosition = new THREE.Vector3(
                    groupCenter.x + Math.cos(angle) * distance,
                    groupCenter.y + Math.sin(angle) * distance,
                    (Math.random() - 0.5) * 10
                );
                
                // Animate the node to its new position
                new TWEEN.Tween(node.mesh.position)
                    .to(targetPosition, 2000)
                    .easing(TWEEN.Easing.Quadratic.InOut)
                    .start();
            });
        });
        
        // Update connections after layout
        this._updateConnectionPositions();
    }
    
    /**
     * Update positions of connections to follow nodes
     * @private
     */
    _updateConnectionPositions() {
        this.linksGroup.children.forEach(line => {
            const [sourceId, targetId] = line.name.replace('connection_', '').split('_');
            const sourceNode = this.nodes.get(sourceId);
            const targetNode = this.nodes.get(targetId);
            
            if (sourceNode && targetNode) {
                const positions = [
                    sourceNode.mesh.position,
                    targetNode.mesh.position
                ];
                
                line.geometry.setFromPoints(positions);
                line.geometry.attributes.position.needsUpdate = true;
            }
        });
    }
    
    /**
     * Select a node and show its details
     * 
     * @param {string} nodeId - Node ID to select
     * @private
     */
    _selectNode(nodeId) {
        // Deselect previous node if any
        this._deselectNode();
        
        const node = this.nodes.get(nodeId);
        if (!node) return;
        
        // Set as selected
        this.selectedNode = nodeId;
        
        // Highlight the node
        const originalScale = node.mesh.scale.clone();
        node.originalScale = originalScale;
        
        new TWEEN.Tween(node.mesh.scale)
            .to({ x: originalScale.x * 1.5, y: originalScale.y * 1.5, z: originalScale.z * 1.5 }, 300)
            .easing(TWEEN.Easing.Quadratic.Out)
            .start();
        
        // Highlight connections
        node.connections.forEach(connectionId => {
            const connection = this.linksGroup.getObjectByName(connectionId);
            if (connection) {
                connection.material.color.setHex(0xffff00);
                connection.material.opacity = 0.8;
            }
        });
        
        // Show node details panel
        this._showNodeDetails(nodeId);
    }
    
    /**
     * Deselect the currently selected node
     * @private
     */
    _deselectNode() {
        if (!this.selectedNode) return;
        
        const node = this.nodes.get(this.selectedNode);
        if (node) {
            // Reset scale
            if (node.originalScale) {
                new TWEEN.Tween(node.mesh.scale)
                    .to({ x: node.originalScale.x, y: node.originalScale.y, z: node.originalScale.z }, 300)
                    .easing(TWEEN.Easing.Quadratic.Out)
                    .start();
                
                node.originalScale = null;
            }
            
            // Reset connections
            node.connections.forEach(connectionId => {
                const connection = this.linksGroup.getObjectByName(connectionId);
                if (connection) {
                    connection.material.color.setHex(0xffffff);
                    connection.material.opacity = 0.3;
                }
            });
        }
        
        // Hide node details panel
        this._hideNodeDetails();
        
        this.selectedNode = null;
    }
    
    /**
     * Show node details in UI panel
     * 
     * @param {string} nodeId - Node ID
     * @private
     */
    _showNodeDetails(nodeId) {
        const node = this.nodes.get(nodeId);
        if (!node) return;
        
        // Create or update details panel
        let detailsPanel = document.getElementById('node-details-panel');
        if (!detailsPanel) {
            detailsPanel = document.createElement('div');
            detailsPanel.id = 'node-details-panel';
            detailsPanel.style.position = 'absolute';
            detailsPanel.style.top = '20px';
            detailsPanel.style.right = '20px';
            detailsPanel.style.width = '300px';
            detailsPanel.style.padding = '15px';
            detailsPanel.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
            detailsPanel.style.borderRadius = '8px';
            detailsPanel.style.color = 'white';
            detailsPanel.style.fontFamily = 'Arial, sans-serif';
            detailsPanel.style.zIndex = '1000';
            this.container.appendChild(detailsPanel);
        }
        
        // Populate details
        const nodeData = node.data;
        
        detailsPanel.innerHTML = `
            <h3 style="margin-top: 0; color: #3498db;">Node: ${nodeId}</h3>
            <div style="margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);">
                <div><strong>Type:</strong> ${nodeData.node_type}</div>
                <div><strong>Status:</strong> <span style="color: ${new THREE.Color(NODE_TYPES[nodeData.node_type]?.glowColor || 0xffffff).getStyle()}">${nodeData.status}</span></div>
                <div><strong>Host:</strong> ${nodeData.host}:${nodeData.port}</div>
            </div>
            
            <div style="margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);">
                <h4 style="margin: 5px 0;">Resources</h4>
                <div>CPU: ${Math.round(nodeData.resources.cpu)}%</div>
                <div>Memory: ${Math.round(nodeData.resources.memory)}%</div>
                <div>Storage: ${Math.round(nodeData.resources.storage)}%</div>
            </div>
            
            <div>
                <h4 style="margin: 5px 0;">Network</h4>
                <div>Connections: ${node.connections.size}</div>
                <div>Last Heartbeat: ${new Date(nodeData.last_heartbeat).toLocaleTimeString()}</div>
                <div>Error Count: ${nodeData.error_count}</div>
            </div>
            
            <div style="margin-top: 15px;">
                <button id="node-action-btn" style="background: #2980b9; border: none; padding: 8px 15px; color: white; border-radius: 4px; cursor: pointer;">
                    ${nodeData.status === 'online' ? 'Stop Node' : 'Start Node'}
                </button>
            </div>
        `;
        
        // Add action button handler
        document.getElementById('node-action-btn').addEventListener('click', () => {
            const action = nodeData.status === 'online' ? 'stop' : 'start';
            this._performNodeAction(nodeId, action);
        });
        
        // Show panel with animation
        detailsPanel.style.opacity = '0';
        detailsPanel.style.transform = 'translateX(20px)';
        detailsPanel.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        
        // Force reflow
        detailsPanel.offsetHeight;
        
        detailsPanel.style.opacity = '1';
        detailsPanel.style.transform = 'translateX(0)';
    }
    
    /**
     * Hide node details panel
     * @private
     */
    _hideNodeDetails() {
        const detailsPanel = document.getElementById('node-details-panel');
        if (!detailsPanel) return;
        
        // Animate out
        detailsPanel.style.opacity = '0';
        detailsPanel.style.transform = 'translateX(20px)';
        
        // Remove after animation
        setTimeout(() => {
            if (detailsPanel.parentNode) {
                detailsPanel.parentNode.removeChild(detailsPanel);
            }
        }, 300);
    }
    
    /**
     * Perform an action on a node
     * 
     * @param {string} nodeId - Node ID
     * @param {string} action - Action to perform ('start', 'stop', etc.)
     * @private
     */
    _performNodeAction(nodeId, action) {
        console.log(`Performing action ${action} on node ${nodeId}`);
        
        // TODO: Replace with actual API call
        // fetch(`${this.apiUrl}/nodes/${nodeId}/${action}`, {
        //     method: 'POST'
        // })
        //     .then(response => response.json())
        //     .then(data => {
        //         console.log(`Action ${action} completed:`, data);
        //         this._fetchNetworkData();  // Refresh data
        //     })
        //     .catch(error => console.error(`Error performing ${action}:`, error));
        
        // For demo: simulate the action
        const node = this.nodes.get(nodeId);
        if (node) {
            if (action === 'start') {
                node.data.status = 'online';
            } else if (action === 'stop') {
                node.data.status = 'offline';
            }
            
            // Update node visualization
            this._updateNode(nodeId, node.data);
            
            // Update details panel
            if (this.selectedNode === nodeId) {
                this._showNodeDetails(nodeId);
            }
        }
    }
    
    /**
     * Focus the camera on a specific node
     * 
     * @param {string} nodeId - Node ID to focus on
     */
    focusNode(nodeId) {
        const node = this.nodes.get(nodeId);
        if (!node) return;
        
        // Animate camera to look at the node
        const targetPosition = node.mesh.position.clone();
        const distance = 20;
        const offset = new THREE.Vector3(distance, distance / 2, distance);
        
        new TWEEN.Tween(this.camera.position)
            .to({
                x: targetPosition.x + offset.x,
                y: targetPosition.y + offset.y,
                z: targetPosition.z + offset.z
            }, 1000)
            .easing(TWEEN.Easing.Cubic.InOut)
            .start();
        
        // Make the controls look at the node
        new TWEEN.Tween(this.controls.target)
            .to({
                x: targetPosition.x,
                y: targetPosition.y,
                z: targetPosition.z
            }, 1000)
            .easing(TWEEN.Easing.Cubic.InOut)
            .start();
        
        // Select the node
        this._selectNode(nodeId);
    }
    
    /**
     * Set auto-rotation of the camera
     * 
     * @param {boolean} enabled - Whether auto-rotation should be enabled
     */
    setAutoRotate(enabled) {
        this.autoRotate = enabled;
        this.controls.autoRotate = enabled;
    }
    
    /**
     * Toggle effects (bloom, etc.) on or off
     * 
     * @param {boolean} enabled - Whether effects should be enabled
     */
    setEffects(enabled) {
        this.enableEffects = enabled;
    }
    
    /**
     * Clean up resources when destroying the UI
     */
    dispose() {
        // Stop animation loop
        this.isInitialized = false;
        
        // Dispose geometries, materials, textures
        this.scene.traverse(object => {
            if (object.geometry) {
                object.geometry.dispose();
            }
            
            if (object.material) {
                if (Array.isArray(object.material)) {
                    object.material.forEach(material => {
                        material.dispose();
                    });
                } else {
                    object.material.dispose();
                }
            }
        });
        
        // Dispose renderer
        this.renderer.dispose();
        
        // Remove event listeners
        window.removeEventListener('resize', this._onWindowResize);
        
        // Remove elements
        while (this.container.firstChild) {
            this.container.removeChild(this.container.firstChild);
        }
        
        console.log('TRILOGY BRAIN UI disposed');
    }
} 