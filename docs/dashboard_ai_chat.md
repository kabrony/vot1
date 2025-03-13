# Dashboard AI Chat Integration

The VOT1 Dashboard includes a powerful AI chat interface that allows users to interact with the memory system and control the visualization through natural language. This document provides details on how to use the chat feature, its technical implementation, and configuration options.

## Table of Contents

- [Overview](#overview)
- [Usage](#usage)
- [Technical Implementation](#technical-implementation)
- [API Endpoints](#api-endpoints)
- [Memory Context Integration](#memory-context-integration)
- [Visualization Commands](#visualization-commands)
- [Configuration](#configuration)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)

## Overview

The AI chat feature integrates with the VOT1 dashboard, providing an intuitive way to interact with the memory system. The chat uses the MCP (Model Control Protocol) to process natural language input, retrieve relevant memories, and execute visualization commands.

Key capabilities include:
- Natural language interaction with the memory system
- Contextual responses based on memory content
- Visualization control through chat commands
- Memory search and exploration
- System explanations and guidance

## Usage

### Opening the Chat Interface

1. Navigate to the VOT1 dashboard at `http://localhost:5000`
2. Click the chat icon in the bottom right corner of the screen

### Example Interactions

Here are some examples of how to interact with the AI chat:

**Memory Exploration:**
- "What memories do I have about machine learning?"
- "Show me the most recent memories in the system"
- "What types of memories are stored?"

**Visualization Control:**
- "Focus on memories related to Python"
- "Highlight the most connected nodes"
- "Filter memories created in the last week"
- "Reset the visualization view"

**System Information:**
- "How does the memory system work?"
- "Explain how memories are connected"
- "What is the difference between memory types?"

### Memory References

When the AI responds, it may include memory references that relate to your query. These references include:
- Memory ID
- Brief summary
- Relevance score

You can click on any memory reference to focus on it in the visualization.

## Technical Implementation

The AI chat integration consists of several components:

1. **Frontend Interface**: JavaScript-based chat UI in the dashboard
2. **Backend API**: Flask endpoints for processing messages and retrieving data
3. **MCP Connector**: Integration with Model Control Protocol for AI processing
4. **Memory Context**: Integration with the memory system for relevant context

### Architecture Flow

1. User sends a message through the chat interface
2. The message is sent to the server via the `/api/chat/message` endpoint
3. The server retrieves relevant memory context based on the message
4. The server processes the message with MCP, including memory context
5. MCP returns a response, potentially including visualization commands
6. The server returns the formatted response to the frontend
7. The frontend displays the response and executes any visualization commands

## API Endpoints

The chat integration provides several API endpoints:

### `POST /api/chat/message`

Process a chat message and return a response.

**Request Body:**
```json
{
  "message": "Show me memories about Python",
  "conversation_id": "conv-123456",
  "include_memory_context": true,
  "visualization_mode": "auto"
}
```

**Response:**
```json
{
  "response": "I found several memories related to Python...",
  "message_id": "msg-789012",
  "conversation_id": "conv-123456",
  "memory_references": [
    {
      "id": "mem-abc123",
      "relevance": 0.92,
      "summary": "Python Data Structures"
    }
  ],
  "visualization_update": {
    "command": "focus",
    "params": {
      "query": "python"
    }
  }
}
```

### `GET /api/chat/history`

Retrieve chat history for a conversation.

**Query Parameters:**
- `conversation_id`: The ID of the conversation
- `limit` (optional): Maximum number of messages to return (default: 50)

### `PUT /api/chat/system-prompt`

Update the system prompt for a conversation.

**Request Body:**
```json
{
  "conversation_id": "conv-123456",
  "system_prompt": "Custom system prompt text..."
}
```

### `GET /api/chat/memory-search`

Search memories based on a query.

**Query Parameters:**
- `q`: The search query
- `limit` (optional): Maximum number of results (default: 10)

### `POST /api/chat/visualization-command`

Execute a visualization command.

**Request Body:**
```json
{
  "command": "focus",
  "params": {
    "query": "machine learning"
  }
}
```

## Memory Context Integration

The chat system integrates with VOT1's memory system to provide relevant context for responses:

1. When a user sends a message, the system performs a semantic search of memories
2. The most relevant memories are retrieved and included in the AI prompt
3. The AI uses these memories to provide more accurate and contextual responses
4. Memory references are returned with the response for user exploration

## Visualization Commands

The chat can execute the following visualization commands:

| Command | Description | Parameters |
|---------|-------------|------------|
| `focus` | Zoom in on specific memories | `id` (string): Memory ID<br>`query` (string): Search query |
| `highlight` | Highlight specific nodes | `ids` (array): Array of memory IDs |
| `filter` | Filter the visualization | `type` (string): Memory type<br>`date` (string): Date range<br>`relevance` (number): Minimum relevance |
| `reset` | Reset to default view | None |

### Visualization Command Format

Visualization commands are embedded in the AI's response using a special format:

```
[VISUALIZATION:{"command":"focus","params":{"query":"memory topic"}}]
```

The chat frontend extracts and processes these commands based on the user's visualization mode setting.

## Configuration

The chat feature can be configured through the dashboard settings:

### Visualization Command Mode

Controls how visualization commands from the AI are handled:

- **Auto** (default): Automatically apply visualization commands
- **Manual**: Ask for confirmation before applying commands
- **Disabled**: Ignore visualization commands

### Memory Context

Controls whether memory context is included with chat messages:

- **Enabled** (default): Include relevant memory context with messages
- **Disabled**: Process messages without memory context

## Customization

### System Prompt

You can customize the AI's behavior by modifying the system prompt. This defines how the AI responds and what capabilities it has. The default system prompt includes:

- Introduction to VOT1 Assistant
- Capabilities description
- Guidelines for responses
- Available visualization commands

### Styling

The chat interface styling can be customized by modifying the `chat.css` file. The styling uses CSS variables for colors and dimensions, making it easy to adapt to different themes.

## Troubleshooting

### Common Issues

**Chat not responding:**
- Check that the backend server is running
- Verify MCP configuration in environment variables
- Check browser console for JavaScript errors

**Visualization commands not working:**
- Verify that visualization mode is not set to "Disabled"
- Check that the visualization engine is properly initialized
- Check browser console for errors in command execution

**Memory context not relevant:**
- The semantic search may need tuning
- Try more specific queries
- Verify that memories are properly indexed

### Logging

The chat system includes comprehensive logging:

- Frontend: Console logs for message sending and receiving
- Backend: Logs for API requests, MCP communication, and memory retrieval

To enable debug logging, add the following to your `.env` file:

```
VOT1_LOG_LEVEL=DEBUG
``` 