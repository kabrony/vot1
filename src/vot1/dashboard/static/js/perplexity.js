/**
 * VOT1 Dashboard Perplexity Integration v1.0 (2025)
 * Handles Perplexity AI search functionality for the VOT1 dashboard.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Perplexity search functionality
    initPerplexitySearch();
    
    // Set up event listeners for search form
    setupSearchForm();
    
    // Set up event listeners for question answering form
    setupQuestionForm();
    
    // Set up event listeners for summarize form
    setupSummarizeForm();
});

/**
 * Initialize Perplexity search functionality
 */
function initPerplexitySearch() {
    // Check if Perplexity tab exists
    const perplexityTab = document.getElementById('perplexity-tab');
    if (!perplexityTab) return;
    
    // Add click event to tab
    perplexityTab.addEventListener('click', function() {
        document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        perplexityTab.classList.add('active');
        document.getElementById('perplexity-content').classList.add('active');
    });
    
    // Check Perplexity connection status
    checkPerplexityStatus();
}

/**
 * Check Perplexity connection status
 */
function checkPerplexityStatus() {
    const statusIndicator = document.getElementById('perplexity-status');
    const statusText = document.getElementById('perplexity-status-text');
    
    if (!statusIndicator || !statusText) return;
    
    statusText.textContent = 'Checking connection...';
    statusIndicator.classList.remove('connected', 'disconnected');
    statusIndicator.classList.add('checking');
    
    fetch('/api/perplexity/status')
        .then(response => response.json())
        .then(data => {
            statusIndicator.classList.remove('checking');
            
            if (data.connected) {
                statusIndicator.classList.add('connected');
                statusText.textContent = 'Connected';
                enablePerplexityForms(true);
            } else {
                statusIndicator.classList.add('disconnected');
                statusText.textContent = data.error ? `Disconnected: ${data.error}` : 'Disconnected';
                enablePerplexityForms(false);
            }
        })
        .catch(error => {
            console.error('Error checking Perplexity connection:', error);
            statusIndicator.classList.remove('checking');
            statusIndicator.classList.add('disconnected');
            statusText.textContent = 'Error checking connection';
            enablePerplexityForms(false);
        });
}

/**
 * Enable or disable Perplexity forms based on connection status
 */
function enablePerplexityForms(enabled) {
    const forms = [
        document.getElementById('perplexity-search-form'),
        document.getElementById('perplexity-question-form'),
        document.getElementById('perplexity-summarize-form')
    ];
    
    forms.forEach(form => {
        if (form) {
            const inputs = form.querySelectorAll('input, textarea, select, button');
            inputs.forEach(input => {
                input.disabled = !enabled;
            });
        }
    });
}

/**
 * Set up event listeners for search form
 */
function setupSearchForm() {
    const form = document.getElementById('perplexity-search-form');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const query = document.getElementById('search-query').value.trim();
        const focus = document.getElementById('search-focus').value;
        const maxResults = parseInt(document.getElementById('search-max-results').value) || 5;
        
        if (!query) {
            showNotification('Please enter a search query', 'error');
            return;
        }
        
        // Show loading state
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
        }
        
        // Clear previous results
        const resultsContainer = document.getElementById('search-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = '<div class="loading-indicator">Searching...</div>';
        }
        
        // Perform search
        fetch('/api/perplexity/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                focus: focus || undefined,
                max_results: maxResults
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showNotification(data.error, 'error');
                if (resultsContainer) {
                    resultsContainer.innerHTML = `<div class="error-message">${data.error}</div>`;
                }
            } else {
                renderSearchResults(data, resultsContainer);
            }
        })
        .catch(error => {
            console.error('Error performing search:', error);
            showNotification('Error: ' + error.message, 'error');
            if (resultsContainer) {
                resultsContainer.innerHTML = `<div class="error-message">Error: ${error.message}</div>`;
            }
        })
        .finally(() => {
            // Reset button state
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = 'Search';
            }
        });
    });
}

