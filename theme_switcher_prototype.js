/**
 * VOT1 Dashboard - Theme Switcher
 * 
 * This module provides theme switching functionality for the VOT1 Dashboard,
 * with support for light, dark, and cyberpunk themes.
 */

// Theme Switcher Module
const VOT1ThemeSwitcher = (() => {
    // Available themes
    const THEMES = {
        LIGHT: 'light',
        DARK: 'dark',
        CYBERPUNK: 'cyberpunk'
    };

    // Default theme
    const DEFAULT_THEME = THEMES.LIGHT;

    // Local storage key
    const STORAGE_KEY = 'vot1_theme_preference';

    // State
    let currentTheme = DEFAULT_THEME;
    let observers = [];

    /**
     * Initialize the theme switcher
     * @param {Object} options - Configuration options
     * @param {boolean} options.respectSystemPreference - Whether to respect system color scheme preference
     * @param {Function} options.onChange - Callback for theme changes
     * @return {boolean} Success status
     */
    function initialize(options = {}) {
        try {
            const { respectSystemPreference = true, onChange = null } = options;

            // Register change callback if provided
            if (onChange && typeof onChange === 'function') {
                observers.push(onChange);
            }

            // Try to load saved preference
            const savedTheme = localStorage.getItem(STORAGE_KEY);
            
            // Check if we should respect system preference for dark mode
            if (respectSystemPreference && !savedTheme) {
                // Check system preference
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                currentTheme = prefersDark ? THEMES.DARK : DEFAULT_THEME;
            } else if (savedTheme && Object.values(THEMES).includes(savedTheme)) {
                // Use saved preference
                currentTheme = savedTheme;
            }

            // Apply current theme
            applyTheme(currentTheme);

            // Set up system preference change listener
            if (respectSystemPreference) {
                window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
                    // Only auto-switch if user hasn't explicitly chosen a theme
                    if (!localStorage.getItem(STORAGE_KEY)) {
                        const newTheme = event.matches ? THEMES.DARK : THEMES.LIGHT;
                        applyTheme(newTheme);
                    }
                });
            }

            console.log(`Theme switcher initialized with ${currentTheme} theme`);
            return true;
        } catch (error) {
            console.error('Error initializing theme switcher:', error);
            return false;
        }
    }

    /**
     * Apply a theme to the document
     * @param {string} theme - Theme name
     */
    function applyTheme(theme) {
        if (!Object.values(THEMES).includes(theme)) {
            console.error(`Invalid theme: ${theme}`);
            return;
        }

        // Remove existing theme attributes
        document.documentElement.removeAttribute('data-theme');
        document.body.classList.remove(...Object.values(THEMES).map(t => `theme-${t}`));

        // Apply new theme
        document.documentElement.setAttribute('data-theme', theme);
        document.body.classList.add(`theme-${theme}`);

        // Update state
        currentTheme = theme;

        // Save preference
        localStorage.setItem(STORAGE_KEY, theme);

        // Notify observers
        notifyObservers();

        console.log(`Theme switched to: ${theme}`);
    }

    /**
     * Switch to the next theme in rotation
     */
    function cycleTheme() {
        const themes = Object.values(THEMES);
        const currentIndex = themes.indexOf(currentTheme);
        const nextIndex = (currentIndex + 1) % themes.length;
        applyTheme(themes[nextIndex]);
    }

    /**
     * Get the current theme
     * @return {string} Current theme name
     */
    function getCurrentTheme() {
        return currentTheme;
    }

    /**
     * Check if the current theme is dark
     * @return {boolean} True if current theme is dark or cyberpunk
     */
    function isDarkTheme() {
        return currentTheme === THEMES.DARK || currentTheme === THEMES.CYBERPUNK;
    }

    /**
     * Add a theme change observer
     * @param {Function} callback - Function to call when theme changes
     */
    function addObserver(callback) {
        if (typeof callback === 'function' && !observers.includes(callback)) {
            observers.push(callback);
        }
    }

    /**
     * Remove a theme change observer
     * @param {Function} callback - Observer function to remove
     */
    function removeObserver(callback) {
        const index = observers.indexOf(callback);
        if (index !== -1) {
            observers.splice(index, 1);
        }
    }

    /**
     * Notify all observers of theme change
     * @private
     */
    function notifyObservers() {
        observers.forEach(callback => {
            try {
                callback(currentTheme, isDarkTheme());
            } catch (error) {
                console.error('Error in theme change observer:', error);
            }
        });
    }

    /**
     * Create theme toggle UI elements
     * @param {string} containerId - ID of container element
     * @return {HTMLElement} The created toggle element
     */
    function createToggle(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container not found: ${containerId}`);
            return null;
        }

        // Create toggle wrapper
        const wrapper = document.createElement('div');
        wrapper.className = 'theme-toggle-wrapper';

        // Create toggle button
        const toggle = document.createElement('button');
        toggle.className = 'theme-toggle-btn';
        toggle.setAttribute('aria-label', 'Toggle theme');
        toggle.setAttribute('title', 'Change theme');

        // Create icon
        const icon = document.createElement('span');
        icon.className = 'theme-toggle-icon';
        updateToggleIcon(icon);

        // Add event listener
        toggle.addEventListener('click', () => {
            cycleTheme();
            updateToggleIcon(icon);
        });

        // Add observer to update icon
        addObserver(() => updateToggleIcon(icon));

        // Assemble elements
        toggle.appendChild(icon);
        wrapper.appendChild(toggle);
        container.appendChild(wrapper);

        return wrapper;
    }

    /**
     * Update toggle icon based on current theme
     * @param {HTMLElement} iconElement - Icon element to update
     * @private
     */
    function updateToggleIcon(iconElement) {
        // Clear existing classes
        iconElement.className = 'theme-toggle-icon';

        // Add theme-specific icon class
        switch (currentTheme) {
            case THEMES.LIGHT:
                iconElement.classList.add('theme-toggle-icon-light');
                iconElement.innerHTML = '<i class="fas fa-sun"></i>';
                break;
            case THEMES.DARK:
                iconElement.classList.add('theme-toggle-icon-dark');
                iconElement.innerHTML = '<i class="fas fa-moon"></i>';
                break;
            case THEMES.CYBERPUNK:
                iconElement.classList.add('theme-toggle-icon-cyberpunk');
                iconElement.innerHTML = '<i class="fas fa-ghost"></i>';
                break;
            default:
                iconElement.innerHTML = '<i class="fas fa-adjust"></i>';
        }
    }

    // Public API
    return {
        initialize,
        applyTheme,
        cycleTheme,
        getCurrentTheme,
        isDarkTheme,
        addObserver,
        removeObserver,
        createToggle,
        THEMES
    };
})();

// CSS to add to the page (can be moved to a separate CSS file)
const themeStyles = `
/* Theme Switcher Styles */
.theme-toggle-wrapper {
    display: inline-block;
    position: relative;
    margin: 0 0.5rem;
}

.theme-toggle-btn {
    background: transparent;
    border: 2px solid currentColor;
    color: inherit;
    border-radius: 50%;
    width: 2.5rem;
    height: 2.5rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.theme-toggle-btn:hover {
    transform: scale(1.1);
    box-shadow: 0 0 8px rgba(0,0,0,0.2);
}

.theme-toggle-btn:focus {
    outline: none;
    box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.5);
}

.theme-toggle-icon {
    font-size: 1.2rem;
    transition: transform 0.5s ease;
}

.theme-toggle-icon-light {
    color: #f59e0b;
}

.theme-toggle-icon-dark {
    color: #6366f1;
}

.theme-toggle-icon-cyberpunk {
    color: #ff2a6d;
}

/* Theme-specific CSS variables */
:root {
    /* Light theme (default) */
    --color-primary: #3366cc;
    --color-secondary: #33cc33;
    --color-accent: #cc3366;
    --color-background: #f8f9fa;
    --color-surface: #ffffff;
    --color-text: #333333;
    --color-text-secondary: #666666;
    --color-border: #e0e0e0;
}

[data-theme="dark"] {
    --color-primary: #5588ee;
    --color-secondary: #44ee44;
    --color-accent: #ee4488;
    --color-background: #121212;
    --color-surface: #1e1e1e;
    --color-text: #f0f0f0;
    --color-text-secondary: #a0a0a0;
    --color-border: #383838;
}

[data-theme="cyberpunk"] {
    --color-primary: #ff2a6d;
    --color-secondary: #05d9e8;
    --color-accent: #01c853;
    --color-background: #0a0a16;
    --color-surface: #1a1a35;
    --color-text: #d7d7d9;
    --color-text-secondary: #a0a0a6;
    --color-border: #2d2d50;
}

/* Apply theme transitions */
body {
    transition: background-color 0.3s ease, color 0.3s ease;
    background-color: var(--color-background);
    color: var(--color-text);
}
`;

// Add the CSS to the document
function injectStyles() {
    const styleElement = document.createElement('style');
    styleElement.textContent = themeStyles;
    document.head.appendChild(styleElement);
}

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    // Inject theme switcher styles
    injectStyles();
    
    // Initialize theme switcher
    VOT1ThemeSwitcher.initialize({
        respectSystemPreference: true,
        onChange: (theme) => {
            console.log(`Theme changed to ${theme}`);
        }
    });
    
    // Create theme toggle in header controls if it exists
    const headerControls = document.querySelector('.user-controls, .header-controls');
    if (headerControls) {
        VOT1ThemeSwitcher.createToggle(headerControls.id || 'theme-container');
    } else {
        // Create a container if none exists
        const container = document.createElement('div');
        container.id = 'theme-container';
        container.style.position = 'fixed';
        container.style.top = '1rem';
        container.style.right = '1rem';
        container.style.zIndex = '1000';
        document.body.appendChild(container);
        
        VOT1ThemeSwitcher.createToggle('theme-container');
    }
}); 