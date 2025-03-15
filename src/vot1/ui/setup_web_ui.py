#!/usr/bin/env python3
"""
TRILOGY BRAIN Web UI Setup Script

This script sets up the web UI directory structure for the TRILOGY BRAIN interface.
It creates the necessary directories and moves the UI files to the proper locations.

Usage:
    python setup_web_ui.py

Author: Organix (VOT1 Project)
"""

import os
import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("web_ui_setup")

def setup_web_ui():
    """Set up the web UI directory structure"""
    
    # Get the current script directory
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # Define the target web directory
    web_dir = current_dir / "web"
    
    # Create the web directory if it doesn't exist
    web_dir.mkdir(exist_ok=True)
    logger.info(f"Created web directory: {web_dir}")
    
    # Create the assets directory if it doesn't exist
    assets_dir = web_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    logger.info(f"Created assets directory: {assets_dir}")
    
    # Move the index.html file to the web directory
    index_html_src = current_dir / "web" / "index.html"
    if not index_html_src.exists():
        logger.error(f"Source file not found: {index_html_src}")
        logger.info("Creating web directory structure without copying files")
        return False
    
    try:
        # Copy HTML file
        shutil.copy2(index_html_src, web_dir / "index.html")
        logger.info(f"Copied index.html to {web_dir}")
        
        # Copy JS file
        js_src = current_dir / "web" / "trilogy_brain_ui.js"
        shutil.copy2(js_src, web_dir / "trilogy_brain_ui.js")
        logger.info(f"Copied trilogy_brain_ui.js to {web_dir}")
        
        # Copy assets
        for asset_file in (current_dir / "web" / "assets").glob("*"):
            shutil.copy2(asset_file, assets_dir / asset_file.name)
            logger.info(f"Copied asset {asset_file.name} to {assets_dir}")
        
        logger.info("Successfully set up the web UI files")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up web UI: {e}")
        return False

