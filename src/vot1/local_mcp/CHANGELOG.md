# VOTai Agent Ecosystem Changelog

## Version 0.3.2 (2025-03-14)

### New Features and Improvements
- Added VOTai branding across the entire agent ecosystem
- Integrated ASCII art representations of VOTai through a new `ascii_art.py` module
- Updated all agents to display VOTai signature on initialization
- Enhanced documentation to reflect VOTai branding and holistic paradigm
- Added `display_signature` method to FeedbackAgent for consistent branding

### Documentation Updates
- Updated README.md with VOTai branding and ASCII art
- Updated README_AGENTS.md with VOTai information and usage examples
- Added section on VOTai integration in documentation
- Improved comments and docstrings to reference VOTai ecosystem

## Version 0.3.1 (2025-03-14)

### Bug Fixes
- Fixed DevelopmentAgent initialization issue by properly handling the constructor parameters
- Updated server_agents.py to not pass capabilities parameter to DevelopmentAgent
- Fixed start_agent_ecosystem function to create DevelopmentAgent with correct parameters
- Improved error handling in agent creation to support specialized agent types

### New Features and Improvements
- Added comprehensive test script for DevelopmentAgent tasks (test_development_agent_tasks.py)
- Enhanced code generation and code review task handling
- Added better error reporting for development-specific tasks

## Version 0.3.0 (2025-03-14)

### New Features and Improvements
- Added specialized DevelopmentAgent for software development tasks
- Implemented advanced code generation capabilities using Perplexity AI
- Added code review functionality with customizable criteria
- Implemented repository analysis for GitHub repositories
- Added documentation generation for existing code
- Added code improvement suggestions with language-specific style guides
- Implemented dependency analysis for various programming languages
- Added test generation capabilities for Python and JavaScript code
- Added GitHub PR analysis functionality

### Testing
- Created comprehensive test script for DevelopmentAgent (test_development_agent.py)
- Added tests for code generation, code review, repository analysis, and documentation

## Version 0.2.1 (2025-03-13)

### Bug Fixes
- Fixed memory retrieval task handling by adding support for "memory_retrieval" task type
- Improved message handling in agents to properly process and respond to messages
- Fixed memory search functionality to correctly check for memory values in search results
- Corrected syntax error in `bridge.py` file related to path definitions
- Enhanced agent message event handling to add messages to the response queue

### New Features and Improvements
- Added simplified test script `test_memory_and_tasks.py` for testing memory operations and task execution
- Improved test reliability with better error handling and timeouts
- Enhanced agent response handling for better cross-agent communication

## Version 0.2.0 (2025-03-13)

### Bug Fixes
- Fixed method name mismatch in `orchestrator.py` and `server_agents.py`
- Added missing memory-related methods to `MCPOrchestrator` class
- Fixed port conflict issue with the default port 5678 using port finder utility
- Fixed task ID issue in `FeedbackAgent` class implementation
- Corrected inconsistent agent state access
- Updated memory-related tool handlers in `register_internal_tools` to use the correct method names
- Fixed `get_agent_state` method to correctly work as an alias for `get_agent`

### New Features and Improvements
- Added port finder utility to automatically find available ports
- Made the port finder functionality the default behavior for the agent ecosystem
- Added comprehensive test scripts for both the agent ecosystem and the Local MCP Bridge
- Enhanced error handling in the server and bridge components
- Updated documentation and code comments for better clarity
- Added logging for important operations and error cases

### New Scripts
- `test_all_agents.py`: Tests all components of the agent ecosystem
- `test_local_mcp_bridge.py`: Tests the Local MCP Bridge functionality including port finding
- Both scripts include comprehensive testing of core functionality and report results clearly

## Version 0.1.0 (Initial Release)

- Basic agent ecosystem functionality
- Support for agent creation, connection, and communication
- Memory operations for storing and retrieving data
- Task execution capabilities
- Integration with the Local MCP Bridge 