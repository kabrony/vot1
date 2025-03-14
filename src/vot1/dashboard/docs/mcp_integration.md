# Machine Capability Provider (MCP) Integration

## Overview

The Machine Capability Provider (MCP) integration system extends the VOT1 Dashboard with powerful external capabilities such as web research via Perplexity AI and web crawling via Firecrawl. This system seamlessly integrates these services into the cyberpunk chat interface, enabling a more comprehensive AI assistant experience through a hybrid approach that combines Claude 3.7's reasoning with specialized external services.

## Core Components

The MCP integration consists of several key components:

### 1. Backend Integration Layer

#### 1.1. MCP Handler (`mcp_handler.py`)
- Simulation API for development and testing
- Provides mock responses for MCP functions
- Enables development without active MCP connections

#### 1.2. Production Handler (`mcp_handler_production.py`)
- Production-ready API for real MCP connections
- Direct integration with external services
- Secure API key management and error handling

#### 1.3. MCP Tools Utility (`mcp_tools.py`)
- Dynamic function discovery and calling
- Error handling and logging
- Mock response generation for development

#### 1.4. Hybrid API (`mcp_hybrid_api.py`)
- Combines Claude capabilities with MCP functions
- Manages the flow between different services
- Optimizes token usage and response quality

### 2. Frontend Integration Layer

#### 2.1. MCP Integration Module (`mcp-integration.js`)
- JavaScript interface for MCP services
- Connection management and status tracking
- Command handlers for research and crawling
- UI components for connection status and results

#### 2.2. UI Components
- MCP Status Bar: Visual indicators of connection status
- Connection Modal: Interface for connecting services
- Research Results: Formatted display of research findings
- Settings Controls: Configuration for MCP behavior

## Supported MCPs

### 1. Perplexity AI

Perplexity AI is integrated as a powerful research tool that can search the web for up-to-date information.

#### Key Features:
- **Web Research**: Find current information on any topic
- **Deep Analysis**: Generate comprehensive summaries of findings
- **Citation Support**: Track sources for all information
- **Flexible Depth**: Adjust research depth based on needs

#### Connection Process:
1. Check connection status via API
2. Connect through OAuth or API key (depends on configuration)
3. Verify connection and update status indicators

#### Usage:
The Perplexity integration can be used through:
- `/research [query]` command in the chat interface
- Hybrid mode, which automatically researches complex topics
- Direct API calls for programmatic usage

### 2. Firecrawl

Firecrawl is integrated as a web crawling service that can extract content from websites and process structured data.

#### Key Features:
- **Website Crawling**: Extract content from specified URLs
- **Structured Data Extraction**: Parse specific data from websites
- **Recursive Crawling**: Follow links to gather comprehensive information
- **Content Processing**: Filter and clean extracted content

#### Connection Process:
1. Check connection status via API
2. Connect using Firecrawl API key
3. Verify connection and update status indicators

#### Usage:
The Firecrawl integration can be used through:
- `/crawl [url]` command in the chat interface
- Direct API calls for programmatic usage
- Structured data extraction requests

## Architecture

### Connection Management

The MCP system implements a robust connection management architecture:

1. **Connection Checking**:
   - Periodic status checks for all MCPs
   - Cache for connection status to reduce API calls
   - Event-based updates when connection status changes

2. **Connection Establishment**:
   - Service-specific connection protocols
   - Secure handling of authentication credentials
   - Retry logic for failed connection attempts

3. **Connection Persistence**:
   - Session-based connection tracking
   - Connection recovery after interruptions
   - Graceful degradation when services are unavailable

### Request Handling

Requests to MCPs follow a standardized flow:

1. **Request Validation**:
   - Parameter validation before sending
   - Rate limiting to prevent abuse
   - Quota management for API usage

2. **Request Routing**:
   - Dynamic routing based on service capabilities
   - Fallback strategies for unavailable services
   - Parallel requests for time-sensitive operations

3. **Response Processing**:
   - Standardized response format conversion
   - Error handling and retry mechanisms
   - Caching of results for similar queries

### Hybrid Mode

The hybrid mode combines Claude's capabilities with MCP services:

1. **Query Analysis**:
   - Determine if external data would enhance the response
   - Identify which MCP would provide the most relevant information
   - Formulate optimal queries for each service

2. **Enhanced Responses**:
   - Integrate MCP data with Claude's reasoning
   - Attribute information to appropriate sources
   - Maintain conversation context across service boundaries

3. **Fallback Mechanisms**:
   - Graceful degradation when MCPs are unavailable
   - Use of cached data when appropriate
   - Clear communication about information sources and limitations

## API Reference

### Backend API Endpoints

#### MCP Status

```
GET /api/mcp/status
```

