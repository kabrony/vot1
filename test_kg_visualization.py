#!/usr/bin/env python3
"""
Test script for knowledge graph generation and visualization.
Using Claude 3.7 Sonnet with hybrid reasoning capabilities.
IMPORTANT: Always use the latest Claude model version (currently claude-3-7-sonnet-20250219).
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestKGVisualization")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("dotenv module not found, using existing environment variables")
    try:
        with open(".env", "r") as env_file:
            for line in env_file:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip("'\"")
        logger.info("Environment variables manually loaded from .env file")
    except Exception as e:
        logger.warning(f"Failed to manually load .env file: {e}")

# Import Claude client
try:
    import anthropic
except ImportError:
    logger.error("Anthropic library not installed. Please install with: pip install anthropic")
    exit(1)

class KnowledgeGraphTest:
    """
    Test class for knowledge graph and visualization functionality.
    Uses Claude 3.7 Sonnet with hybrid reasoning and extended thinking capabilities
    for complex tasks like knowledge graph construction.
    
    Always use the latest Claude model as it provides superior reasoning abilities.
    """
    
    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize the test class."""
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            raise ValueError("No ANTHROPIC_API_KEY provided or found in environment variables")
        
        self.claude_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        # Use the latest available Claude model
        self.claude_model = "claude-3-7-sonnet-20250219"  # Latest Claude 3.7 Sonnet model
        logger.info(f"Using Claude model: {self.claude_model}")
        self.session_id = str(uuid.uuid4())
        
        # Create output directory
        os.makedirs("output/test_kg", exist_ok=True)
        
        logger.info("Initialized KnowledgeGraphTest with Claude client")
    
    async def construct_knowledge_graph(
        self, 
        topic: str, 
        research_results: Dict[str, Any], 
        analysis_results: Optional[Dict[str, Any]] = None,
        graph_type: str = "standard"
    ) -> Dict[str, Any]:
        """
        Constructs a knowledge graph from research findings and analysis.
        
        Creates structured representation of concepts, relationships, and insights
        that can be visualized and explored in THREE.js.
        
        Args:
            topic: The research topic
            research_results: Primary and follow-up research results
            analysis_results: Optional analysis results to include
            graph_type: Type of knowledge graph to construct (standard, detailed, technical, threejs)
            
        Returns:
            Dictionary with knowledge graph data
        """
        if not self.claude_client:
            return {"error": "Claude client not initialized"}
        
        try:
            # Prepare content from research and analysis
            content = f"## Research Topic: {topic}\n\n"
            
            # Add primary research
            if "primary_research" in research_results:
                content += f"## Primary Research\n\n{research_results['primary_research']}\n\n"
            
            # Add follow-up research
            if "followup_research" in research_results:
                content += "## Follow-up Research\n\n"
                for question, answer in research_results["followup_research"].items():
                    content += f"### Question: {question}\n{answer}\n\n"
            
            # Add code examples if available
            if "code_search" in research_results and research_results["code_search"]:
                content += "## Code Examples\n\n"
                for i, code_item in enumerate(research_results["code_search"][:2], 1):
                    if isinstance(code_item, dict) and "error" not in code_item:
                        code_name = code_item.get("name", f"Example {i}")
                        content += f"### {code_name}\n{code_item.get('description', 'No description')}\n\n"
            
            # Add analysis if available
            if analysis_results and "analysis" in analysis_results:
                content += f"## Analysis\n\n{analysis_results['analysis']}\n\n"
            
            # Configure graph type
            graph_config = {
                "standard": {
                    "prompt": "Please analyze this research and create a knowledge graph with key concepts and their relationships.",
                    "thinking_prompt": "Let's identify the key concepts, entities, relationships, and insights in this research that should be represented in a knowledge graph.",
                    "system_role": "You are an expert knowledge graph specialist. Create a well-structured, comprehensive knowledge graph from research findings, identifying complex relationships through careful analysis."
                },
                "detailed": {
                    "prompt": "Please analyze this research and create a detailed knowledge graph with concepts, properties, relationships, and hierarchies.",
                    "thinking_prompt": "Let's create a comprehensive ontology and knowledge graph from this research, focusing on detailed relationships, properties, and hierarchical structures.",
                    "system_role": "You are a knowledge graph expert specializing in detailed ontologies and complex knowledge structures. Identify nuanced relationships and hierarchies through careful step-by-step analysis."
                },
                "technical": {
                    "prompt": "Please analyze this research and create a technical knowledge graph focused on implementation details, components, and dependencies.",
                    "thinking_prompt": "Let's analyze the technical components, dependencies, architectures, and implementation details in this research for a technical knowledge graph.",
                    "system_role": "You are a technical knowledge graph expert specializing in software architecture and technical relationships. Identify technical dependencies and implementation patterns by breaking down complex systems step-by-step."
                },
                "threejs": {
                    "prompt": "Please analyze this research and create a knowledge graph optimized for THREE.js visualization with visual properties and interaction hints.",
                    "thinking_prompt": "Let's create a knowledge graph specifically designed for visualization in THREE.js, with visual properties, groupings, and interaction possibilities.",
                    "system_role": "You are an expert in knowledge representation and THREE.js visualization. Create knowledge graphs optimized for interactive 3D visualization with understanding of spatial relationships and visual hierarchies."
                }
            }
            
            # Default to standard if graph type not recognized
            if graph_type not in graph_config:
                logger.warning(f"Graph type '{graph_type}' not recognized, defaulting to 'standard'")
                graph_type = "standard"
            
            config = graph_config[graph_type]
            
            # Add specialized instructions for knowledge graph structure
            graph_instructions = """
            Please create a structured knowledge graph with the following components:

            1. Nodes representing key concepts, entities, and ideas
            2. Edges representing relationships between nodes
            3. Properties for nodes and edges that describe their attributes
            4. Groups or categories that nodes belong to

            Structure your response as valid JSON with the following format:
            ```json
            {
                "nodes": [
                    {
                        "id": "unique_id",
                        "label": "Concept Name",
                        "type": "concept|entity|process|technology|resource|etc",
                        "properties": {
                            "property1": "value1",
                            "property2": "value2"
                        },
                        "group": "category_name",
                        "description": "Brief description of this concept",
                        "size": 1-10 (relative importance/size),
                        "source": "primary_research|followup|code|analysis"
                    },
                    ...
                ],
                "edges": [
                    {
                        "source": "source_node_id",
                        "target": "target_node_id",
                        "label": "relationship_type",
                        "properties": {
                            "property1": "value1"
                        },
                        "weight": 1-10 (relationship strength),
                        "description": "Brief description of this relationship"
                    },
                    ...
                ],
                "groups": [
                    {
                        "id": "group_id",
                        "label": "Group Name",
                        "description": "Description of this group of nodes"
                    },
                    ...
                ],
                "metadata": {
                    "topic": "research topic",
                    "nodeCount": integer,
                    "edgeCount": integer,
                    "groupCount": integer,
                    "description": "Brief description of this knowledge graph",
                    "suggestedVisualization": "Description of how to visualize this graph effectively"
                }
            }
            ```
            
            Ensure your knowledge graph:
            - Has clear, meaningful relationships
            - Captures the key concepts from the research
            - Uses descriptive labels for relationships
            - Has appropriate grouping of related concepts
            - Includes 15-40 nodes for standard graphs, more for detailed graphs
            - Has properly connected edges (no orphaned nodes)
            - Represents hierarchical relationships where appropriate
            - Creates a balanced graph structure that can be effectively visualized
            """
            
            # Add specialized instructions based on graph type
            if graph_type == "threejs":
                graph_instructions += """
                For THREE.js visualization optimization, also include these additional properties:
                
                - For nodes:
                  - "visualProperties": {
                      "color": "#hexcolor",
                      "texture": "suggested texture type",
                      "shape": "sphere|cube|cylinder|custom",
                      "initialPosition": [x, y, z], (suggested coordinates)
                      "highlightColor": "#hexcolor",
                      "labelVisibility": "always|onHover|onSelect"
                    }
                
                - For edges:
                  - "visualProperties": {
                      "color": "#hexcolor",
                      "style": "solid|dashed|dotted|arrow",
                      "width": 1-5 (visual width),
                      "curvature": 0-1 (how curved the connection should be),
                      "animated": true|false
                    }
                
                - For the overall graph:
                  - Add a "visualization" object in metadata with:
                    "visualization": {
                      "layout": "force|radial|hierarchical|cluster",
                      "groups": { "groupId": {"color": "#hexcolor"} },
                      "background": "#hexcolor",
                      "defaultNodeSize": number,
                      "defaultEdgeWidth": number,
                      "physics": {
                        "gravity": number,
                        "linkDistance": number,
                        "charge": number
                      }
                    }
                """
            
            # Create prompt for Claude
            system_message = config["system_role"]
            prompt = f"{config['thinking_prompt']}\n\n{config['prompt']}\n\n{graph_instructions}\n\nResearch content:\n\n{content}"
            
            # Call Claude API - with standard parameters supported by the current SDK
            logger.info(f"Calling Claude with model: {self.claude_model}")
            
            # Standard API call with current SDK support 
            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=4000,
                system=system_message,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract thinking content if available
            thinking_content = None
            # Note: Current SDK may not support thinking content extraction
            if hasattr(response, 'thinking'):
                thinking_content = response.thinking
                logger.info("Thinking process captured")
                
                # Save thinking content to file
                thinking_file = f"output/test_kg/thinking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(thinking_file, "w") as f:
                    f.write(thinking_content)
                logger.info(f"Thinking process saved to {thinking_file}")
            
            # Extract JSON from response
            analysis_content = response.content[0].text
            
            # Extract JSON
            import re
            import json
            
            # Find JSON in the response
            json_pattern = r"```(?:json)?\s*({[\s\S]*?})```"
            json_matches = re.findall(json_pattern, analysis_content)
            
            if not json_matches:
                # Try to find anything that looks like JSON
                json_pattern = r"{[\s\S]*\"nodes\"[\s\S]*\"edges\"[\s\S]*}"
                json_matches = re.findall(json_pattern, analysis_content)
            
            if json_matches:
                try:
                    # Clean up the JSON string to fix potential formatting issues
                    json_str = json_matches[0].strip()
                    # Fix common issues with trailing commas
                    json_str = re.sub(r',\s*}', '}', json_str)
                    json_str = re.sub(r',\s*]', ']', json_str)
                    
                    # Additional fixes for JSON formatting issues
                    json_str = re.sub(r'([^\\])\\([^"\\/bfnrtu])', r'\1\\\\\2', json_str)  # Escape backslashes properly
                    json_str = re.sub(r'([^"])\\\'([^"])', r'\1\\\\\'\2', json_str)  # Fix single quotes
                    json_str = re.sub(r'([^\\])"([^"])', r'\1\\"\2', json_str)  # Escape unescaped quotes
                    
                    # Fix arrays with commas right after opening bracket
                    json_str = re.sub(r'\[\s*,', '[', json_str)
                    
                    # Try to fix missing commas between objects
                    json_str = re.sub(r'}(\s*){', r'},\1{', json_str)
                    json_str = re.sub(r'](\s*)\[', r'],\1[', json_str)
                    
                    try:
                        graph_data = json.loads(json_str)
                    except json.JSONDecodeError as json_err:
                        logger.warning(f"Initial JSON parsing failed: {json_err}")
                        logger.warning("Attempting to fix and parse again")
                        
                        # Try removing the problematic line based on error position
                        error_line = str(json_err).split("line ")[1].split(" ")[0]
                        error_col = str(json_err).split("column ")[1].split(" ")[0]
                        lines = json_str.split("\n")
                        logger.warning(f"Error at line {error_line}, column {error_col}")
                        
                        if len(lines) >= int(error_line):
                            problematic_line = lines[int(error_line) - 1]
                            logger.warning(f"Problematic line: {problematic_line}")
                            
                            # Try fixing common issues
                            if ":" in problematic_line and "," not in problematic_line and "}" not in problematic_line:
                                lines[int(error_line) - 1] = problematic_line + ","
                            elif "}" in problematic_line and "," in problematic_line and problematic_line.strip().endswith(",}"):
                                lines[int(error_line) - 1] = problematic_line.replace(",}", "}")
                                
                            json_str = "\n".join(lines)
                            graph_data = json.loads(json_str)
                        else:
                            raise
                    
                    # Validate the structure
                    if "nodes" not in graph_data or "edges" not in graph_data:
                        return {
                            "error": "Invalid knowledge graph structure",
                            "raw_content": analysis_content,
                            "success": False
                        }
                    
                    # Add metadata if missing
                    if "metadata" not in graph_data:
                        graph_data["metadata"] = {
                            "topic": topic,
                            "nodeCount": len(graph_data["nodes"]),
                            "edgeCount": len(graph_data["edges"]),
                            "groupCount": len(graph_data.get("groups", [])),
                            "description": f"Knowledge graph for {topic}",
                            "graphType": graph_type,
                            "model": self.claude_model
                        }
                    else:
                        # Add model info to existing metadata
                        graph_data["metadata"]["model"] = self.claude_model
                    
                    # Create result with graph data
                    result = {
                        "knowledge_graph": graph_data,
                        "graph_id": str(uuid.uuid4()),
                        "success": True,
                        "graph_type": graph_type,
                        "model": self.claude_model,
                        "thinking_content": thinking_content
                    }
                    
                    return result
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing knowledge graph JSON: {e}")
                    # Save the raw JSON for debugging
                    debug_file = f"output/test_kg/failed_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(debug_file, "w") as f:
                        f.write(json_str)
                    logger.error(f"Saved problematic JSON to {debug_file}")
                    
                    return {
                        "error": "Failed to parse knowledge graph JSON",
                        "raw_content": analysis_content,
                        "json_error": str(e),
                        "success": False
                    }
            else:
                return {
                    "error": "No knowledge graph JSON found in response",
                    "raw_content": analysis_content,
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Error in knowledge graph construction: {e}")
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error details: {error_details}")
            return {"error": str(e), "error_details": error_details, "success": False}
    
    async def generate_threejs_visualization(
        self,
        knowledge_graph: Dict[str, Any],
        visualization_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates THREE.js visualization code from a knowledge graph.
        
        Takes a knowledge graph structure and produces ready-to-use THREE.js
        code for visualizing the graph in an interactive 3D environment.
        
        Args:
            knowledge_graph: The knowledge graph data with nodes and edges
            visualization_options: Optional customization options for the visualization
                Can include: backgroundColor, nodeSize, edgeWidth, physics settings, etc.
                
        Returns:
            Dictionary with visualization code and metadata
        """
        if not self.claude_client:
            return {"error": "Claude client not initialized"}
        
        try:
            # Set default visualization options
            default_options = {
                "backgroundColor": "#000000",
                "defaultNodeSize": 5,
                "defaultEdgeWidth": 1,
                "highlightColor": "#ffffff",
                "useForceDirectedLayout": True,
                "useOrbitControls": True,
                "enableLabels": True,
                "colorByGroup": True,
                "animateEdges": True,
                "enableProgressiveLoading": True,
                "usePostprocessing": True,
                "enableInteraction": True,
                "useModernRendering": True
            }
            
            # Merge with provided options
            options = default_options.copy()
            if visualization_options:
                options.update(visualization_options)
            
            # Extract graph metadata
            nodes = knowledge_graph.get("nodes", [])
            edges = knowledge_graph.get("edges", [])
            groups = knowledge_graph.get("groups", [])
            metadata = knowledge_graph.get("metadata", {})
            
            if not nodes or not edges:
                return {"error": "Knowledge graph missing nodes or edges"}
            
            # Prepare prompt for Claude
            system_message = """You are an expert in THREE.js visualization and 3D graphics programming with exceptional coding capabilities.

Your task is to generate complete, production-ready THREE.js code to visualize a knowledge graph in an interactive 3D environment.

The code should:
1. Be well-structured, modular, and optimized for performance
2. Include all necessary HTML, CSS, and JavaScript
3. Implement modern THREE.js best practices (r160+)
4. Handle user interactions (zooming, panning, selecting)
5. Be aesthetically pleasing with good lighting and effects
6. Include detailed comments explaining key implementation details
7. Be ready to copy-paste and run immediately
8. Use the latest THREE.js rendering techniques for optimal performance
9. Include responsive design for different screen sizes
10. Implement accessibility features where appropriate

Your code should be COMPLETE and SELF-CONTAINED without requiring any external dependencies beyond THREE.js itself.
"""

            prompt = f"""I need complete THREE.js code to visualize this knowledge graph:

KNOWLEDGE GRAPH METADATA:
- Nodes: {len(nodes)}
- Edges: {len(edges)}
- Groups: {len(groups)}
- Topic: {metadata.get('topic', 'Knowledge Graph')}

VISUALIZATION OPTIONS:
{json.dumps(options, indent=2)}

KNOWLEDGE GRAPH DATA (SAMPLE):
Nodes: {json.dumps(nodes[:3] if len(nodes) > 3 else nodes, indent=2)}
Edges: {json.dumps(edges[:3] if len(edges) > 3 else edges, indent=2)}
Groups: {json.dumps(groups[:3] if len(groups) > 3 else groups, indent=2)}

Please generate complete, production-ready THREE.js code to visualize this knowledge graph with the following components:

1. HTML file with proper structure and embedded CSS for styling
2. JavaScript code using modern THREE.js that:
   - Creates a scene with the specified background color
   - Implements a force-directed layout for the graph
   - Creates nodes as spheres/objects with sizes based on their importance
   - Creates edges as lines/tubes connecting the nodes
   - Implements color coding based on node groups
   - Adds proper lighting and camera controls
   - Handles user interactions (hover, click, zoom, pan)
   - Shows node labels on hover/selection
   - Implements progressive loading for performance
   - Adds subtle animations for visual appeal
   - Includes post-processing effects if specified
   - Uses WebGL 2.0 features when available
   - Implements responsive design for different screen sizes

Make sure the code is complete, well-commented, and ready to use. Include all necessary initialization, setup, and event handling.
"""

            # Call Claude API
            logger.info(f"Generating THREE.js visualization with Claude {self.claude_model}")
            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=4000,
                system=system_message,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract thinking content if available
            thinking_content = None
            if hasattr(response, 'thinking'):
                thinking_content = response.thinking
                logger.info("Thinking process captured for visualization")
                
                # Save thinking content to file
                thinking_file = f"output/test_kg/viz_thinking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(thinking_file, "w") as f:
                    f.write(thinking_content)
                logger.info(f"Visualization thinking process saved to {thinking_file}")
            
            response_content = response.content[0].text
            
            # Extract code blocks
            import re
            
            # Extract HTML
            html_pattern = r"```html\s*([\s\S]*?)```"
            html_matches = re.findall(html_pattern, response_content)
            html_code = html_matches[0] if html_matches else ""
            
            # Extract JavaScript
            js_pattern = r"```(?:javascript|js)\s*([\s\S]*?)```"
            js_matches = re.findall(js_pattern, response_content)
            js_code = js_matches[0] if js_matches else ""
            
            # Extract CSS
            css_pattern = r"```(?:css)\s*([\s\S]*?)```"
            css_matches = re.findall(css_pattern, response_content)
            css_code = css_matches[0] if css_matches else ""
            
            # If no HTML found but we have JS, try to extract a complete HTML file
            if not html_code and js_code:
                complete_html_pattern = r"<!DOCTYPE html>[\s\S]*?<html>[\s\S]*?</html>"
                complete_matches = re.findall(complete_html_pattern, response_content)
                if complete_matches:
                    html_code = complete_matches[0]
            
            # Create result with visualization code
            result = {
                "visualization": {
                    "html": html_code,
                    "javascript": js_code,
                    "css": css_code,
                    "combined": html_code if html_code and "<script>" in html_code else None,
                    "options": options
                },
                "metadata": {
                    "nodeCount": len(nodes),
                    "edgeCount": len(edges),
                    "groupCount": len(groups),
                    "topic": metadata.get('topic', 'Knowledge Graph'),
                    "model": self.claude_model
                },
                "success": True,
                "thinking_content": thinking_content
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating THREE.js visualization: {e}")
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error details: {error_details}")
            return {"error": str(e), "error_details": error_details, "success": False}

async def run_test():
    """Run the test."""
    logger.info("Starting knowledge graph and visualization test with Claude")
    
    # Create test instance
    test = KnowledgeGraphTest()
    
    # Mock research data
    mock_research = {
        "primary_research": "Force-directed graphs in THREE.js use physics simulations to layout nodes. Key aspects include performance optimization, edge bundling, and interactive features.",
        "followup_research": {
            "What libraries are commonly used?": "Popular libraries for force-directed graphs in THREE.js include force-graph, 3d-force-graph, and THREE-forcegraph. These provide high-level abstractions over raw THREE.js.",
            "How can performance be optimized?": "Performance can be optimized by using WebGL for rendering, implementing level-of-detail techniques, using web workers for physics calculations, and spatial partitioning for large graphs."
        }
    }
    
    # Test knowledge graph construction
    logger.info("Generating knowledge graph...")
    graph_results = await test.construct_knowledge_graph(
        topic="THREE.js force-directed graph visualization",
        research_results=mock_research,
        graph_type="threejs"
    )
    
    if "error" in graph_results:
        logger.error(f"Knowledge graph generation failed: {graph_results['error']}")
        return False
    
    logger.info(f"Knowledge graph generated with {len(graph_results['knowledge_graph']['nodes'])} nodes using {test.claude_model}")
    
    # Save knowledge graph to file
    with open("output/test_kg/knowledge_graph.json", "w") as f:
        json.dump(graph_results["knowledge_graph"], f, indent=2)
    logger.info("Knowledge graph saved to output/test_kg/knowledge_graph.json")
    
    # Test THREE.js visualization
    logger.info("Generating THREE.js visualization...")
    viz_results = await test.generate_threejs_visualization(
        knowledge_graph=graph_results["knowledge_graph"],
        visualization_options={
            "backgroundColor": "#111133",
            "useForceDirectedLayout": True,
            "colorByGroup": True,
            "useModernRendering": True
        }
    )
    
    if "error" in viz_results:
        logger.error(f"Visualization generation failed: {viz_results['error']}")
        return False
    
    # Save visualization files
    os.makedirs("output/test_kg/visualization", exist_ok=True)
    
    # Save HTML
    html_code = viz_results["visualization"].get("html", "")
    if html_code:
        with open("output/test_kg/visualization/graph_visualization.html", "w") as f:
            f.write(html_code)
        logger.info("Visualization HTML saved to output/test_kg/visualization/graph_visualization.html")
    
    # Save JavaScript
    js_code = viz_results["visualization"].get("javascript", "")
    if js_code:
        with open("output/test_kg/visualization/graph_visualization.js", "w") as f:
            f.write(js_code)
        logger.info("Visualization JavaScript saved to output/test_kg/visualization/graph_visualization.js")
    
    # Save combined file with full graph data
    try:
        combined_visualization = html_code
        
        # Insert the full graph data into the visualization
        if combined_visualization and "<script>" in combined_visualization and graph_results["knowledge_graph"]:
            # Convert graph data to JSON string
            graph_data_json = json.dumps(graph_results["knowledge_graph"], indent=2)
            
            # Find a good place to insert the data (after the first script tag)
            script_index = combined_visualization.find("<script>") + 8
            data_insertion = f"\n  // Knowledge graph data\n  const graphData = {graph_data_json};\n"
            
            # Insert the data
            combined_visualization = combined_visualization[:script_index] + data_insertion + combined_visualization[script_index:]
            
            # Save the combined file
            with open("output/test_kg/visualization/complete_visualization.html", "w") as f:
                f.write(combined_visualization)
            logger.info("Complete visualization saved to output/test_kg/visualization/complete_visualization.html")
    except Exception as e:
        logger.error(f"Error creating combined visualization: {e}")
    
    logger.info("Test completed successfully with Claude")
    return True

if __name__ == "__main__":
    asyncio.run(run_test()) 