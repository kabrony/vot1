/**
 * GitHub Ecosystem Analyzer Frontend
 * 
 * This module provides the frontend interface for the GitHub ecosystem analyzer.
 * It handles API interactions and UI rendering for repository analysis.
 */

// GitHub Analyzer Class
class GitHubAnalyzer {
    constructor() {
        this.apiEndpoint = '/api/github-ecosystem';
        this.repositories = [];
        this.activeRepoKey = null;
        this.activeAnalysis = null;
        this.isLoading = false;
        this.lastUpdates = null;
        this.visualization = null;
        
        // Initialize UI components
        this.initUI();
        this.bindEvents();
        
        // Set up results tabs
        this.setupResultsTabs();
        
        // Initialize slider value display
        const maxUpdatesSlider = document.getElementById('max-updates');
        if (maxUpdatesSlider) {
            const maxUpdatesValue = document.getElementById('max-updates-value');
            if (maxUpdatesValue) {
                maxUpdatesValue.textContent = maxUpdatesSlider.value;
                maxUpdatesSlider.addEventListener('input', (e) => {
                    maxUpdatesValue.textContent = e.target.value;
                });
            }
        }
        
        // Check API status
        this.checkAPIStatus();
    }
    
    /**
     * Initialize UI components
     */
    initUI() {
        // Create main container if it doesn't exist
        if (!document.getElementById('github-analyzer-container')) {
            const container = document.createElement('div');
            container.id = 'github-analyzer-container';
            container.className = 'github-analyzer-container';
            container.innerHTML = `
                <div class="analyzer-header">
                    <h2>GitHub Ecosystem Analyzer</h2>
                    <div class="analyzer-status">
                        <span class="status-indicator"></span>
                        <span class="status-text">Checking status...</span>
                    </div>
                </div>
                <div class="analyzer-controls">
                    <div class="row">
                        <div class="input-group">
                            <label for="repo-owner">Repository Owner</label>
                            <input type="text" id="repo-owner" placeholder="e.g., microsoft">
                        </div>
                        <div class="input-group">
                            <label for="repo-name">Repository Name</label>
                            <input type="text" id="repo-name" placeholder="e.g., vscode">
                        </div>
                        <div class="checkbox-group">
                            <input type="checkbox" id="deep-analysis" checked>
                            <label for="deep-analysis">Deep Analysis</label>
                        </div>
                        <button id="analyze-repo-btn" class="primary-button">Analyze Repository</button>
                    </div>
                    <div class="row ecosystem-controls">
                        <h3>Ecosystem Analysis</h3>
                        <div id="repository-list" class="repository-list">
                            <p>No repositories analyzed yet</p>
                        </div>
                        <button id="analyze-ecosystem-btn" class="secondary-button" disabled>Analyze as Ecosystem</button>
                        <button id="generate-plan-btn" class="secondary-button" disabled>Generate Improvement Plan</button>
                    </div>
                </div>
                <div class="analysis-results-container">
                    <div class="analysis-tabs">
                        <button class="tab-button active" data-tab="overview">Overview</button>
                        <button class="tab-button" data-tab="code-quality">Code Quality</button>
                        <button class="tab-button" data-tab="architecture">Architecture</button>
                        <button class="tab-button" data-tab="improvements">Improvements</button>
                    </div>
                    <div class="analysis-content">
                        <div id="loading-indicator" class="hidden">
                            <div class="spinner"></div>
                            <p>Analyzing repository... This may take a few minutes for deep analysis.</p>
                        </div>
                        <div id="analysis-results">
                            <div id="analysis-placeholder">
                                <p>Select a repository to analyze or view previous analysis results</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Find the appropriate place to insert the container
            const mainContent = document.querySelector('.dashboard-content') || document.body;
            mainContent.appendChild(container);
            
            // Add CSS styles
            this.addStyles();
        }
        
        // Cache UI elements
        this.elements = {
            statusIndicator: document.querySelector('.analyzer-status .status-indicator'),
            statusText: document.querySelector('.analyzer-status .status-text'),
            repoOwnerInput: document.getElementById('repo-owner'),
            repoNameInput: document.getElementById('repo-name'),
            deepAnalysisCheckbox: document.getElementById('deep-analysis'),
            analyzeRepoBtn: document.getElementById('analyze-repo-btn'),
            analyzeEcosystemBtn: document.getElementById('analyze-ecosystem-btn'),
            generatePlanBtn: document.getElementById('generate-plan-btn'),
            repositoryList: document.getElementById('repository-list'),
            loadingIndicator: document.getElementById('loading-indicator'),
            analysisResults: document.getElementById('analysis-results'),
            analysisPlaceholder: document.getElementById('analysis-placeholder'),
            tabButtons: document.querySelectorAll('.tab-button')
        };
    }
    
    /**
     * Add CSS styles for the GitHub analyzer interface
     */
    addStyles() {
        const styleElement = document.createElement('style');
        styleElement.textContent = `
            .github-analyzer-container {
                margin: 20px;
                padding: 20px;
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            
            .analyzer-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }
            
            .analyzer-status {
                display: flex;
                align-items: center;
            }
            
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background-color: #ccc;
                margin-right: 8px;
            }
            
            .status-indicator.online {
                background-color: #28a745;
            }
            
            .status-indicator.offline {
                background-color: #dc3545;
            }
            
            .analyzer-controls {
                margin-bottom: 20px;
            }
            
            .row {
                display: flex;
                gap: 15px;
                margin-bottom: 20px;
                align-items: flex-end;
            }
            
            .input-group {
                display: flex;
                flex-direction: column;
                flex: 1;
            }
            
            .input-group label {
                margin-bottom: 5px;
                font-weight: 500;
            }
            
            .input-group input {
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            
            .checkbox-group {
                display: flex;
                align-items: center;
                margin-bottom: 8px;
            }
            
            .checkbox-group label {
                margin-left: 5px;
            }
            
            .primary-button {
                padding: 8px 16px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            
            .secondary-button {
                padding: 8px 16px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            
            .primary-button:hover, .secondary-button:hover {
                opacity: 0.9;
            }
            
            .primary-button:disabled, .secondary-button:disabled {
                background-color: #cccccc;
                cursor: not-allowed;
            }
            
            .ecosystem-controls {
                flex-direction: column;
                align-items: flex-start;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 8px;
            }
            
            .repository-list {
                width: 100%;
                min-height: 100px;
                max-height: 200px;
                overflow-y: auto;
                margin: 10px 0;
                padding: 10px;
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            
            .repo-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px;
                border-bottom: 1px solid #eee;
                cursor: pointer;
            }
            
            .repo-item:hover {
                background-color: #f5f5f5;
            }
            
            .repo-item.active {
                background-color: #e6f2ff;
            }
            
            .repo-remove-btn {
                background: none;
                border: none;
                color: #dc3545;
                cursor: pointer;
                font-size: 16px;
            }
            
            .analysis-tabs {
                display: flex;
                border-bottom: 1px solid #ddd;
                margin-bottom: 15px;
            }
            
            .tab-button {
                padding: 10px 15px;
                background: none;
                border: none;
                border-bottom: 2px solid transparent;
                cursor: pointer;
            }
            
            .tab-button.active {
                border-bottom: 2px solid #007bff;
                font-weight: 500;
            }
            
            .analysis-content {
                position: relative;
                min-height: 400px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 4px;
            }
            
            #loading-indicator {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                background-color: rgba(255, 255, 255, 0.8);
                z-index: 10;
            }
            
            .spinner {
                width: 40px;
                height: 40px;
                border: 4px solid #f3f3f3;
                border-top: 4px solid #007bff;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-bottom: 15px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .hidden {
                display: none !important;
            }
            
            .result-section {
                margin-bottom: 20px;
            }
            
            .result-section h3 {
                margin-bottom: 10px;
                padding-bottom: 5px;
                border-bottom: 1px solid #eee;
            }
            
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .metric-card {
                padding: 15px;
                background-color: white;
                border-radius: 4px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            
            .metric-value {
                font-size: 24px;
                font-weight: 500;
                color: #007bff;
            }
            
            .metric-label {
                font-size: 14px;
                color: #6c757d;
            }
            
            pre {
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 4px;
                overflow-x: auto;
            }
            
            .tag-list {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin: 10px 0;
            }
            
            .tag {
                display: inline-block;
                padding: 4px 8px;
                background-color: #e6f2ff;
                border-radius: 4px;
                font-size: 12px;
            }
        `;
        document.head.appendChild(styleElement);
    }
    
    /**
     * Bind event handlers to UI elements
     */
    bindEvents() {
        // Analyze repository button
        this.elements.analyzeRepoBtn.addEventListener('click', () => {
            this.analyzeRepository();
        });
        
        // Analyze ecosystem button
        this.elements.analyzeEcosystemBtn.addEventListener('click', () => {
            this.analyzeEcosystem();
        });
        
        // Generate improvement plan button
        this.elements.generatePlanBtn.addEventListener('click', () => {
            this.generateImprovementPlan();
        });
        
        // Update repository button
        document.getElementById('update-repo-btn').addEventListener('click', () => {
            this.updateRepository();
        });
        
        // Check updates status button
        document.getElementById('check-updates-btn').addEventListener('click', () => {
            this.checkUpdatesStatus();
        });
        
        // Tab switching
        this.elements.tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Update active tab
                this.elements.tabButtons.forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
                
                // Update displayed content based on active tab and repository
                if (this.activeAnalysis) {
                    this.renderAnalysisTab(e.target.dataset.tab);
                }
            });
        });
    }
    
    /**
     * Check API status
     */
    async checkAPIStatus() {
        try {
            const response = await fetch(`${this.apiEndpoint}?action=status`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.elements.statusIndicator.classList.add('online');
                this.elements.statusText.textContent = 'API Online';
                this.loadRepositories();
            } else {
                this.elements.statusIndicator.classList.add('offline');
                this.elements.statusText.textContent = 'API Offline';
            }
        } catch (error) {
            console.error('Error checking API status:', error);
            this.elements.statusIndicator.classList.add('offline');
            this.elements.statusText.textContent = 'API Error';
        }
    }
    
    /**
     * Load repositories that have been analyzed
     */
    async loadRepositories() {
        try {
            const response = await fetch(`${this.apiEndpoint}?action=repositories`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.repositories = data.repositories || [];
                this.updateRepositoryList();
            }
        } catch (error) {
            console.error('Error loading repositories:', error);
        }
    }
    
    /**
     * Update the repository list in the UI
     */
    updateRepositoryList() {
        if (this.repositories.length === 0) {
            this.elements.repositoryList.innerHTML = '<p>No repositories analyzed yet</p>';
            this.elements.analyzeEcosystemBtn.disabled = true;
            this.elements.generatePlanBtn.disabled = true;
            return;
        }
        
        // Enable ecosystem analysis if we have more than one repository
        this.elements.analyzeEcosystemBtn.disabled = this.repositories.length < 2;
        this.elements.generatePlanBtn.disabled = false;
        
        // Update list of repositories
        const repoListHTML = this.repositories.map(repoKey => {
            const isActive = repoKey === this.activeRepoKey;
            return `
                <div class="repo-item ${isActive ? 'active' : ''}" data-repo="${repoKey}">
                    <span>${repoKey}</span>
                    <button class="repo-remove-btn" data-repo="${repoKey}">×</button>
                </div>
            `;
        }).join('');
        
        this.elements.repositoryList.innerHTML = repoListHTML;
        
        // Add event listeners for repository selection
        document.querySelectorAll('.repo-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.classList.contains('repo-remove-btn')) {
                    // Handle remove button click
                    const repoKey = e.target.dataset.repo;
                    this.removeRepository(repoKey);
                } else {
                    // Handle repository selection
                    const repoKey = item.dataset.repo;
                    this.selectRepository(repoKey);
                }
            });
        });
    }
    
    /**
     * Select a repository to display its analysis
     */
    async selectRepository(repoKey) {
        this.activeRepoKey = repoKey;
        this.updateRepositoryList();
        
        // Show loading indicator
        this.elements.loadingIndicator.classList.remove('hidden');
        
        try {
            // Fetch analysis results from memory
            const response = await fetch(`${this.apiEndpoint}?action=memories&limit=10`);
            const data = await response.json();
            
            if (data.status === 'success') {
                // Find memory for this repository
                const memory = data.memories.find(m => {
                    return m.metadata && 
                           m.metadata.type === 'github_analysis' && 
                           m.metadata.repository === repoKey;
                });
                
                if (memory) {
                    try {
                        this.activeAnalysis = JSON.parse(memory.content);
                        
                        // Render the active tab
                        const activeTab = document.querySelector('.tab-button.active').dataset.tab;
                        this.renderAnalysisTab(activeTab);
                    } catch (e) {
                        console.error('Error parsing analysis data:', e);
                        this.elements.analysisResults.innerHTML = '<p>Error loading analysis results</p>';
                    }
                } else {
                    this.elements.analysisResults.innerHTML = '<p>No analysis found for this repository</p>';
                }
            }
        } catch (error) {
            console.error('Error selecting repository:', error);
            this.elements.analysisResults.innerHTML = '<p>Error loading analysis results</p>';
        } finally {
            // Hide loading indicator
            this.elements.loadingIndicator.classList.add('hidden');
        }
    }
    
    /**
     * Remove a repository from the list
     */
    removeRepository(repoKey) {
        this.repositories = this.repositories.filter(repo => repo !== repoKey);
        
        if (this.activeRepoKey === repoKey) {
            this.activeRepoKey = null;
            this.activeAnalysis = null;
            this.elements.analysisPlaceholder.classList.remove('hidden');
            this.elements.analysisResults.innerHTML = '';
        }
        
        this.updateRepositoryList();
    }
    
    /**
     * Analyze a repository
     */
    async analyzeRepository() {
        const owner = this.elements.repoOwnerInput.value.trim();
        const repo = this.elements.repoNameInput.value.trim();
        const deepAnalysis = this.elements.deepAnalysisCheckbox.checked;
        
        if (!owner || !repo) {
            alert('Please enter repository owner and name');
            return;
        }
        
        // Show loading indicator
        this.elements.loadingIndicator.classList.remove('hidden');
        this.isLoading = true;
        this.elements.analyzeRepoBtn.disabled = true;
        
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: 'analyze_repository',
                    owner,
                    repo,
                    deep_analysis: deepAnalysis
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Add repository to list if not already present
                const repoKey = `${owner}/${repo}`;
                if (!this.repositories.includes(repoKey)) {
                    this.repositories.push(repoKey);
                }
                
                // Set as active repository
                this.activeRepoKey = repoKey;
                this.activeAnalysis = data.result;
                
                // Render the active tab
                const activeTab = document.querySelector('.tab-button.active').dataset.tab;
                this.renderAnalysisTab(activeTab);
                
                // Update repository list
                this.updateRepositoryList();
            } else {
                alert(`Error analyzing repository: ${data.message || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error analyzing repository:', error);
            alert('Error analyzing repository. Check console for details.');
        } finally {
            // Hide loading indicator
            this.elements.loadingIndicator.classList.add('hidden');
            this.isLoading = false;
            this.elements.analyzeRepoBtn.disabled = false;
        }
    }
    
    /**
     * Analyze repositories as an ecosystem
     */
    async analyzeEcosystem() {
        if (this.repositories.length < 2) {
            alert('At least two repositories are required for ecosystem analysis');
            return;
        }
        
        // Prepare repository data
        const reposData = this.repositories.map(repoKey => {
            const [owner, repo] = repoKey.split('/');
            return { owner, repo };
        });
        
        // Show loading indicator
        this.elements.loadingIndicator.classList.remove('hidden');
        this.isLoading = true;
        this.elements.analyzeEcosystemBtn.disabled = true;
        
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: 'analyze_ecosystem',
                    repositories: reposData,
                    deep_analysis: true
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                alert('Ecosystem analysis completed successfully!');
                
                // TODO: Add UI to display ecosystem analysis results
                console.log('Ecosystem analysis results:', data.result);
            } else {
                alert(`Error analyzing ecosystem: ${data.message || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error analyzing ecosystem:', error);
            alert('Error analyzing ecosystem. Check console for details.');
        } finally {
            // Hide loading indicator
            this.elements.loadingIndicator.classList.add('hidden');
            this.isLoading = false;
            this.elements.analyzeEcosystemBtn.disabled = false;
        }
    }
    
    /**
     * Generate improvement plan
     */
    async generateImprovementPlan() {
        if (!this.activeRepoKey && this.repositories.length === 0) {
            alert('Please analyze at least one repository first');
            return;
        }
        
        const useEcosystem = this.repositories.length > 1 && 
                           confirm('Generate an ecosystem-wide improvement plan for all repositories? Select Cancel to generate a plan for only the selected repository.');
        
        let requestData;
        
        if (useEcosystem) {
            requestData = {
                action: 'generate_plan',
                ecosystem: true
            };
        } else if (this.activeRepoKey) {
            const [owner, repo] = this.activeRepoKey.split('/');
            requestData = {
                action: 'generate_plan',
                owner,
                repo,
                ecosystem: false
            };
        } else {
            const [owner, repo] = this.repositories[0].split('/');
            requestData = {
                action: 'generate_plan',
                owner,
                repo,
                ecosystem: false
            };
        }
        
        // Show loading indicator
        this.elements.loadingIndicator.classList.remove('hidden');
        this.isLoading = true;
        this.elements.generatePlanBtn.disabled = true;
        
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Display improvement plan
                this.elements.analysisPlaceholder.classList.add('hidden');
                
                let planContent = '';
                
                if (useEcosystem) {
                    planContent = `
                        <div class="result-section">
                            <h3>Ecosystem Improvement Plan</h3>
                            <p>Repositories analyzed: ${data.result.repositories.join(', ')}</p>
                            <pre>${data.result.ecosystem_improvement_plan}</pre>
                        </div>
                    `;
                } else {
                    planContent = `
                        <div class="result-section">
                            <h3>Repository Improvement Plan: ${data.result.repository}</h3>
                            <pre>${data.result.improvement_plan}</pre>
                        </div>
                    `;
                }
                
                this.elements.analysisResults.innerHTML = planContent;
                
                // Set focus to improvements tab
                this.elements.tabButtons.forEach(btn => btn.classList.remove('active'));
                document.querySelector('.tab-button[data-tab="improvements"]').classList.add('active');
            } else {
                alert(`Error generating improvement plan: ${data.message || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error generating improvement plan:', error);
            alert('Error generating improvement plan. Check console for details.');
        } finally {
            // Hide loading indicator
            this.elements.loadingIndicator.classList.add('hidden');
            this.isLoading = false;
            this.elements.generatePlanBtn.disabled = false;
        }
    }
    
    /**
     * Render analysis content based on the selected tab
     */
    renderAnalysisTab(tabName) {
        if (!this.activeAnalysis) {
            return;
        }
        
        this.elements.analysisPlaceholder.classList.add('hidden');
        
        switch (tabName) {
            case 'overview':
                this.renderOverviewTab();
                break;
            case 'code-quality':
                this.renderCodeQualityTab();
                break;
            case 'architecture':
                this.renderArchitectureTab();
                break;
            case 'improvements':
                this.renderImprovementsTab();
                break;
            default:
                this.renderOverviewTab();
        }
    }
    
    /**
     * Render overview tab content
     */
    renderOverviewTab() {
        const analysis = this.activeAnalysis;
        
        // Format date if available
        let updatedDate = 'N/A';
        if (analysis.updated_at) {
            try {
                updatedDate = new Date(analysis.updated_at).toLocaleDateString();
            } catch (e) {
                updatedDate = analysis.updated_at;
            }
        }
        
        // Format topics/tags
        let topicsHTML = '<p>No topics available</p>';
        if (analysis.topics && analysis.topics.length > 0) {
            topicsHTML = `
                <div class="tag-list">
                    ${analysis.topics.map(topic => `<span class="tag">${topic}</span>`).join('')}
                </div>
            `;
        }
        
        const html = `
            <div class="result-section">
                <h3>Repository Overview</h3>
                <p><strong>${analysis.full_name || this.activeRepoKey}</strong></p>
                <p>${analysis.description || 'No description available'}</p>
            </div>
            
            <div class="result-section">
                <h3>Key Metrics</h3>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">${analysis.stargazers_count || 0}</div>
                        <div class="metric-label">Stars</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${analysis.forks_count || 0}</div>
                        <div class="metric-label">Forks</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${analysis.open_issues_count || 0}</div>
                        <div class="metric-label">Open Issues</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${analysis.watchers_count || 0}</div>
                        <div class="metric-label">Watchers</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${updatedDate}</div>
                        <div class="metric-label">Last Updated</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${analysis.language || 'N/A'}</div>
                        <div class="metric-label">Primary Language</div>
                    </div>
                </div>
            </div>
            
            <div class="result-section">
                <h3>Topics</h3>
                ${topicsHTML}
            </div>
            
            <div class="result-section">
                <h3>License</h3>
                <p>${analysis.license ? analysis.license.name : 'No license information available'}</p>
            </div>
        `;
        
        this.elements.analysisResults.innerHTML = html;
    }
    
    /**
     * Render code quality tab content
     */
    renderCodeQualityTab() {
        const analysis = this.activeAnalysis;
        
        let codeQualityHTML = '<p>No code quality analysis available</p>';
        
        // Check if enhanced analysis is available
        if (analysis.enhanced_analysis && analysis.enhanced_analysis.analysis_text) {
            // Try to extract code quality section from analysis text
            const analysisText = analysis.enhanced_analysis.analysis_text;
            
            // Simple attempt to extract code quality section - this is basic and may need improvement
            const codeQualityMatch = analysisText.match(/Code Quality[\s\S]*?(?=\n#|\n\d\.|\n\*\*\d\.|\n\*\*\*|$)/i);
            
            if (codeQualityMatch) {
                codeQualityHTML = `<pre>${codeQualityMatch[0]}</pre>`;
            } else {
                codeQualityHTML = `<pre>${analysisText}</pre>`;
            }
        } else if (analysis.code_quality) {
            codeQualityHTML = `<pre>${analysis.code_quality}</pre>`;
        }
        
        const html = `
            <div class="result-section">
                <h3>Code Quality Analysis</h3>
                ${codeQualityHTML}
            </div>
        `;
        
        this.elements.analysisResults.innerHTML = html;
    }
    
    /**
     * Render architecture tab content
     */
    renderArchitectureTab() {
        const analysis = this.activeAnalysis;
        
        let architectureHTML = '<p>No architecture analysis available</p>';
        
        // Check if enhanced analysis is available
        if (analysis.enhanced_analysis && analysis.enhanced_analysis.analysis_text) {
            // Try to extract architecture section from analysis text
            const analysisText = analysis.enhanced_analysis.analysis_text;
            
            // Simple attempt to extract architecture section - this is basic and may need improvement
            const architectureMatch = analysisText.match(/Architecture[\s\S]*?(?=\n#|\n\d\.|\n\*\*\d\.|\n\*\*\*|$)/i);
            
            if (architectureMatch) {
                architectureHTML = `<pre>${architectureMatch[0]}</pre>`;
            } else {
                architectureHTML = `<pre>${analysisText}</pre>`;
            }
        } else if (analysis.architecture) {
            architectureHTML = `<pre>${analysis.architecture}</pre>`;
        }
        
        const html = `
            <div class="result-section">
                <h3>Architecture Analysis</h3>
                ${architectureHTML}
            </div>
        `;
        
        this.elements.analysisResults.innerHTML = html;
    }
    
    /**
     * Render improvements tab content
     */
    renderImprovementsTab() {
        const analysis = this.activeAnalysis;
        
        let improvementsHTML = '<p>No improvement recommendations available</p>';
        
        // Check if enhanced analysis is available
        if (analysis.enhanced_analysis && analysis.enhanced_analysis.analysis_text) {
            // Try to extract improvements section from analysis text
            const analysisText = analysis.enhanced_analysis.analysis_text;
            
            // Simple attempt to extract improvements section - this is basic and may need improvement
            const improvementsMatch = analysisText.match(/Improvement|Recommendations|Future Development|Roadmap[\s\S]*?(?=\n#|\n\d\.|\n\*\*\d\.|\n\*\*\*|$)/i);
            
            if (improvementsMatch) {
                improvementsHTML = `<pre>${improvementsMatch[0]}</pre>`;
            } else {
                improvementsHTML = `<pre>${analysisText}</pre>`;
            }
        } else if (analysis.improvements) {
            improvementsHTML = `<pre>${analysis.improvements}</pre>`;
        }
        
        const html = `
            <div class="result-section">
                <h3>Improvement Recommendations</h3>
                ${improvementsHTML}
            </div>
            
            <div class="result-section">
                <button id="detailed-plan-btn" class="primary-button">Generate Detailed Improvement Plan</button>
            </div>
        `;
        
        this.elements.analysisResults.innerHTML = html;
        
        // Add event listener for detailed plan button
        document.getElementById('detailed-plan-btn').addEventListener('click', () => {
            this.generateImprovementPlan();
        });
    }

    async updateRepository() {
        const owner = document.getElementById('update-owner-input').value;
        const repo = document.getElementById('update-repo-input').value;
        const deepAnalysis = document.getElementById('update-deep-analysis').checked;
        const autoApprove = document.getElementById('auto-approve-prs').checked;
        
        // Get selected update areas
        const updateAreas = [];
        if (document.getElementById('update-documentation').checked) updateAreas.push('documentation');
        if (document.getElementById('update-workflows').checked) updateAreas.push('workflows');
        if (document.getElementById('update-dependencies').checked) updateAreas.push('dependencies');
        if (document.getElementById('update-code-quality').checked) updateAreas.push('code_quality');
        
        const maxUpdates = parseInt(document.getElementById('max-updates').value) || 3;
        
        if (!owner || !repo) {
            this.showAlert('Please provide repository owner and name', 'danger');
            return;
        }
        
        this.showAlert(`Starting automated updates for ${owner}/${repo}...`, 'info');
        this.showLoading('update-results');
        
        // Clear previous visualizations
        document.getElementById('update-results').innerHTML = '';
        document.getElementById('ai-reasoning-display').innerHTML = '<p class="placeholder-text">Analyzing repository...</p>';
        document.getElementById('related-memories').innerHTML = '<p class="placeholder-text">Retrieving related memories...</p>';
        
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: 'update_repository',
                    owner,
                    repo,
                    deep_analysis: deepAnalysis,
                    update_areas: updateAreas,
                    max_updates: maxUpdates,
                    auto_approve: autoApprove,
                    include_reasoning: true,
                    include_memory: true
                })
            });
            
            const data = await response.json();
            this.hideLoading('update-results');
            
            if (data.status === 'success') {
                this.showAlert(`Created ${data.updates?.length || 0} updates for ${owner}/${repo}`, 'success');
                
                // Store updates for visualization
                this.lastUpdates = data.updates;
                
                // Display standard view
                this.displayUpdateResults(data);
                
                // Initialize 3D visualization if data is available
                this.setupResultsTabs();
                
                // Display reasoning data if available
                if (data.reasoning) {
                    this.displayReasoning(data);
                }
                
                // Display related memories if available
                if (data.related_memories) {
                    this.displayRelatedMemories(data.related_memories);
                }
                
                // Update the max-updates-value span when the slider changes
                document.getElementById('max-updates').addEventListener('input', (e) => {
                    document.getElementById('max-updates-value').textContent = e.target.value;
                });
            } else {
                this.showAlert(`Error: ${data.message}`, 'danger');
            }
        } catch (error) {
            this.hideLoading('update-results');
            this.showAlert(`Error: ${error.message}`, 'danger');
        }
    }
    
    async checkUpdatesStatus() {
        const owner = document.getElementById('update-owner-input').value;
        const repo = document.getElementById('update-repo-input').value;
        
        if (!owner || !repo) {
            this.showAlert('Please provide repository owner and name', 'danger');
            return;
        }
        
        this.showAlert(`Checking update status for ${owner}/${repo}...`, 'info');
        this.showLoading('update-history');
        
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: 'get_update_status',
                    owner,
                    repo
                })
            });
            
            const data = await response.json();
            this.hideLoading('update-history');
            
            if (data.status === 'success') {
                this.showAlert(`Found ${data.update_history?.length || 0} update records for ${owner}/${repo}`, 'success');
                this.displayUpdateHistory(data.update_history);
            } else {
                this.showAlert(`Error: ${data.message}`, 'danger');
            }
        } catch (error) {
            this.hideLoading('update-history');
            this.showAlert(`Error: ${error.message}`, 'danger');
        }
    }
    
