/**
 * VOT1 Dashboard - Integrations Module
 * 
 * Handles all integration-related functionality in the dashboard,
 * including Composio, OpenAPI, and other third-party integrations.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize all integration tabs
    initIntegrationTabs();
    
    // Initialize Composio-specific functionality
    initComposioIntegration();
    
    // Initialize OpenAPI-specific functionality
    initOpenAPIIntegration();
    
    // Initialize GitHub analyzer
    initGitHubAnalyzer();
});

/**
 * Initialize integration tabs
 */
function initIntegrationTabs() {
    const tabButtons = document.querySelectorAll('#section-integrations .tabs .tab');
    const tabContents = document.querySelectorAll('#section-integrations .tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            
            // Remove active class from all tabs and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            button.classList.add('active');
            document.getElementById(`tab-${tabName}`).classList.add('active');
        });
    });
    
    // Initialize sub-tabs within the Composio tab
    const composioTabButtons = document.querySelectorAll('#tab-composio .tabs .tab');
    const composioTabContents = document.querySelectorAll('#tab-composio .tab-content');
    
    composioTabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            
            // Remove active class from all tabs and contents
            composioTabButtons.forEach(btn => btn.classList.remove('active'));
            composioTabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            button.classList.add('active');
            document.getElementById(`tab-${tabName}`).classList.add('active');
        });
    });
}

/**
 * Initialize Composio integration
 */
function initComposioIntegration() {
    // Check Composio connection status
    checkComposioStatus();
    
    // Set up refresh button
    document.getElementById('refresh-composio-status').addEventListener('click', checkComposioStatus);
    
    // Load models
    loadComposioModels();
    
    // Set up generate form
    initGenerateForm();
    
    // Set up embedding form
    initEmbeddingForm();
    
    // Load usage data
    loadComposioUsage();
    
    // Set up refresh usage button
    document.getElementById('refresh-usage').addEventListener('click', loadComposioUsage);
}

/**
 * Initialize OpenAPI integration
 */
function initOpenAPIIntegration() {
    // Load OpenAPI tools
    loadOpenAPITools();
    
    // Set up OpenAPI upload form
    initOpenAPIUploadForm();
    
    // Set up tool detail modal
    initToolDetailModal();
}

/**
 * Initialize GitHub analyzer
 */
function initGitHubAnalyzer() {
    // Create GitHub analyzer instance for repository analysis and automation
    if (document.getElementById('tab-github')) {
        window.githubAnalyzer = new GitHubAnalyzer();
        console.log('GitHub Analyzer initialized');
    }
}

/**
 * Check Composio connection status
 */
function checkComposioStatus() {
    const statusIcon = document.querySelector('#composio-status .status-icon');
    const statusText = document.getElementById('composio-status-text');
    
    statusIcon.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    statusText.textContent = 'Checking connection...';
    
    // Also update the status in the chat options panel
    const chatStatusIcon = document.querySelector('#composio-status-chat .status-indicator');
    const chatStatusText = document.getElementById('composio-status-text-chat');
    
    if (chatStatusIcon && chatStatusText) {
        chatStatusIcon.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        chatStatusText.textContent = 'Checking connection...';
    }
    
    fetch('/api/composio/status')
        .then(response => response.json())
        .then(data => {
            if (data.connected) {
                statusIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
                statusText.textContent = `Connected (${data.version || 'unknown version'})`;
                
                if (chatStatusIcon && chatStatusText) {
                    chatStatusIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
                    chatStatusText.textContent = 'Connected';
                }
            } else {
                statusIcon.innerHTML = '<i class="fas fa-times-circle"></i>';
                statusText.textContent = `Not connected: ${data.error || 'Unknown error'}`;
                
                if (chatStatusIcon && chatStatusText) {
                    chatStatusIcon.innerHTML = '<i class="fas fa-times-circle"></i>';
                    chatStatusText.textContent = 'Not connected';
                }
            }
        })
        .catch(error => {
            console.error('Error checking Composio status:', error);
            statusIcon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
            statusText.textContent = 'Error checking connection';
            
            if (chatStatusIcon && chatStatusText) {
                chatStatusIcon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                chatStatusText.textContent = 'Error checking connection';
            }
        });
}

/**
 * Load Composio models
 */