/**
 * Render search results in the container
 */
function renderSearchResults(data, container) {
    if (!container) return;
    
    // Clear container
    container.innerHTML = '';
    
    // Create results header
    const header = document.createElement('div');
    header.className = 'results-header';
    header.innerHTML = `
        <h3>Search Results for "${data.query || ''}"</h3>
        <span class="results-count">${data.results ? data.results.length : 0} results</span>
    `;
    container.appendChild(header);
    
    // Check if there are results
    if (!data.results || data.results.length === 0) {
        const noResults = document.createElement('div');
        noResults.className = 'no-results';
        noResults.textContent = 'No results found';
        container.appendChild(noResults);
        return;
    }
    
    // Create results list
    const resultsList = document.createElement('div');
    resultsList.className = 'results-list';
    
    data.results.forEach(result => {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item';
        
        // Format result based on its structure
        let resultContent = '';
        
        if (result.title) {
            resultContent += `<h4 class="result-title">${result.title}</h4>`;
        }
        
        if (result.url) {
            resultContent += `<a href="${result.url}" target="_blank" class="result-url">${result.url}</a>`;
        }
        
        if (result.snippet || result.content) {
            resultContent += `<p class="result-snippet">${result.snippet || result.content}</p>`;
        }
        
        // Add metadata if available
        if (result.metadata) {
            resultContent += '<div class="result-metadata">';
            for (const [key, value] of Object.entries(result.metadata)) {
                resultContent += `<span class="metadata-item">${key}: ${value}</span>`;
            }
            resultContent += '</div>';
        }
        
        resultItem.innerHTML = resultContent;
        resultsList.appendChild(resultItem);
    });
    
    container.appendChild(resultsList);
    
    // Add save to memory button
    const saveButton = document.createElement('button');
    saveButton.className = 'btn save-to-memory';
    saveButton.innerHTML = '<i class="fas fa-brain"></i> Save to Memory';
    saveButton.addEventListener('click', function() {
        saveSearchResultsToMemory(data);
    });
    
    container.appendChild(saveButton);
}

/**
 * Save search results to memory
 */
function saveSearchResultsToMemory(data) {
    fetch('/api/memory/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            content: `Search results for "${data.query}": ${JSON.stringify(data.results)}`,
            type: 'search_results',
            metadata: {
                source: 'perplexity',
                query: data.query,
                timestamp: new Date().toISOString()
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Search results saved to memory', 'success');
        } else {
            showNotification(data.error || 'Failed to save to memory', 'error');
        }
    })
    .catch(error => {
        console.error('Error saving to memory:', error);
        showNotification('Error: ' + error.message, 'error');
    });
}

/**
 * Set up event listeners for question answering form
 */
function setupQuestionForm() {
    const form = document.getElementById('perplexity-question-form');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const question = document.getElementById('question-input').value.trim();
        const includeSources = document.getElementById('include-sources').checked;
        
        if (!question) {
            showNotification('Please enter a question', 'error');
            return;
        }
        
        // Show loading state
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        }
        
        // Clear previous results
        const resultsContainer = document.getElementById('question-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = '<div class="loading-indicator">Getting answer...</div>';
        }
        
        // Get answer
        fetch('/api/perplexity/answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                include_sources: includeSources
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showNotification(data.error, 'error');
                if (resultsContainer) {
                    resultsContainer.innerHTML = `<div class="error-message">${data.error}</div>`;
                }
            } else {
                renderQuestionResults(data, resultsContainer);
            }
        })
        .catch(error => {
            console.error('Error getting answer:', error);
            showNotification('Error: ' + error.message, 'error');
            if (resultsContainer) {
                resultsContainer.innerHTML = `<div class="error-message">Error: ${error.message}</div>`;
            }
        })
        .finally(() => {
            // Reset button state
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = 'Get Answer';
            }
        });
    });
}

