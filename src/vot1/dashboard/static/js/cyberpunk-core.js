/**
 * VOT1 Cyberpunk Core
 * Core functionality for the cyberpunk-themed dashboard
 * Advanced version with memory management and WebGL capabilities
 */

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeCyberpunkEffects();
    initializeModalSystem();
    initializeNotifications();
    initializeAudioEffects();
    initializeMemoryManagement();
    initializeWebGLContext();
});

/**
 * Advanced state persistence and memory management system
 */
class CyberStorage {
    constructor() {
        this.volatile = new Map();
        this.persistQueue = new Set();
        this.persistenceEnabled = true;
        this.persistenceStrategy = 'indexeddb'; // 'indexeddb', 'localstorage', 'memory'
        this.cacheTTL = 1000 * 60 * 60; // 1 hour default
        this.db = null;
        this._initStorage();
        
        // Memory monitoring
        this.memoryUsage = {
            heapSize: 0,
            heapUsed: 0,
            nonHeapSize: 0,
            externalSize: 0
        };
        
        // Setup interval for memory monitoring
        this.monitorInterval = setInterval(() => this._monitorMemoryUsage(), 30000);
    }
    
    async _initStorage() {
        if (this.persistenceStrategy === 'memory') return;
        
        if (this.persistenceStrategy === 'indexeddb') {
            try {
                const request = indexedDB.open('cyberpunk-state', 1);
                
                request.onupgradeneeded = (event) => {
                    const db = event.target.result;
                    const stateStore = db.createObjectStore('state', { keyPath: 'id' });
                    stateStore.createIndex('timestamp', 'timestamp', { unique: false });
                    console.log('Cyberpunk state database created');
                };
                
                request.onsuccess = (event) => {
                    this.db = event.target.result;
                    this._loadPersistedState();
                    console.log('Cyberpunk state database loaded');
                };
                
                request.onerror = (event) => {
                    console.error('IndexedDB error:', event.target.error);
                    // Fallback to localStorage
                    this.persistenceStrategy = 'localstorage';
                };
            } catch (err) {
                console.error('Failed to initialize IndexedDB, falling back to localStorage', err);
                this.persistenceStrategy = 'localstorage';
            }
        }
    }
    
    async _loadPersistedState() {
        if (this.persistenceStrategy === 'indexeddb' && this.db) {
            const transaction = this.db.transaction(['state'], 'readonly');
            const stateStore = transaction.objectStore('state');
            const request = stateStore.getAll();
            
            request.onsuccess = (event) => {
                const states = event.target.result;
                states.forEach(item => {
                    if (Date.now() - item.timestamp < this.cacheTTL) {
                        this.volatile.set(item.id, item.value);
                    }
                });
                showNotification('State loaded successfully', 'info', { persist: false });
            };
        } else if (this.persistenceStrategy === 'localstorage') {
            try {
                const storedState = localStorage.getItem('cyberpunk-state');
                if (storedState) {
                    const parsedState = JSON.parse(storedState);
                    Object.keys(parsedState).forEach(key => {
                        const item = parsedState[key];
                        if (Date.now() - item.timestamp < this.cacheTTL) {
                            this.volatile.set(key, item.value);
                        }
                    });
                    showNotification('State loaded successfully', 'info', { persist: false });
                }
            } catch (err) {
                console.error('Failed to load state from localStorage', err);
            }
        }
    }
    
    async setState(key, value) {
        this.volatile.set(key, value);
        
        if (this.persistenceEnabled) {
            this.persistQueue.add(key);
            // Use requestIdleCallback for non-critical state persistence
            if ('requestIdleCallback' in window) {
                requestIdleCallback(() => this._flushToPersistence());
            } else {
                setTimeout(() => this._flushToPersistence(), 1000);
            }
        }
    }
    
    getState(key, defaultValue = null) {
        return this.volatile.has(key) ? this.volatile.get(key) : defaultValue;
    }
    