def create_sample_files():
    """Create sample web UI files if they don't exist"""
    
    # Get the current script directory
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # Define the paths for source files
    html_path = current_dir / "web" / "index.html"
    js_path = current_dir / "web" / "trilogy_brain_ui.js"
    assets_dir = current_dir / "web" / "assets"
    logo_path = assets_dir / "trilogy-logo.svg"
    favicon_path = assets_dir / "favicon.svg"
    
    # Skip file creation if files already exist
    if html_path.exists() and js_path.exists():
        logger.info("UI files already exist, skipping sample file creation")
        return
    
    # Create directories
    html_path.parent.mkdir(exist_ok=True)
    assets_dir.mkdir(exist_ok=True)
    
    # Check if the original source files exist in this directory
    src_html = current_dir / "index.html"
    src_js = current_dir / "trilogy_brain_ui.js"
    src_logo = current_dir / "assets" / "trilogy-logo.svg"
    src_favicon = current_dir / "assets" / "favicon.svg"
    
    try:
        # Copy HTML if it exists or create minimal sample
        if src_html.exists():
            shutil.copy2(src_html, html_path)
        else:
            with open(html_path, "w") as f:
                f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRILOGY BRAIN</title>
    <link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #0f0f1a;
            color: #ffffff;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            flex-direction: column;
        }
        
        #trilogy-brain-container {
            width: 80vw;
            height: 80vh;
            border: 1px solid #3498db;
            border-radius: 8px;
            overflow: hidden;
        }
        
        h1 {
            color: #3498db;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <h1>TRILOGY BRAIN</h1>
    <div id="trilogy-brain-container"></div>
    
    <script type="importmap">
    {
        "imports": {
            "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
            "three/addons/": "https://unpkg.com/three@0.160.0/examples/"
        }
    }
    </script>
    <script type="module" src="trilogy_brain_ui.js"></script>
    <script type="module">
        import TrilogyBrainUI from './trilogy_brain_ui.js';
        
        // Initialize TRILOGY BRAIN UI
        document.addEventListener('DOMContentLoaded', async () => {
            try {
                const trilogyBrainUI = new TrilogyBrainUI({
                    containerId: 'trilogy-brain-container',
                    apiUrl: '/api',
                    enableEffects: true,
                    autoRotate: true
                });
            } catch (error) {
                console.error('Error initializing TRILOGY BRAIN UI:', error);
            }
        });
    </script>
</body>
</html>""")
        logger.info(f"Created index.html at {html_path}")
        
        # Copy JS if it exists or create minimal sample
        if src_js.exists():
            shutil.copy2(src_js, js_path)
        else:
            with open(js_path, "w") as f:
                f.write("""/**
 * TRILOGY BRAIN UI - 3D Memory Network Visualization
 * 
 * This is a minimal sample version of the TRILOGY BRAIN UI.
 * Replace this with the full implementation.
 */

import * as THREE from 'three';

export default class TrilogyBrainUI {
    constructor(options) {
        this.containerId = options.containerId;
        this.apiUrl = options.apiUrl;
        this.enableEffects = options.enableEffects || false;
        this.autoRotate = options.autoRotate || false;
        
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            throw new Error(`Container with ID "${this.containerId}" not found`);
        }
        
        this._initScene();
        this._initCamera();
        this._initRenderer();
        this._initLights();
        
        // Start animation loop
        this._animate();
        
        console.log('Minimal TRILOGY BRAIN UI initialized');
    }
    
    _initScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0f0f1a);
        
        // Add a sphere to represent a node
        const geometry = new THREE.SphereGeometry(5, 32, 32);
        const material = new THREE.MeshStandardMaterial({
            color: 0x3498db,
            emissive: 0x3498db,
            emissiveIntensity: 0.5,
            metalness: 0.8,
            roughness: 0.2
        });
        
        this.sphere = new THREE.Mesh(geometry, material);
        this.scene.add(this.sphere);
    }
    
    _initCamera() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
        this.camera.position.z = 20;
    }
    
    _initRenderer() {
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);
        
        // Handle window resize
        window.addEventListener('resize', () => {
            const width = this.container.clientWidth;
            const height = this.container.clientHeight;
            
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(width, height);
        });
    }
    
    _initLights() {
        // Add ambient light
        const ambientLight = new THREE.AmbientLight(0x404040);
        this.scene.add(ambientLight);
        
        // Add directional light
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(1, 1, 1);
        this.scene.add(directionalLight);
    }
    
    _animate() {
        requestAnimationFrame(() => this._animate());
        
        // Rotate the sphere
        if (this.autoRotate) {
            this.sphere.rotation.x += 0.01;
            this.sphere.rotation.y += 0.01;
        }
        
        this.renderer.render(this.scene, this.camera);
    }
}""")
        logger.info(f"Created trilogy_brain_ui.js at {js_path}")
        
        # Copy logo if it exists or create a simple one
        if src_logo.exists():
            shutil.copy2(src_logo, logo_path)
        else:
            with open(logo_path, "w") as f:
                f.write("""<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="45" fill="#16162e" stroke="#3498db" stroke-width="2" />
    <text x="50" y="45" font-family="Arial" font-size="14" fill="white" text-anchor="middle">TRILOGY</text>
    <text x="50" y="65" font-family="Arial" font-size="12" fill="#3498db" text-anchor="middle">BRAIN</text>
</svg>""")
        logger.info(f"Created trilogy-logo.svg at {logo_path}")
        
        # Copy favicon if it exists or create a simple one
        if src_favicon.exists():
            shutil.copy2(src_favicon, favicon_path)
        else:
            with open(favicon_path, "w") as f:
                f.write("""<svg width="32" height="32" xmlns="http://www.w3.org/2000/svg">
    <circle cx="16" cy="16" r="15" fill="#16162e" stroke="#3498db" stroke-width="1" />
    <text x="16" y="20" font-family="Arial" font-size="10" fill="#3498db" text-anchor="middle">TB</text>
</svg>""")
        logger.info(f"Created favicon.svg at {favicon_path}")
        
        logger.info("Successfully created sample UI files")
        
    except Exception as e:
        logger.error(f"Error creating sample files: {e}")

if __name__ == "__main__":
    # First create sample files if needed
    create_sample_files()
    
    # Then set up the web UI
    if setup_web_ui():
        logger.info("Web UI setup completed successfully")
    else:
        logger.warning("Web UI setup completed with warnings or errors") 