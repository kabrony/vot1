"""
Enhanced Perplexity Client

This module provides an enhanced client for Perplexity AI with advanced 
caching strategies, rate limiting, and error handling.
"""

import os
import json
import time
import logging
import hashlib
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Optional Redis import
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom exceptions
class PerplexityError(Exception):
    """Base class for Perplexity client errors"""
    pass

class RateLimitExceeded(PerplexityError):
    """Exception raised when rate limit is exceeded"""
    pass

class NetworkError(PerplexityError):
    """Exception raised for network-related errors"""
    pass

class CacheError(PerplexityError):
    """Exception raised for cache-related errors"""
    pass


class EnhancedPerplexityClient:
    """
    Enhanced Perplexity Client with advanced caching and rate limiting.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        redis_url: Optional[str] = None,
        cache_ttl: int = 3600,  # Default: 1 hour
        max_retries: int = 3,
        rate_limit_per_minute: int = 20
    ):
        """
        Initialize the enhanced Perplexity client.
        
        Args:
            api_key: Perplexity API key (defaults to environment variable)
            redis_url: Redis connection URL for distributed caching
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
            max_retries: Maximum retry attempts for failed requests
            rate_limit_per_minute: Rate limit for requests per minute
        """
        self.api_key = api_key or os.environ.get("PERPLEXITY_API_KEY")
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
        self.rate_limit_per_minute = rate_limit_per_minute
        
        # Rate limiting state
        self.request_times = []
        
        # Initialize cache
        self._init_cache(redis_url)
        
        # Initialize MCP client if available
        self.use_mcp = self._check_mcp_available()
        
        logger.info(f"Enhanced Perplexity Client initialized with {'MCP' if self.use_mcp else 'direct API'} mode")
    
    def _init_cache(self, redis_url: Optional[str] = None):
        """Initialize the cache system."""
        self.redis = None
        self.local_cache = {}
        
        # Try to use Redis if available
        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis = redis.from_url(redis_url)
                # Test connection
                self.redis.ping()
                self.cache_type = "redis"
                logger.info("Using Redis for Perplexity cache")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Falling back to local cache.")
                self.cache_type = "local"
        else:
            self.cache_type = "local"
            if not redis_url:
                logger.info("No Redis URL provided. Using local cache.")
            elif not REDIS_AVAILABLE:
                logger.info("Redis package not available. Using local cache.")
    
    def _check_mcp_available(self) -> bool:
        """Check if MCP is available for Perplexity."""
        try:
            from ..api.mcp_tools import call_mcp_function
            
            # Test MCP connection
            response = call_mcp_function("mcp_PERPLEXITY_PERPLEXITYAI_CHECK_ACTIVE_CONNECTION", {
                "params": {"tool": "PERPLEXITYAI"}
            })
            
            return response.get('data', {}).get('active_connection', False)
        except ImportError:
            logger.info("MCP tools not available, using direct API")
            return False
        except Exception as e:
            logger.warning(f"Error checking MCP connection: {e}")
            return False
    
    def _enforce_rate_limit(self):
        """Enforce the rate limit."""
        # Clean up old request times
        current_time = time.time()
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        # Check if rate limit is exceeded
        if len(self.request_times) >= self.rate_limit_per_minute:
            oldest_request = min(self.request_times)
            wait_time = 60 - (current_time - oldest_request)
            
            if wait_time > 0:
                raise RateLimitExceeded(f"Rate limit exceeded. Try again in {wait_time:.2f} seconds.")
        
        # Add current request time
        self.request_times.append(current_time)
    
    def _generate_cache_key(self, query: str, model: str, **params) -> str:
        """Generate a cache key for the query and parameters."""
        # Create a string representation of all parameters
        param_str = json.dumps({
            "query": query,
            "model": model,
            **params
        }, sort_keys=True)
        
        # Hash it with SHA-256
        hash_obj = hashlib.sha256(param_str.encode())
        return f"perplexity:search:{hash_obj.hexdigest()}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get results from cache."""
        if self.cache_type == "redis" and self.redis:
            try:
                cached_data = self.redis.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Error getting from Redis cache: {e}")
        
        # Fall back to local cache
        return self.local_cache.get(cache_key)
    
    def _store_in_cache(self, cache_key: str, data: Dict, ttl: Optional[int] = None):
        """Store results in cache."""
        ttl = ttl or self.cache_ttl
        
        if self.cache_type == "redis" and self.redis:
            try:
                self.redis.setex(cache_key, ttl, json.dumps(data))
            except Exception as e:
                logger.warning(f"Error storing in Redis cache: {e}")
                # Fall back to local cache
                self.local_cache[cache_key] = data
        else:
            # Store in local cache
            self.local_cache[cache_key] = data
            
            # Set expiry for the local cache
            # (In a real implementation, you'd want a background task to clean this up)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(NetworkError)
    )
    def search(
        self,
        query: str,
        model: str = "sonar-reasoning-pro",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        return_citations: bool = True,
        skip_cache: bool = False,
        cache_ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Perform a search query using Perplexity AI.
        
        Args:
            query: The search query text
            model: The model to use (default: sonar-reasoning-pro)
            system_prompt: Optional system prompt to guide the model
            temperature: Temperature parameter (0.0 to 1.0)
            max_tokens: Maximum tokens in the response
            return_citations: Whether to include citations in the response
            skip_cache: Whether to skip the cache and force a new request
            cache_ttl: Optional custom cache TTL for this specific query
        
        Returns:
            Dict containing the search results
        """
        # Set default system prompt if none provided
        if not system_prompt:
            system_prompt = (
                "You are a research assistant. Provide detailed information on the query, "
                "including facts, recent developments, and multiple perspectives."
            )
        
        # Generate cache key
        cache_key = self._generate_cache_key(
            query=query,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            return_citations=return_citations
        )
        
        # Check cache unless skip_cache is True
        if not skip_cache:
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"Using cached result for query: {query[:30]}...")
                return cached_result
        
        # Enforce rate limit
        self._enforce_rate_limit()
        
        try:
            # Use MCP if available, otherwise use direct API
            if self.use_mcp:
                return self._search_with_mcp(
                    query=query,
                    model=model,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    return_citations=return_citations,
                    cache_key=cache_key,
                    cache_ttl=cache_ttl
                )
            else:
                raise NotImplementedError("Direct API not implemented yet, MCP required")
        
        except RateLimitExceeded as e:
            logger.warning(f"Rate limit exceeded: {e}")
            raise
        
        except Exception as e:
            logger.error(f"Error in Perplexity search: {e}")
            # Check if we have a cached result we can return as fallback
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"Using cached result as fallback for query: {query[:30]}...")
                return {
                    **cached_result,
                    "from_cache": True,
                    "fallback": True,
                    "error": str(e)
                }
            raise PerplexityError(f"Search failed: {e}")
    
    def _search_with_mcp(
        self,
        query: str,
        model: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        return_citations: bool,
        cache_key: str,
        cache_ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """Perform search using MCP."""
        try:
            from ..api.mcp_tools import call_mcp_function
            
            response = call_mcp_function("mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH", {
                "params": {
                    "systemContent": system_prompt,
                    "userContent": query,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "return_citations": return_citations,
                    "model": model
                }
            })
            
            # Process the response
            if not response.get('successful', False):
                raise PerplexityError(f"MCP search failed: {response.get('error')}")
            
            content_text = ""
            citations = []
            
            # Extract content
            response_data = response.get('content', [])
            for item in response_data:
                if item.get('type') == 'text':
                    content_text += item.get('text', '')
            
            # Try to parse JSON content
            result = None
            
            try:
                parsed_content = json.loads(content_text)
                data = parsed_content.get('data', {})
                
                # Extract content from choices
                choices = data.get('choices', [])
                if choices:
                    content = choices[0].get('message', {}).get('content', '')
                    citations = data.get('citations', [])
                    
                    result = {
                        "query": query,
                        "content": content,
                        "citations": citations,
                        "timestamp": datetime.now().isoformat(),
                        "model": model,
                        "from_cache": False
                    }
            except json.JSONDecodeError:
                # If not valid JSON, use the raw text
                result = {
                    "query": query,
                    "content": content_text,
                    "citations": citations,
                    "timestamp": datetime.now().isoformat(),
                    "model": model,
                    "from_cache": False
                }
            
            # Cache the result
            if result:
                self._store_in_cache(cache_key, result, cache_ttl)
                return result
            else:
                raise PerplexityError("Failed to parse response")
            
        except Exception as e:
            logger.error(f"Error in MCP search: {e}")
            if isinstance(e, PerplexityError):
                raise
            raise NetworkError(f"MCP search failed: {e}")
    
    def clear_cache(self, query: Optional[str] = None):
        """
        Clear the cache.
        
        Args:
            query: Optional query to clear specific cache entry
        """
        if query:
            # Generate cache key for the specific query
            cache_key = self._generate_cache_key(query=query, model="sonar-reasoning-pro")
            
            # Clear from Redis if available
            if self.cache_type == "redis" and self.redis:
                try:
                    self.redis.delete(cache_key)
                except Exception as e:
                    logger.warning(f"Error clearing Redis cache: {e}")
            
            # Clear from local cache
            if cache_key in self.local_cache:
                del self.local_cache[cache_key]
        else:
            # Clear all cache
            if self.cache_type == "redis" and self.redis:
                try:
                    self.redis.flushdb()
                except Exception as e:
                    logger.warning(f"Error clearing Redis cache: {e}")
            
            # Clear local cache
            self.local_cache.clear() 