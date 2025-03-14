# OpenAPI Integration for VOT1

This document describes how to use the OpenAPI integration in VOT1.

## Overview

The OpenAPI integration allows you to import OpenAPI specifications into VOT1, which can then be used to create tools for your agents. These tools can be used to interact with external APIs and services.

## Importing OpenAPI Specifications

You can import OpenAPI specifications in two ways:

1. Using the dashboard UI
2. Using the command-line script

### Using the Dashboard UI

1. Navigate to the "Integrations" tab in the dashboard
2. Select the "Composio OpenAPI" tab
3. Click on the "Import OpenAPI Specification" button
4. Fill in the form with the following information:
   - Upload the OpenAPI specification file (YAML or JSON)
   - Optionally upload an authentication configuration file
   - Optionally provide a custom tool name, description, and tags
5. Click "Import" to start the import process

### Using the Command-Line Script

You can use the `import_openapi.py` script to import OpenAPI specifications from the command line:

```bash
python scripts/import_openapi.py --spec path/to/spec.yaml [--auth path/to/auth.yaml] [--name "Custom Tool Name"] [--description "Custom description"] [--tags tag1 tag2]
```

#### Arguments

- `--spec`, `-s`: Path to the OpenAPI specification file (required)
- `--auth`, `-a`: Path to the authentication configuration file (optional)
- `--name`, `-n`: Custom name for the tool (optional)
- `--description`, `-d`: Custom description for the tool (optional)
- `--tags`, `-t`: List of tags for the tool (optional)

## Authentication Configuration

The authentication configuration file is a YAML file that specifies how to authenticate with the API. It should contain the following fields:

```yaml
type: apiKey  # Authentication type (apiKey, http, oauth2)
in: header    # Where the authentication is applied (header, query, cookie)
name: X-API-Key  # Name of the authentication parameter
value: ${API_KEY}  # Value of the authentication parameter (can use environment variables)
description: API key for authentication  # Description of the authentication
```

## Using Imported Tools

Once you've imported an OpenAPI specification, you can use the tool in your agents. The tool will be available in the dashboard under the "Composio OpenAPI" tab.

### Viewing Tool Details

1. Navigate to the "Integrations" tab in the dashboard
2. Select the "Composio OpenAPI" tab
3. Find the tool in the list of imported tools
4. Click on the "View" button to see the tool details

### Executing Tool Actions

1. Navigate to the tool details page
2. Select an action from the dropdown menu
3. Enter the parameters for the action in JSON format
4. Click "Execute" to run the action

## Example

Here's an example of importing and using an OpenAPI specification:

1. Create an OpenAPI specification file:

```yaml
openapi: 3.0.0
info:
  title: Sample API
  description: A sample API for testing
  version: 1.0.0
paths:
  /items:
    get:
      summary: List all items
      operationId: listItems
      responses:
        '200':
          description: A list of items
```

2. Import the specification using the dashboard UI or command-line script

3. Use the tool in your agent:

```python
from src.vot1.integrations.composio import ComposioClient

client = ComposioClient()
tools = client.list_tools()

# Find the imported tool
sample_tool = next((tool for tool in tools.get('tools', []) if tool.get('name') == 'Sample API'), None)

if sample_tool:
    # Execute the listItems action
    result = client.execute_tool_action(
        tool_id=sample_tool['id'],
        action='listItems',
        parameters={}
    )
    print(result)
```

## Troubleshooting

If you encounter issues with the OpenAPI integration, check the following:

1. Make sure the OpenAPI specification is valid
2. Check that the authentication configuration is correct
3. Verify that the Composio API key is set in the environment variables
4. Check the logs for error messages

For more information, see the [Composio documentation](https://docs.composio.dev). 