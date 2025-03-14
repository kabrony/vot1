# Development Assistant Documentation

## Overview

The Development Assistant is a powerful tool integrated into the VOT1 Dashboard that combines code analysis, research capabilities, memory management, and script generation to create an advanced development workflow. It leverages Claude 3.7's thinking capabilities and Perplexity's research prowess to provide comprehensive assistance throughout the development lifecycle.

## Core Components

The Development Assistant consists of four main components:

### 1. Code Analysis System

The Code Analysis system provides deep insights into the structure and quality of your codebase.

#### Key Features:
- **Structure Analysis**: Examines files, classes, functions, and their relationships
- **Dependency Tracking**: Identifies imports and module dependencies
- **Complexity Assessment**: Evaluates code complexity and maintainability
- **Visualization**: Creates visual representations of code structure

#### Usage:
```python
# Programmatic usage
from vot1.dashboard.utils.dev_assistant import init_dev_assistant

dev_assistant = init_dev_assistant(project_root='/path/to/project')
analysis = dev_assistant.analyze_codebase(directory='/path/to/analyze', file_extension='.py')
```

### 2. Perplexity Research Integration

The Research system connects to Perplexity AI to provide up-to-date information on programming topics, libraries, best practices, and more.

#### Key Features:
- **Deep Research**: Comprehensive information on complex topics
- **Citation Support**: References to sources and documentation
- **Contextual Awareness**: Research tailored to your current project
- **Memory Integration**: Stores research results for future reference

#### Usage:
```python
# Programmatic usage
research_result = dev_assistant.research_topic(
    "Modern Python error handling best practices", 
    depth="deep"  # Options: "basic", "medium", "deep"
)
```

### 3. Memory Subsystem

The Memory Subsystem provides persistent storage for code analysis results, research findings, generated scripts, and other development insights.

#### Key Features:
- **Categorized Storage**: Organizes data into logical categories
- **Persistent Retention**: Maintains knowledge across sessions
- **Retrieval API**: Easy access to stored information
- **Memory Management**: Tools for listing, retrieving, and deleting entries

#### Usage:
```python
# Programmatic usage
# Store information
dev_assistant.memory.store("research_results", "python_error_handling", research_data)

# Retrieve information
error_handling_data = dev_assistant.memory.retrieve("research_results", "python_error_handling")

# List categories
categories = dev_assistant.memory.list_categories()

# List keys in a category
research_keys = dev_assistant.memory.list_keys("research_results")
```

### 4. Script Generation System

The Script Generation system creates code, documentation, and tests based on descriptions and best practices.

#### Key Features:
- **Intelligent Code Generation**: Creates code based on descriptions
- **Research-Informed Scripts**: Incorporates best practices from research
- **Multiple Script Types**: Supports Python, JavaScript, Bash, and more
- **Template Support**: Can follow specified templates or structures

#### Usage:
```python
# Programmatic usage
script = dev_assistant.generate_script(
    description="A utility function that validates email addresses with regex",
    script_type="python",
    template=None  # Optional template
)

# Save to file
dev_assistant.save_script(script["key"], "src/utils/email_validator.py")
```

## Architecture

### Class Structure

The Development Assistant implements the following class hierarchy:

```
DevelopmentAssistant
├── CodeAnalysis (static methods)
│   ├── extract_imports()
│   ├── extract_classes_and_functions()
│   ├── analyze_dependencies()
│   └── scan_directory()
├── PerplexityResearcher
│   ├── connect()
│   └── research()
├── MemorySubsystem
│   ├── store()
│   ├── retrieve()
│   ├── list_categories()
│   └── list_keys()
└── ScriptGenerator
    ├── generate_script()
    └── save_script_to_file()
```

### Data Flow

1. **Code Analysis Flow**:
   - Input: Project directory or specific path
   - Processing: File scanning, AST parsing, statistics gathering
   - Output: Structured analysis with file details and aggregate statistics

