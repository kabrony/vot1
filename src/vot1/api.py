"""
VOT1 API Module

This module provides a RESTful API for VOT1, allowing external systems
to integrate with the memory visualization and knowledge management system.
"""

import os
import json
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# FastAPI imports
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator

# Local imports
try:
    from vot1.memory_graph import MemoryGraph
    from vot1.dashboard.github_ecosystem_api import GithubEcosystemAPI
    from vot1.mcp_integration import MCPIntegration
    from vot1.knowledge_retriever import KnowledgeRetriever
    from vot1.feedback_loop import FeedbackLoop
except ImportError:
    # Relative imports for when imported from the same directory
    from memory_graph import MemoryGraph
    from dashboard.github_ecosystem_api import GithubEcosystemAPI  
    from mcp_integration import MCPIntegration
    from knowledge_retriever import KnowledgeRetriever
    from feedback_loop import FeedbackLoop

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define API models
class TokenRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: int

class MemoryNodeBase(BaseModel):
    title: str
    content: str
    node_type: str = Field(default="note")
    tags: List[str] = Field(default_factory=list)
    
class MemoryNodeCreate(MemoryNodeBase):
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class MemoryNodeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    node_type: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
class MemoryNode(MemoryNodeBase):
    id: str
    created_at: datetime
    updated_at: datetime
    parent_id: Optional[str] = None
    children: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class MemoryLinkBase(BaseModel):
    source_id: str
    target_id: str
    link_type: str = Field(default="related")
    
class MemoryLinkCreate(MemoryLinkBase):
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class MemoryLinkUpdate(BaseModel):
    link_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
class MemoryLink(MemoryLinkBase):
    id: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class SearchQuery(BaseModel):
    query: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    max_results: int = 10
    
class GithubRepoInfo(BaseModel):
    repo_url: str
    branch: str = "main"
    
class MCPRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    tools: Optional[List[Dict[str, Any]]] = None
    
class FeedbackRequest(BaseModel):
    feature_id: str
    rating: int = Field(ge=1, le=5)
    feedback_text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Security