function loadComposioModels() {
    const modelsContainer = document.getElementById('composio-models-container');
    const generateModelSelect = document.getElementById('generate-model');
    const embeddingModelSelect = document.getElementById('embedding-model');
    
    modelsContainer.innerHTML = '<div class="loading-indicator">Loading models...</div>';
    generateModelSelect.innerHTML = '<option value="">Loading models...</option>';
    embeddingModelSelect.innerHTML = '<option value="">Loading models...</option>';
    
    fetch('/api/composio/models')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                modelsContainer.innerHTML = `<div class="error-message">Error: ${data.error}</div>`;
                generateModelSelect.innerHTML = '<option value="">Error loading models</option>';
                embeddingModelSelect.innerHTML = '<option value="">Error loading models</option>';
                return;
            }
            
            const models = data.models || [];
            
            if (models.length === 0) {
                modelsContainer.innerHTML = '<div class="empty-message">No models available</div>';
                generateModelSelect.innerHTML = '<option value="">No models available</option>';
                embeddingModelSelect.innerHTML = '<option value="">No models available</option>';
                return;
            }
            
            // Update models container
            modelsContainer.innerHTML = '';
            
            const template = document.getElementById('model-card-template');
            
            models.forEach(model => {
                const modelCard = template.content.cloneNode(true);
                
                modelCard.querySelector('.model-name').textContent = model.name || model.id || 'Unknown Model';
                modelCard.querySelector('.model-type').textContent = `Type: ${model.type || 'Unknown'}`;
                modelCard.querySelector('.model-context').textContent = `Context: ${model.context_length || 'Unknown'} tokens`;
                modelCard.querySelector('.model-description').textContent = model.description || 'No description available';
                
                modelsContainer.appendChild(modelCard);
            });
            
            // Update model selects
            generateModelSelect.innerHTML = '';
            embeddingModelSelect.innerHTML = '';
            
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Default model';
            generateModelSelect.appendChild(defaultOption.cloneNode(true));
            embeddingModelSelect.appendChild(defaultOption.cloneNode(true));
            
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.name || model.id;
                
                if (model.type === 'text-generation' || model.type === 'completion') {
                    generateModelSelect.appendChild(option.cloneNode(true));
                }
                
                if (model.type === 'embedding') {
                    embeddingModelSelect.appendChild(option.cloneNode(true));
                } else {
                    // If no specific embedding models, add all models to both selects
                    embeddingModelSelect.appendChild(option.cloneNode(true));
                }
            });
        })
        .catch(error => {
            console.error('Error loading Composio models:', error);
            modelsContainer.innerHTML = '<div class="error-message">Failed to load models</div>';
            generateModelSelect.innerHTML = '<option value="">Failed to load models</option>';
            embeddingModelSelect.innerHTML = '<option value="">Failed to load models</option>';
        });
}

/**
 * Initialize text generation form
 */
function initGenerateForm() {
    const generateForm = document.getElementById('generate-form');
    const temperatureSlider = document.getElementById('generate-temperature');
    const temperatureValue = document.getElementById('temperature-value');
    const resultContainer = document.getElementById('generate-result-container');
    const resultContent = document.getElementById('generate-result');
    const resultMetadata = document.getElementById('generate-metadata');
    
    // Update temperature value display
    temperatureSlider.addEventListener('input', () => {
        temperatureValue.textContent = temperatureSlider.value;
    });
    
    // Handle form submission
    generateForm.addEventListener('submit', event => {
        event.preventDefault();
        
        const model = document.getElementById('generate-model').value;
        const prompt = document.getElementById('generate-prompt').value;
        const maxTokens = parseInt(document.getElementById('generate-max-tokens').value);
        const temperature = parseFloat(temperatureSlider.value);
        
        if (!prompt) {
            alert('Please enter a prompt');
            return;
        }
        
        resultContent.innerHTML = '<div class="loading-indicator">Generating...</div>';
        resultMetadata.innerHTML = '';
        resultContainer.style.display = 'block';
        
        fetch('/api/composio/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: model || undefined,
                prompt,
                max_tokens: maxTokens,
                temperature
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    resultContent.innerHTML = `<div class="error-message">Error: ${data.error}</div>`;
                    return;
                }
                
                // Display the generated text
                resultContent.innerHTML = '';
                const textPre = document.createElement('pre');
                textPre.textContent = data.text || '';
                resultContent.appendChild(textPre);
                
                // Display metadata
                resultMetadata.innerHTML = '';
                
                const metadataList = document.createElement('ul');
                metadataList.classList.add('metadata-list');
                
                const modelItem = document.createElement('li');
                modelItem.textContent = `Model: ${data.model || 'unknown'}`;
                metadataList.appendChild(modelItem);
                
                if (data.usage) {
                    const tokensItem = document.createElement('li');
                    tokensItem.textContent = `Total tokens: ${data.usage.total_tokens || 0}`;
                    metadataList.appendChild(tokensItem);
                    
                    const promptTokensItem = document.createElement('li');
                    promptTokensItem.textContent = `Prompt tokens: ${data.usage.prompt_tokens || 0}`;
                    metadataList.appendChild(promptTokensItem);
                    
                    const completionTokensItem = document.createElement('li');
                    completionTokensItem.textContent = `Completion tokens: ${data.usage.completion_tokens || 0}`;
                    metadataList.appendChild(completionTokensItem);
                }
                
                resultMetadata.appendChild(metadataList);
            })
            .catch(error => {
                console.error('Error generating text:', error);
                resultContent.innerHTML = '<div class="error-message">Failed to generate text</div>';
            });
    });
}

