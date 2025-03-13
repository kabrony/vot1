#!/bin/bash
# daily_mcp_automation.sh
#
# This script automates daily MCP tasks, including code analysis, 
# feedback loop execution, and other maintenance tasks.
# 
# Usage: bash scripts/daily_mcp_automation.sh [--no-analysis] [--no-feedback]

# Exit on any error
set -e

# Directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Project root directory
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
# Log directory
LOG_DIR="$ROOT_DIR/logs"
# Timestamp for logs
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Initialize variables
RUN_ANALYSIS=true
RUN_FEEDBACK=true

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    --no-analysis)
      RUN_ANALYSIS=false
      shift
      ;;
    --no-feedback)
      RUN_FEEDBACK=false
      shift
      ;;
  esac
done

# Log header
echo "==================================================" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
echo "VOT1 Daily MCP Automation - Started at $(date)" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
echo "==================================================" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
echo "" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"

# Set up environment
echo "Setting up environment..." | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
source "$SCRIPT_DIR/setup_env.sh" 2>&1 | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
echo "" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"

# Run code analysis if enabled
if $RUN_ANALYSIS; then
  echo "Running code analysis..." | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
  # Analyze src directory with extended thinking
  python "$SCRIPT_DIR/mcp_code_analysis.py" \
    "$ROOT_DIR/src/vot1" \
    --extensions .py .js .html .css \
    --output "$LOG_DIR/code_analysis_$TIMESTAMP.json" \
    --summary "$LOG_DIR/code_analysis_summary_$TIMESTAMP.md" \
    --thinking-tokens 10000 \
    2>&1 | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
  
  echo "Code analysis complete. Results saved to $LOG_DIR/code_analysis_$TIMESTAMP.json" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
  echo "Summary saved to $LOG_DIR/code_analysis_summary_$TIMESTAMP.md" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
  echo "" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
else
  echo "Code analysis skipped (--no-analysis flag provided)" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
  echo "" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
fi

# Run feedback loop if enabled
if $RUN_FEEDBACK; then
  echo "Running feedback loop..." | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
  python "$SCRIPT_DIR/run_feedback_loop.py" --run-once 2>&1 | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
  echo "Feedback loop complete." | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
  echo "" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
else
  echo "Feedback loop skipped (--no-feedback flag provided)" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
  echo "" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
fi

# Run self-improvement workflow
echo "Running self-improvement workflow..." | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
python "$SCRIPT_DIR/run_self_improvement.py" --analyze-only 2>&1 | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
echo "Self-improvement workflow complete." | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
echo "" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"

# Update issue tracking with analysis results if GitHub token is set
if [ -n "$GITHUB_TOKEN" ] && [ -n "$GITHUB_OWNER" ] && [ -n "$GITHUB_REPO" ]; then
  echo "Updating GitHub issues with analysis results..." | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
  python "$SCRIPT_DIR/run_github_bridge.py" update-issues \
    --analysis-file "$LOG_DIR/code_analysis_$TIMESTAMP.json" \
    --summary-file "$LOG_DIR/code_analysis_summary_$TIMESTAMP.md" \
    2>&1 | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
  echo "GitHub issues updated." | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
  echo "" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
fi

# Make all scripts executable
echo "Making scripts executable..." | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
chmod +x "$SCRIPT_DIR"/*.py "$SCRIPT_DIR"/*.sh 2>&1 | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
echo "" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"

# Log footer
echo "==================================================" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
echo "VOT1 Daily MCP Automation - Completed at $(date)" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"
echo "==================================================" | tee -a "$LOG_DIR/daily_automation_$TIMESTAMP.log"

echo "Daily automation completed successfully!"
echo "Log file: $LOG_DIR/daily_automation_$TIMESTAMP.log" 