    async _flushToPersistence() {
        if (!this.persistenceEnabled || this.persistQueue.size === 0) return;
        
        const batch = Array.from(this.persistQueue);
        const timestamp = Date.now();
        
        if (this.persistenceStrategy === 'indexeddb' && this.db) {
            const transaction = this.db.transaction(['state'], 'readwrite');
            const stateStore = transaction.objectStore('state');
            
            batch.forEach(key => {
                stateStore.put({
                    id: key,
                    value: this.volatile.get(key),
                    timestamp
                });
            });
        } else if (this.persistenceStrategy === 'localstorage') {
            try {
                const currentState = localStorage.getItem('cyberpunk-state') || '{}';
                const parsedState = JSON.parse(currentState);
                
                batch.forEach(key => {
                    parsedState[key] = {
                        value: this.volatile.get(key),
                        timestamp
                    };
                });
                
                localStorage.setItem('cyberpunk-state', JSON.stringify(parsedState));
            } catch (err) {
                console.error('Failed to persist state to localStorage', err);
            }
        }
        
        // Clear the persistence queue
        batch.forEach(key => this.persistQueue.delete(key));
    }
    
    clearState() {
        this.volatile.clear();
        this.persistQueue.clear();
        
        if (this.persistenceStrategy === 'indexeddb' && this.db) {
            const transaction = this.db.transaction(['state'], 'readwrite');
            const stateStore = transaction.objectStore('state');
            stateStore.clear();
        } else if (this.persistenceStrategy === 'localstorage') {
            localStorage.removeItem('cyberpunk-state');
        }
    }
    
    async _monitorMemoryUsage() {
        if ('performance' in window && 'memory' in performance) {
            const memory = performance.memory;
            this.memoryUsage.heapSize = memory.totalJSHeapSize;
            this.memoryUsage.heapUsed = memory.usedJSHeapSize;
            
            // Log warning if memory usage is high (>80% of total)
            const usageRatio = memory.usedJSHeapSize / memory.totalJSHeapSize;
            if (usageRatio > 0.8) {
                console.warn('High memory usage detected:', usageRatio.toFixed(2) * 100, '%');
                // Force garbage collection (not actually possible in JS, but can suggest it)
                this._suggestGarbageCollection();
            }
        }
        
        // If available, use the newer memory measurement API
        if ('performance' in window && 'measureUserAgentSpecificMemory' in performance) {
            try {
                const result = await performance.measureUserAgentSpecificMemory();
                this.memoryUsage.detailed = result;
                console.debug('Memory measurement:', result);
            } catch (e) {
                console.warn('Memory measurement failed:', e);
            }
        }
    }
    
    _suggestGarbageCollection() {
        // In reality, we can't force GC in JavaScript, but we can:
        // 1. Clear references to large objects
        // 2. Clear caches we control
        
        // Clear any cached data older than 15 minutes
        const oldThreshold = Date.now() - 15 * 60 * 1000;
        
        if (this.persistenceStrategy === 'indexeddb' && this.db) {
            const transaction = this.db.transaction(['state'], 'readwrite');
            const stateStore = transaction.objectStore('state');
            const index = stateStore.index('timestamp');
            const range = IDBKeyRange.upperBound(oldThreshold);
            
            index.openCursor(range).onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    stateStore.delete(cursor.primaryKey);
                    cursor.continue();
                }
            };
        }
        
        // Clear old items from volatile memory too
        this.volatile.forEach((value, key) => {
            if (value && value.timestamp && value.timestamp < oldThreshold) {
                this.volatile.delete(key);
            }
        });
    }
    
    dispose() {
        clearInterval(this.monitorInterval);
        // Force final flush
        this._flushToPersistence();
    }
}

// Global instance of the storage system
let cyberStorage;

/**
 * WebGL context for advanced visualizations
 */
let glContext = {
    gl: null,
    canvas: null,
    programs: {},
    buffers: {},
    textures: {},
    frameCount: 0,
    initialized: false
};

/**
 * Initialize the memory management system
 */
function initializeMemoryManagement() {
    cyberStorage = new CyberStorage();
    console.log('Cyberpunk memory management system initialized');
    
    // Register cleanup on page unload
    window.addEventListener('beforeunload', () => {
        cyberStorage.dispose();
    });
}

/**
 * Initialize WebGL context for advanced visualizations
 */
