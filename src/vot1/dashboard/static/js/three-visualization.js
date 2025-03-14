/**
 * VOT1 Cyberpunk Memory Visualization v3.0
 * 
 * An immersive 80s/90s arcade-style cyberpunk visualization of the VOT1 memory system
 * using THREE.js with advanced effects, data flow animations, and real-time interaction.
 */

// Global variables
let scene, camera, renderer, controls;
let graph = {nodes: [], links: []};
let nodeObjects = {};
let linkObjects = {};
let particles, grid, gridFloor, gridCeiling; 
let raycaster, mouse;
let clock, deltaTime, elapsedTime = 0;
let selectedNode = null;
let composer, bloomPass, glitchPass, filmPass;
let nodeGroups = {};
let audioContext, audioAnalyser, audioData;
let audioInitialized = false;
let dataPulses = [];
let visualizationActive = true;

// CRT shader uniforms
const crtUniforms = {
    time: { value: 0 },
    resolution: { value: new THREE.Vector2() },
    scanlineIntensity: { value: 0.5 },
    noiseIntensity: { value: 0.1 }
};

// Configuration
const config = {
    // Core parameters
    nodeSizeBase: 5,
    nodeSizeVariation: 3,
    nodeColors: {
        conversation: 0x00ffdd, // Cyan
        semantic: 0xff00ff,     // Magenta
        swarm: 0x2fff8f,        // Neon green
        feedback: 0xffff00,     // Yellow
        default: 0x8844ff       // Purple
    },
    highlightColor: 0xffffff,    // White
    linkColor: 0x44bbff,         // Blue
    highlightLinkColor: 0xff44bb, // Pink
    backgroundColor: 0x020408,   // Almost black
    
    // Visual effects
    glowIntensity: 0.9,          // Glow strength
    glowSize: 2.3,               // Glow size multiplier
    particleCount: 1500,         // Background particles
    gridColor: 0x0088ff,         // Grid color
    gridOpacity: 0.15,           // Grid opacity
    gridSize: 100,               // Grid size
    gridDivisions: 20,           // Grid divisions
    
    // Camera and animation
    cameraDistance: 150,         // Initial camera distance
    animationSpeed: 0.5,         // Animation speed multiplier
    nodeAnimationSpeed: 0.8,     // Node animation speed
    dataFlowSpeed: 2.0,          // Data flow speed
    
    // Post-processing
    enableBloom: true,           // Enable bloom effect
    bloomStrength: 1.5,          // Bloom strength
    bloomRadius: 0.5,            // Bloom radius
    bloomThreshold: 0.1,         // Bloom threshold
    enableFilm: true,            // Enable film grain effect
    enableGlitch: true,          // Enable occasional glitches
    glitchProbability: 0.01,     // Probability of glitch per frame
    
    // Audio visualization
    enableAudio: true,           // Enable audio visualization
    audioReactivity: 0.5,        // How much audio affects the visualization
    
    // Performance
    maxVisibleNodes: 150,        // Maximum nodes to display at once
    maxVisibleLinks: 300,        // Maximum links to display at once
    enableLOD: true,             // Enable level of detail optimization
};

/**
 * Initialize the 3D visualization
 * @param {string} containerId - ID of the container element
 */