    displayUpdateResults(data) {
        const resultsContainer = document.getElementById('update-results');
        resultsContainer.innerHTML = '';
        
        const updates = data.updates || [];
        if (updates.length === 0) {
            resultsContainer.innerHTML = '<div class="alert alert-info">No updates were created.</div>';
            return;
        }
        
        // Create a card for each update
        updates.forEach(update => {
            const card = document.createElement('div');
            card.className = 'card mb-3';
            
            const cardHeader = document.createElement('div');
            cardHeader.className = `card-header bg-${this.getUpdateTypeColor(update.type)}`;
            cardHeader.textContent = `${update.type.charAt(0).toUpperCase() + update.type.slice(1)}: ${update.description}`;
            
            const cardBody = document.createElement('div');
            cardBody.className = 'card-body';
            
            const fileInfo = document.createElement('p');
            fileInfo.innerHTML = `<strong>File:</strong> ${update.file}`;
            
            const prLink = document.createElement('p');
            prLink.innerHTML = `<strong>Pull Request:</strong> <a href="${update.pr_url}" target="_blank">#${update.pr_number}</a>`;
            
            cardBody.appendChild(fileInfo);
            cardBody.appendChild(prLink);
            
            card.appendChild(cardHeader);
            card.appendChild(cardBody);
            
            resultsContainer.appendChild(card);
        });
    }
    