function initializeWebGLContext() {
    // Create canvas element if not present
    if (!document.getElementById('cyberpunk-gl-canvas')) {
        const canvas = document.createElement('canvas');
        canvas.id = 'cyberpunk-gl-canvas';
        canvas.className = 'cyberpunk-webgl-canvas';
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        document.body.appendChild(canvas);
        
        glContext.canvas = canvas;
    } else {
        glContext.canvas = document.getElementById('cyberpunk-gl-canvas');
    }
    
    // Initialize WebGL2 context
    try {
        glContext.gl = glContext.canvas.getContext('webgl2');
        if (!glContext.gl) {
            glContext.gl = glContext.canvas.getContext('webgl');
        }
        
        if (!glContext.gl) {
            throw new Error('WebGL not supported');
        }
        
        // Initialize basic shader program
        initializeShaders();
        glContext.initialized = true;
        
        // Start animation loop
        requestAnimationFrame(renderGLEffects);
        
        // Handle resize
        window.addEventListener('resize', resizeGLCanvas);
        
        console.log('WebGL context initialized successfully');
    } catch (err) {
        console.error('Failed to initialize WebGL context:', err);
        // Remove canvas if initialization failed
        if (glContext.canvas && glContext.canvas.parentNode) {
            glContext.canvas.parentNode.removeChild(glContext.canvas);
        }
    }
}

/**
 * Initialize WebGL shaders for particle effects
 */
function initializeShaders() {
    const gl = glContext.gl;
    
    // Vertex shader for particles
    const vsSource = `
        attribute vec2 position;
        attribute vec3 color;
        attribute float size;
        
        uniform mat4 modelViewMatrix;
        uniform mat4 projectionMatrix;
        
        varying vec3 vColor;
        
        void main() {
            vColor = color;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 0.0, 1.0);
            gl_PointSize = size;
        }
    `;
    
    // Fragment shader for particles with glow effect
    const fsSource = `
        precision mediump float;
        varying vec3 vColor;
        
        void main() {
            vec2 center = vec2(0.5, 0.5);
            float dist = distance(gl_PointCoord, center);
            float alpha = 1.0 - smoothstep(0.0, 0.5, dist);
            gl_FragColor = vec4(vColor, alpha);
        }
    `;
    
    // Create shader program
    const vertexShader = compileShader(gl, gl.VERTEX_SHADER, vsSource);
    const fragmentShader = compileShader(gl, gl.FRAGMENT_SHADER, fsSource);
    
    const shaderProgram = gl.createProgram();
    gl.attachShader(shaderProgram, vertexShader);
    gl.attachShader(shaderProgram, fragmentShader);
    gl.linkProgram(shaderProgram);
    
    if (!gl.getProgramParameter(shaderProgram, gl.LINK_STATUS)) {
        console.error('Unable to initialize shader program:', gl.getProgramInfoLog(shaderProgram));
        return;
    }
    
    // Store program info
    glContext.programs.particles = {
        program: shaderProgram,
        attribLocations: {
            position: gl.getAttribLocation(shaderProgram, 'position'),
            color: gl.getAttribLocation(shaderProgram, 'color'),
            size: gl.getAttribLocation(shaderProgram, 'size')
        },
        uniformLocations: {
            modelViewMatrix: gl.getUniformLocation(shaderProgram, 'modelViewMatrix'),
            projectionMatrix: gl.getUniformLocation(shaderProgram, 'projectionMatrix')
        }
    };
    
    // Create buffers
    initializeParticleSystem();
}

/**
 * Initialize particle system
 */