function initVisualization(containerId) {
    // Get container
    container = document.getElementById(containerId);
    if (!container) {
        console.error('Container element not found:', containerId);
        return;
    }

    // Initialize clock for animations
    clock = new THREE.Clock();

    // Create scene with fog for depth
    scene = new THREE.Scene();
    scene.background = new THREE.Color(config.backgroundColor);
    scene.fog = new THREE.FogExp2(config.backgroundColor, 0.0015);
    
    // Create perspective camera
    const width = container.clientWidth;
    const height = container.clientHeight;
    camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.z = config.cameraDistance;
    
    // Create renderer with enhanced settings
    renderer = new THREE.WebGLRenderer({ 
        antialias: true, 
        alpha: true,
        logarithmicDepthBuffer: true,
        powerPreference: 'high-performance'
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Limit pixel ratio for performance
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // Add orbit controls with damping for smooth movement
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.12;
    controls.rotateSpeed = 0.7;
    controls.zoomSpeed = 1.2;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.3;
    controls.minDistance = 30;
    controls.maxDistance = 300;
    
    // Setup raycaster for interaction
    raycaster = new THREE.Raycaster();
    raycaster.params.Line.threshold = 3; // Increase line selection threshold
    mouse = new THREE.Vector2();

    // Initialize node groups for organization
    initNodeGroups();
    
    // Set up scene elements
    addLights();
    createCyberpunkEnvironment();
    
    // Initialize post-processing effects
    if (typeof THREE.EffectComposer !== 'undefined') {
        initPostProcessing(width, height);
    } else {
        console.warn('Post-processing not available, some visual effects disabled');
    }
    
    // Set up audio context for visualization
    if (config.enableAudio && window.AudioContext) {
        initAudio();
    }

    // Add event listeners
    setupEventListeners(container);

    // Start animation loop
    animate();

    // Load memory data
    loadMemoryData();

    // Add UI controls for visualization settings
    setupUIControls();

    // Setup real-time updates
    setupRealTimeUpdates();

    // Log initialization
    console.log("VOT1 Cyberpunk Memory Visualization initialized");
}

// Initialize post-processing effects for cyberpunk visual style
function initPostProcessing(width, height) {
        composer = new THREE.EffectComposer(renderer);
    composer.setSize(width, height);
    
    // Standard render pass
        const renderPass = new THREE.RenderPass(scene, camera);
        composer.addPass(renderPass);
        
    if (config.enableBloom) {
        // Add bloom effect for neon glow
        bloomPass = new THREE.UnrealBloomPass(
            new THREE.Vector2(width, height),
            config.bloomStrength,
            config.bloomRadius,
            config.bloomThreshold
        );
        composer.addPass(bloomPass);
    }
    
    if (config.enableFilm) {
        // Add film grain effect for retro look
        filmPass = new THREE.FilmPass(0.35, 0.025, 648, false);
        composer.addPass(filmPass);
    }
    
    if (config.enableGlitch) {
        // Add digital glitch effect for cyberpunk aesthetic
        glitchPass = new THREE.GlitchPass();
        glitchPass.goWild = false;
        glitchPass.enabled = false; // Disabled by default, triggered occasionally
        composer.addPass(glitchPass);
    }
    
    // Add CRT shader effect - custom retro monitor effect
    const crtShader = {
        uniforms: crtUniforms,
        vertexShader: `
            varying vec2 vUv;
            void main() {
                vUv = uv;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            uniform float time;
            uniform vec2 resolution;
            uniform float scanlineIntensity;
            uniform float noiseIntensity;
            varying vec2 vUv;
            
            float random(vec2 st) {
                return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
            }
            
            void main() {
                vec2 uv = vUv;
                
                // Slight curved screen effect
                vec2 curvedUV = uv * 2.0 - 1.0;
                float distortion = 0.1;
                float barrelFactor = 1.0 - distortion * dot(curvedUV, curvedUV);
                curvedUV = curvedUV * barrelFactor + 0.5;
                
                vec4 previousPassColor = texture2D(tDiffuse, curvedUV);
                
                // Add slight vignette
                float vignette = smoothstep(1.0, 0.0, length(curvedUV - 0.5) * 1.5);
                
                // Add scanlines
                float scanline = sin(uv.y * resolution.y * 1.0) * 0.5 + 0.5;
                scanline = pow(scanline, 3.0) * scanlineIntensity;
                
                // Add noise
                float noise = random(vUv + time * 0.01) * noiseIntensity;
                
                // Final color
                vec4 finalColor = previousPassColor * (1.0 - scanline) * vignette;
                finalColor.rgb += vec3(noise);
                
                // Chromatic aberration
                float aberration = 0.003;
                finalColor.r = texture2D(tDiffuse, curvedUV + vec2(aberration, 0.0)).r;
                finalColor.b = texture2D(tDiffuse, curvedUV - vec2(aberration, 0.0)).b;
                
                gl_FragColor = finalColor;
            }
        `
    };
    
    const crtPass = new THREE.ShaderPass(crtShader);
    crtPass.uniforms.resolution.value.set(width, height);
    composer.addPass(crtPass);
}

// Create node groups for organizing different types of nodes
function initNodeGroups() {
    // Create groups for different node types
    const types = ['conversation', 'semantic', 'swarm', 'feedback'];
    
    // Create a parent group for all memory nodes
    nodeGroups['all'] = new THREE.Group();
    nodeGroups['all'].name = 'all-nodes';
    scene.add(nodeGroups['all']);
        
        types.forEach(type => {
        nodeGroups[type] = new THREE.Group();
        nodeGroups[type].name = `${type}-nodes`;
        nodeGroups['all'].add(nodeGroups[type]);
    });

    // Create a group for connections
    nodeGroups['connections'] = new THREE.Group();
    nodeGroups['connections'].name = 'connections';
    scene.add(nodeGroups['connections']);
    
    // Create a group for data flow particles
    nodeGroups['dataFlow'] = new THREE.Group();
    nodeGroups['dataFlow'].name = 'data-flow';
    scene.add(nodeGroups['dataFlow']);
}

// Initialize audio for reactive visualization
function initAudio() {
    try {
        // Create audio context
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Create audio source from an oscillator (silent by default)
        const oscillator = audioContext.createOscillator();
        oscillator.frequency.value = 0;
        
        // Create analyser
        audioAnalyser = audioContext.createAnalyser();
        audioAnalyser.fftSize = 128;
        audioData = new Uint8Array(audioAnalyser.frequencyBinCount);
        
        // Connect audio nodes
        oscillator.connect(audioAnalyser);
        
        // Start oscillator
        oscillator.start();
        
        audioInitialized = true;
        console.log('Audio visualization initialized');
    } catch (error) {
        console.warn('Failed to initialize audio visualization:', error);
        config.enableAudio = false;
    }
}

// Create cyberpunk environment with grids, particles, and ambient effects
function createCyberpunkEnvironment() {
    // Create endless grid floor
    createGrid('floor', -20, true);
    
    // Create ceiling grid
    createGrid('ceiling', 20, false);
    
    // Create distant vertical grids
    createVerticalGrids();
    
    // Add particle system for cyber atmosphere
    createParticleSystem();
    
    // Add digital rain effect
    createDigitalRain();
}

// Create a horizontal grid plane
function createGrid(type, yPosition, isFloor) {
    const gridMaterial = new THREE.LineBasicMaterial({
        color: config.gridColor,
                transparent: true,
        opacity: config.gridOpacity,
        fog: true
    });
    
    // Create grid with divisions
    const gridSize = config.gridSize * 2;
    const gridHelper = new THREE.GridHelper(gridSize, config.gridDivisions, config.gridColor, config.gridColor);
    gridHelper.material = gridMaterial;
    gridHelper.position.y = yPosition;
    scene.add(gridHelper);
    
    // Make the grid infinite by adding multiple layers with fading opacity
    const gridLayers = 3;
    for (let i = 1; i <= gridLayers; i++) {
        const layerSize = gridSize * (i + 1);
        const layerGrid = new THREE.GridHelper(layerSize, Math.floor(config.gridDivisions / 2), config.gridColor, config.gridColor);
        layerGrid.material = new THREE.LineBasicMaterial({
            color: config.gridColor,
                transparent: true,
            opacity: config.gridOpacity * (1 - i / (gridLayers + 1)),
            fog: true
        });
        layerGrid.position.y = yPosition;
        scene.add(layerGrid);
    }
    
    // Store reference
    if (isFloor) {
        gridFloor = gridHelper;
            } else {
        gridCeiling = gridHelper;
    }
    
    // Add a large plane underneath the grid for glow effect
    if (isFloor) {
        const glowGeometry = new THREE.PlaneGeometry(gridSize * 4, gridSize * 4);
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: config.gridColor,
            transparent: true,
            opacity: 0.03,
            side: THREE.DoubleSide
        });
        const glowPlane = new THREE.Mesh(glowGeometry, glowMaterial);
        glowPlane.rotation.x = Math.PI / 2;
        glowPlane.position.y = yPosition - 0.1;
        scene.add(glowPlane);
    }
}

