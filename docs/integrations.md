# VOT1 External Integrations

VOT1 provides powerful integration capabilities with external services through its dashboard interface. This document explains how to use and configure these integrations.

## Table of Contents

- [OpenAPI Integration with Composio](#openapi-integration-with-composio)
  - [Setting Up OpenAPI Integration](#setting-up-openapi-integration)
  - [Importing API Specifications](#importing-api-specifications)
  - [Using OpenAPI Tools](#using-openapi-tools)
  - [Troubleshooting](#troubleshooting-openapi)
- [GitHub Integration](#github-integration)
  - [Connection Setup](#connection-setup)
  - [Repository Analysis](#repository-analysis)
  - [Analysis Types](#analysis-types)
  - [Viewing Analysis Results](#viewing-analysis-results)
  - [Troubleshooting GitHub Integration](#troubleshooting-github)
- [Integration with AI Chat](#integration-with-ai-chat)
  - [Using Tools via Chat](#using-tools-via-chat)
- [API Reference](#api-reference)

## OpenAPI Integration with Composio

VOT1 integrates with Composio to enable importing and using external APIs through OpenAPI specifications. This allows the system to interact with a wide range of services and tools.

### Setting Up OpenAPI Integration

To use the OpenAPI integration:

1. Ensure you have a valid Composio API key configured in your environment:
   ```
   export COMPOSIO_API_KEY=your_api_key_here
   ```

2. Restart the VOT1 system or reload the configuration to apply the API key.

3. Navigate to the Integrations tab in the VOT1 dashboard and select the "Composio OpenAPI" tab.

4. Verify the connection status shows "Connected" with a green status indicator.

### Importing API Specifications

To import an OpenAPI specification:

1. Obtain an OpenAPI specification file (YAML or JSON format) for the API you want to integrate.

2. In the "Import OpenAPI Specification" section:
   - Upload the specification file
   - Optionally upload an authentication configuration file (if required by the API)
   - Provide a custom name for the tool (optional)
   - Add a description and tags for better organization

3. Click "Import OpenAPI Spec" to process the import.

4. The system will validate and import the specification, making it available as a tool.

#### Authentication Configuration

For APIs requiring authentication, create a JSON configuration file with the following structure:

```json
{
  "type": "api_key",
  "api_key": {
    "location": "header",
    "name": "Authorization",
    "value": "Bearer your_api_key_here"
  }
}
```

Supported authentication types:
- `api_key`: API key in header, query, or cookie
- `http_basic`: Basic authentication with username and password
- `oauth2`: OAuth 2.0 authentication (client credentials flow)

### Using OpenAPI Tools

After importing APIs, you can:

1. View all imported tools in the "Imported OpenAPI Tools" section.

2. Click the eye icon to view details about a specific tool, including available actions and parameters.

3. Execute actions directly from the interface:
   - Select an action from the dropdown
   - Provide required parameters in JSON format
   - Click "Execute" to run the action
   - View the results displayed below

4. Use tools programmatically through the VOT1 API or via the AI chat interface.

### Troubleshooting OpenAPI

Common issues and solutions:

- **Connection Failed**: Verify your Composio API key is valid and properly configured.
- **Import Failed**: Ensure the OpenAPI specification is valid and complies with the OpenAPI 3.0 standard.
- **Authentication Error**: Check that the authentication configuration matches the requirements of the API.
- **Execution Failed**: Verify the parameters match the expected format and all required parameters are provided.

## GitHub Integration

VOT1 provides GitHub integration for analyzing repositories, tracking code quality, and receiving development insights.

### Connection Setup

To connect to GitHub:

1. Configure your GitHub credentials either through:
   - Environment variables:
     ```
     export GITHUB_TOKEN=your_personal_access_token
     export GITHUB_USERNAME=your_username
     ```
   - The VOT1 configuration file:
     ```yaml
     integrations:
       github:
         token: your_personal_access_token
         username: your_username
     ```

2. Restart VOT1 or reload the configuration to apply the changes.

3. Navigate to the "GitHub" tab in the Integrations section of the dashboard.

4. Verify the connection status shows "Connected as [username]".

### Repository Analysis

To analyze a GitHub repository:

1. In the Repository Analysis section, enter:
   - Repository Owner/Organization name
   - Repository Name
   - Select Analysis Type

2. Click "Analyze Repository" to start the analysis.

3. The system will queue the analysis and display its status in the Recent Analyses section.

### Analysis Types

VOT1 supports several types of repository analyses:

- **Standard Analysis**: General overview of code structure, quality metrics, and basic insights
- **Deep Analysis**: Comprehensive analysis including architecture evaluation, code patterns, and detailed quality metrics
- **Code Quality Focus**: Emphasis on code quality metrics, test coverage, and improvement recommendations
- **Security Focus**: Analysis of security vulnerabilities, dependency issues, and security best practices

### Viewing Analysis Results

Analysis results are available:

1. In the "Recent Analyses" section, click "View Results" for a completed analysis.

2. The results include:
   - Summary of repository statistics
   - Code quality metrics
   - Identified issues and recommendations
   - Architecture diagrams (for Deep Analysis)
   - Security findings (for Security Focus)

3. Results can be exported in various formats including PDF, JSON, and HTML.

### Troubleshooting GitHub

Common issues and solutions:

- **Connection Failed**: Verify your GitHub token has the necessary permissions for the repositories.
- **Analysis Failed**: Check that the repository exists and you have access to it.
- **Rate Limit Exceeded**: GitHub API has rate limits; try again later or use a token with higher limits.
- **Incomplete Results**: For large repositories, some analyses may time out; try a more focused analysis type.

## Integration with AI Chat

VOT1's AI chat interface can interact with both GitHub and OpenAPI integrations, providing a natural language interface to these tools.

### Using Tools via Chat

To use integrations through the chat interface:

1. Enable the Composio toggle in the chat settings panel.

2. Ask the assistant to use a specific tool:
   ```
   Could you check the weather in San Francisco using the weather API?
   ```

3. For GitHub functionality:
   ```
   Analyze the code quality of the username/repo repository
   ```
   ```
   Show me recent commits in the username/repo repository
   ```

4. The assistant will utilize the appropriate integration to execute your request and return formatted results.

## API Reference

For programmatic access to integrations, VOT1 provides the following API endpoints:

### OpenAPI Endpoints

- `GET /api/openapi/tools`: List all imported OpenAPI tools
- `POST /api/openapi/tools`: Import a new OpenAPI specification
- `GET /api/openapi/tools/<tool_id>`: Get details of a specific tool
- `POST /api/openapi/tools/<tool_id>`: Execute an action on a tool
- `DELETE /api/openapi/tools/<tool_id>`: Delete an imported tool
- `GET /api/openapi/status`: Check Composio connection status
- `GET /api/openapi/usage`: Check daily repository usage

### GitHub Endpoints

- `GET /api/integrations/github/status`: Check GitHub connection status
- `POST /api/integrations/github/analyze`: Start a repository analysis
- `GET /api/integrations/github/analyses`: List recent analyses
- `GET /api/integrations/github/analyses/<analysis_id>`: Get analysis results
- `GET /api/integrations/github/repositories`: List accessible repositories 