function initializeParticleSystem() {
    const gl = glContext.gl;
    const NUM_PARTICLES = 1000;
    
    // Create positions and colors for particles
    const positions = new Float32Array(NUM_PARTICLES * 2);
    const colors = new Float32Array(NUM_PARTICLES * 3);
    const sizes = new Float32Array(NUM_PARTICLES);
    
    // Generate random particle data
    for (let i = 0; i < NUM_PARTICLES; i++) {
        // Position (spread across screen)
        positions[i * 2] = (Math.random() - 0.5) * 2.0;
        positions[i * 2 + 1] = (Math.random() - 0.5) * 2.0;
        
        // Color (cyberpunk neon palette)
        const colorChoice = Math.random();
        if (colorChoice < 0.33) {
            // Cyan
            colors[i * 3] = 0.0;
            colors[i * 3 + 1] = 1.0;
            colors[i * 3 + 2] = 0.8 + Math.random() * 0.2;
        } else if (colorChoice < 0.66) {
            // Pink
            colors[i * 3] = 1.0;
            colors[i * 3 + 1] = 0.0;
            colors[i * 3 + 2] = 0.5 + Math.random() * 0.5;
        } else {
            // Yellow
            colors[i * 3] = 1.0;
            colors[i * 3 + 1] = 0.9 + Math.random() * 0.1;
            colors[i * 3 + 2] = 0.0;
        }
        
        // Size (varies)
        sizes[i] = 2.0 + Math.random() * 8.0;
    }
    
    // Create and bind buffers
    const positionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, positions, gl.DYNAMIC_DRAW);
    
    const colorBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, colorBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, colors, gl.STATIC_DRAW);
    
    const sizeBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, sizeBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, sizes, gl.STATIC_DRAW);
    
    // Store particle system data
    glContext.buffers.particles = {
        position: positionBuffer,
        color: colorBuffer,
        size: sizeBuffer,
        count: NUM_PARTICLES,
        data: {
            positions,
            velocities: new Float32Array(NUM_PARTICLES * 2), // x,y velocities
            sizes,
            colors
        }
    };
}

/**
 * Helper function to compile a shader
 */
function compileShader(gl, type, source) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        console.error('An error occurred compiling the shader:', gl.getShaderInfoLog(shader));
        gl.deleteShader(shader);
        return null;
    }
    
    return shader;
}

/**
 * Update and render WebGL effects
 */
function renderGLEffects() {
    if (!glContext.initialized) return;
    
    const gl = glContext.gl;
    glContext.frameCount++;
    
    // Clear the canvas
    gl.clearColor(0.0, 0.0, 0.05, 0.1); // Dark blue with transparency
    gl.clear(gl.COLOR_BUFFER_BIT);
    
    // Enable blending for particle glow effects
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
    
    // Update particle positions and render
    updateParticles();
    renderParticles();
    
    // Continue animation loop
    requestAnimationFrame(renderGLEffects);
}

/**
 * Update particle positions and properties
 */
function updateParticles() {
    const gl = glContext.gl;
    const particles = glContext.buffers.particles;
    const data = particles.data;
    const count = particles.count;
    
    const time = glContext.frameCount * 0.01;
    
    // Update particle positions based on velocities and time
    for (let i = 0; i < count; i++) {
        const index = i * 2;
        
        // Add some oscillating motion to particles
        data.velocities[index] = 0.001 * Math.sin(time + i * 0.1);
        data.velocities[index + 1] = 0.001 * Math.cos(time + i * 0.23);
        
        // Update positions
        data.positions[index] += data.velocities[index];
        data.positions[index + 1] += data.velocities[index + 1];
        
        // Wrap particles that go off-screen
        if (data.positions[index] > 1.0) data.positions[index] = -1.0;
        if (data.positions[index] < -1.0) data.positions[index] = 1.0;
        if (data.positions[index + 1] > 1.0) data.positions[index + 1] = -1.0;
        if (data.positions[index + 1] < -1.0) data.positions[index + 1] = 1.0;
        
        // Pulse size with sin wave
        data.sizes[i] = (2.0 + Math.random() * 3.0) * (0.5 + 0.5 * Math.sin(time * 0.5 + i * 0.1));
    }
    
    // Update buffers with new data
    gl.bindBuffer(gl.ARRAY_BUFFER, particles.position);
    gl.bufferData(gl.ARRAY_BUFFER, data.positions, gl.DYNAMIC_DRAW);
    
    gl.bindBuffer(gl.ARRAY_BUFFER, particles.size);
    gl.bufferData(gl.ARRAY_BUFFER, data.sizes, gl.DYNAMIC_DRAW);
}

/**
 * Render particles
 */