// Create vertical grid planes in the distance
function createVerticalGrids() {
    const gridSize = config.gridSize * 2;
    const distance = gridSize * 0.8;
    
    // Four vertical grids in cardinal directions
    for (let i = 0; i < 4; i++) {
        const angle = (i * Math.PI / 2) + Math.PI / 4;
        const x = Math.sin(angle) * distance;
        const z = Math.cos(angle) * distance;
        
        createVerticalGrid(x, 0, z, angle);
    }
}

// Create a single vertical grid
function createVerticalGrid(x, y, z, rotation) {
    const gridSize = config.gridSize * 2;
    const height = gridSize * 0.8;
    
    // Create vertical grid geometry
    const gridGeometry = new THREE.PlaneGeometry(gridSize * 1.5, height);
    const gridMaterial = new THREE.ShaderMaterial({
        uniforms: {
            color: { value: new THREE.Color(config.gridColor) },
            time: { value: 0 },
            opacity: { value: config.gridOpacity * 0.4 }
        },
        vertexShader: `
            varying vec2 vUv;
            void main() {
                vUv = uv;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            uniform vec3 color;
            uniform float time;
            uniform float opacity;
            varying vec2 vUv;
            
            void main() {
                // Grid pattern
                float gridX = step(0.95, mod(vUv.x * 20.0, 1.0));
                float gridY = step(0.95, mod(vUv.y * 20.0, 1.0));
                float grid = gridX + gridY;
                
                // Pulse effect
                float pulse = sin(time * 0.5) * 0.5 + 0.5;
                
                // Distance fade
                float distanceFromCenter = length(vUv - 0.5) * 2.0;
                float fade = 1.0 - smoothstep(0.8, 1.0, distanceFromCenter);
                
                vec3 finalColor = color;
                float finalOpacity = grid * opacity * fade * mix(0.5, 1.0, pulse);
                
                gl_FragColor = vec4(finalColor, finalOpacity);
            }
        `,
        transparent: true,
        side: THREE.DoubleSide,
        fog: true
    });
    
    const grid = new THREE.Mesh(gridGeometry, gridMaterial);
    grid.position.set(x, y, z);
    grid.rotation.y = rotation;
    scene.add(grid);
    
    // Add to updateable objects
    const update = (time) => {
        grid.material.uniforms.time.value = time;
    };
    
    updateFunctions.push(update);
}