/**
 * Initialize embedding form
 */
function initEmbeddingForm() {
    const embeddingForm = document.getElementById('embedding-form');
    const resultContainer = document.getElementById('embedding-result-container');
    const resultContent = document.getElementById('embedding-result');
    const resultMetadata = document.getElementById('embedding-metadata');
    
    // Handle form submission
    embeddingForm.addEventListener('submit', event => {
        event.preventDefault();
        
        const model = document.getElementById('embedding-model').value;
        const text = document.getElementById('embedding-text').value;
        
        if (!text) {
            alert('Please enter text to embed');
            return;
        }
        
        resultContent.innerHTML = '<div class="loading-indicator">Creating embedding...</div>';
        resultMetadata.innerHTML = '';
        resultContainer.style.display = 'block';
        
        fetch('/api/composio/embedding', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: model || undefined,
                text
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    resultContent.innerHTML = `<div class="error-message">Error: ${data.error}</div>`;
                    return;
                }
                
                // Display the embedding information
                resultContent.innerHTML = '';
                
                if (data.embedding) {
                    const embeddingInfo = document.createElement('div');
                    embeddingInfo.innerHTML = `
                        <p>Embedding created successfully</p>
                        <p>Dimension: ${data.embedding.length}</p>
                        <details>
                            <summary>View first 10 values</summary>
                            <pre>${JSON.stringify(data.embedding.slice(0, 10), null, 2)}</pre>
                        </details>
                    `;
                    resultContent.appendChild(embeddingInfo);
                } else {
                    resultContent.innerHTML = '<div class="warning-message">No embedding data returned</div>';
                }
                
                // Display metadata
                resultMetadata.innerHTML = '';
                
                const metadataList = document.createElement('ul');
                metadataList.classList.add('metadata-list');
                
                const modelItem = document.createElement('li');
                modelItem.textContent = `Model: ${data.model || 'unknown'}`;
                metadataList.appendChild(modelItem);
                
                if (data.usage) {
                    const tokensItem = document.createElement('li');
                    tokensItem.textContent = `Total tokens: ${data.usage.total_tokens || 0}`;
                    metadataList.appendChild(tokensItem);
                }
                
                resultMetadata.appendChild(metadataList);
            })
            .catch(error => {
                console.error('Error creating embedding:', error);
                resultContent.innerHTML = '<div class="error-message">Failed to create embedding</div>';
            });
    });
}

/**
 * Load Composio usage data
 */