/**
 * Render question results in the container
 */
function renderQuestionResults(data, container) {
    if (!container) return;
    
    // Clear container
    container.innerHTML = '';
    
    // Create results header
    const header = document.createElement('div');
    header.className = 'results-header';
    header.innerHTML = `
        <h3>Answer to "${data.question || ''}"</h3>
    `;
    container.appendChild(header);
    
    // Create answer container
    const answerContainer = document.createElement('div');
    answerContainer.className = 'answer-container';
    
    // Add answer text
    if (data.answer) {
        const answerText = document.createElement('div');
        answerText.className = 'answer-text';
        answerText.innerHTML = data.answer;
        answerContainer.appendChild(answerText);
    } else {
        const noAnswer = document.createElement('div');
        noAnswer.className = 'no-answer';
        noAnswer.textContent = 'No answer available';
        answerContainer.appendChild(noAnswer);
    }
    
    // Add sources if available
    if (data.sources && data.sources.length > 0) {
        const sourcesContainer = document.createElement('div');
        sourcesContainer.className = 'sources-container';
        sourcesContainer.innerHTML = '<h4>Sources</h4>';
        
        const sourcesList = document.createElement('ul');
        sourcesList.className = 'sources-list';
        
        data.sources.forEach(source => {
            const sourceItem = document.createElement('li');
            sourceItem.className = 'source-item';
            
            if (source.url) {
                sourceItem.innerHTML = `<a href="${source.url}" target="_blank">${source.title || source.url}</a>`;
            } else {
                sourceItem.textContent = source.title || 'Unknown source';
            }
            
            sourcesList.appendChild(sourceItem);
        });
        
        sourcesContainer.appendChild(sourcesList);
        answerContainer.appendChild(sourcesContainer);
    }
    
    container.appendChild(answerContainer);
    
    // Add save to memory button
    const saveButton = document.createElement('button');
    saveButton.className = 'btn save-to-memory';
    saveButton.innerHTML = '<i class="fas fa-brain"></i> Save to Memory';
    saveButton.addEventListener('click', function() {
        saveAnswerToMemory(data);
    });
    
    container.appendChild(saveButton);
}

/**
 * Save answer to memory
 */
function saveAnswerToMemory(data) {
    fetch('/api/memory/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            content: `Question: "${data.question}"\n\nAnswer: ${data.answer}`,
            type: 'qa_pair',
            metadata: {
                source: 'perplexity',
                question: data.question,
                has_sources: data.sources && data.sources.length > 0,
                timestamp: new Date().toISOString()
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Answer saved to memory', 'success');
        } else {
            showNotification(data.error || 'Failed to save to memory', 'error');
        }
    })
    .catch(error => {
        console.error('Error saving to memory:', error);
        showNotification('Error: ' + error.message, 'error');
    });
}

/**
 * Set up event listeners for summarize form
 */
function setupSummarizeForm() {
    const form = document.getElementById('perplexity-summarize-form');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const topic = document.getElementById('summarize-topic').value.trim();
        const depth = document.getElementById('summarize-depth').value;
        
        if (!topic) {
            showNotification('Please enter a topic', 'error');
            return;
        }
        
        // Show loading state
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Summarizing...';
        }
        
        // Clear previous results
        const resultsContainer = document.getElementById('summarize-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = '<div class="loading-indicator">Generating summary...</div>';
        }
        
        // Get summary
        fetch('/api/perplexity/summarize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                topic: topic,
                depth: depth
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showNotification(data.error, 'error');
                if (resultsContainer) {
                    resultsContainer.innerHTML = `<div class="error-message">${data.error}</div>`;
                }
            } else {
                renderSummaryResults(data, resultsContainer);
            }
        })
        .catch(error => {
            console.error('Error getting summary:', error);
            showNotification('Error: ' + error.message, 'error');
            if (resultsContainer) {
                resultsContainer.innerHTML = `<div class="error-message">Error: ${error.message}</div>`;
            }
        })
        .finally(() => {
            // Reset button state
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = 'Summarize';
            }
        });
    });
}

