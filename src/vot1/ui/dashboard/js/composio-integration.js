/**
 * Composio Integration Module for VOTai Dashboard
 * 
 * This module handles the integration between the VOTai dashboard UI
 * and the Composio tool ecosystem, enabling seamless tool discovery,
 * execution, and visualization.
 * 
 * @version 2.0.0
 * @author VOTai Team
 */

// Composio SDK configuration
const COMPOSIO_CONFIG = {
    apiKey: null,
    apiEndpoint: "https://api.composio.dev/v1",
    integrationId: null,
    environment: "production",
    maxConcurrentRequests: 3,
    requestTimeout: 60000,
    useCache: true,
    debugMode: false
};

// UI state management
const COMPOSIO_UI_STATE = {
    isInitialized: false,
    isConnecting: false,
    connectionStatus: "disconnected", // disconnected, connecting, connected, error
    availableTools: [],
    selectedToolId: null,
    executingToolIds: new Set(),
    toolResults: new Map(),
    historyItems: []
};

// DOM elements (set after initialization)
let toolContainer;
let statusBadge;
let initButton;
let refreshButton;
let toolList;
let executionForm;
let resultDisplay;
let historyContainer;

/**
 * Initialize the Composio integration
 * @param {Object} config - Configuration options
 * @returns {Promise<boolean>} - Whether initialization was successful
 */
async function initializeComposio(config = {}) {
    if (COMPOSIO_UI_STATE.isInitialized || COMPOSIO_UI_STATE.isConnecting) {
        console.warn("Composio integration already initialized or initializing");
        return false;
    }

    // Update UI state
    COMPOSIO_UI_STATE.isConnecting = true;
    COMPOSIO_UI_STATE.connectionStatus = "connecting";
    updateConnectionStatusUI();

    try {
        // Merge configuration
        Object.assign(COMPOSIO_CONFIG, config);

        // Validate required configuration
        if (!COMPOSIO_CONFIG.apiKey) {
            COMPOSIO_CONFIG.apiKey = await promptForApiKey();
        }

        if (!COMPOSIO_CONFIG.integrationId) {
            COMPOSIO_CONFIG.integrationId = await promptForIntegrationId();
        }

        // Load Composio SDK dynamically
        await loadComposioSDK();

        // Initialize Composio client
        window.composioClient = new ComposioSDK.Client({
            apiKey: COMPOSIO_CONFIG.apiKey,
            endpoint: COMPOSIO_CONFIG.apiEndpoint,
            integrationId: COMPOSIO_CONFIG.integrationId,
            environment: COMPOSIO_CONFIG.environment,
            onError: handleComposioError
        });

        // Fetch available tools
        await refreshToolList();

        // Update UI state
        COMPOSIO_UI_STATE.isInitialized = true;
        COMPOSIO_UI_STATE.isConnecting = false;
        COMPOSIO_UI_STATE.connectionStatus = "connected";
        updateConnectionStatusUI();

        console.log("Composio integration initialized successfully");
        
        // Display banner notification
        showNotification("Composio integration initialized successfully", "success");
        
        return true;
    } catch (error) {
        console.error("Failed to initialize Composio integration:", error);
        
        // Update UI state
        COMPOSIO_UI_STATE.isInitialized = false;
        COMPOSIO_UI_STATE.isConnecting = false;
        COMPOSIO_UI_STATE.connectionStatus = "error";
        updateConnectionStatusUI();
        
        // Display error notification
        showNotification(`Failed to initialize Composio: ${error.message}`, "error");
        
        return false;
    }
}

/**
 * Refresh the list of available tools
 * @returns {Promise<Array>} The list of available tools
 */
async function refreshToolList() {
    if (!COMPOSIO_UI_STATE.isInitialized && !COMPOSIO_UI_STATE.isConnecting) {
        console.warn("Composio not initialized. Call initializeComposio first.");
        return [];
    }

    try {
        const tools = await window.composioClient.listTools();
        COMPOSIO_UI_STATE.availableTools = tools;
        renderToolList();
        return tools;
    } catch (error) {
        console.error("Failed to refresh tool list:", error);
        showNotification(`Failed to refresh tools: ${error.message}`, "error");
        return [];
    }
}

/**
 * Execute a Composio tool with the given parameters
 * @param {string} toolId - The ID of the tool to execute
 * @param {Object} parameters - The parameters for the tool execution
 * @returns {Promise<Object>} The result of the tool execution
 */