    displayUpdateHistory(updateHistory) {
        const historyContainer = document.getElementById('update-history');
        historyContainer.innerHTML = '';
        
        if (!updateHistory || updateHistory.length === 0) {
            historyContainer.innerHTML = '<div class="alert alert-info">No update history found.</div>';
            return;
        }
        
        // Create an accordion for the update history
        const accordion = document.createElement('div');
        accordion.className = 'accordion';
        accordion.id = 'updateHistoryAccordion';
        
        updateHistory.forEach((record, index) => {
            const date = new Date(record.timestamp * 1000).toLocaleString();
            const accordionItem = document.createElement('div');
            accordionItem.className = 'accordion-item';
            
            const accordionHeader = document.createElement('h2');
            accordionHeader.className = 'accordion-header';
            accordionHeader.id = `heading${index}`;
            
            const button = document.createElement('button');
            button.className = 'accordion-button collapsed';
            button.type = 'button';
            button.dataset.bsToggle = 'collapse';
            button.dataset.bsTarget = `#collapse${index}`;
            button.setAttribute('aria-expanded', 'false');
            button.setAttribute('aria-controls', `collapse${index}`);
            button.innerHTML = `Update on ${date} (${record.updates?.length || 0} changes)`;
            
            accordionHeader.appendChild(button);
            
            const collapseDiv = document.createElement('div');
            collapseDiv.id = `collapse${index}`;
            collapseDiv.className = 'accordion-collapse collapse';
            collapseDiv.setAttribute('aria-labelledby', `heading${index}`);
            collapseDiv.dataset.bsParent = '#updateHistoryAccordion';
            
            const accordionBody = document.createElement('div');
            accordionBody.className = 'accordion-body';
            
            // Add update areas
            const areasDiv = document.createElement('div');
            areasDiv.className = 'mb-3';
            areasDiv.innerHTML = `<strong>Areas:</strong> ${record.update_areas.join(', ')}`;
            accordionBody.appendChild(areasDiv);
            
            // Add update details
            if (record.updates && record.updates.length > 0) {
                const updatesDiv = document.createElement('div');
                updatesDiv.className = 'list-group';
                
                record.updates.forEach(update => {
                    const updateItem = document.createElement('div');
                    updateItem.className = 'list-group-item';
                    updateItem.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <h5 class="mb-1">${update.type}: ${update.description}</h5>
                            <span class="badge bg-${this.getUpdateTypeColor(update.type)}">${update.type}</span>
                        </div>
                        <p class="mb-1"><strong>File:</strong> ${update.file}</p>
                        <small><a href="${update.pr_url}" target="_blank">Pull Request #${update.pr_number}</a></small>
                    `;
                    updatesDiv.appendChild(updateItem);
                });
                
                accordionBody.appendChild(updatesDiv);
            } else {
                accordionBody.innerHTML += '<div class="alert alert-info">No updates in this record.</div>';
            }
            
            collapseDiv.appendChild(accordionBody);
            
            accordionItem.appendChild(accordionHeader);
            accordionItem.appendChild(collapseDiv);
            
            accordion.appendChild(accordionItem);
        });
        
        historyContainer.appendChild(accordion);
    }
    
    getUpdateTypeColor(updateType) {
        const typeColorMap = {
            'documentation': 'info',
            'workflows': 'primary',
            'dependencies': 'warning',
            'code_quality': 'success',
            'security': 'danger'
        };
        
        return typeColorMap[updateType] || 'secondary';
    }

    // ... existing utility methods ...

    /**
     * Sets up the 3D visualization of updates using Three.js
     * @param {Array} updates - The repository updates to visualize
     */
    setupThreeJsVisualization(updates) {
        if (!updates || updates.length === 0) return;
        
        const container = document.getElementById('updates-3d-view');
        container.innerHTML = '';
        
        // Set up scene
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x111111);
        
        // Set up camera
        const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
        camera.position.z = 30;
        
        // Set up renderer
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        container.appendChild(renderer.domElement);
        
        // Add light
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(0, 10, 10);
        scene.add(directionalLight);
        
        // Create update nodes
        const updateGroup = new THREE.Group();
        scene.add(updateGroup);
        
        // Map to store nodes by type for connecting related nodes
        const nodesByType = {};
        
        updates.forEach((update, index) => {
            const node = this.createUpdateNode(update, index, updates.length);
            updateGroup.add(node);
            
            // Store node by type for connections
            if (!nodesByType[update.type]) {
                nodesByType[update.type] = [];
            }
            nodesByType[update.type].push(node);
        });
        
        // Connect nodes of the same type
        Object.values(nodesByType).forEach(nodes => {
            if (nodes.length > 1) {
                for (let i = 0; i < nodes.length - 1; i++) {
                    const material = new THREE.LineBasicMaterial({ 
                        color: 0x0088ff,
                        transparent: true,
                        opacity: 0.6
                    });
                    
                    const geometry = new THREE.BufferGeometry().setFromPoints([
                        nodes[i].position,
                        nodes[i + 1].position
                    ]);
                    
                    const line = new THREE.Line(geometry, material);
                    updateGroup.add(line);
                }
            }
        });
        
        // Controls
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.25;
        
        // Setup rotation
        let rotation = true;
        document.getElementById('toggle-rotation').addEventListener('click', () => {
            rotation = !rotation;
        });
        
        document.getElementById('reset-3d-view').addEventListener('click', () => {
            controls.reset();
        });
        
        // Handle window resize
        window.addEventListener('resize', () => {
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        });
        
        // Animation
        function animate() {
            requestAnimationFrame(animate);
            
            if (rotation) {
                updateGroup.rotation.y += 0.005;
            }
            
            controls.update();
            renderer.render(scene, camera);
        }
        
        animate();
        
        // Store references for later use
        this.visualization = {
            scene,
            camera,
            renderer,
            controls,
            updateGroup
        };
    }
    
    /**
     * Creates a 3D node representing a repository update
     * @param {Object} update - The update data
     * @param {number} index - The index of the update
     * @param {number} total - Total number of updates
     * @returns {THREE.Mesh} The created node
     */
    createUpdateNode(update, index, total) {
        // Create different geometry based on update type
        let geometry;
        const size = 2.5;
        
        switch (update.type) {
            case 'documentation':
                geometry = new THREE.TorusKnotGeometry(size * 0.6, size * 0.2);
                break;
            case 'workflows':
                geometry = new THREE.ConeGeometry(size * 0.7, size * 1.3);
                break;
            case 'dependencies':
                geometry = new THREE.DodecahedronGeometry(size * 0.7);
                break;
            case 'code_quality':
                geometry = new THREE.OctahedronGeometry(size * 0.8);
                break;
            default:
                geometry = new THREE.SphereGeometry(size * 0.7);
        }
        
        // Create material based on update type color
        const typeColor = this.getUpdateTypeColor(update.type);
        const colorMap = {
            'primary': 0x0088ff,
            'success': 0x28a745,
            'info': 0x17a2b8,
            'warning': 0xffc107,
            'danger': 0xdc3545,
            'secondary': 0x6c757d
        };
        
        const material = new THREE.MeshStandardMaterial({ 
            color: colorMap[typeColor] || 0xffffff,
            metalness: 0.3,
            roughness: 0.7
        });
        
        const mesh = new THREE.Mesh(geometry, material);
        
        // Position in a circle
        const angle = (index / total) * Math.PI * 2;
        const radius = Math.min(15, total * 1.5);
        mesh.position.x = Math.cos(angle) * radius;
        mesh.position.y = Math.sin(angle) * radius;
        mesh.position.z = (Math.random() - 0.5) * 5;
        
        // Add label
        const label = new THREE.Sprite(new THREE.SpriteMaterial({
            map: this.createTextTexture(update.description.substring(0, 20) + '...'),
            transparent: true
        }));
        
        label.scale.set(10, 5, 1);
        label.position.y = 4;
        mesh.add(label);
        
        // Store update data for interaction
        mesh.userData = { update };
        
        return mesh;
    }
    
    /**
     * Creates a texture with text for labels
     * @param {string} text - The text to render
     * @returns {THREE.CanvasTexture} The texture with rendered text
     */
    createTextTexture(text) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = 256;
        canvas.height = 128;
        
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.font = '16px Arial';
        ctx.fillStyle = 'white';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(text, canvas.width / 2, canvas.height / 2);
        
        return new THREE.CanvasTexture(canvas);
    }
    
    /**
     * Set up tab switching for result views (standard vs 3D)
     */
    setupResultsTabs() {
        const tabs = document.querySelectorAll('[data-results-tab]');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Update active tab
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                // Show corresponding content
                const tabName = tab.getAttribute('data-results-tab');
                const contents = document.querySelectorAll('[data-results-content]');
                
                contents.forEach(content => {
                    if (content.getAttribute('data-results-content') === tabName) {
                        content.classList.add('active');
                        
                        // Initialize 3D view if needed
                        if (tabName === '3d' && this.lastUpdates) {
                            this.setupThreeJsVisualization(this.lastUpdates);
                        }
                    } else {
                        content.classList.remove('active');
                    }
                });
            });
        });
    }
    
    /**
     * Display reasoning about repository updates
     * @param {Object} data - The reasoning data
     */
    displayReasoning(data) {
        const container = document.getElementById('ai-reasoning-display');
        if (!container) return;
        
        if (!data || !data.reasoning) {
            container.innerHTML = '<p class="placeholder-text">No reasoning data available</p>';
            return;
        }
        
        let html = '<div class="reasoning-content">';
        html += `<h5>Analysis Approach</h5>`;
        html += `<p>${data.reasoning.approach || 'Standard approach was used for analysis.'}</p>`;
        
        if (data.reasoning.key_observations) {
            html += `<h5>Key Observations</h5>`;
            html += `<ul>`;
            data.reasoning.key_observations.forEach(observation => {
                html += `<li>${observation}</li>`;
            });
            html += `</ul>`;
        }
        
        if (data.reasoning.decision_factors) {
            html += `<h5>Decision Factors</h5>`;
            html += `<p>${data.reasoning.decision_factors}</p>`;
        }
        
        html += '</div>';
        container.innerHTML = html;
    }
    
    /**
     * Display related memories from previous analyses
     * @param {Array} memories - The related memories
     */
    displayRelatedMemories(memories) {
        const container = document.getElementById('related-memories');
        if (!container) return;
        
        if (!memories || memories.length === 0) {
            container.innerHTML = '<p class="placeholder-text">No related memories found</p>';
            return;
        }
        
        let html = '<div class="memory-items">';
        memories.forEach(memory => {
            html += `<div class="memory-item">`;
            html += `<div class="memory-header">`;
            html += `<span class="memory-type">${memory.type}</span>`;
            html += `<span class="memory-date">${new Date(memory.timestamp * 1000).toLocaleString()}</span>`;
            html += `</div>`;
            html += `<div class="memory-content">${memory.content}</div>`;
            html += `</div>`;
        });
        html += '</div>';
        
        container.innerHTML = html;
    }
}

// Initialize the analyzer when the page loads
const githubAnalyzer = new GitHubAnalyzer();

// ... existing code ... console.log('GitHub UI loaded successfully');