// Array to store update functions
const updateFunctions = [];

// Create particle system for cyber atmosphere
function createParticleSystem() {
    const geometry = new THREE.BufferGeometry();
    const vertices = [];
    const sizes = [];
    const colors = [];
    const particleCount = config.particleCount;
    
    // Generate random particles in a spherical volume
    const radiusRange = config.gridSize * 1.5;
    for (let i = 0; i < particleCount; i++) {
        // Use spherical distribution
        const radius = THREE.MathUtils.randFloat(radiusRange * 0.2, radiusRange);
        const theta = THREE.MathUtils.randFloat(0, Math.PI * 2);
        const phi = THREE.MathUtils.randFloat(0, Math.PI);
        
        const x = radius * Math.sin(phi) * Math.cos(theta);
        const y = radius * Math.sin(phi) * Math.sin(theta) * 0.6; // Flatten y for more disc-like distribution
        const z = radius * Math.cos(phi);
        
        vertices.push(x, y, z);
        
        // Random size variation
        sizes.push(THREE.MathUtils.randFloat(0.5, 3));
        
        // Color variation
        const colorChoice = Math.random();
        if (colorChoice < 0.3) {
            // Cyan particles
            colors.push(0, 1, 1);
        } else if (colorChoice < 0.6) {
            // Purple particles
            colors.push(0.5, 0, 1);
        } else if (colorChoice < 0.9) {
            // Blue particles
            colors.push(0, 0.5, 1);
    } else {
            // White particles (rare)
            colors.push(1, 1, 1);
        }
    }
    
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    geometry.setAttribute('size', new THREE.Float32BufferAttribute(sizes, 1));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    
    // Custom shader material for particles
    const particleMaterial = new THREE.ShaderMaterial({
        uniforms: {
            time: { value: 0 },
            pointTexture: { value: new THREE.TextureLoader().load('/static/img/particle.png') }
        },
        vertexShader: `
            attribute float size;
            attribute vec3 color;
            varying vec3 vColor;
            uniform float time;
            
            void main() {
                vColor = color;
                
                // Subtle movement
                vec3 pos = position;
                pos.x += sin(time * 0.1 + position.z * 0.05) * 2.0;
                pos.z += cos(time * 0.1 + position.x * 0.05) * 2.0;
                pos.y += sin(time * 0.2 + position.x * 0.05) * 1.0;
                
                vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
                
                // Size attenuation based on distance
                gl_PointSize = size * (300.0 / length(mvPosition.xyz));
                gl_Position = projectionMatrix * mvPosition;
            }
        `,
        fragmentShader: `
            uniform sampler2D pointTexture;
            varying vec3 vColor;
            
            void main() {
                gl_FragColor = vec4(vColor, 1.0) * texture2D(pointTexture, gl_PointCoord);
                
                // Discard nearly transparent pixels
                if (gl_FragColor.a < 0.1) discard;
            }
        `,
        blending: THREE.AdditiveBlending,
        depthTest: false,
        transparent: true
    });
    
    particles = new THREE.Points(geometry, particleMaterial);
    scene.add(particles);
}

