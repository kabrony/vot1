#!/bin/bash

# VOT1 Application Update Script
# This script updates the VOT1 application and commits changes to git

set -e

echo "Updating VOT1 application..."

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Navigate to the root directory
cd "$ROOT_DIR"

# Pull the latest changes from git
echo "Pulling latest changes from git..."
git pull

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run database migrations if needed
if [ -f "$ROOT_DIR/src/vot1/db/migrations/run_migrations.py" ]; then
    echo "Running database migrations..."
    python "$ROOT_DIR/src/vot1/db/migrations/run_migrations.py"
fi

# Restart services
echo "Restarting services..."
if [ -f "$SCRIPT_DIR/restart_services.sh" ]; then
    bash "$SCRIPT_DIR/restart_services.sh"
else
    echo "No restart_services.sh script found. Please restart services manually."
fi

# Create a git commit with changes
if [ "$1" == "--commit" ]; then
    COMMIT_MESSAGE="$2"
    if [ -z "$COMMIT_MESSAGE" ]; then
        COMMIT_MESSAGE="Update VOT1 application $(date '+%Y-%m-%d %H:%M:%S')"
    fi
    
    echo "Committing changes to git with message: $COMMIT_MESSAGE"
    git add .
    git commit -m "$COMMIT_MESSAGE"
    
    # Push changes if requested
    if [ "$3" == "--push" ]; then
        echo "Pushing changes to remote repository..."
        git push
    fi
fi

echo "VOT1 application update completed successfully!" 