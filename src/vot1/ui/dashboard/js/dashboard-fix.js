/**
 * VOTai TRILOGY BRAIN - Dashboard Bug Fixes
 * This script checks for and fixes common issues in the dashboard components
 */

// Run when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('VOTai TRILOGY BRAIN - Dashboard Bug Fix Script Running');
    
    // Check for required components
    checkDependencies();
    
    // Fix common bugs
    fixThreeVisualizationReference();
    fixChartInitialization();
    fixTerminalInitialization();
    fixSystemMonitoring();
    
    console.log('Bug fixes applied. Dashboard should now be functional');
});

// Check if all required dependencies are loaded
function checkDependencies() {
    console.log('Checking dependencies...');
    
    const dependencies = [
        { name: 'THREE.js', obj: window.THREE, cdnUrl: 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js' },
        { name: 'Chart.js', obj: window.Chart, cdnUrl: 'https://cdn.jsdelivr.net/npm/chart.js' },
        { name: 'GSAP', obj: window.gsap, cdnUrl: 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.9.1/gsap.min.js' }
    ];
    
    let allLoaded = true;
    
    dependencies.forEach(dep => {
        if (!dep.obj) {
            console.error(`Missing dependency: ${dep.name}. Please ensure it's loaded before this script.`);
            console.log(`Try adding: <script src="${dep.cdnUrl}"></script>`);
            allLoaded = false;
        } else {
            console.log(`✓ ${dep.name} loaded successfully`);
        }
    });
    
    // Check for THREE.js plugins
    if (window.THREE && !window.THREE.OrbitControls) {
        console.warn('THREE.js OrbitControls not found. Some functionality may be limited.');
        console.log('Try adding: <script src="https://unpkg.com/three@0.128.0/examples/js/controls/OrbitControls.js"></script>');
    }
    
    if (!allLoaded) {
        console.error('Critical dependencies missing. Dashboard functionality will be limited.');
    }
    
    return allLoaded;
}

// Fix reference to memory-network.js vs three-visualization.js
function fixThreeVisualizationReference() {
    console.log('Checking for memory network visualization...');
    
    // If we don't find the expected class, try to dynamically load the correct file
    if (!window.MemoryNetworkVisualization) {
        console.warn('MemoryNetworkVisualization not found. Attempting to fix...');
        
        // Create symlink between files (already done in previous steps)
        
        // Check if we need to dynamically load the script
        if (document.querySelector('script[src="js/memory-network.js"]') || 
            document.querySelector('script[src="js/three-visualization.js"]')) {
            console.log('Visualization script reference exists but class not loaded. Check for JavaScript errors.');
        } else {
            console.warn('No visualization script found. Adding reference...');
            
            // Try to dynamically add the script
            const script = document.createElement('script');
            script.src = 'js/memory-network.js';
            script.onerror = function() {
                console.error('Failed to load memory-network.js');
                
                // Try the alternative name as fallback
                const fallbackScript = document.createElement('script');
                fallbackScript.src = 'js/three-visualization.js';
                fallbackScript.onerror = function() {
                    console.error('Failed to load three-visualization.js. Visualization will not function.');
                };
                document.head.appendChild(fallbackScript);
            };
            document.head.appendChild(script);
        }
    } else {
        console.log('✓ MemoryNetworkVisualization class found');
    }
}

// Fix Chart.js initialization issues
function fixChartInitialization() {
    console.log('Checking Chart.js initialization...');
    
    // If dashboardCharts doesn't exist but the script is loaded
    if (!window.dashboardCharts && window.Chart) {
        console.warn('DashboardCharts not initialized. Attempting to fix...');
        
        // Check if the charts.js script is loaded
        if (document.querySelector('script[src="js/charts.js"]')) {
            console.log('Charts script exists but not initialized. Manually initializing...');
            
            // Try to manually initialize
            try {
                window.dashboardCharts = new DashboardCharts();
                console.log('✓ DashboardCharts manually initialized');
            } catch (error) {
                console.error('Failed to initialize DashboardCharts:', error);
            }
        } else {
            console.warn('No charts script found. Adding reference...');
            
            // Try to dynamically add the script
            const script = document.createElement('script');
            script.src = 'js/charts.js';
            script.onload = function() {
                console.log('Charts script loaded');
                
                // Initialize after loading
                setTimeout(() => {
                    try {
                        window.dashboardCharts = new DashboardCharts();
                        console.log('✓ DashboardCharts initialized after dynamic load');
                    } catch (error) {
                        console.error('Failed to initialize DashboardCharts after dynamic load:', error);
                    }
                }, 500);
            };
            script.onerror = function() {
                console.error('Failed to load charts.js. Chart functionality will not be available.');
            };
            document.head.appendChild(script);
        }
    } else if (window.dashboardCharts) {
        console.log('✓ DashboardCharts already initialized');
    }
}

// Fix Terminal initialization issues
function fixTerminalInitialization() {
    console.log('Checking Terminal initialization...');
    
    // If terminalInterface doesn't exist
    if (!window.terminalInterface) {
        console.warn('TerminalInterface not initialized. Attempting to fix...');
        
        // Check if the terminal.js script is loaded
        if (document.querySelector('script[src="js/terminal.js"]')) {
            console.log('Terminal script exists but not initialized. Checking DOM elements...');
            
            // Check if terminal DOM elements exist
            const terminalElement = document.getElementById('system-console');
            if (!terminalElement) {
                console.error('Terminal DOM element #system-console not found');
                return;
            }
            
            // Try to manually initialize
            try {
                window.terminalInterface = new TerminalInterface();
                console.log('✓ TerminalInterface manually initialized');
            } catch (error) {
                console.error('Failed to initialize TerminalInterface:', error);
            }
        } else {
            console.warn('No terminal script found. Adding reference...');
            
            // Try to dynamically add the script
            const script = document.createElement('script');
            script.src = 'js/terminal.js';
            script.onload = function() {
                console.log('Terminal script loaded');
                
                // Initialize after loading
                setTimeout(() => {
                    try {
                        window.terminalInterface = new TerminalInterface();
                        console.log('✓ TerminalInterface initialized after dynamic load');
                    } catch (error) {
                        console.error('Failed to initialize TerminalInterface after dynamic load:', error);
                    }
                }, 500);
            };
            script.onerror = function() {
                console.error('Failed to load terminal.js. Terminal functionality will not be available.');
            };
            document.head.appendChild(script);
        }
    } else {
        console.log('✓ TerminalInterface already initialized');
    }
}

// Fix system monitoring initialization
function fixSystemMonitoring() {
    console.log('Checking System Monitoring...');
    
    // If dashboard doesn't exist
    if (!window.dashboard) {
        console.warn('Dashboard controller not initialized. Attempting to fix...');
        
        // Check if the dashboard.js script is loaded
        if (document.querySelector('script[src="js/dashboard.js"]')) {
            console.log('Dashboard script exists but not initialized. Manually initializing...');
            
            // Wait for other components to initialize first
            setTimeout(() => {
                try {
                    window.dashboard = new TrilogyDashboard();
                    console.log('✓ TrilogyDashboard manually initialized');
                } catch (error) {
                    console.error('Failed to initialize TrilogyDashboard:', error);
                }
            }, 1000);
        } else {
            console.warn('No dashboard script found. Adding reference...');
            
            // Try to dynamically add the script
            const script = document.createElement('script');
            script.src = 'js/dashboard.js';
            script.onload = function() {
                console.log('Dashboard script loaded');
                
                // Initialize after loading
                setTimeout(() => {
                    try {
                        window.dashboard = new TrilogyDashboard();
                        console.log('✓ TrilogyDashboard initialized after dynamic load');
                    } catch (error) {
                        console.error('Failed to initialize TrilogyDashboard after dynamic load:', error);
                    }
                }, 1000);
            };
            script.onerror = function() {
                console.error('Failed to load dashboard.js. Dashboard functionality will not be available.');
            };
            document.head.appendChild(script);
        }
    } else {
        console.log('✓ TrilogyDashboard already initialized');
    }
}

// Apply patches to fix known bugs in specific components
function applyPatches() {
    console.log('Applying patches to specific components...');
    
    // Patch for MemoryNetworkVisualization if available
    if (window.MemoryNetworkVisualization) {
        const originalSetData = MemoryNetworkVisualization.prototype.setData;
        MemoryNetworkVisualization.prototype.setData = function(data) {
            // Safety check for memory data format
            if (!data || !data.memories || !Array.isArray(data.memories)) {
                console.error('Invalid memory data format. Expected {memories: Array}');
                data = { memories: [] };
            }
            
            // Call original method with fixed data
            return originalSetData.call(this, data);
        };
        
        console.log('✓ Applied patches to MemoryNetworkVisualization');
    }
    
    // Patch for Chart initialization timing issues
    if (window.Chart) {
        const originalInit = Chart.prototype.initialize;
        Chart.prototype.initialize = function() {
            try {
                return originalInit.apply(this, arguments);
            } catch (error) {
                console.error('Chart initialization error:', error);
                // Try to recover by applying a timeout
                setTimeout(() => {
                    try {
                        originalInit.apply(this, arguments);
                    } catch (e) {
                        console.error('Failed to recover from Chart initialization error');
                    }
                }, 200);
            }
        };
        
        console.log('✓ Applied patches to Chart.js');
    }
}

// This function will be called after a brief delay to allow for normal initialization
setTimeout(applyPatches, 2000); 