async function executeComposioTool(toolId, parameters) {
    if (!COMPOSIO_UI_STATE.isInitialized) {
        throw new Error("Composio not initialized. Call initializeComposio first.");
    }

    // Add to executing tools set
    COMPOSIO_UI_STATE.executingToolIds.add(toolId);
    updateToolExecutionUI();

    try {
        // Execute the tool
        const tool = COMPOSIO_UI_STATE.availableTools.find(t => t.id === toolId);
        
        if (!tool) {
            throw new Error(`Tool with ID ${toolId} not found`);
        }
        
        // Start execution timer
        const startTime = performance.now();
        
        // Update UI to show executing status
        updateToolExecutionStatus(toolId, "executing");
        
        // Execute the tool
        const result = await window.composioClient.executeTool(toolId, parameters);
        
        // Calculate execution time
        const executionTime = (performance.now() - startTime) / 1000;
        
        // Store the result
        const resultWithMetadata = {
            ...result,
            executionTime,
            timestamp: new Date().toISOString(),
            toolId,
            toolName: tool.name,
            parameters
        };
        
        COMPOSIO_UI_STATE.toolResults.set(toolId, resultWithMetadata);
        
        // Add to history
        COMPOSIO_UI_STATE.historyItems.unshift(resultWithMetadata);
        if (COMPOSIO_UI_STATE.historyItems.length > 50) {
            COMPOSIO_UI_STATE.historyItems.pop();
        }
        
        // Store in memory bridge if enabled
        await storeExecutionInMemory(resultWithMetadata);
        
        // Update UI
        updateToolExecutionStatus(toolId, "success");
        renderToolResult(resultWithMetadata);
        renderHistory();
        
        return resultWithMetadata;
    } catch (error) {
        console.error(`Error executing tool ${toolId}:`, error);
        
        // Update UI to show error
        updateToolExecutionStatus(toolId, "error", error.message);
        
        // Log event to memory bridge
        await storeExecutionError(toolId, parameters, error);
        
        throw error;
    } finally {
        // Remove from executing tools
        COMPOSIO_UI_STATE.executingToolIds.delete(toolId);
        updateToolExecutionUI();
    }
}

/**
 * Store tool execution result in memory bridge
 * @param {Object} result - The result of the tool execution
 * @returns {Promise<void>}
 */
async function storeExecutionInMemory(result) {
    // Skip if VOTai memory bridge is not available
    if (!window.vot1 || !window.vot1.memoryBridge) {
        return;
    }
    
    try {
        const content = JSON.stringify({
            type: "tool_execution",
            toolId: result.toolId,
            toolName: result.toolName,
            parameters: result.parameters,
            result: result.data,
            executionTime: result.executionTime,
            timestamp: result.timestamp
        });
        
        await window.vot1.memoryBridge.storeMemory(
            content,
            "tool_execution",
            {
                toolId: result.toolId,
                executionTime: result.executionTime,
                success: true
            }
        );
    } catch (err) {
        console.error("Failed to store tool execution in memory:", err);
    }
}

/**
 * Store tool execution error in memory bridge
 * @param {string} toolId - The ID of the tool
 * @param {Object} parameters - The execution parameters
 * @param {Error} error - The error object
 * @returns {Promise<void>}
 */
async function storeExecutionError(toolId, parameters, error) {
    // Skip if VOTai memory bridge is not available
    if (!window.vot1 || !window.vot1.memoryBridge) {
        return;
    }
    
    try {
        const content = JSON.stringify({
            type: "tool_execution_error",
            toolId,
            parameters,
            error: error.message,
            timestamp: new Date().toISOString()
        });
        
        await window.vot1.memoryBridge.storeMemory(
            content,
            "tool_execution_error",
            {
                toolId,
                errorMessage: error.message,
                success: false
            }
        );
    } catch (err) {
        console.error("Failed to store tool execution error in memory:", err);
    }
}

/**
 * Load the Composio SDK script dynamically
 * @returns {Promise<void>}
 */
function loadComposioSDK() {
    return new Promise((resolve, reject) => {
        // Skip if already loaded
        if (window.ComposioSDK) {
            resolve();
            return;
        }
        
        const script = document.createElement("script");
        script.src = "https://cdn.jsdelivr.net/npm/composio-core@latest/dist/index.min.js";
        script.async = true;
        
        script.onload = () => {
            console.log("Composio SDK loaded successfully");
            resolve();
        };
        
        script.onerror = (error) => {
            console.error("Failed to load Composio SDK:", error);
            reject(new Error("Failed to load Composio SDK"));
        };
        
        document.head.appendChild(script);
    });
}