// Create digital rain effect
function createDigitalRain() {
    const rainCount = 50;
    const rainGeometry = new THREE.BufferGeometry();
    const rainPositions = [];
    const rainColors = [];
    const rainSpeeds = [];
    
    const spread = config.gridSize * 1.5;
    
    for (let i = 0; i < rainCount; i++) {
        const x = THREE.MathUtils.randFloat(-spread, spread);
        const z = THREE.MathUtils.randFloat(-spread, spread);
        const y = THREE.MathUtils.randFloat(20, 100);
        
        rainPositions.push(x, y, z);
        
        // Green-cyan color palette for the matrix effect
        const green = THREE.MathUtils.randFloat(0.5, 1.0);
        rainColors.push(0, green, THREE.MathUtils.randFloat(0, 0.5));
        
        // Random falling speed
        rainSpeeds.push(THREE.MathUtils.randFloat(10, 30));
    }
    
    rainGeometry.setAttribute('position', new THREE.Float32BufferAttribute(rainPositions, 3));
    rainGeometry.setAttribute('color', new THREE.Float32BufferAttribute(rainColors, 3));
    rainGeometry.setAttribute('speed', new THREE.Float32BufferAttribute(rainSpeeds, 1));
    
    const rainMaterial = new THREE.ShaderMaterial({
        uniforms: {
            time: { value: 0 }
        },
        vertexShader: `
            attribute vec3 color;
            attribute float speed;
            varying vec3 vColor;
            uniform float time;
            
            void main() {
                vColor = color;
                
                // Digital rain falling effect
                vec3 pos = position;
                float fallDistance = time * speed;
                pos.y = position.y - mod(fallDistance, 120.0);
                
                gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
                gl_PointSize = 2.0;
            }
        `,
        fragmentShader: `
            varying vec3 vColor;
            
            void main() {
                gl_FragColor = vec4(vColor, 1.0);
            }
        `,
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false
    });
    
    const rain = new THREE.Points(rainGeometry, rainMaterial);
    scene.add(rain);
    
    // Add update function
    const update = (time) => {
        rain.material.uniforms.time.value = time;
    };
    
    updateFunctions.push(update);
}

