#!/bin/bash
#
# VOT1 Environment Setup Script
#
# This script sets up the environment for VOT1, including:
# - Python virtual environment
# - Required packages
# - Directory structure
# - API keys and configuration

# Exit on error
set -e

# Set script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create or update virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
source venv/bin/activate

# Install required packages
echo "Installing required packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p memory/vector_store
mkdir -p memory/composio
mkdir -p logs

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file to add your API keys."
else
    echo ".env file already exists."
fi

# Load environment variables
echo "Loading environment variables..."
export $(grep -v '^#' .env | xargs)

# Configure memory paths
if [ -z "$VOT1_MEMORY_PATH" ]; then
    echo "Setting VOT1_MEMORY_PATH in .env..."
    # Use sed to add or update the VOT1_MEMORY_PATH
    if grep -q "VOT1_MEMORY_PATH=" .env; then
        sed -i "s|VOT1_MEMORY_PATH=.*|VOT1_MEMORY_PATH=$SCRIPT_DIR/memory|g" .env
    else
        echo "VOT1_MEMORY_PATH=$SCRIPT_DIR/memory" >> .env
    fi
fi

# Generate a random secret key for Flask if not exists
if grep -q "FLASK_SECRET_KEY=generate_a_random_secret_key" .env; then
    echo "Generating Flask secret key..."
    FLASK_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(24))")
    sed -i "s|FLASK_SECRET_KEY=generate_a_random_secret_key|FLASK_SECRET_KEY=$FLASK_SECRET_KEY|g" .env
fi

# Check for required API keys
echo "Checking API keys..."
MISSING_KEYS=0

if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" == "your_anthropic_api_key_here" ]; then
    echo "WARNING: ANTHROPIC_API_KEY is not set. Claude models will not work."
    MISSING_KEYS=1
fi

if [ -z "$PERPLEXITY_API_KEY" ] || [ "$PERPLEXITY_API_KEY" == "your_perplexity_api_key_here" ]; then
    echo "WARNING: PERPLEXITY_API_KEY is not set. Perplexity models will not work."
    MISSING_KEYS=1
fi

if [ -z "$COMPOSIO_API_KEY" ] || [ "$COMPOSIO_API_KEY" == "your_composio_api_key_here" ]; then
    echo "WARNING: COMPOSIO_API_KEY is not set. Composio MCP integration will not work."
    MISSING_KEYS=1
fi

if [ "$MISSING_KEYS" -eq 1 ]; then
    echo "Some API keys are missing. Please edit the .env file to add your API keys."
fi

# Set up Composio MCP integration
if [ -f "setup_mcp.sh" ]; then
    echo "Do you want to set up Composio MCP integration? (y/n)"
    read -r SETUP_MCP
    if [ "$SETUP_MCP" == "y" ] || [ "$SETUP_MCP" == "Y" ]; then
        echo "Setting up Composio MCP integration..."
        bash setup_mcp.sh
    else
        echo "Skipping Composio MCP setup."
    fi
fi

# Install the package in development mode
echo "Installing VOT1 in development mode..."
pip install -e .

echo "Environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure your API keys are set in .env"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Run the dashboard: python -m vot1.dashboard"
echo ""