/**
 * Prompt the user for an API key
 * @returns {Promise<string>} The API key
 */
function promptForApiKey() {
    return new Promise((resolve) => {
        const apiKey = prompt("Please enter your Composio API key:");
        resolve(apiKey);
    });
}

/**
 * Prompt the user for an integration ID
 * @returns {Promise<string>} The integration ID
 */
function promptForIntegrationId() {
    return new Promise((resolve) => {
        const integrationId = prompt("Please enter your Composio integration ID:");
        resolve(integrationId);
    });
}

/**
 * Handle Composio SDK errors
 * @param {Error} error - The error object
 */
function handleComposioError(error) {
    console.error("Composio SDK error:", error);
    
    // Show error notification
    showNotification(`Composio error: ${error.message}`, "error");
    
    // Update connection status if needed
    if (error.message.includes("authentication") || error.message.includes("authorization")) {
        COMPOSIO_UI_STATE.connectionStatus = "error";
        updateConnectionStatusUI();
    }
}

/**
 * Render the list of available tools to the UI
 */
function renderToolList() {
    if (!toolList) return;
    
    // Clear existing list
    toolList.innerHTML = "";
    
    if (COMPOSIO_UI_STATE.availableTools.length === 0) {
        const emptyMessage = document.createElement("div");
        emptyMessage.className = "empty-message";
        emptyMessage.textContent = "No tools available. Try refreshing the list.";
        toolList.appendChild(emptyMessage);
        return;
    }
    
    // Create tool items
    COMPOSIO_UI_STATE.availableTools.forEach(tool => {
        const toolItem = document.createElement("div");
        toolItem.className = "tool-item";
        toolItem.dataset.toolId = tool.id;
        
        // Add click handler
        toolItem.addEventListener("click", () => {
            selectTool(tool.id);
        });
        
        // Tool content
        toolItem.innerHTML = `
            <div class="tool-icon">
                <i class="${getToolIcon(tool.category)}"></i>
            </div>
            <div class="tool-details">
                <div class="tool-name">${tool.name}</div>
                <div class="tool-description">${tool.description || "No description"}</div>
            </div>
        `;
        
        toolList.appendChild(toolItem);
    });
}

/**
 * Update the connection status UI
 */
function updateConnectionStatusUI() {
    if (!statusBadge) return;
    
    // Update status badge
    statusBadge.className = "status-badge " + COMPOSIO_UI_STATE.connectionStatus;
    
    // Set status text
    switch(COMPOSIO_UI_STATE.connectionStatus) {
        case "disconnected":
            statusBadge.textContent = "Disconnected";
            break;
        case "connecting":
            statusBadge.textContent = "Connecting...";
            break;
        case "connected":
            statusBadge.textContent = "Connected";
            break;
        case "error":
            statusBadge.textContent = "Connection Error";
            break;
        default:
            statusBadge.textContent = COMPOSIO_UI_STATE.connectionStatus;
    }
    
    // Update button states
    if (initButton) {
        initButton.disabled = COMPOSIO_UI_STATE.isConnecting || 
                             COMPOSIO_UI_STATE.connectionStatus === "connected";
    }
    
    if (refreshButton) {
        refreshButton.disabled = !COMPOSIO_UI_STATE.isInitialized || 
                                COMPOSIO_UI_STATE.isConnecting;
    }
}

/**
 * Update the tool execution UI
 */
function updateToolExecutionUI() {
    // Update executing tools indicators
    document.querySelectorAll(".tool-item").forEach(item => {
        const toolId = item.dataset.toolId;
        if (COMPOSIO_UI_STATE.executingToolIds.has(toolId)) {
            item.classList.add("executing");
        } else {
            item.classList.remove("executing");
        }
    });
    
    // Update form button state
    if (executionForm) {
        const submitButton = executionForm.querySelector("button[type='submit']");
        if (submitButton) {
            submitButton.disabled = COMPOSIO_UI_STATE.executingToolIds.size > 0;
        }
    }
}

/**
 * Update the status of a specific tool execution
 * @param {string} toolId - The ID of the tool
 * @param {string} status - The status (executing, success, error)
 * @param {string} [message] - Optional status message
 */
