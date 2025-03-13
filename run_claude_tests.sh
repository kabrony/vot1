#!/bin/bash

# Claude Integration Test Runner
echo "===== Claude Integration Test Runner ====="
echo "This script will run multiple tests to verify Claude integration with Cursor AI"
echo ""

# Ensure the script is executable
chmod +x claude_integration_test.py

# Function to check if Cursor AI is available
check_cursor_ai() {
  echo "Checking for Cursor AI environment..."
  # This is a simple check - in a real environment, you might check for specific Cursor indicators
  if [[ "$TERM_PROGRAM" == *"Cursor"* ]] || [[ -n "$CURSOR_TERMINAL" ]]; then
    echo "Cursor AI environment detected!"
    return 0
  else
    echo "NOTE: Not running in a confirmed Cursor environment. Tests may still work if Claude integration is available."
    return 1
  fi
}

# Run JavaScript test
run_js_test() {
  echo ""
  echo "===== Running JavaScript Claude Integration Test ====="
  echo "This test will attempt to trigger Claude completions in JavaScript"
  echo ""
  
  if command -v node &> /dev/null; then
    echo "Running with Node.js:"
    node claude_connection_test.js
  else
    echo "Node.js not found. Please review claude_connection_test.js manually in Cursor AI."
  fi
}

# Run Python test
run_python_test() {
  echo ""
  echo "===== Running Python Claude Integration Test ====="
  echo "This test will attempt to trigger Claude completions in Python"
  echo ""
  
  if command -v python3 &> /dev/null; then
    echo "Running with Python 3:"
    python3 claude_integration_test.py
  elif command -v python &> /dev/null; then
    echo "Running with Python:"
    python claude_integration_test.py
  else
    echo "Python not found. Please review claude_integration_test.py manually in Cursor AI."
  fi
}

# Analyze results
analyze_results() {
  echo ""
  echo "===== Analysis ====="
  echo "To determine if Claude integration is working properly:"
  echo ""
  echo "1. Check if code completions appeared for the factorial functions"
  echo "2. Check if suggestions were offered for the TODO comments"
  echo "3. Check if additional context was provided about the Claude API"
  echo "4. Verify if responses mention Claude or Anthropic"
  echo ""
  echo "If you saw completions that reference Claude specifically, the integration is likely working."
  echo "If completions appeared but didn't mention Claude, they might be from a different model."
  echo "If no completions appeared, the integration may need troubleshooting."
  echo ""
  echo "Next Steps for Troubleshooting:"
  echo "- Verify your Anthropic API key is properly configured in Cursor AI settings"
  echo "- Check that Claude integration is enabled in Cursor AI preferences"
  echo "- Restart Cursor AI and try again"
  echo "- Check the Cursor AI logs for any API connection errors"
}

# Main execution
check_cursor_ai
run_js_test
run_python_test
analyze_results

echo ""
echo "Tests completed. If you need more detailed diagnostics, please check the Cursor AI logs." 