// Add different types of lights to enhance the scene
function addLights() {
    // Add ambient light for base illumination
    const ambientLight = new THREE.AmbientLight(0x111122, 0.2);
    scene.add(ambientLight);
    
    // Add directional light for subtle shadows
    const directionalLight = new THREE.DirectionalLight(0x3333ff, 0.3);
    directionalLight.position.set(0, 100, 0);
    scene.add(directionalLight);
    
    // Add point lights with different colors for cyberpunk aesthetic
    const pointLightColors = [
        0x00ffff, // Cyan
        0xff00ff, // Magenta
        0x2fff8f, // Neon green
        0xffff00  // Yellow
    ];
    
    pointLightColors.forEach((color, index) => {
        const intensity = 0.7;
        const pointLight = new THREE.PointLight(color, intensity, 150);
        
        // Position lights around the scene
        const angle = (index / pointLightColors.length) * Math.PI * 2;
        const radius = 80;
        pointLight.position.set(
            Math.cos(angle) * radius,
            20 * Math.sin(index * 2.5),
            Math.sin(angle) * radius
        );
        
        scene.add(pointLight);
        
        // Animate the lights
        const update = (time) => {
            const newAngle = angle + time * 0.1 * (index % 2 === 0 ? 1 : -1);
            pointLight.position.x = Math.cos(newAngle) * radius;
            pointLight.position.z = Math.sin(newAngle) * radius;
            pointLight.intensity = intensity * (0.8 + Math.sin(time * 2 + index) * 0.2);
        };
        
        updateFunctions.push(update);
    });
}

// ====== Remaining functions implementing the visualization ======
// ... existing code for visualization functions ...

// Handle window resizing
function onWindowResize() {
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    
    renderer.setSize(width, height);
    
    if (composer) {
        composer.setSize(width, height);
        if (typeof crtUniforms !== 'undefined') {
            crtUniforms.resolution.value.set(width, height);
        }
    }
}

// Animation loop
function animate() {
    if (!visualizationActive) return;
    
    requestAnimationFrame(animate);
    
    deltaTime = clock.getDelta();
    elapsedTime += deltaTime;
    
    // Update controls
    controls.update();
    
    // Update all animation functions
    updateFunctions.forEach(fn => fn(elapsedTime));
    
    // Update particles
    if (particles) {
        particles.material.uniforms.time.value = elapsedTime;
        particles.rotation.y = elapsedTime * 0.03;
    }
    
    // Update data flow animations
    updateDataFlow(deltaTime);
    
    // Update node animations
    animateNodes(elapsedTime);
    
    // Update audio visualization
    updateAudioVisualization();
    
    // Trigger random glitches
    if (config.enableGlitch && glitchPass && Math.random() < config.glitchProbability) {
        glitchPass.enabled = true;
        setTimeout(() => {
            glitchPass.enabled = false;
        }, 200 + Math.random() * 400);
    }
    
    // Render the scene
    if (composer) {
        composer.render();
                } else {
        renderer.render(scene, camera);
    }
}

// Update functions to be implemented later
// ... existing update functions ...

// Export public API
window.VOT1MemoryVisualization = {
    init: initVisualization,
    update: updateMemoryGraph,
    focusNode: focusOnNode,
    clear: clearGraph,
    toggleRotation: function(enabled) {
        if (controls) controls.autoRotate = enabled;
    },
    resetCamera: function() {
        if (camera) {
            gsap.to(camera.position, {
                x: 0,
                y: 0,
                z: config.cameraDistance,
                duration: 1.5,
                ease: "power2.inOut"
            });
            
            gsap.to(controls.target, {
                x: 0,
                y: 0,
                z: 0,
                duration: 1.5,
                ease: "power2.inOut"
            });
        }
    },
    setTheme: function(theme) {
        // Customize visualization based on theme (light/dark)
        if (theme === 'dark') {
            scene.background = new THREE.Color(config.backgroundColor);
            scene.fog = new THREE.FogExp2(config.backgroundColor, 0.0015);
        } else {
            scene.background = new THREE.Color(0x1a1a2e);
            scene.fog = new THREE.FogExp2(0x1a1a2e, 0.0015);
        }
    }
};

// Initialize when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Look for visualization container
    const container = document.getElementById('visualization-container');
    if (container) {
        initVisualization('visualization-container');
    }
});