function renderParticles() {
    const gl = glContext.gl;
    const programInfo = glContext.programs.particles;
    const particles = glContext.buffers.particles;
    
    // Use the particle shader program
    gl.useProgram(programInfo.program);
    
    // Set up vertex attributes
    // Position attribute
    gl.bindBuffer(gl.ARRAY_BUFFER, particles.position);
    gl.vertexAttribPointer(
        programInfo.attribLocations.position,
        2, // 2 values per vertex (x,y)
        gl.FLOAT,
        false,
        0,
        0
    );
    gl.enableVertexAttribArray(programInfo.attribLocations.position);
    
    // Color attribute
    gl.bindBuffer(gl.ARRAY_BUFFER, particles.color);
    gl.vertexAttribPointer(
        programInfo.attribLocations.color,
        3, // 3 values per vertex (r,g,b)
        gl.FLOAT,
        false,
        0,
        0
    );
    gl.enableVertexAttribArray(programInfo.attribLocations.color);
    
    // Size attribute
    gl.bindBuffer(gl.ARRAY_BUFFER, particles.size);
    gl.vertexAttribPointer(
        programInfo.attribLocations.size,
        1, // 1 value per vertex
        gl.FLOAT,
        false,
        0,
        0
    );
    gl.enableVertexAttribArray(programInfo.attribLocations.size);
    
    // Set uniforms
    // For simplicity, just use identity matrices
    const modelViewMatrix = new Float32Array([
        1, 0, 0, 0,
        0, 1, 0, 0,
        0, 0, 1, 0,
        0, 0, 0, 1
    ]);
    
    const projectionMatrix = new Float32Array([
        1, 0, 0, 0,
        0, 1, 0, 0,
        0, 0, 1, 0,
        0, 0, 0, 1
    ]);
    
    gl.uniformMatrix4fv(
        programInfo.uniformLocations.modelViewMatrix,
        false,
        modelViewMatrix
    );
    
    gl.uniformMatrix4fv(
        programInfo.uniformLocations.projectionMatrix,
        false,
        projectionMatrix
    );
    
    // Draw particles
    gl.drawArrays(gl.POINTS, 0, particles.count);
}

/**
 * Handle WebGL canvas resize
 */
function resizeGLCanvas() {
    if (!glContext.initialized || !glContext.canvas) return;
    
    const canvas = glContext.canvas;
    const gl = glContext.gl;
    
    // Resize canvas to match window size
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    // Update viewport
    gl.viewport(0, 0, canvas.width, canvas.height);
}

/**
 * Initialize cyberpunk visual effects
 */
function initializeCyberpunkEffects() {
    // Create and apply glitch effects
    applyGlitchEffects();
    
    // Add hover effects to UI elements
    addHoverEffects();
    
    // Random flicker effects
    startRandomFlicker();
    
    // Initialize terminal-style animations
    initTerminalAnimations();
}

/**
 * Apply glitch effects to elements with .glitch-effect class
 */
function applyGlitchEffects() {
    // Apply to logo and other glitch elements
    document.querySelectorAll('.logo-glitch').forEach(element => {
        // Make sure the data-text attribute is set
        if (!element.getAttribute('data-text')) {
            element.setAttribute('data-text', element.textContent);
        }
        
        // Random glitches
        setInterval(() => {
            if (Math.random() > 0.95) {
                element.classList.add('active-glitch');
                setTimeout(() => {
                    element.classList.remove('active-glitch');
                }, 100 + Math.random() * 300);
            }
        }, 2000);
    });
}

/**
 * Add hover effects to buttons and navigation
 */
function addHoverEffects() {
    // Add neon hover sound to buttons
    document.querySelectorAll('button, .nav-link, .control-btn').forEach(element => {
        element.addEventListener('mouseenter', function() {
            playAudioEffect('hover');
        });
        
        element.addEventListener('click', function() {
            playAudioEffect('click');
        });
    });
}

/**
 * Start random flickering effects
 */
