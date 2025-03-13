# Composio Integration for VOT1

This package provides integration with Composio's API for various services, including text generation, embeddings, and model management.

## Features

- Connect to Composio's API using MCP (Model Control Plane)
- List available models and get model information
- Generate text using various models
- Create embeddings for text
- Check usage information
- Command-line interface for easy interaction

## Configuration

The integration can be configured in several ways:

1. **Environment Variables**:
   - `COMPOSIO_MCP_URL`: URL for the Composio MCP endpoint
   - `COMPOSIO_API_KEY`: API key for Composio

2. **Configuration File**:
   - The integration will look for a configuration file at `src/vot1/config/mcp.json`
   - The file should contain a `mcpServers` section with a `COMPOSIO` entry

Example configuration:

```json
{
  "mcpServers": {
    "COMPOSIO": {
      "url": "https://mcp.composio.dev/composio/your-account-id"
    }
  }
}
```

## Usage

### Python API

```python
from vot1.integrations.composio import ComposioClient
from vot1.integrations.composio.utils import generate_with_model, create_text_embedding

# Create a client
client = ComposioClient()

# Check connection
status = client.check_connection()
print(f"Connected: {status['connected']}")

# List models
models = client.list_models()
for model in models.get("models", []):
    print(f"Model: {model.get('name')}")

# Generate text
text, metadata = generate_with_model(
    prompt="Write a short poem about AI.",
    model_name="gpt-4",
    max_tokens=100,
    temperature=0.7
)
print(text)

# Create embedding
embedding, metadata = create_text_embedding(
    text="This is a sample text for embedding.",
    model_name="text-embedding-ada-002"
)
print(f"Embedding dimension: {len(embedding)}")
```

### Command-Line Interface

The integration includes a command-line interface for easy interaction with Composio.

```bash
# Check connection status
python scripts/composio_cli.py status

# List available models
python scripts/composio_cli.py models

# Get information about a specific model
python scripts/composio_cli.py model-info gpt-4

# Generate text
python scripts/composio_cli.py generate --prompt "Write a short poem about AI." --model gpt-4

# Create embedding
python scripts/composio_cli.py embedding --text "This is a sample text for embedding."

# Check usage information
python scripts/composio_cli.py usage
```

## Advanced Usage

### Custom MCP URL and API Key

You can specify a custom MCP URL and API key when creating a client:

```python
client = ComposioClient(
    mcp_url="https://mcp.composio.dev/composio/your-account-id",
    api_key="your-api-key"
)
```

### Formatting Usage Reports

The integration includes utilities for formatting usage reports:

```python
from vot1.integrations.composio.utils import get_daily_usage, format_usage_report

# Get usage data
usage_data = get_daily_usage()

# Format as a readable report
report = format_usage_report(usage_data)
print(report)
```

## Error Handling

All methods in the integration include robust error handling. If an error occurs, the methods will return a dictionary with an `error` key containing the error message.

```python
response = client.generate_text(prompt="Hello")
if "error" in response:
    print(f"Error: {response['error']}")
else:
    print(f"Generated text: {response.get('text', '')}")
```

## Development

To contribute to this integration, please follow these guidelines:

1. Add new features to the `client.py` module for core functionality
2. Add utility functions to the `utils.py` module
3. Update the CLI in `cli.py` for new commands
4. Update the README with new features and examples 