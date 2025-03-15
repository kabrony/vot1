"""
VOT1 Swarm Agent Architecture

This module implements a swarm intelligence approach to AI problem-solving, 
where multiple specialized agents collaborate to solve complex tasks.

The system uses a combination of:
1. Agent specialization - different agents focus on different aspects
2. Orchestration - a coordinator agent assigns tasks and consolidates results
3. Iterative refinement - solutions are improved through multiple rounds of feedback
4. Emergent intelligence - the system as a whole exhibits capabilities beyond individual agents
"""

import logging
import threading
import uuid
import time
from typing import Dict, List, Optional, Any, Union, Callable
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SwarmAgent:
    """
    Individual agent in the swarm with specialized capabilities.
    Each agent has a particular focus, system prompt, and model configuration.
    """
    
    def __init__(self, 
                 agent_id: str,
                 name: str,
                 specialization: str,
                 system_prompt: str,
                 model_name: str = "claude-3-7-sonnet", 
                 temperature: float = 0.5,
                 client=None):
        """
        Initialize a swarm agent with specific capabilities.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            specialization: Area of expertise (e.g., "creativity", "analysis", "coding")
            system_prompt: Custom system prompt defining the agent's behavior
            model_name: LLM model to use
            temperature: Temperature setting for generation
            client: Optional pre-configured client instance
        """
        self.agent_id = agent_id
        self.name = name
        self.specialization = specialization
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.temperature = temperature
        self._client = client
        self.active = True
        self.task_history = []
        
        # Lazily load the client when needed
        if self._client is None:
            self._load_client()
    
    def _load_client(self):
        """Initialize the Claude client."""
        try:
            from vot1.client import EnhancedClaudeClient
            self._client = EnhancedClaudeClient(
                model=self.model_name,
                temperature=self.temperature,
                system=self.system_prompt
            )
            logger.info(f"Agent {self.name} initialized with {self.model_name}")
        except ImportError as e:
            logger.error(f"Failed to load EnhancedClaudeClient: {e}")
            raise
    
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task assigned to this agent.
        
        Args:
            task: Dictionary containing task details
            
        Returns:
            Dictionary with task results and metadata
        """
        if not self.active:
            logger.warning(f"Agent {self.name} is inactive but received a task")
            return {
                "agent_id": self.agent_id,
                "name": self.name,
                "status": "inactive",
                "result": None,
                "error": "Agent is inactive"
            }
        
        if not self._client:
            self._load_client()
        
        task_id = task.get("task_id", str(uuid.uuid4()))
        prompt = task.get("prompt", "")
        context = task.get("context", {})
        
        logger.info(f"Agent {self.name} processing task {task_id}")
        
        try:
            # Add agent specialization context to the prompt
            enhanced_prompt = f"As a specialist in {self.specialization}, {prompt}"
            
            # Generate response using the enhanced client
            response = self._client.generate(
                enhanced_prompt,
                context=context
            )
            
            result = {
                "agent_id": self.agent_id,
                "name": self.name,
                "task_id": task_id,
                "specialization": self.specialization,
                "status": "completed",
                "result": response,
                "timestamp": time.time()
            }
            
            # Add to task history
            self.task_history.append({
                "task_id": task_id,
                "prompt": prompt,
                "result": result,
                "timestamp": time.time()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error in agent {self.name} processing task {task_id}: {e}")
            return {
                "agent_id": self.agent_id,
                "name": self.name,
                "task_id": task_id,
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def update_system_prompt(self, new_prompt: str) -> None:
        """Update the agent's system prompt."""
        self.system_prompt = new_prompt
        # Recreate client with new settings if it exists
        if self._client:
            self._load_client()