function startRandomFlicker() {
    // Create flicker overlay if it doesn't exist
    if (!document.querySelector('.flicker-overlay')) {
        const flickerOverlay = document.createElement('div');
        flickerOverlay.className = 'flicker-overlay';
        document.body.appendChild(flickerOverlay);
    }
    
    // Random screen flicker
    setInterval(() => {
        if (Math.random() > 0.97) {
            const flickerOverlay = document.querySelector('.flicker-overlay');
            flickerOverlay.style.opacity = (Math.random() * 0.1).toString();
            setTimeout(() => {
                flickerOverlay.style.opacity = '0';
            }, 50 + Math.random() * 100);
        }
    }, 3000);
}

/**
 * Initialize terminal-style animations for specific elements
 */
function initTerminalAnimations() {
    // Look for elements with .terminal-text class
    document.querySelectorAll('.terminal-text').forEach(element => {
        const text = element.textContent;
        element.textContent = '';
        
        let i = 0;
        const speed = 30; // typing speed in ms
        
        function typeWriter() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, speed + Math.random() * 20);
            }
        }
        
        typeWriter();
    });
}

/**
 * Modal System
 */
function initializeModalSystem() {
    const modalOverlay = document.getElementById('modal-overlay');
    const modalContent = document.getElementById('modal-content');
    const modalClose = document.getElementById('modal-close');
    
    // Close modal when clicking the X button
    if (modalClose) {
        modalClose.addEventListener('click', closeModal);
    }
    
    // Close modal when clicking outside content
    if (modalOverlay) {
        modalOverlay.addEventListener('click', function(e) {
            if (e.target === modalOverlay) {
                closeModal();
            }
        });
    }
    
    // Close on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

/**
 * Show modal with content
 * @param {string} title - Modal title
 * @param {string|HTMLElement} content - HTML content or element to display in modal
 * @param {Object} options - Additional modal options
 */
function showModal(title, content, options = {}) {
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const modalFooter = document.getElementById('modal-footer');
    const modalOverlay = document.getElementById('modal-overlay');
    
    // Set modal title
    if (modalTitle) {
        modalTitle.textContent = title;
    }
    
    // Set modal content
    if (modalBody) {
        if (typeof content === 'string') {
            modalBody.innerHTML = content;
        } else if (content instanceof HTMLElement) {
            modalBody.innerHTML = '';
            modalBody.appendChild(content);
        }
    }
    
    // Set footer content if provided
    if (modalFooter && options.footer) {
        if (typeof options.footer === 'string') {
            modalFooter.innerHTML = options.footer;
        } else if (options.footer instanceof HTMLElement) {
            modalFooter.innerHTML = '';
            modalFooter.appendChild(options.footer);
        }
        modalFooter.style.display = 'block';
    } else if (modalFooter) {
        modalFooter.style.display = 'none';
    }
    
    // Add a CSS class if specified
    if (options.className && modalOverlay) {
        modalOverlay.classList.add(options.className);
    }
    
    // Show the modal
    if (modalOverlay) {
        modalOverlay.style.display = 'flex';
        setTimeout(() => {
            modalOverlay.classList.add('active');
        }, 10);
    }
    
    // Play open sound
    playAudioEffect('modalOpen');
    
    return {
        close: closeModal
    };
}

/**
 * Close the modal
 */
function closeModal() {
    const modalOverlay = document.getElementById('modal-overlay');
    
    if (modalOverlay) {
        modalOverlay.classList.remove('active');
        
        // Wait for transition to complete before hiding
        setTimeout(() => {
            modalOverlay.style.display = 'none';
            
            // Remove any extra classes
            Array.from(modalOverlay.classList).forEach(className => {
                if (className !== 'modal-overlay') {
                    modalOverlay.classList.remove(className);
                }
            });
        }, 300);
    }
    
    // Play close sound
    playAudioEffect('modalClose');
}

/**
 * Notification System
 */
function initializeNotifications() {
    // Create notification container if it doesn't exist
    if (!document.getElementById('notification-container')) {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
}

/**
 * Show a notification
 * @param {string} message - Notification message
 * @param {string} type - Notification type (info, success, warning, error)
 * @param {Object} options - Additional options (duration, icon)
 */
function showNotification(message, type = 'info', options = {}) {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    
    // Default options
    const defaultOptions = {
        duration: 5000,
        icon: null
    };
    
    // Merge options
    const settings = {...defaultOptions, ...options};
    
    // Set default icons based on type
    if (!settings.icon) {
        switch (type) {
            case 'success':
                settings.icon = 'fas fa-check-circle';
                break;
            case 'warning':
                settings.icon = 'fas fa-exclamation-triangle';
                break;
            case 'error':
                settings.icon = 'fas fa-times-circle';
                break;
            default:
                settings.icon = 'fas fa-info-circle';
        }
    }
    
    // Create notification element
    notification.className = `notification notification-${type}`;
    
    // Add icon if provided
    if (settings.icon) {
        const iconElement = document.createElement('i');
        iconElement.className = settings.icon;
        notification.appendChild(iconElement);
    }
    
    // Add message
    const messageElement = document.createElement('span');
    messageElement.className = 'notification-message';
    messageElement.textContent = message;
    notification.appendChild(messageElement);
    
    // Add close button
    const closeButton = document.createElement('button');
    closeButton.className = 'notification-close';
    closeButton.innerHTML = '&times;';
    closeButton.addEventListener('click', () => {
        removeNotification(notification);
    });
    notification.appendChild(closeButton);
    
    // Add to container
    if (container) {
        container.appendChild(notification);
    }
    
    // Play notification sound
    playAudioEffect(type === 'error' ? 'error' : 'notification');
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('active');
    }, 10);
    
    // Auto remove after duration
    if (settings.duration > 0) {
        setTimeout(() => {
            removeNotification(notification);
        }, settings.duration);
    }
    
    // Return object with methods
    return {
        remove: () => removeNotification(notification),
        update: (newMessage) => {
            messageElement.textContent = newMessage;
        }
    };
}

