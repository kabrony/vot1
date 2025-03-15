"""
VOTai Memory Bridge for Composio

This module provides a bridge between Composio tools and VOTai's memory system,
enabling hybrid thinking capabilities with Claude 3.7 Sonnet and maximum token utilization.
"""

import os
import json
import time
import asyncio
import datetime
from typing import Dict, List, Any, Optional, Union, Callable, Tuple, AsyncGenerator

try:
    # Absolute imports (for installed package)
    from vot1.utils.branding import format_status, format_memory_entry
    from vot1.utils.logging import get_logger
except ImportError:
    # Relative imports (for development)
    from src.vot1.utils.branding import format_status, format_memory_entry
    from src.vot1.utils.logging import get_logger

logger = get_logger(__name__)

class ComposioMemoryBridge:
    """
    Memory bridge for Composio integration with Claude 3.7 Sonnet.
    
    Features:
    - Stores tool execution results and contexts in memory
    - Provides hybrid thinking capabilities with Claude 3.7 Sonnet
    - Integrates with Perplexity for deep research
    - Maximum token utilization across memory interactions
    - Supports streaming responses
    """
    
    # Claude 3.7 Sonnet context window size (tokens)
    CLAUDE_37_SONNET_MAX_TOKENS = 15000
    
    # Memory type constants
    MEMORY_TYPE_TOOL_EXECUTION = "tool_execution"
    MEMORY_TYPE_OBSERVATION = "observation"
    MEMORY_TYPE_THOUGHT = "thought"
    MEMORY_TYPE_ACTION = "action"
    MEMORY_TYPE_QUERY = "query"
    MEMORY_TYPE_RESPONSE = "response"
    
    def __init__(
        self,
        memory_storage: Optional[Any] = None,
        max_memory_items: int = 1000,
        token_estimator: Optional[Callable[[str], int]] = None,
        max_tokens_per_memory: int = 500,
        enable_hybrid_thinking: bool = True,
        streaming_buffer_size: int = 100,
        claude_client: Optional[Any] = None,
        perplexity_client: Optional[Any] = None
    ):
        """
        Initialize the memory bridge.
        
        Args:
            memory_storage: External memory storage system (if None, uses in-memory storage)
            max_memory_items: Maximum number of memory items to store
            token_estimator: Function to estimate tokens in a string (if None, uses default)
            max_tokens_per_memory: Maximum tokens per memory item
            enable_hybrid_thinking: Whether to enable hybrid thinking with Claude
            streaming_buffer_size: Buffer size for streaming responses
            claude_client: Claude API client instance
            perplexity_client: Perplexity API client instance
        """
        self.memory_storage = memory_storage
        self.max_memory_items = max_memory_items
        self.max_tokens_per_memory = max_tokens_per_memory
        self.enable_hybrid_thinking = enable_hybrid_thinking
        self.streaming_buffer_size = streaming_buffer_size
        self.claude_client = claude_client
        self.perplexity_client = perplexity_client
        
        # In-memory storage if no external storage provided
        if not self.memory_storage:
            self._memory = []
        
        # Token estimator (simple approximation if not provided)
        self.token_estimator = token_estimator or self._default_token_estimator
        
        # Total tokens stored in memory
        self.total_tokens = 0
        
        # Memory stats
        self.stats = {
            "total_memories": 0,
            "hybrid_thinking_calls": 0,
            "retrievals": 0,
            "tool_executions": 0,
            "tokens_saved": 0,
            "start_time": time.time()
        }
        
        logger.info(format_status("info", "Composio memory bridge initialized"))
    
    async def store_memory(
        self,
        content: str,
        memory_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
        importance: float = 0.5,
        vector_embed: bool = True
    ) -> str:
        """
        Store content in memory.
        
        Args:
            content: Content to store
            memory_type: Type of memory (tool_execution, thought, etc.)
            metadata: Additional metadata
            timestamp: Custom timestamp (defaults to current time)
            importance: Importance score (0.0-1.0)
            vector_embed: Whether to create vector embedding
            
        Returns:
            Memory ID
        """
        # Generate timestamp if not provided
        if timestamp is None:
            timestamp = time.time()
        
        # Ensure metadata exists
        metadata = metadata or {}
        
        # Truncate content if needed to stay within token limits
        original_tokens = self.token_estimator(content)
        if original_tokens > self.max_tokens_per_memory:
            # Truncate content to stay within limits
            # This is a simple approach - a smarter approach would be to summarize
            content = content[:int(len(content) * (self.max_tokens_per_memory / original_tokens))]
            self.stats["tokens_saved"] += (original_tokens - self.token_estimator(content))
            
            # Add truncation notice to metadata
            metadata["truncated"] = True
            metadata["original_tokens"] = original_tokens
        
        # Create memory object
        memory_id = f"{memory_type}_{int(timestamp)}_{hash(content) % 10000}"
        memory = {
            "id": memory_id,
            "content": content,
            "type": memory_type,
            "timestamp": timestamp,
            "importance": importance,
            "metadata": metadata,
            "tokens": self.token_estimator(content),
            "embedding": None  # Will be filled later if vector_embed is True
        }
        
        # Update stats
        self.stats["total_memories"] += 1
        if memory_type == self.MEMORY_TYPE_TOOL_EXECUTION:
            self.stats["tool_executions"] += 1
        
        # Generate embedding if requested (and possible)
        if vector_embed and self.claude_client and hasattr(self.claude_client, "create_embedding"):
            try:
                embedding = await self.claude_client.create_embedding(content)
                memory["embedding"] = embedding
            except Exception as e:
                logger.warning(format_status("warning", f"Failed to create embedding: {str(e)}"))
        
        # Store in external storage if available
        if self.memory_storage:
            try:
                # Use the external storage system
                if asyncio.iscoroutinefunction(self.memory_storage.store):
                    await self.memory_storage.store(memory)
                else:
                    self.memory_storage.store(memory)
            except Exception as e:
                logger.error(format_status("error", f"Failed to store memory in external storage: {str(e)}"))
                # Fall back to in-memory storage
                self._store_in_memory(memory)
        else:
            # Use in-memory storage
            self._store_in_memory(memory)
        
        logger.debug(format_status("debug", f"Stored memory of type {memory_type} with {memory['tokens']} tokens"))
        
        return memory_id
    
    def _store_in_memory(self, memory: Dict[str, Any]) -> None:
        """Store memory in the in-memory storage"""
        self._memory.append(memory)
        self.total_tokens += memory["tokens"]
        
        # Remove old memories if exceeding max
        while len(self._memory) > self.max_memory_items:
            # Remove least important memory
            self._memory.sort(key=lambda m: m["importance"])
            removed = self._memory.pop(0)
            self.total_tokens -= removed["tokens"]
    
    async def retrieve_memories(
        self,
        query: Optional[str] = None,
        memory_types: Optional[List[str]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        max_results: int = 10,
        min_importance: float = 0.0,
        sort_by: str = "timestamp",
        sort_descending: bool = True,
        metadata_filter: Optional[Dict[str, Any]] = None,
        semantic_search: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories based on criteria.
        
        Args:
            query: Search query for semantic search
            memory_types: Types of memories to include
            start_time: Start of time range
            end_time: End of time range
            max_results: Maximum number of results
            min_importance: Minimum importance score
            sort_by: Field to sort by
            sort_descending: Whether to sort in descending order
            metadata_filter: Filter by metadata fields
            semantic_search: Whether to use semantic search
            
        Returns:
            List of matching memories
        """
        self.stats["retrievals"] += 1
        
        # If using external storage
        if self.memory_storage and hasattr(self.memory_storage, "retrieve"):
            try:
                # Build filter parameters
                params = {
                    "query": query,
                    "memory_types": memory_types,
                    "start_time": start_time,
                    "end_time": end_time,
                    "max_results": max_results,
                    "min_importance": min_importance,
                    "sort_by": sort_by,
                    "sort_descending": sort_descending,
                    "metadata_filter": metadata_filter,
                    "semantic_search": semantic_search
                }
                
                # Use the external storage retrieval
                if asyncio.iscoroutinefunction(self.memory_storage.retrieve):
                    return await self.memory_storage.retrieve(**params)
                else:
                    return self.memory_storage.retrieve(**params)
            except Exception as e:
                logger.error(format_status("error", f"Failed to retrieve from external storage: {str(e)}"))
                # Fall back to in-memory retrieval
        
        # Use in-memory retrieval
        results = self._retrieve_from_memory(
            query=query,
            memory_types=memory_types,
            start_time=start_time,
            end_time=end_time,
            min_importance=min_importance,
            metadata_filter=metadata_filter,
            semantic_search=semantic_search
        )
        
        # Sort results
        if sort_by in results[0] if results else False:
            results.sort(
                key=lambda m: m.get(sort_by),
                reverse=sort_descending
            )
        
        # Limit results
        return results[:max_results]
    
    def _retrieve_from_memory(
        self,
        query: Optional[str] = None,
        memory_types: Optional[List[str]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        min_importance: float = 0.0,
        metadata_filter: Optional[Dict[str, Any]] = None,
        semantic_search: bool = True
    ) -> List[Dict[str, Any]]:
        """Retrieve from in-memory storage"""
        results = []
        
        # Apply filters
        for memory in self._memory:
            # Check memory type
            if memory_types and memory["type"] not in memory_types:
                continue
            
            # Check time range
            if start_time and memory["timestamp"] < start_time:
                continue
            if end_time and memory["timestamp"] > end_time:
                continue
            
            # Check importance
            if memory["importance"] < min_importance:
                continue
            
            # Check metadata filter
            if metadata_filter:
                match = True
                for key, value in metadata_filter.items():
                    if key not in memory["metadata"] or memory["metadata"][key] != value:
                        match = False
                        break
                if not match:
                    continue
            
            results.append(memory)
        
        # Apply semantic search if requested
        if query and semantic_search and self.claude_client and hasattr(self.claude_client, "create_embedding"):
            try:
                # Get query embedding
                query_embedding = asyncio.run(self.claude_client.create_embedding(query))
                
                # Calculate semantic similarity for results with embeddings
                for memory in results:
                    if memory["embedding"]:
                        # Simple dot product similarity
                        similarity = sum(a * b for a, b in zip(query_embedding, memory["embedding"]))
                        memory["similarity"] = similarity
                
                # Sort by similarity
                results.sort(key=lambda m: m.get("similarity", 0), reverse=True)
            except Exception as e:
                logger.warning(format_status("warning", f"Semantic search failed: {str(e)}"))
        
        return results
    
    async def prompt_with_memory(
        self,
        prompt: str,
        memory_query: Optional[str] = None,
        memory_types: Optional[List[str]] = None,
        max_memories: int = 10,
        max_memory_tokens: int = 4000,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        streaming: bool = False,
        store_response: bool = True
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Send a prompt to Claude with relevant memories.
        
        Args:
            prompt: User prompt
            memory_query: Query to find relevant memories
            memory_types: Types of memories to include
            max_memories: Maximum number of memories to include
            max_memory_tokens: Maximum tokens for memories
            system_prompt: Custom system prompt
            tools: Tools to provide to Claude
            streaming: Whether to stream the response
            store_response: Whether to store the response in memory
            
        Returns:
            Response from Claude or streaming generator
        """
        if not self.claude_client:
            raise ValueError("Claude client not available")
        
        # Use the prompt as query if not specified
        memory_query = memory_query or prompt
        
        # Retrieve relevant memories
        memories = await self.retrieve_memories(
            query=memory_query,
            memory_types=memory_types,
            max_results=max_memories,
            semantic_search=True
        )
        
        # Construct memory context
        memory_context = ""
        memory_tokens = 0
        
        for memory in memories:
            # Format memory entry
            formatted_memory = format_memory_entry(
                content=memory["content"],
                memory_type=memory["type"],
                timestamp=memory["timestamp"],
                truncate=False
            )
            
            # Check if adding this memory would exceed token limit
            memory_tokens_estimate = self.token_estimator(formatted_memory)
            if memory_tokens + memory_tokens_estimate > max_memory_tokens:
                break
            
            memory_context += formatted_memory + "\n\n"
            memory_tokens += memory_tokens_estimate
        
        # Create full prompt with memory context
        full_prompt = f"""Here are some relevant memories that might help with the request:

{memory_context}

Given the above context, please respond to the following request:

{prompt}"""
        
        # Store the query in memory
        query_id = await self.store_memory(
            content=prompt,
            memory_type=self.MEMORY_TYPE_QUERY,
            metadata={"with_memory": len(memories) > 0}
        )
        
        # Send to Claude
        if streaming:
            return self._stream_response(
                prompt=full_prompt,
                system_prompt=system_prompt,
                tools=tools,
                query_id=query_id,
                store_response=store_response
            )
        else:
            response = await self.claude_client.generate(
                prompt=full_prompt,
                system_prompt=system_prompt,
                tools=tools
            )
            
            # Store the response in memory
            if store_response:
                await self.store_memory(
                    content=response,
                    memory_type=self.MEMORY_TYPE_RESPONSE,
                    metadata={
                        "query_id": query_id,
                        "with_memory": len(memories) > 0,
                        "memory_tokens": memory_tokens
                    }
                )
            
            return response
    
    async def _stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        query_id: Optional[str] = None,
        store_response: bool = True
    ) -> AsyncGenerator[str, None]:
        """Stream a response from Claude with memory handling"""
        response_buffer = []
        
        # Get response stream
        async for chunk in self.claude_client.generate_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            tools=tools
        ):
            # Add chunk to buffer
            response_buffer.append(chunk)
            
            # Yield the chunk to caller
            yield chunk
            
            # Store partial response if buffer is large enough
            if store_response and len(response_buffer) >= self.streaming_buffer_size:
                partial_response = "".join(response_buffer)
                response_buffer = []
                
                # Store partial response
                await self.store_memory(
                    content=partial_response,
                    memory_type=self.MEMORY_TYPE_RESPONSE,
                    metadata={
                        "query_id": query_id,
                        "partial": True
                    },
                    importance=0.3  # Lower importance for partial responses
                )
        
        # Store final response buffer if not empty
        if store_response and response_buffer:
            final_response = "".join(response_buffer)
            await self.store_memory(
                content=final_response,
                memory_type=self.MEMORY_TYPE_RESPONSE,
                metadata={
                    "query_id": query_id,
                    "partial": False,
                    "final": True
                }
            )
    
    async def hybrid_thinking(
        self,
        prompt: str,
        max_iterations: int = 3,
        max_thinking_tokens: int = 5000,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        memory_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform hybrid thinking process with Claude 3.7 Sonnet.
        
        This uses a multi-step process where Claude:
        1. Generates initial thoughts and identifies information gaps
        2. Retrieves relevant memories or executes tools to fill gaps
        3. Refines thinking with new information
        4. Produces a final response
        
        Args:
            prompt: User prompt
            max_iterations: Maximum number of thinking iterations
            max_thinking_tokens: Maximum tokens for thinking
            system_prompt: Custom system prompt
            tools: Tools to provide to Claude
            memory_types: Memory types to consider
            
        Returns:
            Dictionary with final response and thinking process
        """
        if not self.enable_hybrid_thinking:
            # Fall back to standard prompt with memory
            response = await self.prompt_with_memory(
                prompt=prompt,
                system_prompt=system_prompt,
                tools=tools,
                memory_types=memory_types
            )
            return {
                "response": response,
                "thinking": None,
                "iterations": 0
            }
        
        self.stats["hybrid_thinking_calls"] += 1
        
        # Hybrid thinking process
        thinking = []
        iterations = 0
        information_gaps = []
        
        # Initial thinking system prompt
        thinking_system_prompt = system_prompt or """You are Claude, an AI assistant with hybrid thinking capabilities.
For this request, you will think step by step before providing a final answer.
First, analyze what you know and identify any information gaps.
For each gap, specify what additional information would help and how it might be obtained.
"""
        
        # Step 1: Initial thinking
        initial_thinking = await self.claude_client.generate(
            prompt=prompt,
            system_prompt=thinking_system_prompt
        )
        
        thinking.append({
            "step": "initial_thinking",
            "content": initial_thinking
        })
        
        # Store thinking in memory
        await self.store_memory(
            content=initial_thinking,
            memory_type=self.MEMORY_TYPE_THOUGHT,
            metadata={"step": "initial_thinking", "iteration": iterations}
        )
        
        # Step 2: Extract information gaps
        gaps_prompt = f"""Based on your initial thinking:

{initial_thinking}

Please identify specific information gaps that need to be filled to better answer the original request. 
For each gap, provide:
1. A clear description of what information is missing
2. How this information could be obtained (memory, tool, external knowledge)
3. A specific query or tool call that could retrieve this information

Format each gap as a JSON object with fields: "description", "source", "query".
Return a JSON array of these gaps.
"""
        
        gaps_response = await self.claude_client.generate(
            prompt=gaps_prompt,
            system_prompt="Analyze information gaps and return them in valid JSON format."
        )
        
        # Parse information gaps
        try:
            # Find JSON array in the response
            import re
            json_match = re.search(r'\[[\s\S]*\]', gaps_response)
            if json_match:
                gaps_json = json_match.group(0)
                information_gaps = json.loads(gaps_json)
            else:
                information_gaps = []
        except Exception as e:
            logger.warning(format_status("warning", f"Failed to parse information gaps: {str(e)}"))
            information_gaps = []
        
        # Step 3: Iterative refinement
        for iteration in range(max_iterations):
            iterations += 1
            
            if not information_gaps:
                break
            
            # Process the most important gap first
            current_gap = information_gaps.pop(0)
            
            # Gather additional information based on gap source
            gap_info = None
            if current_gap.get("source") == "memory":
                # Retrieve from memory
                memories = await self.retrieve_memories(
                    query=current_gap.get("query", ""),
                    max_results=5,
                    semantic_search=True,
                    memory_types=memory_types
                )
                
                if memories:
                    gap_info = "Information from memory:\n\n" + "\n\n".join([
                        format_memory_entry(
                            memory["content"],
                            memory["type"],
                            memory["timestamp"]
                        ) for memory in memories
                    ])
                else:
                    gap_info = "No relevant information found in memory."
                    
            elif current_gap.get("source") == "tool" and tools:
                # Find matching tool
                tool_name = current_gap.get("tool", "").strip()
                matching_tools = [t for t in tools if t.get("name") == tool_name]
                
                if matching_tools and "parameters" in current_gap:
                    # Execute tool
                    try:
                        tool_result = await self.claude_client.execute_tool(
                            tool_name=tool_name,
                            parameters=current_gap.get("parameters", {})
                        )
                        gap_info = f"Tool execution result:\n\n{tool_result}"
                    except Exception as e:
                        gap_info = f"Tool execution failed: {str(e)}"
                else:
                    gap_info = "No matching tool found or missing parameters."
            
            elif current_gap.get("source") == "research" and self.perplexity_client:
                # Use Perplexity for deep research
                try:
                    research_result = await self.perplexity_client.query(
                        current_gap.get("query", ""),
                        streaming=False
                    )
                    gap_info = f"Research results:\n\n{research_result}"
                except Exception as e:
                    gap_info = f"Research failed: {str(e)}"
            
            # If we found information, refine thinking
            if gap_info:
                # Update thinking with new information
                refine_prompt = f"""Based on your previous thinking, I've found additional information regarding 
the gap: "{current_gap.get('description')}"

{gap_info}

Given this new information, please refine your thinking. Focus specifically on how this 
new information impacts your understanding and approach to the original request:

{prompt}

If there are still information gaps, please note them for further exploration.
"""
                
                refined_thinking = await self.claude_client.generate(
                    prompt=refine_prompt,
                    system_prompt="Refine your thinking based on new information."
                )
                
                thinking.append({
                    "step": f"refinement_{iteration}",
                    "gap": current_gap.get("description"),
                    "information": gap_info,
                    "refined_thinking": refined_thinking
                })
                
                # Store refined thinking in memory
                await self.store_memory(
                    content=refined_thinking,
                    memory_type=self.MEMORY_TYPE_THOUGHT,
                    metadata={
                        "step": f"refinement_{iteration}",
                        "iteration": iterations,
                        "gap": current_gap.get("description")
                    }
                )
                
                # Check if we're approaching token limits
                thinking_tokens = sum(self.token_estimator(t.get("content", "") or t.get("refined_thinking", "")) 
                                     for t in thinking)
                
                if thinking_tokens > max_thinking_tokens:
                    break
            
            # Stop if no more gaps or reached max iterations
            if not information_gaps or iteration >= max_iterations - 1:
                break
        
        # Step 4: Generate final response
        # Combine all thinking steps
        all_thinking = "\n\n".join([
            t.get("content", "") or t.get("refined_thinking", "")
            for t in thinking
        ])
        
        final_prompt = f"""Based on all your thinking:

{all_thinking}

Please provide a final, comprehensive response to the original request:

{prompt}

Your response should be well-structured, accurate, and incorporate all the important insights 
from your thinking process. Address any remaining uncertainties transparently.
"""
        
        final_response = await self.claude_client.generate(
            prompt=final_prompt,
            system_prompt=system_prompt or "Provide a comprehensive final response based on your hybrid thinking process."
        )
        
        # Store final response
        await self.store_memory(
            content=final_response,
            memory_type=self.MEMORY_TYPE_RESPONSE,
            metadata={
                "hybrid_thinking": True,
                "iterations": iterations,
                "original_prompt": prompt
            }
        )
        
        return {
            "response": final_response,
            "thinking": thinking,
            "iterations": iterations
        }
    
    @staticmethod
    def _default_token_estimator(text: str) -> int:
        """
        Estimate tokens in text - simple approximation.
        
        A more accurate estimator would use a proper tokenizer.
        """
        return len(text.split()) + int(len(text) / 4)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            **self.stats,
            "memory_count": len(self._memory) if not self.memory_storage else "external",
            "total_tokens": self.total_tokens if not self.memory_storage else "external",
            "uptime": time.time() - self.stats["start_time"]
        } 