function loadComposioUsage() {
    const usageContainer = document.getElementById('composio-usage-container');
    
    usageContainer.innerHTML = '<div class="loading-indicator">Loading usage data...</div>';
    
    fetch('/api/composio/usage')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                usageContainer.innerHTML = `<div class="error-message">Error: ${data.error}</div>`;
                return;
            }
            
            usageContainer.innerHTML = '';
            
            // Create usage summary
            const usageSummary = document.createElement('div');
            usageSummary.className = 'usage-summary';
            
            // Daily usage
            const dailyUsage = data.daily || {};
            const dailySection = document.createElement('div');
            dailySection.className = 'usage-section';
            dailySection.innerHTML = `
                <h4>Daily Usage</h4>
                <div class="usage-stats">
                    <div class="usage-stat">
                        <span class="stat-label">Total Requests</span>
                        <span class="stat-value">${dailyUsage.total_requests || 0}</span>
                    </div>
                    <div class="usage-stat">
                        <span class="stat-label">Total Tokens</span>
                        <span class="stat-value">${dailyUsage.total_tokens || 0}</span>
                    </div>
                    <div class="usage-stat">
                        <span class="stat-label">Input Tokens</span>
                        <span class="stat-value">${dailyUsage.input_tokens || 0}</span>
                    </div>
                    <div class="usage-stat">
                        <span class="stat-label">Output Tokens</span>
                        <span class="stat-value">${dailyUsage.output_tokens || 0}</span>
                    </div>
                </div>
            `;
            usageSummary.appendChild(dailySection);
            
            // Monthly usage
            const monthlyUsage = data.monthly || {};
            const monthlySection = document.createElement('div');
            monthlySection.className = 'usage-section';
            monthlySection.innerHTML = `
                <h4>Monthly Usage</h4>
                <div class="usage-stats">
                    <div class="usage-stat">
                        <span class="stat-label">Total Requests</span>
                        <span class="stat-value">${monthlyUsage.total_requests || 0}</span>
                    </div>
                    <div class="usage-stat">
                        <span class="stat-label">Total Tokens</span>
                        <span class="stat-value">${monthlyUsage.total_tokens || 0}</span>
                    </div>
                    <div class="usage-stat">
                        <span class="stat-label">Input Tokens</span>
                        <span class="stat-value">${monthlyUsage.input_tokens || 0}</span>
                    </div>
                    <div class="usage-stat">
                        <span class="stat-label">Output Tokens</span>
                        <span class="stat-value">${monthlyUsage.output_tokens || 0}</span>
                    </div>
                </div>
            `;
            usageSummary.appendChild(monthlySection);
            
            // Model-specific usage
            const modelUsage = data.models || {};
            
            if (Object.keys(modelUsage).length > 0) {
                const modelsSection = document.createElement('div');
                modelsSection.className = 'usage-section';
                modelsSection.innerHTML = '<h4>Model Usage</h4>';
                
                const modelsTable = document.createElement('table');
                modelsTable.className = 'usage-table';
                modelsTable.innerHTML = `
                    <thead>
                        <tr>
                            <th>Model</th>
                            <th>Requests</th>
                            <th>Total Tokens</th>
                            <th>Input Tokens</th>
                            <th>Output Tokens</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                `;
                
                const tableBody = modelsTable.querySelector('tbody');
                
                for (const [modelId, usage] of Object.entries(modelUsage)) {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${modelId}</td>
                        <td>${usage.requests || 0}</td>
                        <td>${usage.total_tokens || 0}</td>
                        <td>${usage.input_tokens || 0}</td>
                        <td>${usage.output_tokens || 0}</td>
                    `;
                    tableBody.appendChild(row);
                }
                
                modelsSection.appendChild(modelsTable);
                usageSummary.appendChild(modelsSection);
            }
            
            usageContainer.appendChild(usageSummary);
        })
        .catch(error => {
            console.error('Error loading Composio usage:', error);
            usageContainer.innerHTML = '<div class="error-message">Failed to load usage data</div>';
        });
}

/**
 * Load OpenAPI tools
 */
function loadOpenAPITools() {
    const toolsContainer = document.getElementById('imported-tools-container');
    
    toolsContainer.innerHTML = '<div class="loading-indicator">Loading imported tools...</div>';
    
    fetch('/api/openapi/tools')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                toolsContainer.innerHTML = `<div class="error-message">Error: ${data.error}</div>`;
                return;
            }
            
            const tools = data.tools || [];
            
            if (tools.length === 0) {
                toolsContainer.innerHTML = '<p>No tools imported yet. Import an OpenAPI specification to get started.</p>';
                return;
            }
            
            toolsContainer.innerHTML = '';
            
            const template = document.getElementById('tool-card-template');
            
            tools.forEach(tool => {
                const toolCard = template.content.cloneNode(true);
                
                toolCard.querySelector('.tool-name').textContent = tool.name || 'Unnamed Tool';
                toolCard.querySelector('.tool-description').textContent = tool.description || 'No description available';
                toolCard.querySelector('.tool-id').textContent = `ID: ${tool.id || tool.tool_id || 'unknown'}`;
                toolCard.querySelector('.tool-version').textContent = `Version: ${tool.version || 'unknown'}`;
                
                // Add actions as badges
                const actionsList = toolCard.querySelector('.tool-actions-list');
                if (tool.actions && tool.actions.length > 0) {
                    tool.actions.forEach(action => {
                        const actionBadge = document.createElement('span');
                        actionBadge.className = 'action-badge';
                        actionBadge.textContent = action.name || action;
                        actionsList.appendChild(actionBadge);
                    });
                }
                
                // Set up view button
                const viewButton = toolCard.querySelector('.view-tool');
                viewButton.addEventListener('click', () => {
                    openToolDetailModal(tool.id || tool.tool_id);
                });
                
                // Set up delete button
                const deleteButton = toolCard.querySelector('.delete-tool');
                deleteButton.addEventListener('click', () => {
                    if (confirm(`Are you sure you want to delete the tool "${tool.name}"?`)) {
                        deleteTool(tool.id || tool.tool_id);
                    }
                });
                
                toolsContainer.appendChild(toolCard);
            });
        })
        .catch(error => {
            console.error('Error loading OpenAPI tools:', error);
            toolsContainer.innerHTML = '<div class="error-message">Failed to load tools</div>';
        });
}

/**
 * Initialize OpenAPI upload form
 */
function initOpenAPIUploadForm() {
    const uploadForm = document.getElementById('openapi-upload-form');
    const specFileInput = document.getElementById('spec-file');
    const specFileName = document.getElementById('spec-file-name');
    const authFileInput = document.getElementById('auth-file');
    const authFileName = document.getElementById('auth-file-name');
    
    // Update file name display when files are selected
    specFileInput.addEventListener('change', () => {
        specFileName.textContent = specFileInput.files.length > 0 ? 
            specFileInput.files[0].name : 'No file chosen';
    });
    
    authFileInput.addEventListener('change', () => {
        authFileName.textContent = authFileInput.files.length > 0 ? 
            authFileInput.files[0].name : 'No file chosen';
    });
    
    // Handle form submission
    uploadForm.addEventListener('submit', event => {
        event.preventDefault();
        
        if (!specFileInput.files.length) {
            alert('Please select an OpenAPI specification file');
            return;
        }
        
        const formData = new FormData(uploadForm);
        
        // Show loading indicator
        const submitButton = document.getElementById('import-openapi');
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Importing...';
        
        fetch('/api/openapi/tools', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(`Error importing OpenAPI spec: ${data.error}`);
                    return;
                }
                
                // Show success message
                alert(`OpenAPI spec imported successfully as "${data.tool.name || 'unknown'}"`);
                
                // Reset form
                uploadForm.reset();
                specFileName.textContent = 'No file chosen';
                authFileName.textContent = 'No file chosen';
                
                // Refresh tool list
                loadOpenAPITools();
            })
            .catch(error => {
                console.error('Error importing OpenAPI spec:', error);
                alert('Failed to import OpenAPI spec');
            })
            .finally(() => {
                // Restore button
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            });
    });
}

/**
 * Initialize tool detail modal
 */
function initToolDetailModal() {
    const modal = document.getElementById('tool-detail-modal');
    const closeButton = modal.querySelector('.close-modal');
    
    // Close modal when the close button is clicked
    closeButton.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    // Close modal when clicking outside the modal content
    window.addEventListener('click', event => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Set up action execution
    const actionSelect = document.getElementById('action-select');
    const actionParameters = document.getElementById('action-parameters');
    const executeButton = document.getElementById('execute-action');
    const actionResult = document.getElementById('action-result');
    
    executeButton.addEventListener('click', () => {
        const toolId = modal.getAttribute('data-tool-id');
        const action = actionSelect.value;
        
        if (!toolId || !action) {
            actionResult.innerHTML = '<div class="error-message">Tool ID or action not specified</div>';
            return;
        }
        
        let parameters = {};
        
        try {
            if (actionParameters.value.trim()) {
                parameters = JSON.parse(actionParameters.value);
            }
        } catch (error) {
            actionResult.innerHTML = `<div class="error-message">Invalid JSON parameters: ${error.message}</div>`;
            return;
        }
        
        // Show loading indicator
        actionResult.innerHTML = '<div class="loading-indicator">Executing action...</div>';
        
        fetch(`/api/openapi/tools/${toolId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action,
                parameters
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    actionResult.innerHTML = `<div class="error-message">Error: ${data.error}</div>`;
                    return;
                }
                
                // Display the result
                actionResult.innerHTML = '<h4>Result:</h4>';
                
                const resultPre = document.createElement('pre');
                resultPre.className = 'json-result';
                resultPre.textContent = JSON.stringify(data.result, null, 2);
                
                actionResult.appendChild(resultPre);
            })
            .catch(error => {
                console.error('Error executing action:', error);
                actionResult.innerHTML = '<div class="error-message">Failed to execute action</div>';
            });
    });
}