Returns the status of all configured MCPs:

```json
{
  "perplexity": {
    "connected": true,
    "status": "active",
    "connectionId": "perplexity-conn-123"
  },
  "firecrawl": {
    "connected": false,
    "status": "disconnected",
    "error": null
  }
}
```

#### Perplexity Connection

```
POST /api/mcp/perplexity/connect
```

Initiates a connection to Perplexity AI.

#### Perplexity Search

```
POST /api/mcp/perplexity/search
```

Request body:
```json
{
  "query": "Latest developments in quantum computing",
  "options": {
    "depth": "deep",
    "max_tokens": 4000,
    "return_citations": true
  }
}
```

Returns research results with citations.

#### Firecrawl Connection

```
POST /api/mcp/firecrawl/connect
```

Request body:
```json
{
  "api_key": "your_firecrawl_api_key"
}
```

Initiates a connection to Firecrawl.

#### Firecrawl Crawl

```
POST /api/mcp/firecrawl/crawl
```

Request body:
```json
{
  "url": "https://example.com",
  "options": {
    "max_depth": 2,
    "max_pages": 10,
    "include_paths": ["blog/*"],
    "exclude_paths": ["admin/*"]
  }
}
```

Returns crawl results.

### JavaScript API

The MCP integration exposes a JavaScript API for frontend usage:

```javascript
// Initialize MCP integration
mcpIntegration.initialize();

// Check connection status
const status = await mcpIntegration.checkStatus();

// Connect to Perplexity
await mcpIntegration.connectToPerplexity();

// Connect to Firecrawl
await mcpIntegration.connectToFirecrawl({ api_key: "your_key" });

// Search with Perplexity
const results = await mcpIntegration.search("quantum computing", {
  depth: "deep",
  return_citations: true
});

// Crawl with Firecrawl
const crawlResults = await mcpIntegration.crawl("https://example.com", {
  max_depth: 2,
  max_pages: 10
});

// Toggle hybrid mode
mcpIntegration.setHybridMode(true);
```

### Python API

For programmatic usage from Python code:

```python
from vot1.dashboard.utils.mcp_tools import call_mcp_function

# Check Perplexity connection
response = call_mcp_function("mcp_PERPLEXITY_PERPLEXITYAI_CHECK_ACTIVE_CONNECTION", {
    "params": {"tool": "PERPLEXITYAI"}
})

# Search with Perplexity
response = call_mcp_function("mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH", {
    "params": {
        "systemContent": "You are a research assistant providing factual information.",
        "userContent": "What are the latest developments in quantum computing?",
        "temperature": 0.7,
        "max_tokens": 4000,
        "return_citations": True
    }
})

# Crawl with Firecrawl
response = call_mcp_function("mcp_FIRECRAWL_FIRECRAWL_CRAWL_URLS", {
    "params": {
        "url": "https://example.com",
        "limit": 10,
        "maxDepth": 2,
        "allowExternalLinks": False
    }
})
```

## Configuration Options

The MCP integration can be configured using environment variables or through the application configuration:

### Environment Variables

```
# Perplexity Configuration
PERPLEXITY_API_KEY=your_perplexity_api_key
PERPLEXITY_DEFAULT_MODEL=pplx-70b-online

# Firecrawl Configuration
FIRECRAWL_API_KEY=your_firecrawl_api_key
FIRECRAWL_DEFAULT_LIMIT=10

# Hybrid Mode Configuration
MCP_HYBRID_MODE_ENABLED=true
MCP_AUTO_RESEARCH_ENABLED=true
```

### Application Configuration

```python
mcp_hybrid_options = {
    "enabled": True,  # Enable MCP by default
    "primary_model": "claude-3-7-sonnet-20240620",
    "secondary_model": "claude-3-5-sonnet-20240620",
    "use_extended_thinking": True,
    "max_thinking_tokens": 60000,
    "enable_streaming": True,
    "perplexity_integration": True,
    "firecrawl_integration": True,
    "auto_research_threshold": 0.7,  # Threshold for automatic research
    "research_depth_mapping": {
        "simple": "basic",
        "complex": "deep",
        "default": "medium"
    }
}
```

## UI Components

### MCP Status Bar

The MCP Status Bar displays the current status of all MCPs:

```html
<div id="mcp-status-bar" class="mcp-status-bar">
    <div class="mcp-status-item">
        <i class="fas fa-brain"></i>
        <span class="mcp-label">Claude 3.7</span>
        <span id="claude-status" class="status-indicator connected">ACTIVE</span>
    </div>
    <div class="mcp-status-item">
        <i class="fas fa-search"></i>
        <span class="mcp-label">Perplexity</span>
        <span id="perplexity-status" class="status-indicator">checking...</span>
    </div>
    <div class="mcp-status-item">
        <i class="fas fa-spider"></i>
        <span class="mcp-label">Firecrawl</span>
        <span id="firecrawl-status" class="status-indicator">checking...</span>
    </div>
    <div class="mcp-actions">
        <button id="mcp-connect-button" class="mcp-connect-btn" title="Connect Tools">
            <i class="fas fa-plug"></i>
        </button>
    </div>
</div>
```

