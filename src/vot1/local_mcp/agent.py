import json
import logging
import time
import threading
import queue
import uuid
from typing import Dict, List, Any, Optional, Callable

# Import the VOTai ASCII art module
from .ascii_art import get_votai_ascii

logger = logging.getLogger(__name__)

class FeedbackAgent:
    """
    An agent that can perform tasks and communicate with other agents.
    Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
    """
    
    def __init__(self, orchestrator, name: str, capabilities: List[str]):
        """
        Initialize a new agent.
        
        Args:
            orchestrator: The MCPOrchestrator instance
            name: Name of the agent
            capabilities: List of agent capabilities
        """
        self.orchestrator = orchestrator
        self.name = name
        self.capabilities = capabilities
        self.agent_id = orchestrator.register_agent(name, capabilities)
        self.id = self.agent_id  # alias for agent_id for simplicity
        self.task_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.running = True  # Start as running by default
        self.thread = None
        self.logger = logging.getLogger(f"agent.{name}")
        self.memory = {}
        self.tasks = {}  # Store tasks by ID
        
        # Create callback for receiving messages
        orchestrator.register_callback("message", self._handle_message_event)
        
        # Start the agent thread to process tasks
        self.start()
        
        # Display the agent signature
        self.display_signature()
    
    def display_signature(self, size="small"):
        """
        Display the VOTai ASCII art signature for this agent.
        
        Args:
            size: Size of the ASCII art ("minimal", "small", "medium", "large")
        """
        signature = get_votai_ascii(size)
        self.logger.info(f"\n{signature}\nVOTai {self.name} agent initialized with capabilities: {self.capabilities}")
    
    def connect_to(self, other_agent) -> bool:
        """Connect to another agent to enable communication."""
        return self.orchestrator.connect_agents(self.agent_id, other_agent.agent_id)
    
    def send_message(self, to_agent_id: str, content: Dict[str, Any]) -> Optional[str]:
        """Send a message to another agent."""
        return self.orchestrator.send_message(self.agent_id, to_agent_id, content)
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages for this agent."""
        return self.orchestrator.get_messages(self.agent_id)
    
    def call_function(self, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP function."""
        return self.orchestrator.call_mcp_function(self.agent_id, function_name, params)
    
    def add_task(self, task_type: str, task_data: Dict[str, Any]) -> str:
        """
        Add a task to the agent's queue.
        
        Args:
            task_type: Type of task to add
            task_data: Data for the task
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "type": task_type,
            "data": task_data,
            "timestamp": time.time(),
            "status": "queued"
        }
        self.tasks[task_id] = task
        self.task_queue.put(task)
        self.logger.info(f"Added task {task_id} of type {task_type}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def _handle_message_event(self, event_data: Dict[str, Any]):
        """Handle incoming message events."""
        if event_data.get("to_agent_id") == self.agent_id:
            # This message is for us
            from_agent_id = event_data.get("from_agent_id")
            content = event_data.get("content", {})
            message_id = event_data.get("id")
            
            self.logger.info(f"Received message from agent {from_agent_id}")
            
            # Add the message to the response queue
            self.response_queue.put({
                "type": "message",
                "from_agent_id": from_agent_id,
                "content": content,
                "message_id": message_id,
                "timestamp": time.time()
            })
            
            # If the message contains a task, also add it as a task
            if isinstance(content, dict) and "task" in content:
                self.logger.info(f"Message contains task: {content['task']}")
                self.add_task(content["task"], content.get("data", {}))
    
    def start(self):
        """Start the agent thread to process tasks."""
        if self.thread and self.thread.is_alive():
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._process_tasks)
        self.thread.daemon = True
        self.thread.start()
        self.logger.info(f"Agent {self.name} started")
    
    def stop(self):
        """Stop the agent thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=3.0)
        self.logger.info(f"Agent {self.name} stopped")
    
    def _process_tasks(self):
        """Process tasks from the queue."""
        while self.running:
            try:
                # Check for new messages
                messages = self.get_messages()
                for message in messages:
                    self.logger.debug(f"Processing message: {message}")
                    content = message.get("content", {})
                    if "task" in content:
                        self.add_task(content["task"], content.get("data", {}))
                
                # Check for tasks
                try:
                    task = self.task_queue.get(timeout=1.0)
                    self.logger.info(f"Processing task: {task['type']} (ID: {task['id']})")
                    task["status"] = "processing"
                    self._handle_task(task)
                    task["status"] = "completed"
                    self.task_queue.task_done()
                except queue.Empty:
                    pass
                    
            except Exception as e:
                self.logger.error(f"Error in agent task processing: {e}")
                time.sleep(1.0)  # Prevent tight loop in case of errors
    
    def _handle_task(self, task: Dict[str, Any]):
        """Handle a specific task."""
        task_id = task.get("id")
        task_type = task.get("type")
        task_data = task.get("data", {})
        
        if task_type == "call_function":
            # Call MCP function
            function_name = task_data.get("function_name")
            params = task_data.get("params", {})
            
            if function_name:
                self.logger.info(f"Calling function: {function_name}")
                result = self.call_function(function_name, params)
                
                # Add response to the response queue
                self.response_queue.put({
                    "task_id": task_id,
                    "type": "function_response",
                    "request": task_data,
                    "result": result,
                    "timestamp": time.time()
                })
        
        elif task_type == "query":
            # Perform a query based on agent capabilities
            query = task_data.get("query")
            
            if query and "search" in self.capabilities:
                # Example: Perform a search with Perplexity
                self.logger.info(f"Performing search for: {query}")
                result = self.call_function("mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH", {
                    "params": {
                        "systemContent": "You are a helpful research assistant.",
                        "userContent": query,
                        "temperature": 0.7
                    }
                })
                
                # Add response to the response queue
                self.response_queue.put({
                    "task_id": task_id,
                    "type": "query_response",
                    "query": query,
                    "result": result,
                    "timestamp": time.time()
                })
        
        elif task_type == "analyze_repo":
            # Analyze a GitHub repository
            repo = task_data.get("repo")
            
            if repo and "github" in self.capabilities:
                self.logger.info(f"Analyzing repository: {repo}")
                parts = repo.split("/")
                if len(parts) == 2:
                    owner, repo_name = parts
                    result = self.call_function("mcp_GITHUB_SEARCH_REPOSITORIES", {
                        "params": {
                            "q": f"repo:{owner}/{repo_name}",
                            "sort": "updated",
                            "order": "desc"
                        }
                    })
                    
                    # Add response to the response queue
                    self.response_queue.put({
                        "task_id": task_id,
                        "type": "repo_analysis",
                        "repo": repo,
                        "result": result,
                        "timestamp": time.time()
                    })
        
        elif task_type == "scrape_url":
            # Scrape a URL
            url = task_data.get("url")
            
            if url and ("web" in self.capabilities or "web_scraping" in self.capabilities or "firecrawl" in self.capabilities):
                self.logger.info(f"Scraping URL: {url}")
                result = self.call_function("mcp_FIRECRAWL_FIRECRAWL_SCRAPE_EXTRACT_DATA_LLM", {
                    "params": {
                        "url": url,
                        "formats": ["text"],
                        "onlyMainContent": True
                    }
                })
                
                # Add response to the response queue
                self.response_queue.put({
                    "task_id": task_id,
                    "type": "url_scrape",
                    "url": url,
                    "result": result,
                    "timestamp": time.time()
                })
        
        elif task_type == "process_search_results":
            # Process search results
            query = task_data.get("query")
            results = task_data.get("results")
            
            if query and results:
                self.logger.info(f"Processing search results for: {query}")
                
                # Extract URLs from the results
                urls = self._extract_urls_from_results(results)
                
                if urls:
                    self.logger.info(f"Found {len(urls)} URLs in search results")
                    
                    # Process the first URL
                    if "web" in self.capabilities or "web_scraping" in self.capabilities or "firecrawl" in self.capabilities:
                        self.add_task("scrape_url", {"url": urls[0]})
                
                # Add response to the response queue
                self.response_queue.put({
                    "task_id": task_id,
                    "type": "search_results_processed",
                    "query": query,
                    "url_count": len(urls) if urls else 0,
                    "timestamp": time.time()
                })
        
        elif task_type == "memory":
            # Handle memory operations
            operation = task_data.get("operation")
            
            if operation == "store":
                # Store a memory
                key = task_data.get("key")
                value = task_data.get("value")
                tags = task_data.get("tags", [])
                
                if key and value is not None:
                    self.orchestrator.store_memory(key, value, tags)
                    self.logger.info(f"Stored memory: {key}")
                    
                    # Add response to the response queue
                    self.response_queue.put({
                        "task_id": task_id,
                        "type": "memory_stored",
                        "key": key,
                        "timestamp": time.time()
                    })
            
            elif operation == "retrieve":
                # Retrieve a memory
                key = task_data.get("key")
                
                if key:
                    value = self.orchestrator.retrieve_memory(key)
                    self.logger.info(f"Retrieved memory: {key}")
                    
                    # Add response to the response queue
                    self.response_queue.put({
                        "task_id": task_id,
                        "type": "memory_retrieved",
                        "key": key,
                        "value": value,
                        "timestamp": time.time()
                    })
        
        # Handle memory_retrieval as an alias for memory with operation retrieve
        elif task_type == "memory_retrieval":
            # Retrieve a memory
            key = task_data.get("key")
            
            if key:
                value = self.orchestrator.retrieve_memory(key)
                self.logger.info(f"Retrieved memory: {key}")
                
                # Add response to the response queue
                self.response_queue.put({
                    "task_id": task_id,
                    "type": "memory_retrieved",
                    "key": key,
                    "value": value,
                    "timestamp": time.time()
                })
        
        else:
            self.logger.warning(f"Unknown task type: {task_type}")
            # Add error response to the response queue
            self.response_queue.put({
                "task_id": task_id,
                "type": "error",
                "error": f"Unknown task type: {task_type}",
                "timestamp": time.time()
            })
    
    def _extract_urls_from_results(self, results: Dict[str, Any]) -> List[str]:
        """Extract URLs from search results."""
        urls = []
        
        # Try to extract from Perplexity results
        if "function" in results and results["function"] == "mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH":
            response = results.get("response", {})
            text = response.get("text", "")
            
            # Simple URL extraction (can be improved)
            import re
            url_pattern = re.compile(r'https?://[^\s]+')
            urls = url_pattern.findall(text)
        
        return urls
    
    def get_responses(self, max_responses: int = 10) -> List[Dict[str, Any]]:
        """Get responses from the response queue."""
        responses = []
        for _ in range(max_responses):
            try:
                response = self.response_queue.get_nowait()
                responses.append(response)
                self.response_queue.task_done()
            except queue.Empty:
                break
        return responses
    
    def wait_for_responses(self, timeout: float = 10.0) -> List[Dict[str, Any]]:
        """
        Wait for responses from the agent.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            List of responses
        """
        start_time = time.time()
        responses = []
        
        while time.time() - start_time < timeout:
            new_responses = self.get_responses()
            if new_responses:
                responses.extend(new_responses)
                
            if not self.task_queue.empty():
                # Still processing tasks, keep waiting
                time.sleep(0.1)
            else:
                # No more tasks, check one more time for responses
                time.sleep(0.5)
                final_responses = self.get_responses()
                if final_responses:
                    responses.extend(final_responses)
                break
        
        return responses 