2. **Research Flow**:
   - Input: Research query and depth
   - Processing: Perplexity AI query with appropriate system prompt
   - Output: Research content with citations and formatting

3. **Memory Flow**:
   - Input: Category, key, and data for storage
   - Processing: JSON serialization and file storage
   - Output: Persistence confirmation or retrieved data

4. **Script Generation Flow**:
   - Input: Script description, type, and optional template
   - Processing: Research on best practices + Claude script generation
   - Output: Generated script content and storage key

## Advanced Feedback Loops

The Development Assistant implements several feedback loops to continuously improve its assistance capabilities:

### 1. Analysis-Research Loop

The Analysis-Research loop combines codebase analysis with targeted research to provide context-aware recommendations:

1. Analyze codebase structure and dependencies
2. Identify key libraries, frameworks, and patterns
3. Research best practices specific to these components
4. Generate recommendations tailored to the project

Example usage:
```python
# Analyze the codebase to understand its structure
analysis = dev_assistant.analyze_codebase()

# Use analysis to formulate a research query
framework_imports = [imp for imp in analysis["unique_imports"] 
                     if any(fw in imp for fw in ["flask", "django", "fastapi"])]

if framework_imports:
    # Research best practices for the detected framework
    framework = framework_imports[0].split('.')[0]
    research = dev_assistant.research_topic(f"{framework} best practices architecture")
    
    # Store the combined analysis and research as architectural insights
    dev_assistant.memory.store("architecture_insights", 
                              f"{framework}_architecture", 
                              {"analysis": analysis, "research": research})
```

### 2. Memory-Assisted Generation Loop

The Memory-Assisted Generation loop leverages past research and analyses to improve script generation:

1. Retrieve relevant past research from memory
2. Analyze similar code in the project
3. Generate script with awareness of both resources
4. Store the generated script for future reference

Example usage:
```python
# Check if we have relevant research in memory
auth_research = dev_assistant.memory.retrieve("research_results", "authentication")

# Generate script with memory-informed context
script = dev_assistant.generate_script(
    description="A secure user authentication function with password hashing",
    script_type="python",
    template=None
)

# Store the script with references to the research that informed it
dev_assistant.memory.store("script_metadata", 
                          script["key"], 
                          {"script_key": script["key"], 
                           "research_used": "authentication"})
```

### 3. Troubleshooting-Analysis Loop

The Troubleshooting-Analysis loop combines code analysis with targeted troubleshooting to resolve issues:

1. Analyze problematic code
2. Identify potential issues through static analysis
3. Research common problems with similar patterns
4. Generate solutions with explanations

Example usage:
```python
# Troubleshoot code with potential issues
result = dev_assistant.troubleshoot_code(
    code="def divide(a, b): return a/b",
    error_message="ZeroDivisionError: division by zero"
)

# Store troubleshooting results for future reference
dev_assistant.memory.store("troubleshooting_patterns", 
                          "division_by_zero", 
                          result)
```

## Optimization Strategies

The Development Assistant includes several optimization strategies to enhance performance and quality:

### 1. Token Optimization

The Development Assistant manages token usage to maximize the value of API calls:

- **Right-sizing Research Depth**: Adjusts research depth based on query complexity
- **Thinking Token Management**: Allocates thinking tokens based on task importance
- **Prompt Engineering**: Crafts efficient prompts to reduce token consumption
- **Caching Mechanism**: Prevents duplicate research on similar topics

Example configuration:
```python
# Configure token optimization
dev_assistant_options = {
    "max_thinking_tokens": 60000,  # Maximum tokens for complex tasks
    "research_depth_mapping": {
        "simple": "basic",    # Simple queries use basic depth (less tokens)
        "complex": "deep",    # Complex queries use deep analysis (more tokens)
        "default": "medium"   # Default depth for most queries
    }
}
```

### 2. Research Quality Enhancement

Strategies to enhance research quality:

- **Depth Control**: Three levels of research depth (basic, medium, deep)
- **Context Enrichment**: Adds project context to research queries
- **Citation Retrieval**: Ensures sources are included with research results
- **Query Reformulation**: Refines queries based on initial results

Example usage for a complex architectural decision:
```python
# Get deep research for an important architectural decision
research = dev_assistant.research_topic(
    "Microservices vs monolith architecture for a Flask application with 50+ endpoints",
    depth="deep"  # Use maximum depth for important architectural decisions
)
```

### 3. Code Generation Quality

Techniques to improve code generation quality:

- **Best Practices Research**: Automatically researches best practices before generation
- **Project Consistency**: Analyzes project code style for consistent generation
- **Error Prevention**: Adds robust error handling by default
- **Documentation**: Includes comprehensive docstrings and comments

Example of quality enhancement in script generation:
```python
# Generate a high-quality script with extensive research
script = dev_assistant.generate_script(
    description="A complete REST API endpoint handler for user registration with validation",
    script_type="python",
    # The template includes error handling patterns and documentation standards
    template="""
    @app.route('/users', methods=['POST'])
    @handle_errors  # Error handling decorator
    def register_user():
        \"\"\"
        Register a new user.
        
        Request Body:
            {
                "username": string,
                "email": string,
                "password": string
            }
        
        Returns:
            201: User created successfully
            400: Invalid input data
            409: Username or email already exists
        \"\"\"
        # Implementation here
    """
)
```

## Smart Token Management

The Development Assistant now includes an intelligent token management system that optimizes token usage based on task complexity and type. Rather than using a fixed token limit of 120,000 tokens, the system now:

1. Uses a default maximum of 20,000 tokens
2. Dynamically allocates tokens based on task type (research, analysis, generation, etc.)
3. Adjusts allocation based on task complexity (low, medium, high)
4. Tracks token usage and automatically resets when needed
5. Can truncate output to fit within token limits

### Token Allocation by Task Type

Different types of tasks receive different token allocations based on their typical requirements:

| Task Type | Low Complexity | Medium Complexity | High Complexity |
|-----------|----------------|-------------------|-----------------|
| Research | 3,000 | 6,000 | 10,000 |
| Analysis | 5,000 | 8,000 | 12,000 |
| Generation | 4,000 | 7,000 | 10,000 |
| Troubleshooting | 5,000 | 8,000 | 12,000 |

### Configuration Options

The smart token management system can be configured with these parameters:

```python
assistant = DevelopmentAssistant(
    memory_path="/path/to/memory",
    project_root="/path/to/project",
    perplexity_api_key="your-api-key",
    max_thinking_tokens=20000,  # Maximum tokens for complex tasks
    smart_token_management=True  # Enable intelligent token allocation
)
```

### Environment Variables

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `VOT1_MAX_THINKING_TOKENS` | Maximum tokens for thinking | `20000` |
| `VOT1_SMART_TOKEN_MANAGEMENT` | Enable smart token management | `True` |

## API Reference

### DevelopmentAssistant Class

