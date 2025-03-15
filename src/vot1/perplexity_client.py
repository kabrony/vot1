#!/usr/bin/env python3
"""
VOTai Perplexity Client

This module provides a client for the Perplexity API with enhanced features for
deep web research, streaming support, and integration with the VOTai memory system.
"""

import os
import re
import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Union, AsyncGenerator, Tuple

try:
    # Absolute imports (for installed package)
    from vot1.utils.branding import format_status
    from vot1.utils.logging import get_logger
except ImportError:
    # Relative imports (for development)
    from src.vot1.utils.branding import format_status
    from src.vot1.utils.logging import get_logger

logger = get_logger(__name__)

class PerplexityClient:
    """
    Client for interacting with the Perplexity API with enhanced capabilities.
    
    Features:
    - Deep web research with multiple queries
    - Streaming support for long-running research
    - Citation tracking and extraction
    - Content summarization and knowledge extraction
    - Memory integration for persistent knowledge
    """
    
    # API endpoint
    API_ENDPOINT = "https://api.perplexity.ai"
    
    # Supported models with capabilities
    MODELS = {
        "llama-3-sonar-small-online": {
            "description": "Llama 3 8B with online search capabilities",
            "context_window": 8000,
            "search_enabled": True
        },
        "llama-3-sonar-large-online": {
            "description": "Llama 3 70B with online search capabilities",
            "context_window": 8000,
            "search_enabled": True
        },
        "mistral-7b-instruct": {
            "description": "Mistral 7B Instruct model",
            "context_window": 8000,
            "search_enabled": False
        },
        "mixtral-8x7b-instruct": {
            "description": "Mixtral 8x7B Instruct model",
            "context_window": 16000,
            "search_enabled": False
        },
        "claude-3-opus-20240229": {
            "description": "Claude 3 Opus",
            "context_window": 100000,
            "search_enabled": False
        },
        "claude-3-sonnet-20240229": {
            "description": "Claude 3 Sonnet",
            "context_window": 80000,
            "search_enabled": False
        },
        "claude-3-haiku-20240307": {
            "description": "Claude 3 Haiku",
            "context_window": 48000,
            "search_enabled": False
        },
        "gpt-4-turbo": {
            "description": "GPT-4 Turbo",
            "context_window": 128000,
            "search_enabled": False
        },
        "gpt-4": {
            "description": "GPT-4",
            "context_window": 8000,
            "search_enabled": False
        },
        "gpt-3.5-turbo": {
            "description": "GPT-3.5 Turbo",
            "context_window": 16000,
            "search_enabled": False
        }
    }
    
    # Default model for search
    DEFAULT_SEARCH_MODEL = "llama-3-sonar-large-online"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 3,
        memory_bridge: Optional[Any] = None
    ):
        """
        Initialize the Perplexity client.
        
        Args:
            api_key: Perplexity API key (defaults to PERPLEXITY_API_KEY env var)
            model_name: Default model to use
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries on failure
            memory_bridge: Optional memory bridge for storing results
        """
        self.api_key = api_key or os.environ.get("PERPLEXITY_API_KEY")
        if not self.api_key:
            logger.warning(format_status("warning", "No Perplexity API key provided; client will be non-functional"))
            
        self.model_name = model_name or self.DEFAULT_SEARCH_MODEL
        self.timeout = timeout
        self.max_retries = max_retries
        self.memory_bridge = memory_bridge
        
        # Validate model
        if self.model_name not in self.MODELS:
            logger.warning(format_status("warning", f"Unrecognized model: {self.model_name}, defaulting to {self.DEFAULT_SEARCH_MODEL}"))
            self.model_name = self.DEFAULT_SEARCH_MODEL
            
        # HTTP client
        self.client = None
        
        # Statistics
        self.stats = {
            "queries": 0,
            "streaming_queries": 0,
            "research_sessions": 0,
            "citations_extracted": 0,
            "errors": 0,
            "total_tokens": 0,
            "start_time": time.time()
        }
        
        logger.info(format_status("info", f"Perplexity client initialized with model: {self.model_name}"))
    
    async def query(
        self,
        query: str,
        model: Optional[str] = None,
        streaming: bool = False,
        store_in_memory: bool = True,
        search_focus: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        additional_context: Optional[str] = None
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Send a query to the Perplexity API.
        
        Args:
            query: The query to send
            model: Model to use (defaults to self.model_name)
            streaming: Whether to stream the response
            store_in_memory: Whether to store the result in memory
            search_focus: Focus for search ("research", "news", "technology", etc.)
            temperature: Temperature for sampling
            max_tokens: Maximum tokens to generate
            additional_context: Additional context for the query
            
        Returns:
            Response text or streaming generator
        """
        if not self.api_key:
            raise ValueError("No Perplexity API key provided")
        
        # Ensure HTTP client is initialized
        if self.client is None:
            import httpx
            self.client = httpx.AsyncClient(timeout=self.timeout)
        
        self.stats["queries"] += 1
        if streaming:
            self.stats["streaming_queries"] += 1
        
        # Use default model if not specified
        model = model or self.model_name
        
        # Prepare the request
        url = f"{self.API_ENDPOINT}/query"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "query": query,
            "stream": streaming,
            "temperature": temperature
        }
        
        # Add optional parameters
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if search_focus and self.MODELS.get(model, {}).get("search_enabled", False):
            payload["search_focus"] = search_focus
        
        if additional_context:
            payload["additional_context"] = additional_context
        
        # Send the request
        for attempt in range(self.max_retries):
            try:
                if streaming:
                    return self._handle_streaming_response(
                        url=url,
                        headers=headers,
                        payload=payload,
                        query=query,
                        store_in_memory=store_in_memory
                    )
                else:
                    response = await self.client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    
                    result = response.json()
                    
                    # Process the response
                    return await self._process_response(
                        result=result, 
                        query=query, 
                        store_in_memory=store_in_memory
                    )
            except Exception as e:
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = 2 ** attempt
                    logger.warning(format_status("warning", f"API error, retrying in {delay}s: {str(e)}"))
                    await asyncio.sleep(delay)
                else:
                    # Last attempt failed
                    self.stats["errors"] += 1
                    logger.error(format_status("error", f"Perplexity API error: {str(e)}"))
                    raise
    
    async def _handle_streaming_response(
        self,
        url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        query: str,
        store_in_memory: bool
    ) -> AsyncGenerator[str, None]:
        """
        Handle streaming response from Perplexity API.
        
        Args:
            url: API endpoint
            headers: Request headers
            payload: Request payload
            query: Original query
            store_in_memory: Whether to store the result in memory
            
        Yields:
            Text chunks as they are generated
        """
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    
                    # For storing complete response
                    buffer = []
                    citations = []
                    
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                            
                        # Parse the response chunk
                        try:
                            chunk = json.loads(line)
                            
                            # Add to buffer for later storage
                            if "text" in chunk:
                                buffer.append(chunk["text"])
                                
                                # Extract citations if available
                                if "citations" in chunk:
                                    for citation in chunk["citations"]:
                                        if citation not in citations:
                                            citations.append(citation)
                                            self.stats["citations_extracted"] += 1
                                
                                # Yield the text to the caller
                                yield chunk["text"]
                            
                            # Check for errors
                            if "error" in chunk:
                                self.stats["errors"] += 1
                                error_msg = chunk.get("error", {}).get("message", "Unknown error")
                                logger.error(format_status("error", f"Error in streaming response: {error_msg}"))
                                yield f"Error: {error_msg}"
                                
                            # Track token usage
                            if "usage" in chunk:
                                self.stats["total_tokens"] += chunk["usage"].get("total_tokens", 0)
                        
                        except json.JSONDecodeError:
                            logger.warning(format_status("warning", f"Could not parse chunk: {line}"))
                            continue
            
            # Store complete response in memory if requested
            if store_in_memory and self.memory_bridge and buffer:
                complete_response = "".join(buffer)
                
                # Format citations if available
                citations_text = ""
                if citations:
                    citations_text = "\n\nSources:\n" + "\n".join([
                        f"[{i+1}] {citation.get('title', 'Unknown')} - {citation.get('url', 'No URL')}"
                        for i, citation in enumerate(citations)
                    ])
                
                await self._store_in_memory(
                    query=query,
                    response=complete_response + citations_text,
                    citations=citations
                )
        
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(format_status("error", f"Error in streaming request: {str(e)}"))
            yield f"Error: {str(e)}"
    
    async def _process_response(
        self,
        result: Dict[str, Any],
        query: str,
        store_in_memory: bool
    ) -> str:
        """
        Process a non-streaming response from Perplexity API.
        
        Args:
            result: API response
            query: Original query
            store_in_memory: Whether to store the result in memory
            
        Returns:
            Response text
        """
        # Extract text
        text = result.get("text", "")
        
        # Extract citations
        citations = result.get("citations", [])
        for citation in citations:
            self.stats["citations_extracted"] += 1
        
        # Track token usage
        if "usage" in result:
            self.stats["total_tokens"] += result["usage"].get("total_tokens", 0)
        
        # Format citations if available
        citations_text = ""
        if citations:
            citations_text = "\n\nSources:\n" + "\n".join([
                f"[{i+1}] {citation.get('title', 'Unknown')} - {citation.get('url', 'No URL')}"
                for i, citation in enumerate(citations)
            ])
        
        # Store in memory if requested
        if store_in_memory and self.memory_bridge:
            await self._store_in_memory(
                query=query,
                response=text + citations_text,
                citations=citations
            )
        
        return text + citations_text
    
    async def _store_in_memory(
        self,
        query: str,
        response: str,
        citations: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Store query and response in memory bridge.
        
        Args:
            query: Query text
            response: Response text
            citations: List of citations
            
        Returns:
            Memory ID
        """
        if not self.memory_bridge:
            return ""
        
        try:
            # Store the response in memory
            memory_id = await self.memory_bridge.store_memory(
                content=response,
                memory_type="perplexity_response",
                metadata={
                    "query": query,
                    "model": self.model_name,
                    "citations_count": len(citations) if citations else 0,
                    "has_citations": bool(citations)
                }
            )
            
            # Store individual citations if available
            if citations:
                for citation in citations:
                    await self.memory_bridge.store_memory(
                        content=f"Title: {citation.get('title', 'Unknown')}\nURL: {citation.get('url', 'No URL')}",
                        memory_type="citation",
                        metadata={
                            "query": query,
                            "response_id": memory_id,
                            "title": citation.get("title"),
                            "url": citation.get("url")
                        },
                        importance=0.7  # Citations are important but less than the main response
                    )
            
            return memory_id
            
        except Exception as e:
            logger.error(format_status("error", f"Error storing in memory: {str(e)}"))
            return ""
    
    async def research(
        self,
        topic: str,
        max_queries: int = 3,
        depth: str = "deep",
        focus: Optional[str] = None,
        streaming: bool = True,
        stream_handler: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Conduct deep research on a topic with multiple queries.
        
        This method performs an initial query, then analyzes the results to 
        generate follow-up queries that dig deeper into the topic.
        
        Args:
            topic: Research topic
            max_queries: Maximum number of queries to perform
            depth: Research depth ("brief", "standard", "deep")
            focus: Research focus area
            streaming: Whether to stream the results
            stream_handler: Optional callback for streaming updates
            
        Returns:
            Research results including summary and all responses
        """
        self.stats["research_sessions"] += 1
        
        # Select model based on depth
        if depth == "deep":
            model = "llama-3-sonar-large-online"
        elif depth == "brief":
            model = "llama-3-sonar-small-online"
        else:  # standard
            model = self.model_name
        
        research_results = {
            "topic": topic,
            "queries": [],
            "responses": [],
            "summary": "",
            "citations": []
        }
        
        # Initial query
        initial_query = f"Research the following topic comprehensively: {topic}"
        if focus:
            initial_query += f". Focus on {focus}."
        
        if stream_handler:
            stream_handler("status", f"Starting research on: {topic}")
            
        # Perform initial query
        try:
            if streaming:
                initial_response = ""
                initial_citations = []
                
                if stream_handler:
                    stream_handler("status", "Performing initial query...")
                
                async for chunk in await self.query(
                    query=initial_query,
                    model=model,
                    streaming=True,
                    search_focus=focus,
                    store_in_memory=False
                ):
                    initial_response += chunk
                    if stream_handler:
                        stream_handler("content", chunk)
            else:
                initial_response = await self.query(
                    query=initial_query,
                    model=model,
                    streaming=False,
                    search_focus=focus,
                    store_in_memory=False
                )
            
            # Extract citations
            citations = self._extract_citations(initial_response)
            
            # Add to research results
            research_results["queries"].append(initial_query)
            research_results["responses"].append(initial_response)
            research_results["citations"].extend(citations)
            
            # Generate follow-up queries if needed
            if max_queries > 1:
                followup_query = await self._generate_followup_queries(
                    topic=topic,
                    initial_response=initial_response,
                    focus=focus,
                    depth=depth
                )
                
                # Perform follow-up queries
                for i, query in enumerate(followup_query[:max_queries-1]):
                    if stream_handler:
                        stream_handler("status", f"Performing follow-up query {i+1}/{len(followup_query)}: {query}")
                    
                    try:
                        if streaming:
                            followup_response = ""
                            async for chunk in await self.query(
                                query=query,
                                model=model,
                                streaming=True,
                                search_focus=focus,
                                store_in_memory=False
                            ):
                                followup_response += chunk
                                if stream_handler:
                                    stream_handler("content", chunk)
                        else:
                            followup_response = await self.query(
                                query=query,
                                model=model,
                                streaming=False,
                                search_focus=focus,
                                store_in_memory=False
                            )
                        
                        # Extract citations
                        followup_citations = self._extract_citations(followup_response)
                        
                        # Add to research results
                        research_results["queries"].append(query)
                        research_results["responses"].append(followup_response)
                        research_results["citations"].extend(followup_citations)
                        
                    except Exception as e:
                        logger.error(format_status("error", f"Error in follow-up query: {str(e)}"))
                        if stream_handler:
                            stream_handler("error", f"Error in follow-up query: {str(e)}")
            
            # Generate summary of all findings
            if stream_handler:
                stream_handler("status", "Generating research summary...")
            
            all_responses = "\n\n".join(research_results["responses"])
            summary = await self._generate_summary(
                topic=topic, 
                responses=all_responses,
                depth=depth
            )
            
            research_results["summary"] = summary
            
            # Store the entire research session in memory
            if self.memory_bridge:
                content = f"Research Topic: {topic}\n\nSummary: {summary}\n\n"
                
                # Add queries and responses
                for i, (query, response) in enumerate(zip(research_results["queries"], research_results["responses"])):
                    content += f"Query {i+1}: {query}\n\nResponse {i+1}:\n{response}\n\n"
                
                # Add citations
                if research_results["citations"]:
                    content += "Citations:\n"
                    for i, citation in enumerate(research_results["citations"]):
                        content += f"[{i+1}] {citation}\n"
                
                await self.memory_bridge.store_memory(
                    content=content,
                    memory_type="research_session",
                    metadata={
                        "topic": topic,
                        "queries_count": len(research_results["queries"]),
                        "focus": focus,
                        "depth": depth,
                        "citations_count": len(research_results["citations"])
                    },
                    importance=0.9  # Research sessions are highly important
                )
                
            return research_results
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(format_status("error", f"Error during research: {str(e)}"))
            if stream_handler:
                stream_handler("error", f"Research error: {str(e)}")
            
            raise
    
    async def _generate_followup_queries(
        self,
        topic: str,
        initial_response: str,
        focus: Optional[str] = None,
        depth: str = "standard",
        max_queries: int = 5
    ) -> List[str]:
        """
        Generate follow-up queries based on initial research results.
        
        Args:
            topic: Research topic
            initial_response: Initial research response
            focus: Research focus
            depth: Research depth
            max_queries: Maximum number of queries to generate
            
        Returns:
            List of follow-up queries
        """
        # Adjust number of queries based on depth
        if depth == "brief":
            max_queries = min(max_queries, 2)
        elif depth == "deep":
            max_queries = max(max_queries, 3)
        
        # Generate follow-up queries using the model
        followup_prompt = f"""Based on the following research about "{topic}":

{initial_response}

Generate {max_queries} focused follow-up questions that would help deepen the research.
These questions should:
1. Target areas that need more exploration or clarification
2. Address potential gaps in the information
3. Explore different perspectives or aspects not covered
4. Be specific enough to yield detailed information
5. Be appropriate for a web search or research query

Return ONLY the numbered list of questions without any other text or explanation.
"""

        try:
            # Use a non-search model for this to avoid recursive searching
            followup_response = await self.query(
                query=followup_prompt,
                model="claude-3-haiku-20240307",  # Use a model without search for this meta-query
                streaming=False,
                store_in_memory=False
            )
            
            # Extract questions from the response
            questions = []
            
            # Look for numbered questions
            pattern = r"(?:\d+\.\s*)(.*?)(?=$|\n\d+\.|\n\n)"
            matches = re.findall(pattern, followup_response, re.DOTALL)
            
            if matches:
                questions = [q.strip() for q in matches]
            else:
                # Fallback: split by newlines
                lines = followup_response.split("\n")
                for line in lines:
                    line = line.strip()
                    if line and (line.startswith(("Q:", "Question:")) or re.match(r"^\d+\..*", line)):
                        # Remove Q: or Question: prefix
                        question = re.sub(r"^(Q:|Question:|\d+\.)\s*", "", line)
                        if question:
                            questions.append(question)
            
            # Ensure we have the right number of questions
            questions = questions[:max_queries]
            
            # Add focus to queries if specified
            if focus:
                questions = [f"{q} (focus on {focus})" for q in questions]
            
            return questions
            
        except Exception as e:
            logger.error(format_status("error", f"Error generating follow-up queries: {str(e)}"))
            # Return a default follow-up query as fallback
            return [f"Provide more detailed information about {topic}"]
    
    async def _generate_summary(
        self,
        topic: str,
        responses: str,
        depth: str = "standard"
    ) -> str:
        """
        Generate a summary of research findings.
        
        Args:
            topic: Research topic
            responses: Combined research responses
            depth: Research depth
            
        Returns:
            Summary of research findings
        """
        # Adjust summary length based on depth
        length = {
            "brief": "concise",
            "standard": "comprehensive",
            "deep": "detailed and thorough"
        }.get(depth, "comprehensive")
        
        # Truncate responses if very long
        max_chars = 16000
        if len(responses) > max_chars:
            responses = responses[:max_chars] + "...[truncated for length]"
        
        summary_prompt = f"""Synthesize the following research findings about "{topic}" into a {length} summary:

{responses}

Your summary should:
1. Highlight the most important findings and insights
2. Organize information logically with clear structure
3. Present different perspectives or contradictions if they exist
4. Identify any limitations or gaps in the research
5. Be factual and objective

The summary should be well-structured with sections and subsections as appropriate.
"""

        try:
            # Use Claude for the summary to get high quality synthesis
            summary = await self.query(
                query=summary_prompt,
                model="claude-3-sonnet-20240229",  # Use Claude for high-quality summarization
                streaming=False,
                store_in_memory=False
            )
            
            return summary
            
        except Exception as e:
            logger.error(format_status("error", f"Error generating summary: {str(e)}"))
            # Return a simple message as fallback
            return f"Research on {topic} completed, but summary generation failed."
    
    def _extract_citations(self, text: str) -> List[Dict[str, str]]:
        """
        Extract citations from response text.
        
        Args:
            text: Response text
    
    Returns:
            List of citations (title, url)
        """
        citations = []
        
        # Look for source blocks at the end, common pattern in Perplexity responses
        source_section = re.search(r"Sources:[\s\S]*$", text)
        if source_section:
            source_text = source_section.group(0)
            
            # Pattern for numbered sources with URLs
            source_pattern = r"\[\s*(\d+)\s*\]\s*([^\n]+?)(?:\s*-\s*|\s*:\s*|\s*,\s*|\s+)(https?://[^\s]+)"
            source_matches = re.findall(source_pattern, source_text)
            
            for _, title, url in source_matches:
                citations.append({
                    "title": title.strip(),
                    "url": url.strip()
                })
        
        # Look for inline citations [number]
        if not citations:
            # Get all possible URLs
            url_pattern = r"(https?://[^\s]+)"
            urls = re.findall(url_pattern, text)
            
            for url in urls:
                # Extract domain as title if no better info
                domain = re.search(r"https?://(?:www\.)?([^/]+)", url)
                title = domain.group(1) if domain else "Source"
                
                citations.append({
                    "title": title,
                    "url": url
                })
        
        return citations
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client usage statistics."""
        current_time = time.time()
        uptime = current_time - self.stats["start_time"]
        
        return {
                **self.stats,
                "uptime": uptime,
                "queries_per_minute": (self.stats["queries"] / (uptime / 60)) if uptime > 0 else 0,
                "current_model": self.model_name,
                "success_rate": (self.stats["queries"] - self.stats["errors"]) / self.stats["queries"] if self.stats["queries"] > 0 else 0
        } 