function updateToolExecutionStatus(toolId, status, message) {
    const toolItem = document.querySelector(`.tool-item[data-tool-id="${toolId}"]`);
    if (!toolItem) return;
    
    // Remove existing status classes
    toolItem.classList.remove("executing", "success", "error");
    
    // Add new status class
    toolItem.classList.add(status);
    
    // Update status message if provided
    if (message && status === "error") {
        // Create or update error tooltip
        let errorTooltip = toolItem.querySelector(".error-tooltip");
        if (!errorTooltip) {
            errorTooltip = document.createElement("div");
            errorTooltip.className = "error-tooltip";
            toolItem.appendChild(errorTooltip);
        }
        errorTooltip.textContent = message;
    }
}

/**
 * Select a tool and display its execution form
 * @param {string} toolId - The ID of the tool to select
 */
function selectTool(toolId) {
    // Update selected state
    COMPOSIO_UI_STATE.selectedToolId = toolId;
    
    // Update UI selection
    document.querySelectorAll(".tool-item").forEach(item => {
        if (item.dataset.toolId === toolId) {
            item.classList.add("selected");
        } else {
            item.classList.remove("selected");
        }
    });
    
    // Get the tool details
    const tool = COMPOSIO_UI_STATE.availableTools.find(t => t.id === toolId);
    if (!tool) return;
    
    // Generate the execution form
    renderExecutionForm(tool);
}

/**
 * Render the execution form for a tool
 * @param {Object} tool - The tool object
 */
function renderExecutionForm(tool) {
    if (!executionForm) return;
    
    // Clear existing form
    executionForm.innerHTML = "";
    
    // Tool header
    const header = document.createElement("div");
    header.className = "tool-form-header";
    header.innerHTML = `
        <h3>${tool.name}</h3>
        <p>${tool.description || ""}</p>
    `;
    executionForm.appendChild(header);
    
    // Create form
    const form = document.createElement("form");
    form.className = "tool-execution-form";
    
    // Add parameter fields
    const parameters = tool.parameters || [];
    
    if (parameters.length === 0) {
        const noParamsMessage = document.createElement("p");
        noParamsMessage.className = "no-params-message";
        noParamsMessage.textContent = "This tool has no parameters";
        form.appendChild(noParamsMessage);
    } else {
        parameters.forEach(param => {
            const fieldGroup = document.createElement("div");
            fieldGroup.className = "form-group";
            
            // Label
            const label = document.createElement("label");
            label.textContent = param.name;
            if (param.required) {
                label.innerHTML += ' <span class="required">*</span>';
            }
            fieldGroup.appendChild(label);
            
            // Input field
            let input;
            
            switch (param.type) {
                case "textarea":
                    input = document.createElement("textarea");
                    input.rows = 5;
                    break;
                case "select":
                    input = document.createElement("select");
                    (param.options || []).forEach(option => {
                        const optionElement = document.createElement("option");
                        optionElement.value = option.value;
                        optionElement.textContent = option.label || option.value;
                        input.appendChild(optionElement);
                    });
                    break;
                case "boolean":
                    input = document.createElement("input");
                    input.type = "checkbox";
                    break;
                case "number":
                    input = document.createElement("input");
                    input.type = "number";
                    if (param.min !== undefined) input.min = param.min;
                    if (param.max !== undefined) input.max = param.max;
                    break;
                default:
                    input = document.createElement("input");
                    input.type = "text";
            }
            
            // Set common attributes
            input.name = param.id;
            input.id = `param-${param.id}`;
            input.placeholder = param.description || "";
            input.required = !!param.required;
            
            // Set default value if provided
            if (param.default !== undefined && param.type !== "boolean") {
                input.value = param.default;
            } else if (param.type === "boolean" && param.default) {
                input.checked = true;
            }
            
            fieldGroup.appendChild(input);
            
            // Description
            if (param.description) {
                const description = document.createElement("small");
                description.className = "param-description";
                description.textContent = param.description;
                fieldGroup.appendChild(description);
            }
            
            form.appendChild(fieldGroup);
        });
    }
    
    // Submit button
    const submitWrapper = document.createElement("div");
    submitWrapper.className = "form-submit";
    
    const submitButton = document.createElement("button");
    submitButton.type = "submit";
    submitButton.className = "execute-button";
    submitButton.textContent = "Execute Tool";
    submitWrapper.appendChild(submitButton);
    
    form.appendChild(submitWrapper);
    
    // Form submission handler
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        // Gather form data
        const formData = new FormData(form);
        const parameters = {};
        
        // Convert form data to parameter object
        tool.parameters.forEach(param => {
            if (param.type === "boolean") {
                parameters[param.id] = !!formData.get(param.id);
            } else {
                parameters[param.id] = formData.get(param.id);
            }
        });
        
        try {
            // Execute the tool
            await executeComposioTool(tool.id, parameters);
        } catch (error) {
            showNotification(`Error executing tool: ${error.message}`, "error");
        }
    });
    
    executionForm.appendChild(form);
    
    // Show the form
    if (resultDisplay) {
        resultDisplay.innerHTML = "";
    }
}