/**
 * Render summary results in the container
 */
function renderSummaryResults(data, container) {
    if (!container) return;
    
    // Clear container
    container.innerHTML = '';
    
    // Create results header
    const header = document.createElement('div');
    header.className = 'results-header';
    header.innerHTML = `
        <h3>Summary of "${data.topic || ''}"</h3>
        <span class="summary-depth">${data.depth || 'medium'} depth</span>
    `;
    container.appendChild(header);
    
    // Create summary container
    const summaryContainer = document.createElement('div');
    summaryContainer.className = 'summary-container';
    
    // Add summary text
    if (data.summary) {
        const summaryText = document.createElement('div');
        summaryText.className = 'summary-text';
        summaryText.innerHTML = data.summary;
        summaryContainer.appendChild(summaryText);
    } else {
        const noSummary = document.createElement('div');
        noSummary.className = 'no-summary';
        noSummary.textContent = 'No summary available';
        summaryContainer.appendChild(noSummary);
    }
    
    // Add key points if available
    if (data.key_points && data.key_points.length > 0) {
        const keyPointsContainer = document.createElement('div');
        keyPointsContainer.className = 'key-points-container';
        keyPointsContainer.innerHTML = '<h4>Key Points</h4>';
        
        const keyPointsList = document.createElement('ul');
        keyPointsList.className = 'key-points-list';
        
        data.key_points.forEach(point => {
            const pointItem = document.createElement('li');
            pointItem.className = 'key-point-item';
            pointItem.textContent = point;
            keyPointsList.appendChild(pointItem);
        });
        
        keyPointsContainer.appendChild(keyPointsList);
        summaryContainer.appendChild(keyPointsContainer);
    }
    
    container.appendChild(summaryContainer);
    
    // Add save to memory button
    const saveButton = document.createElement('button');
    saveButton.className = 'btn save-to-memory';
    saveButton.innerHTML = '<i class="fas fa-brain"></i> Save to Memory';
    saveButton.addEventListener('click', function() {
        saveSummaryToMemory(data);
    });
    
    container.appendChild(saveButton);
}

/**
 * Save summary to memory
 */
function saveSummaryToMemory(data) {
    fetch('/api/memory/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            content: `Summary of "${data.topic}": ${data.summary}`,
            type: 'summary',
            metadata: {
                source: 'perplexity',
                topic: data.topic,
                depth: data.depth,
                timestamp: new Date().toISOString()
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Summary saved to memory', 'success');
        } else {
            showNotification(data.error || 'Failed to save to memory', 'error');
        }
    })
    .catch(error => {
        console.error('Error saving to memory:', error);
        showNotification('Error: ' + error.message, 'error');
    });
}

/**
 * Show a notification message
 */
