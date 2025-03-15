class KnowledgeGraphVisualization {
    constructor(containerId, data, options) {
        this.container = document.getElementById(containerId);
        this.data = data;
        this.options = options;
        
        // Initialize core components
        this.initScene();
        this.initCamera();
        this.initRenderer();
        this.initControls();
        this.initLighting();
        this.initPostProcessing();
        
        // Graph-specific components
        this.nodes = new Map();
        this.edges = new Map();
        this.initGraph();
        
        // Event handling
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        this.initEventListeners();
        
        // Start animation loop
        this.animate();
    }
    
    initScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(this.options.backgroundColor);
    }
    
    initCamera() {
        this.camera = new THREE.PerspectiveCamera(
            75,
            window.innerWidth / window.innerHeight,
            0.1,
            1000
        );
        this.camera.position.z = 50;
    }
    
    initRenderer() {
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);
    }
    
    initControls() {
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
    }
    
    initLighting() {
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 10);
        this.scene.add(directionalLight);
    }
    
    initPostProcessing() {
        if (!this.options.usePostprocessing) return;
        
        this.composer = new THREE.EffectComposer(this.renderer);
        const renderPass = new THREE.RenderPass(this.scene, this.camera);
        this.composer.addPass(renderPass);
        
        const bloomPass = new THREE.UnrealBloomPass(
            new THREE.Vector2(window.innerWidth, window.innerHeight),
            1.5, 0.4, 0.85
        );
        this.composer.addPass(bloomPass);
    }
    
    createNodeGeometry(node) {
        const size = node.size || this.options.defaultNodeSize;
        let geometry;
        
        if (node.visualProperties.shape === 'sphere') {
            geometry = new THREE.SphereGeometry(size, 32, 32);
        } else {
            geometry = new THREE.BoxGeometry(size, size, size);
        }
        
        const material = new THREE.MeshPhongMaterial({
            color: new THREE.Color(node.visualProperties.color),
            specular: 0x444444,
            shininess: 30
        });
        
        return new THREE.Mesh(geometry, material);
    }
    
    createEdgeGeometry(edge) {
        const sourceNode = this.nodes.get(edge.source);
        const targetNode = this.nodes.get(edge.target);
        
        const geometry = new THREE.BufferGeometry();
        const material = new THREE.LineBasicMaterial({
            color: new THREE.Color(edge.visualProperties.color),
            linewidth: edge.visualProperties.width || this.options.defaultEdgeWidth
        });
        
        const points = [
            sourceNode.position,
            targetNode.position
        ];
        
        geometry.setFromPoints(points);
        return new THREE.Line(geometry, material);
    }
    
    initGraph() {
        // Create nodes
        this.data.nodes.forEach(nodeData => {
            const nodeMesh = this.createNodeGeometry(nodeData);
            nodeMesh.position.set(
                nodeData.visualProperties.initialPosition[0],
                nodeData.visualProperties.initialPosition[1],
                nodeData.visualProperties.initialPosition[2]
            );
            nodeMesh.userData = nodeData;
            this.nodes.set(nodeData.id, nodeMesh);
            this.scene.add(nodeMesh);
        });
        
        // Create edges
        this.data.edges.forEach(edgeData => {
            const edgeLine = this.createEdgeGeometry(edgeData);
            this.edges.set(`${edgeData.source}-${edgeData.target}`, edgeLine);
            this.scene.add(edgeLine);
        });
    }
    
    updateEdges() {
        this.edges.forEach((line, key) => {
            const [sourceId, targetId] = key.split('-');
            const sourceNode = this.nodes.get(sourceId);
            const targetNode = this.nodes.get(targetId);
            
            const positions = new Float32Array([
                sourceNode.position.x, sourceNode.position.y, sourceNode.position.z,
                targetNode.position.x, targetNode.position.y, targetNode.position.z
            ]);
            
            line.geometry.setAttribute('position', 
                new THREE.BufferAttribute(positions, 3));
            line.geometry.attributes.position.needsUpdate = true;
        });
    }
    
    initEventListeners() {
        window.addEventListener('resize', this.onWindowResize.bind(this));
        this.renderer.domElement.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.renderer.domElement.addEventListener('click', this.onMouseClick.bind(this));
    }
    
    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        if (this.composer) {
            this.composer.setSize(window.innerWidth, window.innerHeight);
        }
    }
    
    onMouseMove(event) {
        this.mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
        this.mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
        
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(Array.from(this.nodes.values()));
        
        const nodeLabel = document.getElementById('node-label');
        
        if (intersects.length > 0) {
            const node = intersects[0].object;
            nodeLabel.textContent = node.userData.label;
            nodeLabel.style.display = 'block';
            nodeLabel.style.left = `${event.clientX + 10}px`;
            nodeLabel.style.top = `${event.clientY + 10}px`;
        } else {
            nodeLabel.style.display = 'none';
        }
    }
    
    onMouseClick(event) {
        // Handle node selection
    }
    
    applyForceDirectedLayout() {
        // Simple force-directed layout implementation
        this.nodes.forEach((nodeMesh, nodeId) => {
            // Apply repulsion between nodes
            this.nodes.forEach((otherMesh, otherId) => {
                if (nodeId === otherId) return;
                
                const dx = nodeMesh.position.x - otherMesh.position.x;
                const dy = nodeMesh.position.y - otherMesh.position.y;
                const dz = nodeMesh.position.z - otherMesh.position.z;
                
                const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
                const force = 50 / (distance * distance);
                
                nodeMesh.position.x += dx * force;
                nodeMesh.position.y += dy * force;
                nodeMesh.position.z += dz * force;
            });
        });
        
        // Apply edge attraction
        this.edges.forEach((line, key) => {
            const [sourceId, targetId] = key.split('-');
            const sourceNode = this.nodes.get(sourceId);
            const targetNode = this.nodes.get(targetId);
            
            const dx = targetNode.position.x - sourceNode.position.x;
            const dy = targetNode.position.y - sourceNode.position.y;
            const dz = targetNode.position.z - sourceNode.position.z;
            
            const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
            const force = (distance - 20) * 0.05;
            
            sourceNode.position.x += dx * force;
            sourceNode.position.y += dy * force;
            sourceNode.position.z += dz * force;
            
            targetNode.position.x -= dx * force;
            targetNode.position.y -= dy * force;
            targetNode.position.z -= dz * force;
        });
    }
    
    animate() {
        requestAnimationFrame(this.animate.bind(this));
        
        if (this.options.useForceDirectedLayout) {
            this.applyForceDirectedLayout();
            this.updateEdges();
        }
        
        this.controls.update();
        
        if (this.composer && this.options.usePostprocessing) {
            this.composer.render();
        } else {
            this.renderer.render(this.scene, this.camera);
        }
    }
}

// Initialize the visualization
const graphData = {
    nodes: [/* Your nodes data */],
    edges: [/* Your edges data */],
    groups: [/* Your groups data */]
};

const options = {
    backgroundColor: "#111133",
    defaultNodeSize: 5,
    defaultEdgeWidth: 1,
    highlightColor: "#ffffff",
    useForceDirectedLayout: true,
    useOrbitControls: true,
    enableLabels: true,
    colorByGroup: true,
    animateEdges: true,
    enableProgressiveLoading: true,
    usePostprocessing: true,
    enableInteraction: true,
    useModernRendering: true
};

// Create visualization instance
const visualization = new KnowledgeGraphVisualization(
    'graph-container',
    graphData,
    options
);

// Remove loading screen
document.getElementById('loading-screen').style.display = 'none';