class SwarmOrchestrator:
    """
    Coordinates multiple agents in a swarm to solve complex problems.
    Responsible for task distribution, result aggregation, and ensuring
    collaborative problem-solving.
    """
    
    DEFAULT_AGENT_TEMPLATES = {
        "creative": {
            "name": "Creative Explorer",
            "specialization": "creativity and ideation",
            "system_prompt": "You are a creative idea generator that thinks outside the box. Your strength is in generating novel approaches, metaphors, and creative solutions that others might miss. Always prioritize originality over convention."
        },
        "analytical": {
            "name": "Analytical Thinker",
            "specialization": "logical analysis and critical thinking",
            "system_prompt": "You are an analytical problem solver focused on logical reasoning. Your strength is in breaking down complex problems, identifying inconsistencies, and applying structured analysis. Always prioritize clarity and precision in your thinking."
        },
        "research": {
            "name": "Research Specialist",
            "specialization": "information gathering and synthesis",
            "system_prompt": "You are a research specialist adept at gathering and synthesizing information. Your strength is in finding relevant data points, summarizing complex topics, and organizing information coherently. Always prioritize accuracy and comprehensiveness."
        },
        "implementation": {
            "name": "Implementation Expert",
            "specialization": "practical implementation and execution",
            "system_prompt": "You are an implementation specialist focused on turning ideas into actionable plans. Your strength is in creating step-by-step approaches, identifying practical considerations, and considering logistics. Always prioritize feasibility and practicality."
        },
        "critic": {
            "name": "Critical Evaluator",
            "specialization": "evaluation and critique",
            "system_prompt": "You are a critical evaluator that examines ideas for flaws and weaknesses. Your strength is in identifying potential issues, unintended consequences, and areas for improvement. Always prioritize constructive criticism that leads to improvement."
        }
    }
    
    def __init__(self, 
                 num_agents: int = 3,
                 agent_types: Optional[List[str]] = None,
                 custom_agents: Optional[List[Dict[str, Any]]] = None,
                 feedback_loops: int = 2,
                 coordinator_model: str = "claude-3-7-sonnet",
                 memory_manager=None):
        """
        Initialize the swarm orchestrator.
        
        Args:
            num_agents: Number of agents to use if using default templates
            agent_types: List of agent types to use from templates
            custom_agents: List of custom agent configurations
            feedback_loops: Number of refinement iterations
            coordinator_model: Model to use for the coordinator
            memory_manager: Optional memory manager for storing results
        """
        self.feedback_loops = feedback_loops
        self.memory_manager = memory_manager
        
        # Initialize agents
        self.agents = []
        
        if custom_agents:
            # Use custom agent configurations
            for agent_config in custom_agents:
                agent_id = agent_config.get("agent_id", str(uuid.uuid4()))
                agent = SwarmAgent(
                    agent_id=agent_id,
                    name=agent_config.get("name", f"Agent-{agent_id}"),
                    specialization=agent_config.get("specialization", "general"),
                    system_prompt=agent_config.get("system_prompt", ""),
                    model_name=agent_config.get("model_name", "claude-3-7-sonnet"),
                    temperature=agent_config.get("temperature", 0.7)
                )
                self.agents.append(agent)
        else:
            # Use template-based agents
            agent_types = agent_types or list(self.DEFAULT_AGENT_TEMPLATES.keys())[:num_agents]
            
            for agent_type in agent_types[:num_agents]:
                if agent_type in self.DEFAULT_AGENT_TEMPLATES:
                    template = self.DEFAULT_AGENT_TEMPLATES[agent_type]
                    agent_id = str(uuid.uuid4())
                    agent = SwarmAgent(
                        agent_id=agent_id,
                        name=template["name"],
                        specialization=template["specialization"],
                        system_prompt=template["system_prompt"],
                        model_name=coordinator_model
                    )
                    self.agents.append(agent)
        
        # Initialize coordinator
        self.coordinator = self._create_coordinator(coordinator_model)
        
        logger.info(f"Swarm initialized with {len(self.agents)} agents and {feedback_loops} feedback loops")
    
    def _create_coordinator(self, model_name: str):
        """Create the coordinator agent."""
        try:
            from vot1.client import EnhancedClaudeClient
            
            coordinator_prompt = """
            You are a Swarm Coordinator that orchestrates multiple AI agents to solve complex problems.
            Your responsibilities include:
            1. Breaking down complex tasks into subtasks appropriate for specialized agents
            2. Assigning tasks to the most suitable agents based on their specialization
            3. Consolidating and synthesizing results from multiple agents
            4. Identifying conflicts, gaps, or inconsistencies in agent outputs
            5. Producing a cohesive final solution that leverages the strengths of all agents
            
            Always maintain a meta-perspective on the problem-solving process, focusing on how
            different viewpoints and approaches can be combined to create superior solutions.
            """
            
            coordinator = EnhancedClaudeClient(
                model=model_name, 
                system=coordinator_prompt,
                temperature=0.3  # Lower temperature for more consistent coordination
            )
            
            return coordinator
            
        except ImportError as e:
            logger.error(f"Failed to load EnhancedClaudeClient for coordinator: {e}")
            raise
    
    def solve_complex_task(self, 
                          task: str, 
                          context: Optional[Dict[str, Any]] = None,
                          max_workers: int = 3) -> Dict[str, Any]:
        """
        Solve a complex task using the swarm of agents.
        
        Args:
            task: The main task to solve
            context: Additional context for the task
            max_workers: Maximum number of parallel workers
            
        Returns:
            Dictionary with the final solution and process details
        """
        context = context or {}
        task_id = str(uuid.uuid4())
        
        logger.info(f"Starting swarm solution for task: {task_id}")
        
        # Step 1: Task decomposition by coordinator
        decomposition_prompt = f"""
        I need to break down the following complex task into subtasks for specialized agents:
        
        TASK: {task}
        
        For each subtask, please:
        1. Provide a clear description of what needs to be addressed
        2. Explain why this subtask is important to the overall solution
        3. Indicate which type of specialist would be best suited (choose from: {[agent.specialization for agent in self.agents]})
        
        Finally, suggest a process for integrating the results of these subtasks into a cohesive solution.
        """
        
        decomposition = self.coordinator.generate(decomposition_prompt)
        
        # Process decomposition to extract subtasks (simplified for now)
        subtasks = self._parse_subtasks(decomposition, task, self.agents)
        
        # Step 2: Parallel task processing
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(agent.process_task, subtask) for agent, subtask in subtasks]
            for future in futures:
                results.append(future.result())
        
        # Step 3: Result integration and refinement
        solution = self._integrate_results(task, results, context)
        
        # Step 4: Feedback loop refinement
        for i in range(self.feedback_loops):
            logger.info(f"Refinement loop {i+1}/{self.feedback_loops}")
            solution = self._refine_solution(task, solution, results)
        
        # Step 5: Final solution and metadata
        final_solution = {
            "task_id": task_id,
            "task": task,
            "solution": solution,
            "process": {
                "decomposition": decomposition,
                "subtasks": subtasks,
                "agent_results": results,
            },
            "metadata": {
                "num_agents": len(self.agents),
                "feedback_loops": self.feedback_loops,
                "timestamp": time.time()
            }
        }
        
        # Step 6: Store in memory if available
        if self.memory_manager:
            self.memory_manager.add_memory(
                content=f"Swarm solution for: {task}\n\n{solution}",
                memory_type="swarm_solution",
                metadata={
                    "task_id": task_id,
                    "task": task,
                    "num_agents": len(self.agents),
                    "timestamp": time.time()
                }
            )
        
        return final_solution
    
    def _parse_subtasks(self, decomposition: str, main_task: str, agents: List[SwarmAgent]) -> List[tuple]:
        """
        Parse the decomposition output into subtasks assigned to agents.
        
        This is a simplified implementation - in a full system, this would use more 
        sophisticated parsing to extract structured subtasks.
        """
        # For now, we'll do a simple approach - assign the main task to all agents
        # with different perspectives based on their specialization
        subtasks = []
        
        for agent in agents:
            subtask = {
                "task_id": str(uuid.uuid4()),
                "prompt": f"Please address this task from your perspective as a specialist in {agent.specialization}: {main_task}",
                "context": {
                    "main_task": main_task,
                    "decomposition": decomposition,
                    "specialization": agent.specialization
                }
            }
            subtasks.append((agent, subtask))
        
        return subtasks
    
    def _integrate_results(self, task: str, results: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """
        Integrate results from multiple agents into a cohesive solution.
        """
        # Prepare integration prompt
        integration_prompt = f"""
        I need to integrate the results from multiple specialized agents working on this task:
        
        ORIGINAL TASK: {task}
        
        AGENT RESULTS:
        """
        
        for result in results:
            agent_name = result.get("name", "Unknown agent")
            specialization = result.get("specialization", "Unknown")
            agent_result = result.get("result", "No result")
            
            integration_prompt += f"""
            --- {agent_name} (Specialist in {specialization}) ---
            {agent_result}
            """
        
        integration_prompt += """
        Please synthesize these different perspectives into a comprehensive solution that:
        1. Incorporates the valuable insights from each agent
        2. Resolves any contradictions or conflicts
        3. Addresses all aspects of the original task
        4. Presents a cohesive and unified response
        """
        
        # Generate integrated solution
        integrated_solution = self.coordinator.generate(integration_prompt)
        
        return integrated_solution
    
    def _refine_solution(self, task: str, current_solution: str, agent_results: List[Dict[str, Any]]) -> str:
        """
        Refine the current solution through a feedback loop.
        """
        refinement_prompt = f"""
        I need to further refine and improve our current solution to this task:
        
        ORIGINAL TASK: {task}
        
        CURRENT SOLUTION:
        {current_solution}
        
        Please critically evaluate this solution and suggest specific improvements by:
        1. Identifying any weaknesses, gaps, or inconsistencies
        2. Suggesting concrete ways to enhance the solution
        3. Ensuring all important aspects from the specialized agents have been properly incorporated
        4. Making the solution more comprehensive, precise, and actionable
        
        Then provide an improved version of the full solution.
        """
        
        # Generate refined solution
        refined_solution = self.coordinator.generate(refinement_prompt)
        
        return refined_solution 