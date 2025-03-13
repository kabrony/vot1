#!/bin/bash

# VOT1 Repository Setup Script
# This script sets up the VOT1 repository with all necessary components
# Usage: ./setup_repository.sh

set -e  # Exit immediately if a command exits with a non-zero status

# Display ASCII art
echo "=============================================================="
echo "  _    __    ____  ______   __   "
echo " | |  / /__ / __ \/_  __/  / /   "
echo " | | / / _ \ / / / / /     / /    "
echo " | |/ /  __/ /_/ / / /    /_/     "
echo " |___/\___/\____/ /_/    (_)      "
echo "                                  "
echo "=============================================================="
echo "              Repository Setup Script                         "
echo "=============================================================="
echo ""

# Check if script is run with root privileges
if [ "$(id -u)" -eq 0 ]; then
    echo "⚠️  Warning: This script should not be run with sudo."
    echo "    Running with sudo might cause permission issues."
    read -p "Do you want to continue anyway? (y/N): " choice
    if [[ ! "$choice" =~ ^[yY]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
echo "🔍 Checking for required tools..."
REQUIRED_TOOLS=("git" "python3" "pip" "npm" "node")
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command_exists "$tool"; then
        MISSING_TOOLS+=("$tool")
    fi
done

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo "❌ The following required tools are missing:"
    for tool in "${MISSING_TOOLS[@]}"; do
        echo "   - $tool"
    done
    echo ""
    echo "⚠️  Please install these tools and run the script again."
    echo "   On Ubuntu/Debian: sudo apt-get update && sudo apt-get install git python3 python3-pip nodejs npm"
    echo "   On macOS with Homebrew: brew install git python node npm"
    exit 1
fi

# Create virtual environment if it doesn't exist
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created."
else
    echo "✅ Virtual environment already exists."
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# If there's a scripts/requirements.txt, install those too
if [ -f "scripts/requirements.txt" ]; then
    echo "📦 Installing script-specific dependencies..."
    pip install -r scripts/requirements.txt
fi

# Set up Git hooks
echo "🔄 Setting up Git hooks..."
mkdir -p .git/hooks

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
set -e

# Run linting checks before commit
echo "Running pre-commit checks..."

# Check for Python syntax errors
echo "Checking for Python syntax errors..."
find . -name "*.py" -not -path "./venv/*" -not -path "*/\.*" | xargs python -m pylint --errors-only

# Run tests
echo "Running tests..."
python -m pytest tests/ -v

echo "Pre-commit checks completed successfully."
EOF

chmod +x .git/hooks/pre-commit

# Create post-commit hook
cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash
set -e

echo "🔄 Running post-commit tasks..."
# Additional post-commit tasks can be added here
EOF

chmod +x .git/hooks/post-commit

# Set up environment variables
echo "🔧 Setting up environment variables..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file from template."
        echo "⚠️  Remember to update the values in .env with your actual credentials."
    else
        echo "❌ .env.example not found. Please create a .env file manually."
    fi
fi

if [ ! -f ".github_automation.env" ]; then
    if [ -f ".github_automation.env.example" ]; then
        cp .github_automation.env.example .github_automation.env
        echo "✅ Created .github_automation.env file from template."
        echo "⚠️  Remember to update the values in .github_automation.env with your GitHub credentials."
    fi
fi

# Install node modules if package.json exists
if [ -f "package.json" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Initialize or update Git submodules if any
echo "🔄 Updating Git submodules..."
git submodule update --init --recursive

# Create necessary directories if they don't exist
echo "📁 Creating necessary directories..."
mkdir -p data/memory
mkdir -p logs
mkdir -p src/vot1/dashboard/static/js/backup

# Final setup message
echo ""
echo "=============================================================="
echo "✅ VOT1 Repository Setup Complete!"
echo "=============================================================="
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run the dashboard, use:"
echo "  python scripts/run_dashboard.py"
echo ""
echo "To run tests, use:"
echo "  pytest"
echo ""
echo "For more information, see the README.md file."
echo "==============================================================" 