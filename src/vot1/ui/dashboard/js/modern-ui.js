/**
 * VOTai TRILOGY BRAIN - Modern UI Enhancements
 * Inspired by Perplexity AI and Cursor designs with cyberpunk arcade aesthetics
 */

class ModernUIEffects {
  constructor() {
    this.particlesSystems = [];
    this.glitchElements = document.querySelectorAll('.cyber-glitch');
    this.rippleElements = document.querySelectorAll('.ripple-effect');
    this.neonElements = document.querySelectorAll('.neon-text, .neon-border');
    this.typewriterElements = document.querySelectorAll('.typewriter');
    
    // Animation frames tracker
    this.animationFrames = [];
    
    // Initialize
    this.init();
  }
  
  init() {
    console.log('Initializing modern UI effects...');
    
    // Apply effects
    this.initParticleBackgrounds();
    this.initNeonGlowEffects();
    this.initGlitchEffects();
    this.initRippleEffects();
    this.initTypewriterEffects();
    this.initAdvancedTooltips();
    this.initParallaxEffects();
    this.initAdvancedScrollEffects();
    
    // Handle visibility changes to save resources
    document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
    
    console.log('Modern UI effects initialized');
  }
  
  // Create particle backgrounds similar to Perplexity's floating dots
  initParticleBackgrounds() {
    const containers = document.querySelectorAll('.particle-background');
    
    containers.forEach(container => {
      // Only proceed if THREE.js is available
      if (!window.THREE) {
        console.warn('THREE.js not available for particle effects');
        return;
      }
      
      try {
        // Create a simple particle system
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
        
        const renderer = new THREE.WebGLRenderer({ 
          alpha: true,
          antialias: true
        });
        
        renderer.setSize(container.clientWidth, container.clientHeight);
        container.appendChild(renderer.domElement);
        
        // Create particles
        const particleCount = 50;
        const particles = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);
        const sizes = new Float32Array(particleCount);
        
        const color1 = new THREE.Color(0xff2a6d); // Hot Pink
        const color2 = new THREE.Color(0x00ccff); // Cyan
        
        for (let i = 0; i < particleCount; i++) {
          // Position
          positions[i * 3] = (Math.random() - 0.5) * container.clientWidth * 0.05;
          positions[i * 3 + 1] = (Math.random() - 0.5) * container.clientHeight * 0.05;
          positions[i * 3 + 2] = (Math.random() - 0.5) * 50;
          
          // Color (gradient between two colors)
          const ratio = Math.random();
          const mixedColor = new THREE.Color().lerpColors(color1, color2, ratio);
          colors[i * 3] = mixedColor.r;
          colors[i * 3 + 1] = mixedColor.g;
          colors[i * 3 + 2] = mixedColor.b;
          
          // Size
          sizes[i] = Math.random() * 5 + 2;
        }
        
        particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        particles.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        particles.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
        
        // Create particle material
        const particleMaterial = new THREE.PointsMaterial({
          size: 1,
          vertexColors: true,
          transparent: true,
          opacity: 0.8,
          sizeAttenuation: true
        });
        
        // Create point cloud
        const pointCloud = new THREE.Points(particles, particleMaterial);
        scene.add(pointCloud);
        
        // Position camera
        camera.position.z = 50;
        
        // Animation function
        const animate = () => {
          const animationId = requestAnimationFrame(animate);
          this.animationFrames.push(animationId);
          
          // Rotate and move particles
          pointCloud.rotation.x += 0.0005;
          pointCloud.rotation.y += 0.0005;
          
          // Update particle positions for floating effect
          const positions = particles.attributes.position.array;
          for (let i = 0; i < particleCount; i++) {
            positions[i * 3 + 1] += Math.sin(Date.now() * 0.001 + i) * 0.03;
          }
          particles.attributes.position.needsUpdate = true;
          
          renderer.render(scene, camera);
        };
        
        animate();
        
        // Store for reference and cleanup
        this.particlesSystems.push({
          container,
          renderer,
          scene,
          camera,
          animate
        });
        
        // Handle window resize
        window.addEventListener('resize', () => {
          if (!container.isConnected) return;
          
          camera.aspect = container.clientWidth / container.clientHeight;
          camera.updateProjectionMatrix();
          renderer.setSize(container.clientWidth, container.clientHeight);
        });
      } catch (error) {
        console.error('Error creating particle background:', error);
      }
    });
  }
  
  // Neon glow effects inspired by cyberpunk aesthetics
  initNeonGlowEffects() {
    // Add neon glow effect to elements
    this.neonElements.forEach(element => {
      // Create glow animation using CSS custom properties
      const color = element.dataset.glowColor || '#00ccff';
      element.style.setProperty('--glow-color', color);
      
      // Apply animation
      gsap.to(element, {
        boxShadow: `0 0 10px ${color}, 0 0 20px ${color}`,
        textShadow: `0 0 5px ${color}, 0 0 10px ${color}`,
        duration: 1.5,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut"
      });
    });
  }
  
  // Glitch effects similar to Cursor's error states
  initGlitchEffects() {
    this.glitchElements.forEach(element => {
      // Create randomized glitch effect
      const createGlitch = () => {
        const duration = Math.random() * 0.1 + 0.05;
        const offset = Math.random() * 10 - 5;
        
        // Clone element for glitch effect
        const glitch1 = element.cloneNode(true);
        const glitch2 = element.cloneNode(true);
        
        glitch1.style.position = 'absolute';
        glitch1.style.top = 0;
        glitch1.style.left = 0;
        glitch1.style.width = '100%';
        glitch1.style.height = '100%';
        glitch1.style.clip = 'rect(0, 0, 0, 0)';
        glitch1.style.zIndex = 1;
        
        glitch2.style.position = 'absolute';
        glitch2.style.top = 0;
        glitch2.style.left = 0;
        glitch2.style.width = '100%';
        glitch2.style.height = '100%';
        glitch2.style.clip = 'rect(0, 0, 0, 0)';
        glitch2.style.zIndex = 1;
        
        element.appendChild(glitch1);
        element.appendChild(glitch2);
        
        // Animate glitch
        gsap.to(glitch1, {
          clip: `rect(${Math.random() * 100}px, ${Math.random() * 100}px, ${Math.random() * 100}px, ${Math.random() * 100}px)`,
          left: `${offset}px`,
          duration: duration,
          ease: "steps(1)"
        });
        
        gsap.to(glitch2, {
          clip: `rect(${Math.random() * 100}px, ${Math.random() * 100}px, ${Math.random() * 100}px, ${Math.random() * 100}px)`,
          left: `-${offset}px`,
          duration: duration,
          ease: "steps(1)",
          onComplete: () => {
            element.removeChild(glitch1);
            element.removeChild(glitch2);
          }
        });
      };
      
      // Trigger glitch randomly
      setInterval(() => {
        if (Math.random() > 0.7) {
          createGlitch();
        }
      }, 3000);
      
      // Trigger glitch on hover
      element.addEventListener('mouseenter', createGlitch);
    });
  }
  
  // Interactive ripple effects like Material Design
  initRippleEffects() {
    this.rippleElements.forEach(element => {
      element.addEventListener('click', event => {
        const rect = element.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        const ripple = document.createElement('span');
        ripple.classList.add('ripple');
        ripple.style.left = `${x}px`;
        ripple.style.top = `${y}px`;
        
        element.appendChild(ripple);
        
        setTimeout(() => {
          ripple.remove();
        }, 600);
      });
    });
  }
  
  // Typewriter effects for terminal-like UI
  initTypewriterEffects() {
    this.typewriterElements.forEach(element => {
      const text = element.textContent;
      element.textContent = '';
      element.style.visibility = 'visible';
      
      let i = 0;
      const speed = element.dataset.typeSpeed || 50;
      
      function typeWriter() {
        if (i < text.length) {
          element.textContent += text.charAt(i);
          i++;
          setTimeout(typeWriter, Math.random() * speed + speed/2);
        }
      }
      
      // Delay start for staggered effect if multiple typewriters
      setTimeout(typeWriter, element.dataset.typeDelay || 0);
    });
  }
  
  // Advanced tooltips like those in Perplexity
  initAdvancedTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(element => {
      const tooltipText = element.dataset.tooltip;
      
      // Create tooltip element
      const tooltip = document.createElement('div');
      tooltip.classList.add('advanced-tooltip');
      tooltip.innerHTML = tooltipText;
      
      // Position tooltip on hover
      element.addEventListener('mouseenter', () => {
        document.body.appendChild(tooltip);
        
        const updatePosition = () => {
          const rect = element.getBoundingClientRect();
          tooltip.style.left = `${rect.left + rect.width / 2}px`;
          tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
          tooltip.style.transform = 'translateX(-50%)';
          
          // Keep tooltip in viewport
          const tooltipRect = tooltip.getBoundingClientRect();
          if (tooltipRect.left < 10) {
            tooltip.style.left = '10px';
            tooltip.style.transform = 'none';
          } else if (tooltipRect.right > window.innerWidth - 10) {
            tooltip.style.left = 'auto';
            tooltip.style.right = '10px';
            tooltip.style.transform = 'none';
          }
        };
        
        updatePosition();
        
        // Show with animation
        gsap.fromTo(tooltip, 
          { opacity: 0, y: 10 }, 
          { opacity: 1, y: 0, duration: 0.3 }
        );
        
        // Update position on scroll
        window.addEventListener('scroll', updatePosition);
        window.addEventListener('resize', updatePosition);
      });
      
      // Remove tooltip on mouse leave
      element.addEventListener('mouseleave', () => {
        gsap.to(tooltip, {
          opacity: 0,
          y: 10,
          duration: 0.2,
          onComplete: () => {
            if (tooltip.parentNode) {
              document.body.removeChild(tooltip);
            }
          }
        });
        
        window.removeEventListener('scroll', () => {});
        window.removeEventListener('resize', () => {});
      });
    });
  }
  
  // Parallax effects for depth
  initParallaxEffects() {
    const parallaxElements = document.querySelectorAll('.parallax');
    
    window.addEventListener('mousemove', (e) => {
      const x = e.clientX / window.innerWidth;
      const y = e.clientY / window.innerHeight;
      
      parallaxElements.forEach(element => {
        const speed = element.dataset.parallaxSpeed || 20;
        const offsetX = (0.5 - x) * speed;
        const offsetY = (0.5 - y) * speed;
        
        gsap.to(element, {
          x: offsetX,
          y: offsetY,
          duration: 0.5,
          ease: "power1.out"
        });
      });
    });
  }
  
  // Advanced scroll effects like in modern web apps
  initAdvancedScrollEffects() {
    const fadeElements = document.querySelectorAll('.fade-in-view');
    
    // Create intersection observer
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          gsap.fromTo(entry.target, 
            { opacity: 0, y: 50 }, 
            { opacity: 1, y: 0, duration: 0.8, ease: "power2.out" }
          );
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    
    // Observe all fade elements
    fadeElements.forEach(element => {
      observer.observe(element);
    });
  }
  
  // Handle visibility changes to save resources
  handleVisibilityChange() {
    if (document.hidden) {
      // Page is hidden, pause animations
      this.animationFrames.forEach(id => cancelAnimationFrame(id));
      this.animationFrames = [];
    } else {
      // Page is visible again, restart animations
      this.particlesSystems.forEach(system => {
        if (system.animate) {
          system.animate();
        }
      });
    }
  }
  
  // Clean up resources
  destroy() {
    // Cancel all animation frames
    this.animationFrames.forEach(id => cancelAnimationFrame(id));
    
    // Remove event listeners
    document.removeEventListener('visibilitychange', this.handleVisibilityChange);
    
    // Dispose THREE.js resources
    this.particlesSystems.forEach(system => {
      if (system.renderer) {
        system.renderer.dispose();
      }
    });
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.modernUI = new ModernUIEffects();
  console.log('Modern UI effects loaded');
}); 