function showNotification(message, type = 'info') {
    // Check if notification container exists, create if not
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        document.body.appendChild(container);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-message">${message}</div>
            <button class="notification-close">&times;</button>
        </div>
    `;
    
    // Add close functionality
    notification.querySelector('.notification-close').addEventListener('click', function() {
        notification.classList.add('fadeOut');
        setTimeout(() => {
            notification.remove();
        }, 300);
    });
    
    // Add to container
    container.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.add('fadeOut');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }
    }, 5000);
}

/**
 * VOT1 Perplexity Integration
 * 
 * This module provides Perplexity-style streaming animations and enhancements
 * for the VOT1 dashboard.
 */

// Initialize Perplexity features
function initializePerplexity() {
    console.log('Initializing Perplexity features...');
    
    // Configure streaming animations
    configureStreamingAnimations();
    
    // Set up event handlers
    setupPerplexityEventHandlers();
}

/**
 * Configure streaming animations for Perplexity-style responses
 * Based on design patterns from https://github.com/reworkd/perplexity-style-streaming
 */
function configureStreamingAnimations() {
    // Add CSS classes for animations if not already present
    if (!document.getElementById('perplexity-animations')) {
        const style = document.createElement('style');
        style.id = 'perplexity-animations';
        style.textContent = `
            @keyframes thinking-pulse {
                0% { opacity: 0.3; }
                50% { opacity: 1; }
                100% { opacity: 0.3; }
            }
            
            @keyframes text-cursor-blink {
                0% { border-right-color: transparent; }
                50% { border-right-color: var(--accent-color); }
                100% { border-right-color: transparent; }
            }
            
            .thinking-indicator {
                display: flex;
                align-items: center;
                margin-bottom: 10px;
                font-weight: 500;
                color: var(--text-color);
            }
            
            .thinking-dots {
                display: flex;
                margin-left: 10px;
            }
            
            .thinking-dot {
                width: 8px;
                height: 8px;
                margin: 0 3px;
                background-color: var(--accent-color);
                border-radius: 50%;
                animation: thinking-pulse 1.5s infinite ease-in-out;
            }
            
            .thinking-dot:nth-child(2) {
                animation-delay: 0.2s;
            }
            
            .thinking-dot:nth-child(3) {
                animation-delay: 0.4s;
            }
            
            .streaming-cursor {
                border-right: 2px solid var(--accent-color);
                animation: text-cursor-blink 1s infinite;
                padding-right: 2px;
                display: inline-block;
                height: 1.2em;
                vertical-align: text-bottom;
            }
            
            .progress-container {
                height: 4px;
                width: 100%;
                background-color: var(--background-secondary);
                margin-bottom: 15px;
                border-radius: 2px;
                overflow: hidden;
            }
            
            .progress-bar {
                height: 100%;
                width: 0%;
                background-color: var(--accent-color);
                transition: width 0.3s ease;
            }
            
            .reference-item {
                padding: 8px 12px;
                background-color: var(--background-secondary);
                border-radius: 6px;
                margin-bottom: 8px;
                border-left: 3px solid var(--accent-color);
                font-size: 0.9em;
                transition: all 0.2s ease;
            }
            
            .reference-item:hover {
                background-color: var(--background-hover);
            }
            
            .reference-item a {
                color: var(--accent-color);
                text-decoration: none;
                font-weight: 500;
            }
            
            .reference-item a:hover {
                text-decoration: underline;
            }
            
            .reference-item.processing {
                border-left-color: var(--warning-color);
            }
            
            .reference-item.completed {
                border-left-color: var(--success-color);
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * Set up event handlers for the Perplexity features
 */
function setupPerplexityEventHandlers() {
    // Handle search form submission
    $('#search-form').on('submit', function(e) {
        e.preventDefault();
        
        const query = $('#search-input').val().trim();
        if (!query) return;
        
        performPerplexitySearch(query);
    });
    
    // Handle MCP hybrid form submission
    $('#mcp-hybrid-form').on('submit', function(e) {
        e.preventDefault();
        
        const prompt = $('#mcp-hybrid-prompt').val().trim();
        if (!prompt) return;
        
        const useStreaming = $('#mcp-hybrid-stream').is(':checked');
        const temperature = parseFloat($('#mcp-hybrid-temperature').val());
        
        if (useStreaming) {
            performStreamingQuery(prompt, temperature);
        } else {
            performStandardQuery(prompt, temperature);
        }
    });
}

/**
 * Perform a Perplexity-style streaming search
 */
function performPerplexitySearch(query) {
    // Clear previous results
    $('#search-results').empty();
    
    // Create results container
    const resultsContainer = $(`
        <div class="search-results-container">
            <div class="thinking-indicator">
                <span>Searching the web</span>
                <div class="thinking-dots">
                    <div class="thinking-dot"></div>
                    <div class="thinking-dot"></div>
                    <div class="thinking-dot"></div>
                </div>
            </div>
            <div class="progress-container">
                <div class="progress-bar"></div>
            </div>
            <div class="references-container"></div>
            <div class="response-container"></div>
        </div>
    `);
    
    $('#search-results').append(resultsContainer);
    
    // Simulate streaming search response
    $.ajax({
        url: '/api/perplexity/search',
        method: 'POST',
        data: JSON.stringify({ query: query }),
        contentType: 'application/json',
        dataType: 'json',
        success: function(data) {
            handleStreamingSearchResponse(data);
        },
        error: function(xhr, status, error) {
            showNotification('Search failed: ' + error, 'error');
            $('.thinking-indicator').remove();
            $('.progress-container').remove();
        }
    });
}

/**
 * Handle streaming search response
 */
function handleStreamingSearchResponse(data) {
    // Update UI based on response stages
    if (data.status === 'thinking') {
        // Already showing thinking indicator
        $('.progress-bar').css('width', '10%');
        return;
    }
    
    if (data.status === 'processing') {
        $('.thinking-indicator span').text(data.message);
        $('.progress-bar').css('width', (data.progress * 100) + '%');
        
        // Add reference item if present
        if (data.current_reference) {
            const referenceItem = $(`
                <div class="reference-item processing">
                    <span>${data.current_reference}</span>
                </div>
            `);
            $('.references-container').append(referenceItem);
        }
        
        return;
    }
    
    if (data.status === 'responding') {
        $('.thinking-indicator span').text(data.message);
        $('.progress-bar').css('width', '80%');
        
        // Mark references as completed
        $('.reference-item').removeClass('processing').addClass('completed');
        
        // Prepare response container
        $('.response-container').html('<div class="response-content"></div><span class="streaming-cursor"></span>');
        
        return;
    }
    
    if (data.status === 'complete') {
        $('.progress-bar').css('width', (data.progress * 100) + '%');
        
        // Append chunk to response
        $('.response-content').append(data.chunk);
        
        // If progress is 100%, complete the response
        if (data.progress >= 0.99) {
            completeResponse();
        }
        
        return;
    }
}

/**
 * Complete the response
 */
function completeResponse() {
    // Remove thinking indicator and progress bar
    $('.thinking-indicator').remove();
    $('.progress-container').remove();
    
    // Remove streaming cursor
    $('.streaming-cursor').remove();
    
    // Convert markdown in response
    const responseHtml = marked.parse($('.response-content').html());
    $('.response-content').html(responseHtml);
    
    // Apply syntax highlighting
    document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
    
    // Add copy buttons to code blocks
    addCopyButtonsToCodeBlocks();
}

/**
 * Perform a streaming MCP hybrid query
 */
function performStreamingQuery(prompt, temperature) {
    // Clear previous results
    $('#mcp-hybrid-result').empty().show();
    
    // Create results container with streaming UI
    const resultsContainer = $(`
        <div class="mcp-results-container">
            <div class="thinking-indicator">
                <span>Thinking</span>
                <div class="thinking-dots">
                    <div class="thinking-dot"></div>
                    <div class="thinking-dot"></div>
                    <div class="thinking-dot"></div>
                </div>
            </div>
            <div class="progress-container">
                <div class="progress-bar"></div>
            </div>
            <div class="response-container"></div>
        </div>
    `);
    
    $('#mcp-hybrid-result').append(resultsContainer);
    
    // Disable submit button
    $('#mcp-hybrid-submit').prop('disabled', true).text('Processing...');
    
    // Call MCP hybrid API with streaming
    $.ajax({
        url: '/api/mcp-hybrid/query',
        method: 'POST',
        data: JSON.stringify({
            prompt: prompt,
            temperature: temperature,
            stream: true
        }),
        contentType: 'application/json',
        dataType: 'json',
        success: function(data) {
            handleStreamingMcpResponse(data);
        },
        error: function(xhr, status, error) {
            showNotification('Query failed: ' + error, 'error');
            $('#mcp-hybrid-submit').prop('disabled', false).text('Submit');
            $('.thinking-indicator, .progress-container').remove();
        }
    });
}

/**
 * Handle streaming MCP response
 */
function handleStreamingMcpResponse(data) {
    // Similar to search response handling
    if (data.status === 'thinking') {
        $('.progress-bar').css('width', '20%');
        return;
    }
    
    if (data.status === 'processing') {
        $('.thinking-indicator span').text('Processing');
        $('.progress-bar').css('width', (data.progress * 100) + '%');
        return;
    }
    
    if (data.status === 'responding') {
        $('.thinking-indicator span').text('Generating response');
        $('.progress-bar').css('width', '75%');
        $('.response-container').html('<div class="response-content"></div><span class="streaming-cursor"></span>');
        return;
    }
    
    if (data.status === 'complete') {
        $('.progress-bar').css('width', (data.progress * 100) + '%');
        $('.response-content').append(data.chunk);
        
        if (data.progress >= 0.99) {
            completeMcpResponse();
        }
        
        return;
    }
}

/**
 * Complete the MCP response
 */
function completeMcpResponse() {
    // Remove thinking indicator and progress bar
    $('.thinking-indicator, .progress-container').remove();
    $('.streaming-cursor').remove();
    
    // Convert markdown and apply syntax highlighting
    const responseHtml = marked.parse($('.response-content').html());
    $('.response-content').html(responseHtml);
    
    document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
    
    // Add copy buttons to code blocks
    addCopyButtonsToCodeBlocks();
    
    // Re-enable submit button
    $('#mcp-hybrid-submit').prop('disabled', false).text('Submit');
}

/**
 * Add copy buttons to code blocks
 */
function addCopyButtonsToCodeBlocks() {
    document.querySelectorAll('pre').forEach((block) => {
        if (!block.querySelector('.copy-button')) {
            const button = document.createElement('button');
            button.className = 'copy-button';
            button.textContent = 'Copy';
            
            button.addEventListener('click', () => {
                const code = block.querySelector('code').textContent;
                navigator.clipboard.writeText(code).then(() => {
                    button.textContent = 'Copied!';
                    setTimeout(() => {
                        button.textContent = 'Copy';
                    }, 2000);
                });
            });
            
            block.style.position = 'relative';
            block.prepend(button);
        }
    });
}

/**
 * Perform standard (non-streaming) query
 */
function performStandardQuery(prompt, temperature) {
    // Clear previous results
    $('#mcp-hybrid-result').empty().show();
    
    // Show loading indicator
    const loadingIndicator = $('<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> Processing...</div>');
    $('#mcp-hybrid-result').append(loadingIndicator);
    
    // Disable submit button
    $('#mcp-hybrid-submit').prop('disabled', true);
    
    // Call MCP hybrid API
    $.ajax({
        url: '/api/mcp-hybrid/query',
        method: 'POST',
        data: JSON.stringify({
            prompt: prompt,
            temperature: temperature,
            stream: false
        }),
        contentType: 'application/json',
        dataType: 'json',
        success: function(data) {
            // Remove loading indicator
            loadingIndicator.remove();
            
            // Display result
            const resultContainer = $('<div class="result-container"></div>');
            const resultContent = $('<div class="result-content"></div>');
            
            // Convert markdown and add to result
            resultContent.html(marked.parse(data.response));
            resultContainer.append(resultContent);
            $('#mcp-hybrid-result').append(resultContainer);
            
            // Apply syntax highlighting
            document.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
            
            // Add copy buttons to code blocks
            addCopyButtonsToCodeBlocks();
            
            // Re-enable submit button
            $('#mcp-hybrid-submit').prop('disabled', false);
        },
        error: function(xhr, status, error) {
            loadingIndicator.remove();
            showNotification('Query failed: ' + error, 'error');
            $('#mcp-hybrid-submit').prop('disabled', false);
        }
    });
} 