/**
 * Render a tool execution result
 * @param {Object} result - The result object
 */
function renderToolResult(result) {
    if (!resultDisplay) return;
    
    // Clear existing result
    resultDisplay.innerHTML = "";
    
    // Result header
    const header = document.createElement("div");
    header.className = "result-header";
    header.innerHTML = `
        <h3>Result: ${result.toolName}</h3>
        <div class="result-meta">
            <span class="execution-time">Execution time: ${result.executionTime.toFixed(2)}s</span>
            <span class="timestamp">Time: ${new Date(result.timestamp).toLocaleString()}</span>
        </div>
    `;
    resultDisplay.appendChild(header);
    
    // Result content
    const content = document.createElement("div");
    content.className = "result-content";
    
    if (result.data) {
        // Attempt to format based on data type
        if (typeof result.data === "object") {
            // Format as JSON
            const pre = document.createElement("pre");
            pre.className = "json-result";
            pre.textContent = JSON.stringify(result.data, null, 2);
            content.appendChild(pre);
        } else if (typeof result.data === "string" && result.data.startsWith("http")) {
            // Format as URL/image
            if (result.data.match(/\.(jpeg|jpg|gif|png)$/i)) {
                const img = document.createElement("img");
                img.src = result.data;
                img.alt = "Tool result image";
                img.className = "result-image";
                content.appendChild(img);
            } else {
                const link = document.createElement("a");
                link.href = result.data;
                link.textContent = result.data;
                link.target = "_blank";
                link.rel = "noopener noreferrer";
                content.appendChild(link);
            }
        } else {
            // Format as text
            content.textContent = String(result.data);
        }
    } else {
        content.innerHTML = "<p>No result data returned</p>";
    }
    
    resultDisplay.appendChild(content);
    
    // Actions
    const actions = document.createElement("div");
    actions.className = "result-actions";
    
    // Copy button
    const copyButton = document.createElement("button");
    copyButton.className = "action-button copy-button";
    copyButton.innerHTML = '<i class="fas fa-copy"></i> Copy';
    copyButton.addEventListener("click", () => {
        // Copy result to clipboard
        navigator.clipboard.writeText(
            typeof result.data === "object" 
                ? JSON.stringify(result.data, null, 2) 
                : String(result.data)
        ).then(() => {
            showNotification("Result copied to clipboard", "success");
        }).catch(err => {
            showNotification("Failed to copy result", "error");
        });
    });
    actions.appendChild(copyButton);
    
    // Store in memory button (if VOTai memory bridge is available)
    if (window.vot1 && window.vot1.memoryBridge) {
        const storeButton = document.createElement("button");
        storeButton.className = "action-button store-button";
        storeButton.innerHTML = '<i class="fas fa-brain"></i> Store';
        storeButton.addEventListener("click", async () => {
            try {
                await storeExecutionInMemory(result);
                showNotification("Result stored in memory", "success");
            } catch (error) {
                showNotification("Failed to store result", "error");
            }
        });
        actions.appendChild(storeButton);
    }
    
    resultDisplay.appendChild(actions);
}

/**
 * Render the execution history
 */