/**
 * Remove a notification
 * @param {HTMLElement} notification - The notification element to remove
 */
function removeNotification(notification) {
    notification.classList.remove('active');
    
    // Wait for transition to complete before removing from DOM
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 300);
}

/**
 * Audio System for cyberpunk effects
 */
let audioContext = null;
const soundEffects = {};

function initializeAudioEffects() {
    try {
        // Create audio context
        window.AudioContext = window.AudioContext || window.webkitAudioContext;
        audioContext = new AudioContext();
        
        // Preload common sound effects
        loadSoundEffect('hover', '/static/audio/hover.mp3');
        loadSoundEffect('click', '/static/audio/click.mp3');
        loadSoundEffect('notification', '/static/audio/notification.mp3');
        loadSoundEffect('error', '/static/audio/error.mp3');
        loadSoundEffect('modalOpen', '/static/audio/modal-open.mp3');
        loadSoundEffect('modalClose', '/static/audio/modal-close.mp3');
    } catch (e) {
        console.warn('Web Audio API not supported.', e);
    }
}

/**
 * Load a sound effect
 * @param {string} name - Name of the sound effect
 * @param {string} url - URL of the sound file
 */
function loadSoundEffect(name, url) {
    if (!audioContext) return;
    
    fetch(url)
        .then(response => {
            // If the file doesn't exist, create a fallback sound
            if (!response.ok) {
                console.warn(`Sound file ${url} not found, creating synthetic sound.`);
                createSyntheticSound(name);
                return null;
            }
            return response.arrayBuffer();
        })
        .then(arrayBuffer => {
            if (arrayBuffer) {
                return audioContext.decodeAudioData(arrayBuffer);
            }
            return null;
        })
        .then(audioBuffer => {
            if (audioBuffer) {
                soundEffects[name] = audioBuffer;
            }
        })
        .catch(error => {
            console.warn('Error loading sound effect:', error);
            createSyntheticSound(name);
        });
}

/**
 * Create a synthetic sound effect
 * @param {string} name - Name for the synthetic sound
 */