```python
class DevelopmentAssistant:
    def __init__(self, project_root: Optional[str] = None, memory_path: Optional[str] = None):
        """
        Initialize the Development Assistant.
        
        Args:
            project_root: Root directory of the project to analyze
            memory_path: Directory to store memory files
        """
        
    def analyze_codebase(self, directory: Optional[str] = None, file_extension: str = '.py') -> Dict[str, Any]:
        """
        Analyze the structure and dependencies of the codebase.
        
        Args:
            directory: Directory to analyze (defaults to project_root)
            file_extension: File extension to include in analysis
            
        Returns:
            Dict containing analysis results
        """
        
    def research_topic(self, query: str, depth: str = 'deep') -> Dict[str, Any]:
        """
        Research a topic using Perplexity AI.
        
        Args:
            query: Research query
            depth: Research depth ('basic', 'medium', 'deep')
            
        Returns:
            Dict containing research results and citations
        """
        
    def generate_script(self, description: str, script_type: str = 'python', 
                        template: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a script based on description.
        
        Args:
            description: Description of the script functionality
            script_type: Type of script ('python', 'javascript', 'bash', etc.)
            template: Optional template or structure to follow
            
        Returns:
            Dict containing generated script and metadata
        """
        
    def save_script(self, script_key: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Save a generated script to a file.
        
        Args:
            script_key: Key of script in memory
            file_path: Path to save the script (generated if None)
            
        Returns:
            Dict containing save result metadata
        """
        
    def troubleshoot_code(self, code: str, error_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Troubleshoot code issues using Claude and Perplexity research.
        
        Args:
            code: Code to troubleshoot
            error_message: Optional error message
            
        Returns:
            Dict containing analysis and suggested fixes
        """
        
    def analyze_project_architecture(self) -> Dict[str, Any]:
        """
        Analyze the overall project architecture and provide recommendations.
        
        Returns:
            Dict containing architecture analysis and recommendations
        """
```

### API Endpoints

The Development Assistant API exposes the following endpoints:

#### Status Endpoint
```
GET /api/dev-assistant/status
```

Returns the status and configuration of the Development Assistant:
```json
{
  "initialized": true,
  "config": {
    "codebaseRoot": "/path/to/project",
    "memoryPath": "/path/to/memory",
    "defaultResearchDepth": "deep",
    "perplexityConnected": true,
    "memoryEnabled": true
  }
}
```

#### Code Analysis Endpoint
```
POST /api/dev-assistant/analyze
```

Request body:
```json
{
  "path": "/path/to/analyze",
  "file_extension": ".py"
}
```

Returns comprehensive code analysis results.

#### Research Endpoint
```
POST /api/dev-assistant/research
```

Request body:
```json
{
  "query": "How to implement JWT authentication in Flask",
  "depth": "deep"
}
```

Returns research results with citations.

#### Script Generation Endpoint
```
POST /api/dev-assistant/generate
```

Request body:
```json
{
  "description": "A utility function to validate email addresses",
  "script_type": "python",
  "template": null
}
```

Returns generated script content and metadata.

#### Troubleshooting Endpoint
```
POST /api/dev-assistant/troubleshoot
```

Request body:
```json
{
  "code": "def parse_json(json_str): return json.loads(json_str)",
  "error_message": "JSONDecodeError: Expecting value: line 1 column 1 (char 0)"
}
```

Returns troubleshooting analysis and suggested fixes.

#### Memory Management Endpoints
```
GET /api/dev-assistant/memory/list?category=research_results
GET /api/dev-assistant/memory/get?category=research_results&key=flask_auth
POST /api/dev-assistant/memory/save
POST /api/dev-assistant/memory/delete
```

These endpoints allow for managing the memory subsystem.

## UI Components

The Development Assistant includes several UI components for interacting with its capabilities:

### 1. Code Analysis Visualization

The code analysis visualization displays the structure of your codebase:

- **Files Tree**: Hierarchical view of project files
- **Dependencies Graph**: Network graph of module dependencies
- **Stats Panel**: Code statistics and metrics
- **Issue Highlights**: Potential issues and improvements

### 2. Research Results Display

The research results component presents research findings in a readable format:

- **Content Section**: Main research content with formatting
- **Citations Panel**: Sources and references
- **Related Topics**: Links to related research
- **Save Options**: Tools to save research to memory

### 3. Script Generation Interface

The script generation interface provides tools for creating and saving scripts:

- **Description Input**: Field for script description
- **Type Selector**: Options for script type
- **Template Editor**: Optional template input
- **Result Display**: Generated script with syntax highlighting
- **Save Controls**: Options to save to file

### 4. Memory Browser

The memory browser allows exploration of stored knowledge:

- **Category Tree**: Hierarchical view of memory categories
- **Key Listing**: List of keys in each category
- **Content Viewer**: Contents of selected memory item
- **Management Tools**: Options to edit, delete, or export memory items

## Common Workflows

### Workflow 1: New Project Analysis

1. Initialize the Development Assistant with the project root
2. Run a full codebase analysis
3. Research best practices for the detected frameworks
4. Analyze project architecture
5. Generate improvement recommendations

### Workflow 2: Feature Development

1. Research the feature requirements
2. Analyze similar implementations in the codebase
3. Generate script scaffolding
4. Iteratively refine with additional research
5. Save and integrate the completed feature

### Workflow 3: Troubleshooting

1. Identify problematic code
2. Run troubleshooting analysis
3. Research potential solutions
4. Generate fixed code
5. Test and implement the solution

### Workflow 4: Code Review

1. Analyze code for review
2. Research best practices for detected patterns
3. Generate suggestions for improvements
4. Document findings in memory
5. Share results with the team

## Advanced Usage Examples

### Example 1: Customized Architecture Analysis

```python
# Initialize Development Assistant
dev_assistant = init_dev_assistant(project_root='/path/to/project')

# Analyze codebase
analysis = dev_assistant.analyze_codebase()

# Research modern architecture patterns
research = dev_assistant.research_topic("Modern Python architecture patterns for large applications")

# Custom architecture analysis with specific focus
def analyze_layers(analysis, research):
    """Analyze application layers and separation of concerns"""
    layers = {
        "data_access": [],
        "business_logic": [],
        "api": [],
        "utils": []
    }
    
    for file_details in analysis["file_details"]:
        path = file_details["file_path"]
        if "models" in path or "repositories" in path or "dao" in path:
            layers["data_access"].append(path)
        elif "services" in path or "business" in path:
            layers["business_logic"].append(path)
        elif "api" in path or "routes" in path or "views" in path:
            layers["api"].append(path)
        elif "utils" in path or "helpers" in path:
            layers["utils"].append(path)
    
    return {
        "layers": layers,
        "analysis": {
            "separation_of_concerns": len(layers["data_access"]) > 0 and 
                                      len(layers["business_logic"]) > 0 and 
                                      len(layers["api"]) > 0,
            "layer_distribution": {k: len(v) for k, v in layers.items()}
        }
    }

# Run custom analysis
architecture = analyze_layers(analysis, research)

# Store results
dev_assistant.memory.store("architecture_analysis", 
                          "layer_separation", 
                          architecture)
```

### Example 2: Advanced Research-Driven Code Generation

```python
# Initialize Development Assistant
dev_assistant = init_dev_assistant()

# Research API security best practices
security_research = dev_assistant.research_topic(
    "REST API security best practices 2024", 
    depth="deep"
)

# Research input validation techniques
validation_research = dev_assistant.research_topic(
    "Input validation techniques for Python REST APIs", 
    depth="medium"
)

# Combine research findings into a custom template
security_points = security_research.get("content", "").split("\n")
validation_points = validation_research.get("content", "").split("\n")

# Extract key recommendations
security_recommendations = [p for p in security_points if ":" in p or "-" in p][:5]
validation_recommendations = [p for p in validation_points if ":" in p or "-" in p][:5]

# Create template with best practices commented
template = f"""
\"\"\"
Secure API endpoint following best practices:
{chr(10).join('# ' + s for s in security_recommendations)}

With input validation:
{chr(10).join('# ' + v for v in validation_recommendations)}
\"\"\"

@app.route('/api/resource', methods=['POST'])
@jwt_required  # JWT authentication
def create_resource():
    # Get request data
    data = request.get_json()
    
    # Input validation
    validation_result = validate_input(data)
    if not validation_result['valid']:
        return jsonify({"error": validation_result['errors']}), 400
    
    # Process the valid data
    # ...
    
    # Return response
    return jsonify({"status": "success"}), 201
"""

# Generate the complete implementation
script = dev_assistant.generate_script(
    description="A secure API endpoint for user registration with comprehensive validation",
    script_type="python",
    template=template
)

# Save to a file
dev_assistant.save_script(script["key"], "app/api/user_registration.py")
```