function renderHistory() {
    if (!historyContainer) return;
    
    // Clear existing history
    historyContainer.innerHTML = "";
    
    if (COMPOSIO_UI_STATE.historyItems.length === 0) {
        const emptyMessage = document.createElement("div");
        emptyMessage.className = "empty-message";
        emptyMessage.textContent = "No execution history yet";
        historyContainer.appendChild(emptyMessage);
        return;
    }
    
    // Create history list
    const list = document.createElement("div");
    list.className = "history-list";
    
    COMPOSIO_UI_STATE.historyItems.forEach((item, index) => {
        const historyItem = document.createElement("div");
        historyItem.className = "history-item";
        historyItem.dataset.index = index;
        
        historyItem.innerHTML = `
            <div class="history-item-header">
                <div class="history-tool-name">${item.toolName}</div>
                <div class="history-timestamp">${new Date(item.timestamp).toLocaleTimeString()}</div>
            </div>
            <div class="history-item-content">
                <div class="history-params">${formatParameters(item.parameters)}</div>
                <div class="history-result-preview">${formatResultPreview(item.data)}</div>
            </div>
        `;
        
        // Add click handler to show full result
        historyItem.addEventListener("click", () => {
            renderToolResult(item);
        });
        
        list.appendChild(historyItem);
    });
    
    historyContainer.appendChild(list);
}

/**
 * Format parameters for display in history
 * @param {Object} parameters - The parameters object
 * @returns {string} Formatted parameters string
 */
function formatParameters(parameters) {
    if (!parameters || Object.keys(parameters).length === 0) {
        return "No parameters";
    }
    
    const paramStrings = [];
    for (const [key, value] of Object.entries(parameters)) {
        // Truncate long values
        const displayValue = typeof value === "string" && value.length > 20
            ? value.substring(0, 20) + "..."
            : value;
        
        paramStrings.push(`${key}: ${displayValue}`);
    }
    
    return paramStrings.join(", ");
}

/**
 * Format result data for preview in history
 * @param {any} data - The result data
 * @returns {string} Formatted result preview
 */
function formatResultPreview(data) {
    if (data === undefined || data === null) {
        return "No data";
    }
    
    if (typeof data === "object") {
        return "Object data...";
    }
    
    if (typeof data === "string") {
        return data.length > 30 ? data.substring(0, 30) + "..." : data;
    }
    
    return String(data);
}

/**
 * Get an icon class for a tool category
 * @param {string} category - The tool category
 * @returns {string} Icon class
 */
function getToolIcon(category) {
    const categoryIcons = {
        "ai": "fas fa-brain",
        "data": "fas fa-database",
        "communication": "fas fa-comments",
        "file": "fas fa-file",
        "web": "fas fa-globe",
        "media": "fas fa-image",
        "utility": "fas fa-tools",
        "analytics": "fas fa-chart-line",
        "integration": "fas fa-plug"
    };
    
    return categoryIcons[category?.toLowerCase()] || "fas fa-cog";
}

/**
 * Show a notification message
 * @param {string} message - The notification message
 * @param {string} type - The notification type (success, error, info, warning)
 */
function showNotification(message, type = "info") {
    if (!message) return;
    
    // Create notification element
    const notification = document.createElement("div");
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Add close button
    const closeButton = document.createElement("button");
    closeButton.className = "notification-close";
    closeButton.innerHTML = "&times;";
    closeButton.addEventListener("click", () => {
        document.body.removeChild(notification);
    });
    notification.appendChild(closeButton);
    
    // Add to body
    document.body.appendChild(notification);
    
    // Auto-remove after timeout
    setTimeout(() => {
        if (document.body.contains(notification)) {
            document.body.removeChild(notification);
        }
    }, 5000);
}

/**
 * Initialize the UI elements
 */
function initializeUI() {
    // Find UI elements
    toolContainer = document.getElementById("tool-integration-container");
    statusBadge = document.getElementById("composio-status");
    initButton = document.getElementById("initialize-composio");
    refreshButton = document.getElementById("refresh-tools");
    toolList = document.getElementById("tool-list");
    executionForm = document.getElementById("tool-execution-form");
    resultDisplay = document.getElementById("tool-result");
    historyContainer = document.getElementById("execution-history");
    
    // Set up event listeners
    if (initButton) {
        initButton.addEventListener("click", async () => {
            await initializeComposio();
        });
    }
    
    if (refreshButton) {
        refreshButton.addEventListener("click", async () => {
            await refreshToolList();
        });
    }
    
    // Update UI based on initial state
    updateConnectionStatusUI();
}

// Wait for DOM to be ready, then initialize UI
document.addEventListener("DOMContentLoaded", initializeUI);

// Export functions for external use
window.composioIntegration = {
    initialize: initializeComposio,
    refreshTools: refreshToolList,
    executeTool: executeComposioTool,
    getState: () => ({ ...COMPOSIO_UI_STATE }),
    getConfig: () => ({ ...COMPOSIO_CONFIG })
}; 