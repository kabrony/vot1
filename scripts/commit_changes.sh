#!/bin/bash

# VOT1 Git Commit Script
# This script commits changes to git with a detailed message

set -e

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Navigate to the root directory
cd "$ROOT_DIR"

# Check if there are any changes to commit
if [ -z "$(git status --porcelain)" ]; then
    echo "No changes to commit"
    exit 0
fi

# Default commit message
DEFAULT_MESSAGE="Update VOT1 application $(date '+%Y-%m-%d %H:%M:%S')"

# Get commit message from arguments or use default
COMMIT_MESSAGE="$1"
if [ -z "$COMMIT_MESSAGE" ]; then
    COMMIT_MESSAGE="$DEFAULT_MESSAGE"
fi

# Generate a detailed commit message with file changes
DETAILED_MESSAGE="$COMMIT_MESSAGE\n\nChanges:\n"

# Add modified files to the message
MODIFIED_FILES=$(git diff --name-status)
DETAILED_MESSAGE+="$MODIFIED_FILES\n\n"

# Add a summary of the changes
DETAILED_MESSAGE+="Summary:\n"
DETAILED_MESSAGE+="- Fixed bugs in Composio integration\n"
DETAILED_MESSAGE+="- Added OpenAPI import functionality\n"
DETAILED_MESSAGE+="- Created sample OpenAPI specification for testing\n"
DETAILED_MESSAGE+="- Added documentation for OpenAPI integration\n"
DETAILED_MESSAGE+="- Improved error handling and user feedback\n"

# Commit the changes
echo -e "$DETAILED_MESSAGE" | git commit -a -F -

echo "Changes committed successfully!"

# Push changes if requested
if [ "$2" == "--push" ]; then
    echo "Pushing changes to remote repository..."
    git push
fi 