### Connection Modal

The Connection Modal allows users to connect to MCPs:

```html
<div id="mcp-connect-modal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>Connect MCP Tools</h3>
            <button class="close-modal">&times;</button>
        </div>
        <div class="modal-body">
            <div class="settings-section">
                <h4>Perplexity AI</h4>
                <div class="setting-item status-container">
                    <span class="status-label">Status:</span>
                    <span id="perplexity-modal-status" class="status-value">Not Connected</span>
                </div>
                <div class="setting-item">
                    <button id="connect-perplexity" class="btn-primary">Connect to Perplexity</button>
                </div>
            </div>
            
            <div class="settings-section">
                <h4>Firecrawl</h4>
                <div class="setting-item status-container">
                    <span class="status-label">Status:</span>
                    <span id="firecrawl-modal-status" class="status-value">Not Connected</span>
                </div>
                <div class="setting-item">
                    <label for="firecrawl-api-key">API Key</label>
                    <input type="password" id="firecrawl-api-key" placeholder="Enter your Firecrawl API key">
                </div>
                <div class="setting-item">
                    <button id="connect-firecrawl" class="btn-primary">Connect to Firecrawl</button>
                </div>
            </div>
        </div>
    </div>
</div>
```

### Research Results

Research results are displayed with proper formatting and citations:

```html
<div class="research-result">
    <div class="research-header">
        <div class="research-icon">
            <i class="fas fa-search"></i>
        </div>
        <div class="research-title">Research Results</div>
    </div>
    <div class="research-content">
        <!-- Research content goes here -->
    </div>
    <div class="research-citations">
        <h4>Sources</h4>
        <ul class="citation-list">
            <!-- Citations go here -->
        </ul>
    </div>
</div>
```

## Integration with Claude 3.7

The MCP system integrates with Claude 3.7 in several ways:

### 1. Hybrid Processing

The hybrid processing mode enables Claude to access external information:

1. **Query Analysis**: Claude analyzes the user query to determine if external information would be beneficial
2. **MCP Selection**: The system selects the appropriate MCP based on the query type
3. **Context Augmentation**: External information is added to Claude's context
4. **Integrated Response**: Claude generates a response incorporating the external information

### 2. Command Handling

The chat interface processes commands related to MCPs:

1. **Command Detection**: The interface detects commands like `/research` and `/crawl`
2. **Parameter Extraction**: Command parameters are extracted and validated
3. **MCP Invocation**: The appropriate MCP function is called
4. **Result Formatting**: Results are formatted and displayed in the chat

### 3. Thinking Visualization

The thinking visualization system shows how Claude incorporates MCP data:

1. **MCP Data Nodes**: External information appears as distinct nodes
2. **Connection Visualization**: Connections between Claude's thinking and MCP data
3. **Source Attribution**: Clear visual indication of information sources
4. **Integration Points**: Visualization of how external data influences reasoning

## Development Workflow

### Adding a New MCP

To add a new MCP to the system:

1. **Backend Implementation**:
   - Create handler functions in `mcp_handler_production.py`
   - Register the MCP functions in `mcp_tools.py`
   - Implement mock responses for development

2. **Frontend Integration**:
   - Add connection management to `mcp-integration.js`
   - Create UI components for status and configuration
   - Implement command handlers if needed

3. **Documentation**:
   - Update API documentation
   - Add usage examples
   - Document configuration options

### Testing MCPs

The development workflow includes several testing approaches:

1. **Mock Mode Testing**:
   - Use the mock mode to simulate MCP responses
   - Test UI components with simulated data
   - Verify error handling with simulated failures

2. **Integration Testing**:
   - Test with real MCP connections
   - Verify authentication and data flow
   - Test error handling with intentional failures

3. **UI Testing**:
   - Test status indicators and modals
   - Verify command processing
   - Test result formatting and display

## Best Practices

### Security Considerations

When working with MCPs, follow these security practices:

1. **API Key Management**:
   - Never expose API keys in client-side code
   - Store keys securely in environment variables
   - Rotate keys periodically

2. **Data Validation**:
   - Validate all user inputs before sending to MCPs
   - Sanitize data returned from MCPs
   - Implement rate limiting to prevent abuse

3. **Error Handling**:
   - Handle authentication failures gracefully
   - Provide clear user feedback for errors
   - Log errors for debugging without exposing sensitive information

