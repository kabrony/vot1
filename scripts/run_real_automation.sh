#!/bin/bash
# run_real_automation.sh - Execute the real GitHub automation system with actual repositories
# Set environment variables in .github_automation.env file or export them before running this script

# Load environment variables from .github_automation.env file if it exists
if [ -f .github_automation.env ]; then
    echo "Loading environment variables from .github_automation.env file"
    export $(grep -v '^#' .github_automation.env | xargs)
elif [ -f ../.github_automation.env ]; then
    echo "Loading environment variables from ../.github_automation.env file"
    export $(grep -v '^#' ../.github_automation.env | xargs)
fi

# Check if GitHub token is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN environment variable is not set"
    echo "Please set it with: export GITHUB_TOKEN=your_actual_github_token"
    echo "Or create a .github_automation.env file with GITHUB_TOKEN=your_actual_github_token"
    exit 1
fi

# Set default values
OWNER=${GITHUB_OWNER:-""}
REPO=${GITHUB_REPO:-""}
USE_COMPOSIO=${USE_COMPOSIO:-""}
USE_PERPLEXITY=${USE_PERPLEXITY:-""}
DEEP_ANALYSIS=${DEEP_ANALYSIS:-""}
AUTO_APPROVE=${AUTO_APPROVE:-""}
CREATE_WEBHOOK=${CREATE_WEBHOOK:-""}
WEBHOOK_URL=${WEBHOOK_URL:-""}
UPDATE_AREAS=${UPDATE_AREAS:-"documentation workflows code_quality"}
MAX_UPDATES=${MAX_UPDATES:-3}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --owner)
            OWNER="$2"
            shift 2
            ;;
        --repo)
            REPO="$2"
            shift 2
            ;;
        --use-composio)
            USE_COMPOSIO="--use-composio"
            shift
            ;;
        --use-perplexity)
            USE_PERPLEXITY="--use-perplexity"
            shift
            ;;
        --deep-analysis)
            DEEP_ANALYSIS="--deep-analysis"
            shift
            ;;
        --auto-approve)
            AUTO_APPROVE="--auto-approve"
            shift
            ;;
        --create-webhook)
            CREATE_WEBHOOK="--create-webhook"
            shift
            ;;
        --webhook-url)
            WEBHOOK_URL="--webhook-url $2"
            shift 2
            ;;
        --update-areas)
            UPDATE_AREAS="$2"
            shift 2
            ;;
        --max-updates)
            MAX_UPDATES="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$OWNER" ] || [ -z "$REPO" ]; then
    echo "Error: --owner and --repo are required parameters"
    echo "Usage: ./run_real_automation.sh --owner USERNAME --repo REPOSITORY [options]"
    exit 1
fi

# Print confirmation
echo "==============================================="
echo "Running GitHub Automation on REAL repository!"
echo "==============================================="
echo "Repository: $OWNER/$REPO"
echo "Using GitHub token: ${GITHUB_TOKEN:0:4}...${GITHUB_TOKEN: -4}" # Show only first and last 4 chars for security
echo "Features enabled:"
echo "- Composio integration: ${USE_COMPOSIO:+"Yes"}"
echo "- Perplexity search: ${USE_PERPLEXITY:+"Yes"}"
echo "- Deep analysis: ${DEEP_ANALYSIS:+"Yes"}"
echo "- Auto-approve PRs: ${AUTO_APPROVE:+"Yes"}"
echo "- Create webhook: ${CREATE_WEBHOOK:+"Yes"}"
echo "- Webhook URL: ${WEBHOOK_URL:+"Set"}"
echo "- Update areas: $UPDATE_AREAS"
echo "- Max updates per area: $MAX_UPDATES"
echo "==============================================="
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Run the Python script with all parameters
python scripts/run_real_github_automation.py \
    --owner "$OWNER" \
    --repo "$REPO" \
    --token "$GITHUB_TOKEN" \
    $USE_COMPOSIO \
    $USE_PERPLEXITY \
    $DEEP_ANALYSIS \
    $AUTO_APPROVE \
    $CREATE_WEBHOOK \
    $WEBHOOK_URL \
    --update-areas $UPDATE_AREAS \
    --max-updates $MAX_UPDATES

# Check exit code and report
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "==============================================="
    echo "GitHub Automation completed successfully!"
    echo "Check the dashboard at reports/github/dashboard.html"
    echo "==============================================="
else
    echo "==============================================="
    echo "GitHub Automation encountered errors (exit code: $EXIT_CODE)"
    echo "Check logs at logs/real_github_automation.log"
    echo "==============================================="
fi

exit $EXIT_CODE 