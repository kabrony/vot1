"""
VOT1 OWL Reasoning Module

This module implements basic OWL reasoning capabilities for testing the
self-improvement workflow.
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OWLReasoningEngine:
    """
    Basic OWL reasoning engine for testing purposes.
    
    This is a simplified implementation that doesn't perform actual
    OWL reasoning, but mimics the API for testing the workflow.
    """
    
    def __init__(
        self,
                 ontology_path: Optional[str] = None,
                 memory_manager = None,
        embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    ):
        """
        Initialize the OWL reasoning engine.
        
        Args:
            ontology_path: Path to the OWL ontology file
            memory_manager: MemoryManager instance for integrated reasoning
            embedding_model: Model name for embeddings
        """
        self.ontology_path = ontology_path
        self.memory_manager = memory_manager
        self.embedding_model = embedding_model
        
        # Check if ontology file exists
        if ontology_path and os.path.exists(ontology_path):
            logger.info(f"Initialized OWL reasoning engine with ontology: {ontology_path}")
        else:
            logger.warning(f"Ontology file not found: {ontology_path}")
        
        # Mock knowledge base for testing
        self.kb = {
            "CodeComponent": {
                "subclasses": ["Visualization", "Memory", "OWLReasoning", "Agent"],
                "instances": []
            },
            "Visualization": {
                "subclasses": [],
                "instances": ["THREE.js", "Dashboard"]
            },
            "Memory": {
                "subclasses": [],
                "instances": ["VectorStore", "ConversationMemory"]
            },
            "OWLReasoning": {
                "subclasses": [],
                "instances": ["OWLEngine"]
            },
            "Agent": {
                "subclasses": [],
                "instances": ["SelfImprovementAgent"]
            }
        }
    
    def reason(self, query: str, context: Optional[List[str]] = None) -> str:
        """
        Perform reasoning based on the query and context.
        
        Args:
            query: The reasoning query
            context: Optional context to consider during reasoning
            
        Returns:
            Reasoning result as a string
        """
        # Log the reasoning request
        logger.info(f"Reasoning query: {query}")
        if context:
            logger.debug(f"Context: {context[:1]}...")
        
        # Mock reasoning for code analysis
        if "code" in query.lower() or "analyze" in query.lower():
            return self._mock_code_analysis(query, context)
        
        # Mock reasoning for general queries
        return self._mock_general_reasoning(query)
    
    def _mock_code_analysis(self, query: str, context: Optional[List[str]]) -> str:
        """Provide mock code analysis results."""
        if not context:
            return "No code provided for analysis."
        
        # Extract code if available
        code_context = None
        if isinstance(context[0], str):
            try:
                if context[0].startswith("{"):
                    # Try to parse as JSON
                    data = json.loads(context[0])
                    if "code" in data:
                        code_context = data["code"]
                else:
                    code_context = context[0]
            except:
                code_context = context[0]
        
        if not code_context:
            return "Unable to extract code from context."
        
        # Count lines and identify keywords
        line_count = len(code_context.splitlines())
        
        # Determine code type
        code_type = "Unknown"
        contains_class = False
        contains_function = False
        contains_import = False
        
        if "function" in code_context.lower() or "def " in code_context:
            contains_function = True
        
        if "class" in code_context.lower():
            contains_class = True
        
        if "import " in code_context or "require(" in code_context:
            contains_import = True
        
        # Determine language
        language = "Unknown"
        if "def " in code_context or "import " in code_context and ".py" in query:
            language = "Python"
        elif "function" in code_context or "const" in code_context or "let" in code_context:
            language = "JavaScript"
        
        # Generate mock analysis
        analysis = (
            f"Code Analysis:\n"
            f"- Language: {language}\n"
            f"- Line count: {line_count}\n"
            f"- Contains classes: {contains_class}\n"
            f"- Contains functions: {contains_function}\n"
            f"- Contains imports: {contains_import}\n\n"
            f"This code appears to be related to {self._classify_code_purpose(code_context)}.\n"
            f"It is structured as {'a class-based module' if contains_class else 'a collection of functions' if contains_function else 'a script'}.\n"
            f"The code {'seems to be well-organized' if line_count < 200 else 'is quite extensive and might benefit from modularization'}."
        )
        
        return analysis
    
    def _classify_code_purpose(self, code: str) -> str:
        """Classify the purpose of code based on keywords."""
        keywords = {
            "visualization": ["three", "scene", "camera", "render", "graph", "visualization", "canvas"],
            "memory management": ["memory", "store", "cache", "database", "vector", "embedding"],
            "reasoning": ["reason", "inference", "ontology", "owl", "logic", "knowledge"],
            "agent": ["agent", "autonomous", "improve", "workflow", "tool", "action"]
        }
        
        # Count keyword occurrences
        scores = {category: 0 for category in keywords}
        code_lower = code.lower()
        
        for category, words in keywords.items():
            for word in words:
                scores[category] += code_lower.count(word)
        
        # Find category with highest score
        top_category = max(scores.items(), key=lambda x: x[1])
        
        if top_category[1] == 0:
            return "general-purpose programming"
        
        return top_category[0]
    
    def _mock_general_reasoning(self, query: str) -> str:
        """Provide mock results for general reasoning queries."""
        # Check if query is about specific entities in the KB
        for entity in list(self.kb.keys()) + sum([v["instances"] for v in self.kb.values()], []):
            if entity.lower() in query.lower():
                return self._describe_entity(entity)
        
        # Default response
        return (
            "Based on the OWL ontology, I can infer that the VOT1 system is composed "
            "of several interconnected components including visualization, memory management, "
            "reasoning, and agent capabilities. These components work together to form "
            "a cohesive system for AI orchestration and self-improvement."
        )
    
    def _describe_entity(self, entity: str) -> str:
        """Generate a description of an entity based on the KB."""
        # Check if it's a class
        if entity in self.kb:
            subclasses = self.kb[entity]["subclasses"]
            instances = self.kb[entity]["instances"]
            
            description = f"{entity} is a class in the VOT1 ontology."
            
            if subclasses:
                description += f" It has the following subclasses: {', '.join(subclasses)}."
            
            if instances:
                description += f" It has the following instances: {', '.join(instances)}."
            
            return description
        
        # Check if it's an instance
        for class_name, class_info in self.kb.items():
            if entity in class_info["instances"]:
                return f"{entity} is an instance of the {class_name} class in the VOT1 ontology."
        
        return f"No information found about {entity} in the ontology."


class OWLReasoner:
    """
    Higher-level interface for OWL reasoning in VOT1.
    
    This class provides a simplified interface for OWL reasoning,
    abstracting away the complexity of the underlying engine.
    """
    
    def __init__(self, 
                 ontology_path: Optional[str] = None,
                 memory_manager = None):
        """
        Initialize the OWL reasoner.
        
        Args:
            ontology_path: Path to directory containing ontology files (optional)
            memory_manager: VOT1 memory manager instance (optional)
        """
        self.engine = OWLReasoningEngine(
            ontology_path=ontology_path,
            memory_manager=memory_manager
        )
        logger.info("OWL reasoner initialized")
    
    def reason(self, query: str, context: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform reasoning on a natural language query.
        
        Args:
            query: Natural language query to reason about
            context: Additional context statements to consider
            
        Returns:
            Dictionary with reasoning results
        """
        return self.engine.reason(query, context)
    
    def add_knowledge(self, statements: List[str]) -> int:
        """
        Add knowledge statements to the reasoning engine.
        
        Args:
            statements: List of natural language statements
            
        Returns:
            Number of triples added
        """
        triples = self.engine._context_to_triples(statements)
        
        # Add triples to graph
        old_count = len(self.engine.graph)
        for triple in triples:
            self.engine.graph.add(triple)
        new_count = len(self.engine.graph)
        
        added = new_count - old_count
        self.engine.stats["total_axioms"] = new_count
        
        return added
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        return self.engine.get_stats()
    
    def clear(self) -> None:
        """
        Clear the knowledge graph.
        """
        self.engine.clear()
        logger.info("OWL reasoner knowledge graph cleared")


# Example usage
if __name__ == "__main__":
    # Initialize reasoner
    reasoner = OWLReasoner()
    
    # Add some knowledge
    statements = [
        "A mammal is an animal that has fur and produces milk.",
        "A dog is a mammal that barks.",
        "A cat is a mammal that meows.",
        "Fluffy is a cat.",
        "Rex is a dog."
    ]
    
    added = reasoner.add_knowledge(statements)
    print(f"Added {added} triples to knowledge graph.")
    
    # Perform reasoning
    query = "Is Fluffy a mammal?"
    result = reasoner.reason(query)
    
    print(f"\nQuery: {query}")
    print(f"Response: {result['response']}")
    print("\nReasoning chain:")
    for step in result["reasoning_chain"]:
        print(f"- {step}")
    print(f"\nConfidence: {result['confidence']}")
    print(f"Processing time: {result['processing_time']:.3f} seconds") 