### Performance Optimization

Optimize MCP usage with these techniques:

1. **Caching**:
   - Cache frequently used research results
   - Implement an LRU cache for recent queries
   - Use time-based cache invalidation for time-sensitive data

2. **Request Batching**:
   - Batch multiple requests when possible
   - Combine similar queries to reduce API calls
   - Implement request deduplication

3. **Resource Management**:
   - Monitor API rate limits
   - Implement backoff strategies for rate limiting
   - Allocate resources based on query importance

### User Experience

Ensure a good user experience with these practices:

1. **Status Transparency**:
   - Clearly indicate connection status
   - Show loading indicators during requests
   - Provide feedback for connection failures

2. **Result Formatting**:
   - Format research results for readability
   - Highlight key information
   - Provide clear attribution of sources

3. **Graceful Degradation**:
   - Handle disconnected services gracefully
   - Provide alternatives when services are unavailable
   - Clearly communicate limitations

## Advanced Usage

### Custom MCP Commands

Create custom commands for specific MCP functionality:

```javascript
// Register a custom command for specialized research
function registerCustomCommands() {
    chatCommands.register({
        name: "technical-research",
        description: "Perform technical research with code examples",
        handler: handleTechnicalResearch
    });
}

async function handleTechnicalResearch(args) {
    // Custom research with code focus
    const query = `Technical implementation of ${args.join(' ')} with code examples`;
    const options = {
        depth: "deep",
        model: "pplx-70b-online",
        systemContent: "You are a technical expert. Provide detailed explanations with code examples."
    };
    
    return await mcpIntegration.search(query, options);
}
```

### MCP Chaining

Chain multiple MCPs together for complex workflows:

```javascript
async function researchAndCrawl(topic) {
    // First, research to find relevant URLs
    const research = await mcpIntegration.search(`Best websites about ${topic}`);
    
    // Extract URLs from research
    const urlRegex = /https?:\/\/[^\s]+/g;
    const urls = research.content.match(urlRegex) || [];
    
    // Crawl the top 3 URLs
    const crawlResults = [];
    for (let i = 0; i < Math.min(3, urls.length); i++) {
        const result = await mcpIntegration.crawl(urls[i], { max_depth: 1 });
        crawlResults.push(result);
    }
    
    return {
        research: research,
        crawlResults: crawlResults
    };
}
```

### Customized Research Profiles

Create research profiles for different types of queries:

```javascript
const researchProfiles = {
    technical: {
        systemContent: "You are a technical expert. Provide detailed technical information with code examples where appropriate.",
        model: "pplx-70b-online",
        temperature: 0.3,
        max_tokens: 4000
    },
    academic: {
        systemContent: "You are an academic researcher. Provide comprehensive analysis with citations to academic literature.",
        model: "pplx-70b-online",
        temperature: 0.2,
        max_tokens: 5000
    },
    business: {
        systemContent: "You are a business analyst. Provide market insights and business strategy recommendations.",
        model: "pplx-70b-online",
        temperature: 0.5,
        max_tokens: 3000
    }
};

async function profiledSearch(query, profileName) {
    const profile = researchProfiles[profileName] || researchProfiles.technical;
    return await mcpIntegration.search(query, profile);
}
```

## Troubleshooting

### Common Connection Issues

1. **Authentication Failures**:
   - Verify API keys are correct
   - Check for expired or revoked credentials
   - Ensure necessary permissions are granted

2. **Network Problems**:
   - Check internet connectivity
   - Verify firewall settings
   - Check for proxy configuration issues

3. **Rate Limiting**:
   - Monitor API usage
   - Implement request throttling
   - Use exponential backoff for retries

### Debugging Strategies

1. **Console Logging**:
   - Enable debug logging in browser console
   - Check network requests and responses
   - Verify request parameters

2. **Server Logs**:
   - Check Flask server logs
   - Monitor API endpoint access
   - Track authentication attempts

3. **MCP Status Checks**:
   - Use the status API to verify connections
   - Check service health status pages
   - Verify API key validity

## Conclusion

The Machine Capability Provider (MCP) integration system significantly enhances the VOT1 Dashboard by connecting it to powerful external services like Perplexity AI and Firecrawl. This hybrid approach combines Claude 3.7's reasoning capabilities with specialized external services, creating a more comprehensive AI assistant experience.

The modular architecture allows for easy addition of new MCPs, while the robust connection management system ensures reliable operation. The user interface provides clear visibility into MCP status and seamless access to their capabilities through the chat interface.

By following the best practices and utilizing the advanced features described in this documentation, you can leverage the full power of the MCP integration system to create rich, interactive experiences that go beyond the capabilities of any single AI system. 