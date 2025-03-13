# Setting Up Claude 3.7 Sonnet with Cursor AI

This guide will help you properly configure Claude 3.7 Sonnet integration with Cursor AI.

## Prerequisites

1. A Cursor AI installation
2. An Anthropic API key with access to Claude 3.7 Sonnet

## Step-by-Step Setup Guide

### 1. Get Your Anthropic API Key

If you don't already have an Anthropic API key:

1. Go to [Anthropic's website](https://www.anthropic.com/)
2. Create an account or log in
3. Navigate to the API section in your dashboard
4. Create a new API key with appropriate permissions
5. Copy the API key and store it securely

### 2. Configure Cursor AI

1. Open Cursor AI
2. Click on the settings icon (⚙️) in the bottom left corner
3. Navigate to "AI" tab in the settings
4. Look for "Claude" or "Anthropic" section
5. Enter your Anthropic API key in the designated field
6. Select "Claude 3.7 Sonnet" as the model (if available)
7. Save your settings

### 3. Alternative Approach: Using the `cursor-settings.json` File

You can also configure Cursor AI by directly editing the settings file:

1. Locate your Cursor AI settings directory:
   - Windows: `%APPDATA%\Cursor\`
   - macOS: `~/Library/Application Support/Cursor/`
   - Linux: `~/.config/Cursor/`

2. Find and edit the `cursor-settings.json` file:

```json
{
  "anthropic": {
    "apiKey": "YOUR_ANTHROPIC_API_KEY",
    "model": "claude-3-7-sonnet-20240229"
  },
  "aiProvider": "anthropic"
}
```

3. Save the file and restart Cursor AI

### 4. Verify Connection

After configuration, you should:

1. Run the test scripts provided in this repository
2. Look for Claude-specific responses in code completions
3. Check the function implementations to see if they mention Claude

## Troubleshooting

If Claude integration isn't working:

### Common Issues

1. **API Key Issues**
   - Ensure the API key is entered correctly with no trailing spaces
   - Verify the API key has appropriate permissions
   - Check if the API key is active and not expired

2. **Model Selection**
   - Verify you've selected Claude 3.7 Sonnet as the model
   - Check if your API key has access to this model

3. **Connection Problems**
   - Ensure your internet connection is working
   - Check for firewalls that might block API connections
   - Try connecting through a different network

4. **Software Configuration**
   - Make sure Cursor AI is updated to the latest version
   - Try restarting Cursor AI after configuration
   - Check if there are any conflicting AI providers enabled

### Advanced Debugging

To see more detailed information about the Claude integration:

1. Open Cursor AI's developer tools:
   - Windows/Linux: `Ctrl+Shift+I`
   - macOS: `Cmd+Option+I`

2. Navigate to the Console tab and look for any error messages related to Claude or Anthropic

3. Check the Network tab to verify API calls are being made to Anthropic's servers

## Getting Help

If you continue to experience issues:

- Visit the [Cursor AI Support](https://cursor.sh/support)
- Check the [Anthropic API Documentation](https://docs.anthropic.com/claude/reference)
- Join the [Cursor AI Discord community](https://discord.gg/cursor) for peer support 