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