class TokenValidator:
    def __init__(self):
        self.security = HTTPBearer()
        # In a production application, use a proper secret key and token management
        self.api_keys = {
            os.environ.get("VOT1_API_KEY", "default-api-key"): {
                "user_id": "default-user",
                "expires_at": int(time.time()) + 86400 * 30  # 30 days
            }
        }
        
    async def __call__(self, request: Request, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        token = credentials.credentials
        
        if token not in self.api_keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        token_data = self.api_keys[token]
        if token_data["expires_at"] < int(time.time()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return token_data

# API implementation
class VOT1API:
    def __init__(self):
        self.app = FastAPI(
            title="VOT1 API",
            description="REST API for VOT1 Memory Visualization and Knowledge Management System",
            version="1.0.0"
        )
        
        # Initialize components
        self.memory_graph = MemoryGraph()
        self.github_api = GithubEcosystemAPI()
        self.mcp_integration = MCPIntegration()
        self.knowledge_retriever = KnowledgeRetriever()
        self.feedback_loop = FeedbackLoop()
        
        # Setup security
        self.token_validator = TokenValidator()
        
        # Add middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Update for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._register_routes()
        
    def _register_routes(self):
        # Authentication routes
        @self.app.post("/api/token", response_model=TokenResponse)
        async def get_token(request: TokenRequest):
            # In a real application, validate credentials against a database
            if request.username == "admin" and request.password == "password":
                token = os.urandom(16).hex()
                expires_at = int(time.time()) + 86400  # 24 hours
                
                self.token_validator.api_keys[token] = {
                    "user_id": request.username,
                    "expires_at": expires_at
                }
                
                return {
                    "access_token": token,
                    "token_type": "bearer",
                    "expires_at": expires_at
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
        
        # Health check route
        @self.app.get("/api/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        # Memory Graph - Nodes
        @self.app.get("/api/memory/nodes", response_model=List[MemoryNode])
        async def get_nodes(token_data: Dict = Depends(self.token_validator)):
            try:
                nodes = self.memory_graph.get_all_nodes()
                return nodes
            except Exception as e:
                logger.error(f"Error getting nodes: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error getting nodes: {str(e)}"
                )
        
        @self.app.get("/api/memory/nodes/{node_id}", response_model=MemoryNode)
        async def get_node(node_id: str, token_data: Dict = Depends(self.token_validator)):
            try:
                node = self.memory_graph.get_node(node_id)
                if not node:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Node with ID {node_id} not found"
                    )
                return node
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting node {node_id}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error getting node: {str(e)}"
                )
        
        @self.app.post("/api/memory/nodes", response_model=MemoryNode, status_code=status.HTTP_201_CREATED)
        async def create_node(node: MemoryNodeCreate, token_data: Dict = Depends(self.token_validator)):
            try:
                created_node = self.memory_graph.create_node(
                    title=node.title,
                    content=node.content,
                    node_type=node.node_type,
                    tags=node.tags,
                    parent_id=node.parent_id,
                    metadata=node.metadata
                )
                return created_node
            except Exception as e:
                logger.error(f"Error creating node: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error creating node: {str(e)}"
                )
        
        @self.app.put("/api/memory/nodes/{node_id}", response_model=MemoryNode)
        async def update_node(
            node_id: str, 
            node_update: MemoryNodeUpdate, 
            token_data: Dict = Depends(self.token_validator)
        ):
            try:
                # Convert to dict and remove None values
                update_data = node_update.dict(exclude_unset=True)
                
                updated_node = self.memory_graph.update_node(
                    node_id=node_id,
                    **update_data
                )
                
                if not updated_node:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Node with ID {node_id} not found"
                    )
                    
                return updated_node
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error updating node {node_id}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error updating node: {str(e)}"
                )
        
        @self.app.delete("/api/memory/nodes/{node_id}")
        async def delete_node(node_id: str, token_data: Dict = Depends(self.token_validator)):
            try:
                success = self.memory_graph.delete_node(node_id)
                
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Node with ID {node_id} not found"
                    )
                    
                return {"status": "success", "message": f"Node {node_id} deleted"}
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error deleting node {node_id}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error deleting node: {str(e)}"
                )
        
        # Memory Graph - Links
        @self.app.get("/api/memory/links", response_model=List[MemoryLink])
        async def get_links(token_data: Dict = Depends(self.token_validator)):
            try:
                links = self.memory_graph.get_all_links()
                return links
            except Exception as e:
                logger.error(f"Error getting links: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error getting links: {str(e)}"
                )
        
        @self.app.get("/api/memory/links/{link_id}", response_model=MemoryLink)
        async def get_link(link_id: str, token_data: Dict = Depends(self.token_validator)):
            try:
                link = self.memory_graph.get_link(link_id)
                
                if not link:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Link with ID {link_id} not found"
                    )
                    
                return link
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting link {link_id}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error getting link: {str(e)}"
                )
        
        @self.app.post("/api/memory/links", response_model=MemoryLink, status_code=status.HTTP_201_CREATED)
        async def create_link(link: MemoryLinkCreate, token_data: Dict = Depends(self.token_validator)):
            try:
                # Check if source and target nodes exist
                source_node = self.memory_graph.get_node(link.source_id)
                target_node = self.memory_graph.get_node(link.target_id)
                
                if not source_node:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Source node with ID {link.source_id} not found"
                    )
                    
                if not target_node:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Target node with ID {link.target_id} not found"
                    )
                
                created_link = self.memory_graph.create_link(
                    source_id=link.source_id,
                    target_id=link.target_id,
                    link_type=link.link_type,
                    metadata=link.metadata
                )
                
                return created_link
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error creating link: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error creating link: {str(e)}"
                )
        
        @self.app.put("/api/memory/links/{link_id}", response_model=MemoryLink)
        async def update_link(
            link_id: str, 
            link_update: MemoryLinkUpdate, 
            token_data: Dict = Depends(self.token_validator)
        ):
            try:
                # Convert to dict and remove None values
                update_data = link_update.dict(exclude_unset=True)
                
                updated_link = self.memory_graph.update_link(
                    link_id=link_id,
                    **update_data
                )
                
                if not updated_link:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Link with ID {link_id} not found"
                    )
                    
                return updated_link
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error updating link {link_id}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error updating link: {str(e)}"
                )
        
        @self.app.delete("/api/memory/links/{link_id}")
        async def delete_link(link_id: str, token_data: Dict = Depends(self.token_validator)):
            try:
                success = self.memory_graph.delete_link(link_id)
                
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Link with ID {link_id} not found"
                    )
                    
                return {"status": "success", "message": f"Link {link_id} deleted"}
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error deleting link {link_id}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error deleting link: {str(e)}"
                )
        
        # Search and Knowledge Retrieval
        @self.app.post("/api/memory/search", response_model=List[MemoryNode])
        async def search_nodes(query: SearchQuery, token_data: Dict = Depends(self.token_validator)):
            try:
                results = self.knowledge_retriever.search(
                    query=query.query,
                    filters=query.filters,
                    max_results=query.max_results
                )
                
                return results
                
            except Exception as e:
                logger.error(f"Error searching nodes: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error searching nodes: {str(e)}"
                )
        
        @self.app.get("/api/memory/visualize")
        async def get_visualization_data(token_data: Dict = Depends(self.token_validator)):
            try:
                visualization_data = self.memory_graph.get_visualization_data()
                return visualization_data
                
            except Exception as e:
                logger.error(f"Error getting visualization data: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error getting visualization data: {str(e)}"
                )
        
        # GitHub Integration
        @self.app.post("/api/github/analyze", status_code=status.HTTP_202_ACCEPTED)
        async def analyze_github_repo(
            repo_info: GithubRepoInfo, 
            background_tasks: BackgroundTasks,
            token_data: Dict = Depends(self.token_validator)
        ):
            try:
                # Start analysis in the background
                background_tasks.add_task(
                    self.github_api.analyze_repository,
                    repo_url=repo_info.repo_url,
                    branch=repo_info.branch
                )
                
                return {
                    "status": "accepted", 
                    "message": f"Analysis of {repo_info.repo_url} ({repo_info.branch}) started"
                }
                
            except Exception as e:
                logger.error(f"Error starting GitHub analysis: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error starting GitHub analysis: {str(e)}"
                )
        
        @self.app.get("/api/github/status/{repo_id}")
        async def get_github_analysis_status(
            repo_id: str,
            token_data: Dict = Depends(self.token_validator)
        ):
            try:
                status = self.github_api.get_analysis_status(repo_id)
                
                if not status:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Analysis for repository ID {repo_id} not found"
                    )
                    
                return status
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting GitHub analysis status: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error getting GitHub analysis status: {str(e)}"
                )
        
        # Model Context Protocol (MCP) Integration
        @self.app.post("/api/mcp/complete")
        async def complete_with_mcp(
            request: MCPRequest,
            token_data: Dict = Depends(self.token_validator)
        ):
            try:
                response = self.mcp_integration.complete(
                    prompt=request.prompt,
                    model_id=request.model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    tools=request.tools
                )
                
                return response
                
            except Exception as e:
                logger.error(f"Error completing with MCP: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error completing with MCP: {str(e)}"
                )
        
        # Feedback Loop
        @self.app.post("/api/feedback")
        async def submit_feedback(
            feedback: FeedbackRequest,
            token_data: Dict = Depends(self.token_validator)
        ):
            try:
                self.feedback_loop.record_feedback(
                    feature_id=feedback.feature_id,
                    rating=feedback.rating,
                    feedback_text=feedback.feedback_text,
                    metadata=feedback.metadata,
                    user_id=token_data.get("user_id", "anonymous")
                )
                
                return {"status": "success", "message": "Feedback recorded"}
                
            except Exception as e:
                logger.error(f"Error recording feedback: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error recording feedback: {str(e)}"
                )
                
        @self.app.get("/api/metrics")
        async def get_system_metrics(token_data: Dict = Depends(self.token_validator)):
            try:
                metrics = self.feedback_loop.get_system_metrics()
                return metrics
                
            except Exception as e:
                logger.error(f"Error getting system metrics: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error getting system metrics: {str(e)}"
                )
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Run the API server.
        This method is typically called from the CLI or a WSGI server.
        """
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)

# Convenience function to get API instance
def get_api():
    """Get the VOT1 API instance."""
    return VOT1API()

# CLI entrypoint
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VOT1 API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    args = parser.parse_args()
    
    api = VOT1API()
    api.run(host=args.host, port=args.port) 