### Example 3: Memory-Enhanced Troubleshooting

```python
# Initialize Development Assistant
dev_assistant = init_dev_assistant()

# Define the problematic code
problematic_code = """
async def fetch_data(url):
    response = requests.get(url)
    data = response.json()
    return data
"""

# Error message
error_message = "RuntimeWarning: Executing requests.get in asyncio loop"

# Check memory for similar issues
memory_categories = dev_assistant.memory.list_categories()
if "troubleshooting" in memory_categories:
    keys = dev_assistant.memory.list_keys("troubleshooting")
    async_keys = [k for k in keys if "async" in k]
    
    # Get related troubleshooting memory
    related_memories = []
    for key in async_keys:
        memory = dev_assistant.memory.retrieve("troubleshooting", key)
        if memory:
            related_memories.append(memory)

# Perform troubleshooting with memory context
troubleshooting = dev_assistant.troubleshoot_code(problematic_code, error_message)

# Generate a fix with awareness of past solutions
improved_code = dev_assistant.generate_script(
    description=f"Fix the async code issue: {error_message}",
    script_type="python",
    template=problematic_code
)

# Store the troubleshooting pattern
dev_assistant.memory.store(
    "troubleshooting",
    "async_requests_in_loop",
    {
        "problem": problematic_code,
        "error": error_message,
        "analysis": troubleshooting,
        "solution": improved_code["script"]
    }
)
```

## Best Practices

### Code Analysis Best Practices

1. **Regular Analysis**: Run codebase analysis regularly to track changes
2. **Focused Analysis**: Target specific directories for in-depth analysis
3. **Comparative Analysis**: Compare analyses over time to identify trends
4. **Memory Usage**: Store analyses in memory for historical comparison

### Research Best Practices

1. **Specific Queries**: Use specific, focused research queries
2. **Depth Selection**: Choose appropriate research depth for the task
3. **Citation Review**: Always review and verify citations
4. **Memory Efficiency**: Store research results for frequent topics

### Script Generation Best Practices

1. **Clear Descriptions**: Provide detailed, specific descriptions
2. **Template Usage**: Use templates for consistent style and structure
3. **Review Generated Code**: Always review and test generated code
4. **Iterative Refinement**: Refine scripts with additional context

### Memory Management Best Practices

1. **Organized Categories**: Use a consistent categorization system
2. **Descriptive Keys**: Create clear, searchable memory keys
3. **Regular Cleanup**: Remove outdated or redundant memory items
4. **Backup Important Memories**: Export critical memory items

## Conclusion

The Development Assistant provides a comprehensive set of tools for enhancing the development workflow through AI-powered code analysis, research, script generation, and memory management. By integrating Claude 3.7's thinking capabilities with Perplexity's research prowess, it creates powerful feedback loops that continuously improve the development experience.

The system is designed to be extensible, with clear APIs and integration points for adding new capabilities or customizing existing ones. As you use the Development Assistant, its memory subsystem builds a knowledge base tailored to your projects, making it increasingly valuable over time.

## Appendix: Environment Variables

The Development Assistant can be configured using the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `VOT1_PROJECT_ROOT` | Root directory of the project | Current working directory |
| `VOT1_MEMORY_PATH` | Path to memory storage | `./memory` |
| `VOT1_MAX_THINKING_TOKENS` | Maximum tokens for thinking | `20000` |
| `PERPLEXITY_API_KEY` | API key for Perplexity AI | `None` |
| `VOT1_DEFAULT_RESEARCH_DEPTH` | Default research depth | `medium` |
| `VOT1_SMART_TOKEN_MANAGEMENT` | Enable smart token management | `True` | 