function createSyntheticSound(name) {
    if (!audioContext) return;
    
    const settings = {
        hover: { frequency: 2000, duration: 0.05 },
        click: { frequency: 1500, duration: 0.08 },
        notification: { frequency: 880, duration: 0.2 },
        error: { frequency: 220, duration: 0.3 },
        modalOpen: { frequency: 440, duration: 0.15 },
        modalClose: { frequency: 330, duration: 0.1 }
    };
    
    // Use a default if the specific name is not defined
    const config = settings[name] || { frequency: 1000, duration: 0.1 };
    
    // Create an offline audio context to generate the sound
    const offlineContext = new OfflineAudioContext(
        1, 
        audioContext.sampleRate * config.duration, 
        audioContext.sampleRate
    );
    
    const oscillator = offlineContext.createOscillator();
    const gainNode = offlineContext.createGain();
    
    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(config.frequency, 0);
    
    gainNode.gain.setValueAtTime(0, 0);
    gainNode.gain.linearRampToValueAtTime(0.3, 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.01, config.duration);
    
    oscillator.connect(gainNode);
    gainNode.connect(offlineContext.destination);
    
    oscillator.start(0);
    
    offlineContext.startRendering()
        .then(buffer => {
            soundEffects[name] = buffer;
        })
        .catch(error => {
            console.warn('Error creating synthetic sound:', error);
        });
}

/**
 * Play a sound effect
 * @param {string} name - Name of the sound effect to play
 * @param {Object} options - Playback options
 */
function playAudioEffect(name, options = {}) {
    if (!audioContext || !soundEffects[name]) return;
    
    // Resume audio context if suspended (browser autoplay policy)
    if (audioContext.state === 'suspended') {
        audioContext.resume();
    }
    
    // Create audio source
    const source = audioContext.createBufferSource();
    source.buffer = soundEffects[name];
    
    // Create gain node for volume control
    const gainNode = audioContext.createGain();
    gainNode.gain.value = options.volume || 0.3; // Default volume
    
    // Connect nodes
    source.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    // Start playback
    source.start(0);
}

/**
 * Create a cyberpunk-style progress bar
 * @param {string} containerId - ID of the container element
 * @param {Object} options - Configuration options
 * @returns {Object} Control methods for the progress bar
 */
function createCyberpunkProgressBar(containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) return null;
    
    // Default options
    const settings = {
        label: 'Progress',
        min: 0,
        max: 100,
        value: 0,
        height: '15px',
        showPercentage: true,
        ...options
    };
    
    // Create elements
    const progressContainer = document.createElement('div');
    progressContainer.className = 'cyberpunk-progress-container';
    
    const labelElement = document.createElement('div');
    labelElement.className = 'cyberpunk-progress-label';
    labelElement.textContent = settings.label;
    
    const progressBar = document.createElement('div');
    progressBar.className = 'cyberpunk-progress-bar';
    progressBar.style.height = settings.height;
    
    const progressFill = document.createElement('div');
    progressFill.className = 'cyberpunk-progress-fill';
    
    const progressValue = document.createElement('div');
    progressValue.className = 'cyberpunk-progress-value';
    
    // Assemble structure
    progressBar.appendChild(progressFill);
    if (settings.showPercentage) {
        progressBar.appendChild(progressValue);
    }
    progressContainer.appendChild(labelElement);
    progressContainer.appendChild(progressBar);
    container.appendChild(progressContainer);
    
    // Update function
    function updateProgress(value) {
        const clampedValue = Math.min(Math.max(value, settings.min), settings.max);
        const percentage = ((clampedValue - settings.min) / (settings.max - settings.min)) * 100;
        
        progressFill.style.width = `${percentage}%`;
        
        if (settings.showPercentage) {
            progressValue.textContent = `${Math.round(percentage)}%`;
        }
        
        // Return the current value
        return clampedValue;
    }
    
    // Set initial value
    updateProgress(settings.value);
    
    // Return control methods
    return {
        update: updateProgress,
        setLabel: (text) => {
            labelElement.textContent = text;
        },
        getElement: () => progressContainer,
        remove: () => {
            if (progressContainer.parentNode) {
                progressContainer.parentNode.removeChild(progressContainer);
            }
        }
    };
}

// Export functions to global scope
window.CyberpunkUI = {
    showModal,
    closeModal,
    showNotification,
    playAudioEffect,
    createCyberpunkProgressBar
}; 