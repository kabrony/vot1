#!/bin/bash

# VOT1 Environment Setup Script
# This script sets up the necessary environment variables for VOT1

# Core VOT1 settings
export VOT1_PRIMARY_MODEL="anthropic/claude-3-7-sonnet-20240620"
export VOT1_MEMORY_DIR="./memory"
export VOT1_DEBUG=false

# MCP Configuration
export MCP_URL="https://mcp.composio.dev/github/victorious-damaged-branch-0ojHhf"
export PERPLEXITY_MCP_URL="https://mcp.composio.dev/perplexityai/plump-colossal-account-RTix4q"
export FIRECRAWL_MCP_URL="https://mcp.composio.dev/firecrawl/plump-colossal-account-RTix4q"
export FIGMA_MCP_URL="https://mcp.composio.dev/figma/plump-colossal-account-RTix4q"
export COMPOSIO_MCP_URL="https://mcp.composio.dev/composio/plump-colossal-account-RTix4q"

# GitHub Integration
# Replace with your actual GitHub token
export GITHUB_TOKEN="your_github_token_here"

# Composio Integration
# Replace with your actual Composio API key
export COMPOSIO_API_KEY="your_composio_api_key_here"

# Optional: Service-specific API Keys (if you have them)
export PERPLEXITY_API_KEY="your_perplexity_api_key_here"
export FIRECRAWL_API_KEY="your_firecrawl_api_key_here"
export FIGMA_API_KEY="your_figma_api_key_here"

# Feedback Loop Configuration
export FEEDBACK_LOOP_ENABLED=true
export FEEDBACK_LOOP_INTERVAL=3600  # In seconds (1 hour)

echo "VOT1 environment variables set successfully!"
echo "Primary Model: $VOT1_PRIMARY_MODEL"
echo "MCP URL: $MCP_URL"
echo "Perplexity MCP URL: $PERPLEXITY_MCP_URL"
echo "Firecrawl MCP URL: $FIRECRAWL_MCP_URL"
echo "Figma MCP URL: $FIGMA_MCP_URL"
echo "Composio MCP URL: $COMPOSIO_MCP_URL"
echo "Debug Mode: $VOT1_DEBUG"
echo "Feedback Loop: $([ "$FEEDBACK_LOOP_ENABLED" == "true" ] && echo "Enabled" || echo "Disabled")"

# Check if required variables are set
if [ -z "$GITHUB_TOKEN" ] || [ "$GITHUB_TOKEN" == "your_github_token_here" ]; then
  echo "WARNING: GitHub token not set. GitHub integration will be limited."
fi

if [ -z "$COMPOSIO_API_KEY" ] || [ "$COMPOSIO_API_KEY" == "your_composio_api_key_here" ]; then
  echo "WARNING: Composio API key not set. OpenAPI integration will be limited."
fi 