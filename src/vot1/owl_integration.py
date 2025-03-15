"""
OWL Integration for VOT1

This module integrates the Camel-AI's OWL (Ontology and Workflow-based Language) framework 
with VOT1 to enhance reasoning capabilities, structured thinking, and knowledge representation.

OWL provides a powerful framework for:
1. Structured reasoning with ontology-based knowledge organization
2. Step-by-step decision making with workflow management
3. Enhanced problem-solving capabilities
"""

import logging
import os
import sys
from typing import Dict, List, Optional, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Try to import from the local owl repository if it's been cloned
    sys.path.append(os.path.join(os.path.dirname(__file__), '../..', 'owl'))
    from owl.reasoning.base import ReasoningAgent
    from owl.reasoning.react import ReActAgent
    from owl.reasoning.cot import ChainOfThoughtAgent
    from owl.reasoning.reflexion import ReflexionAgent
    from owl.reasoning.tot import TreeOfThoughtAgent
    logger.info("Successfully imported OWL from local repository")
except ImportError:
    try:
        # Try to import from installed package
        from owl.reasoning.base import ReasoningAgent
        from owl.reasoning.react import ReActAgent
        from owl.reasoning.cot import ChainOfThoughtAgent
        from owl.reasoning.reflexion import ReflexionAgent
        from owl.reasoning.tot import TreeOfThoughtAgent
        logger.info("Successfully imported OWL from installed package")
    except ImportError:
        logger.error("Failed to import OWL. Please install it with: pip install camel-owl")
        # Create mock classes to prevent errors if OWL is not installed
        class ReasoningAgent:
            def __init__(self, *args, **kwargs):
                logger.warning("Using mock ReasoningAgent - OWL not properly installed")
            
            def reason(self, *args, **kwargs):
                return {"reasoning": "OWL not installed - using mock reasoning"}
        
        class ReActAgent(ReasoningAgent):
            pass
        
        class ChainOfThoughtAgent(ReasoningAgent):
            pass
        
        class ReflexionAgent(ReasoningAgent):
            pass
        
        class TreeOfThoughtAgent(ReasoningAgent):
            pass

class OwlEnhancedReasoning:
    """
    Enhanced reasoning capabilities using OWL framework.
    This class provides a unified interface to various reasoning strategies
    from the OWL framework.
    """
    
    def __init__(self, 
                 default_strategy: str = "tot", 
                 model_name: str = "claude-3-7-sonnet",
                 verbose: bool = False):
        """
        Initialize OwlEnhancedReasoning with specified strategy and model.
        
        Args:
            default_strategy: One of 'react', 'cot', 'reflexion', 'tot'
            model_name: The LLM model to use
            verbose: Whether to output detailed reasoning steps
        """
        self.verbose = verbose
        self.model_name = model_name
        self.default_strategy = default_strategy
        
        # Map strategy names to their agent classes
        self.strategy_map = {
            "react": ReActAgent,
            "cot": ChainOfThoughtAgent,
            "reflexion": ReflexionAgent,
            "tot": TreeOfThoughtAgent
        }
        
        # Initialize agents dict - will be lazily loaded when needed
        self.agents = {}
        
    def _get_agent(self, strategy: str) -> ReasoningAgent:
        """Get or create an agent for the specified strategy."""
        if strategy not in self.strategy_map:
            raise ValueError(f"Unknown strategy: {strategy}. Choose from {list(self.strategy_map.keys())}")
        
        if strategy not in self.agents:
            agent_class = self.strategy_map[strategy]
            self.agents[strategy] = agent_class(model_name=self.model_name, verbose=self.verbose)
        
        return self.agents[strategy]
    
    def reason(self, 
              query: str, 
              strategy: Optional[str] = None,
              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Apply enhanced reasoning to the query using the specified strategy.
        
        Args:
            query: The question or task to reason about
            strategy: The reasoning strategy to use (defaults to self.default_strategy)
            context: Additional context information
            
        Returns:
            Dict containing reasoning process and final answer
        """
        strategy = strategy or self.default_strategy
        agent = self._get_agent(strategy)
        
        logger.info(f"Reasoning using {strategy} strategy")
        result = agent.reason(query, context=context or {})
        
        return result
    
    def multi_strategy_reason(self, 
                             query: str, 
                             strategies: List[str] = None) -> Dict[str, Any]:
        """
        Apply multiple reasoning strategies and combine their results.
        
        Args:
            query: The question or task to reason about
            strategies: List of strategies to use, if None uses all available strategies
            
        Returns:
            Dict containing reasoning processes and consolidated answer
        """
        strategies = strategies or list(self.strategy_map.keys())
        results = {}
        
        for strategy in strategies:
            results[strategy] = self.reason(query, strategy=strategy)
        
        # TODO: Implement more sophisticated result consolidation
        # For now, we'll return all results and the TOT result as the final answer
        return {
            "detailed_results": results,
            "consolidated_answer": results.get(self.default_strategy, {}).get("answer", 
                                   "No consolidated answer available")
        }

class FeedbackLoopEnhancer:
    """
    Implements a feedback loop for improving reasoning over time.
    This enables the system to learn from past interactions and improve
    its reasoning capabilities.
    """
    
    def __init__(self, 
                 reasoning_engine: OwlEnhancedReasoning,
                 memory_manager=None):
        """
        Initialize the feedback loop enhancer.
        
        Args:
            reasoning_engine: The OwlEnhancedReasoning instance to enhance
            memory_manager: Optional memory manager to store feedback
        """
        self.reasoning_engine = reasoning_engine
        self.memory_manager = memory_manager
        self.feedback_history = []
    
    def reason_with_feedback(self, 
                            query: str, 
                            strategy: Optional[str] = None,
                            previous_feedback: Optional[str] = None) -> Dict[str, Any]:
        """
        Apply reasoning with feedback from previous interactions.
        
        Args:
            query: The question or task to reason about
            strategy: The reasoning strategy to use
            previous_feedback: Any feedback from previous iterations
            
        Returns:
            Dict containing reasoning process, answer, and metadata
        """
        enhanced_context = {
            "previous_feedback": previous_feedback,
            "feedback_history": self.feedback_history[-5:] if self.feedback_history else []
        }
        
        # Apply reasoning
        result = self.reasoning_engine.reason(
            query, 
            strategy=strategy,
            context=enhanced_context
        )
        
        # Add metadata about the feedback process
        result["feedback_enhanced"] = bool(previous_feedback or self.feedback_history)
        
        return result
    
    def add_feedback(self, query: str, reasoning_result: Dict[str, Any], feedback: str) -> None:
        """
        Add feedback for a specific reasoning process.
        
        Args:
            query: The original query
            reasoning_result: The result from the reasoning process
            feedback: The feedback to incorporate
        """
        feedback_entry = {
            "query": query,
            "strategy": reasoning_result.get("strategy", self.reasoning_engine.default_strategy),
            "reasoning": reasoning_result.get("reasoning", ""),
            "answer": reasoning_result.get("answer", ""),
            "feedback": feedback,
            "timestamp": import_time_module_and_get_timestamp()
        }
        
        # Add to history
        self.feedback_history.append(feedback_entry)
        
        # Store in memory if available
        if self.memory_manager:
            self.memory_manager.add_memory(
                content=str(feedback_entry),
                memory_type="feedback",
                metadata=feedback_entry
            )

def import_time_module_and_get_timestamp():
    """Helper function to import time module and get current timestamp."""
    import datetime
    return datetime.datetime.now().isoformat() 