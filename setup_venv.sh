#!/bin/bash
# Setup script for Enhanced Research Agent virtual environment

# Colors for better visibility
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up virtual environment for Enhanced Research Agent...${NC}"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment.${NC}"
        exit 1
    fi
fi

# Activate virtual environment and install packages
echo -e "${YELLOW}Activating virtual environment and installing required packages...${NC}"
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to activate virtual environment.${NC}"
    exit 1
fi

# Install required packages
pip install --upgrade pip
pip install anthropic python-dotenv perplexipy requests

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file template...${NC}"
    cat > .env << EOL
# API Keys for Enhanced Research Agent
# Fill in your API keys below

# Required: Anthropic API Key for Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Required: Perplexity API Key for web research
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Optional: GitHub Token for code search
GITHUB_TOKEN=your_github_token_here

# Optional: Composio API Key for MCP integration
COMPOSIO_API_KEY=your_composio_api_key_here
COMPOSIO_MCP_URL=your_composio_mcp_url_here

# System Configuration
MEMORY_PATH=memory/agent
HEALTH_CHECK_INTERVAL=60
ENABLE_AUTO_REPAIR=true
ENABLE_AUTONOMOUS_MODE=false
EOL
    echo -e "${YELLOW}Please edit the .env file and add your API keys.${NC}"
else
    echo -e "${GREEN}.env file already exists.${NC}"
fi

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p output
mkdir -p memory/agent

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}To activate the virtual environment, run:${NC} source venv/bin/activate"
echo -e "${YELLOW}To run the enhanced research agent, run:${NC} python enhanced_research_agent.py --topic \"Your research topic\" --focus \"Your research focus\"" 