/**
 * Open tool detail modal for a specific tool
 * @param {string} toolId - ID of the tool to display
 */
function openToolDetailModal(toolId) {
    const modal = document.getElementById('tool-detail-modal');
    const nameElement = document.getElementById('modal-tool-name');
    const descriptionElement = document.getElementById('modal-tool-description');
    const idElement = document.getElementById('modal-tool-id');
    const versionElement = document.getElementById('modal-tool-version');
    const createdElement = document.getElementById('modal-tool-created');
    const actionsElement = document.getElementById('modal-tool-actions');
    const actionSelect = document.getElementById('action-select');
    const actionParameters = document.getElementById('action-parameters');
    const actionResult = document.getElementById('action-result');
    
    // Reset modal content
    nameElement.textContent = 'Loading Tool Details...';
    descriptionElement.textContent = '';
    idElement.textContent = '';
    versionElement.textContent = '';
    createdElement.textContent = '';
    actionsElement.innerHTML = '<div class="loading-indicator">Loading actions...</div>';
    actionSelect.innerHTML = '<option value="">Select an action</option>';
    actionParameters.value = '';
    actionResult.innerHTML = '';
    
    // Store tool ID in modal for later use
    modal.setAttribute('data-tool-id', toolId);
    
    // Show modal
    modal.style.display = 'block';
    
    // Fetch tool details
    fetch(`/api/openapi/tools/${toolId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                nameElement.textContent = 'Error Loading Tool';
                descriptionElement.textContent = `Error: ${data.error}`;
                return;
            }
            
            // Update modal content
            nameElement.textContent = data.name || 'Unnamed Tool';
            descriptionElement.textContent = data.description || 'No description available';
            idElement.textContent = data.id || data.tool_id || toolId;
            versionElement.textContent = data.version || 'unknown';
            createdElement.textContent = data.created_at || 'unknown';
            
            // Update actions list
            actionsElement.innerHTML = '';
            
            if (!data.actions || data.actions.length === 0) {
                actionsElement.textContent = 'No actions available';
                return;
            }
            
            const actionsList = document.createElement('ul');
            actionsList.className = 'actions-list';
            
            // Clear and populate action select
            actionSelect.innerHTML = '<option value="">Select an action</option>';
            
            data.actions.forEach(action => {
                const actionName = action.name || action;
                const actionDescription = action.description || 'No description available';
                
                // Add to list
                const actionItem = document.createElement('li');
                actionItem.innerHTML = `
                    <strong>${actionName}</strong>
                    <p>${actionDescription}</p>
                `;
                
                if (action.parameters) {
                    const paramsList = document.createElement('ul');
                    paramsList.className = 'params-list';
                    
                    Object.entries(action.parameters).forEach(([paramName, paramDetails]) => {
                        const paramItem = document.createElement('li');
                        paramItem.innerHTML = `
                            <span class="param-name">${paramName}</span>
                            <span class="param-type">${paramDetails.type || 'any'}</span>
                            <span class="param-description">${paramDetails.description || ''}</span>
                        `;
                        paramsList.appendChild(paramItem);
                    });
                    
                    actionItem.appendChild(paramsList);
                }
                
                actionsList.appendChild(actionItem);
                
                // Add to select
                const option = document.createElement('option');
                option.value = actionName;
                option.textContent = actionName;
                actionSelect.appendChild(option);
            });
            
            actionsElement.appendChild(actionsList);
        })
        .catch(error => {
            console.error('Error loading tool details:', error);
            nameElement.textContent = 'Error Loading Tool';
            descriptionElement.textContent = 'Failed to load tool details';
        });
}

/**
 * Delete a tool
 * @param {string} toolId - ID of the tool to delete
 */
function deleteTool(toolId) {
    fetch(`/api/openapi/tools/${toolId}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error deleting tool: ${data.error}`);
                return;
            }
            
            alert('Tool deleted successfully');
            
            // Refresh tool list
            loadOpenAPITools();
        })
        .catch(error => {
            console.error('Error deleting tool:', error);
            alert('Failed to delete tool');
        });
} 