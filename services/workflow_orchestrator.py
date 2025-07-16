"""
Workflow Orchestrator with full Bedrock integration and dynamic MCP support
"""

import asyncio
import uuid
import time
from typing import AsyncGenerator, Dict, Any, List
from datetime import datetime

from config.settings import Settings
from services.chunking import ChunkingService
from services.memory import MemoryService
from services.mcp_client import get_mcp_client
from services.bedrock_chat import get_chat_service
from services.bedrock_embedding import get_embedding_service
from storage.vector_store import VectorStore
from models.mcp_models import StreamingRequest, StreamingChunk, MCPRequest
from models.memory import MemoryType, MemoryChunk, MemoryQuery
from models.chunks import ChunkRequest, ChunkType
from utils.logging_config import get_logger
from services.bedrock_registry import BedrockModelRegistry

logger = get_logger(__name__)


class WorkflowOrchestrator:
    """Enhanced orchestrator with full Bedrock integration and dynamic MCP support"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Enhanced services - will be initialized during initialize()
        self.vector_store = None
        self.chunking_service = ChunkingService()
        self.memory_service = None
        self.mcp_client = None
        self.chat_service = None
        self.embedding_service = None
        self.bedrock_registry = BedrockModelRegistry()
        
        # State tracking
        self._initialized = False
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self):
        """Initialize all enhanced services"""
        if self._initialized:
            return
        
        logger.info("Initializing enhanced workflow orchestrator")
        
        try:
            # Initialize embedding service first
            self.embedding_service = await get_embedding_service()
            await self.embedding_service.initialize()
            
            # Get dynamic dimension from embedding service
            dimension = self.embedding_service.get_embedding_dimension()
            logger.info(f"Using embedding dimension: {dimension}")
            
            # Initialize vector store with dynamic dimension
            self.vector_store = VectorStore(
                index_path=self.settings.faiss_index_path,
                embedding_model=self.settings.embedding.model_name,
                dimension=dimension
            )
            await self.vector_store.initialize()
            
            # Initialize memory service
            self.memory_service = MemoryService(self.vector_store)
            await self.memory_service.initialize()
            
            # Initialize enhanced MCP client
            self.mcp_client = await get_mcp_client()
            await self.mcp_client.initialize()
            
            # Initialize chat service
            self.chat_service = await get_chat_service()
            await self.chat_service.initialize()
            
            self._initialized = True
            logger.info("Enhanced workflow orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced workflow orchestrator: {e}")
            raise
    
    async def stream_conversation(self, request: StreamingRequest) -> AsyncGenerator[StreamingChunk, None]:
        """
        Enhanced stream conversation with multiple MCP servers and Bedrock models
        """
        await self.initialize()
        
        conversation_id = str(uuid.uuid4())
        logger.info(f"Starting enhanced conversation {conversation_id}")
        
        # Initialize conversation state
        self.active_conversations[conversation_id] = {
            "start_time": time.time(),
            "total_chunks": 0,
            "processed_chunks": 0,
            "mcp_calls": 0,
            "errors": []
        }
        
        try:
            # Yield start chunk
            yield StreamingChunk(
                chunk_id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                content="Starting enhanced workflow processing...",
                chunk_type="status",
                timestamp=datetime.now(),
                metadata={"status": "started", "enhanced": True}
            )
            
            # Process through enhanced memory system
            if request.use_memory:
                yield StreamingChunk(
                    chunk_id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    content="Searching enhanced memory with Bedrock embeddings...",
                    chunk_type="status",
                    timestamp=datetime.now(),
                    metadata={"status": "memory_search"}
                )
                
                # Search memory using enhanced embeddings
                relevant_memories = await self.memory_service.search_memory(
                    MemoryQuery(
                        query=request.message,
                        user_id=request.user_id,
                        conversation_id=request.conversation_id,
                        limit=5
                    )
                )
                
                if relevant_memories.chunks:
                    yield StreamingChunk(
                        chunk_id=str(uuid.uuid4()),
                        conversation_id=conversation_id,
                        content=f"Found {len(relevant_memories.chunks)} relevant memories",
                        chunk_type="memory",
                        timestamp=datetime.now(),
                        metadata={"memory_count": len(relevant_memories.chunks)}
                    )
            
            # Get available MCP tools from all servers
            available_tools = await self.mcp_client.get_available_tools()
            total_tools = sum(len(tools) for tools in available_tools.values())
            
            yield StreamingChunk(
                chunk_id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                content=f"Connected to {len(available_tools)} MCP servers with {total_tools} total tools",
                chunk_type="status",
                timestamp=datetime.now(),
                metadata={"mcp_servers": list(available_tools.keys()), "total_tools": total_tools}
            )
            
            # Enhanced chunking with context
            if request.message:
                chunk_request = ChunkRequest(
                    content=request.message,
                    chunk_type=ChunkType.TEXT,
                    max_chunk_size=request.max_chunk_size or 1000,
                    overlap_size=request.overlap_size or 100
                )
                
                chunk_response = await self.chunking_service.create_chunks(chunk_request)
                chunks = chunk_response.chunks
                self.active_conversations[conversation_id]["total_chunks"] = len(chunks)
                
                yield StreamingChunk(
                    chunk_id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    content=f"Content split into {len(chunks)} semantic chunks",
                    chunk_type="status",
                    timestamp=datetime.now(),
                    metadata={"chunk_count": len(chunks)}
                )
                
                # Process each chunk with enhanced services
                for i, chunk in enumerate(chunks):
                    try:
                        # Store chunk in memory with Bedrock embeddings
                        memory_chunk = MemoryChunk(
                            content=chunk.content,
                            memory_type=MemoryType.DOCUMENT,
                            metadata={
                                "conversation_id": conversation_id,
                                "chunk_index": i,
                                "source": "enhanced_processing"
                            }
                        )
                        
                        await self.memory_service.store_memory(memory_chunk)
                        
                        # Process with MCP tools if requested
                        if request.mcp_tools and available_tools:
                            for tool_name in request.mcp_tools:
                                try:
                                    result = await self.mcp_client.call_tool(
                                        tool_name=tool_name,
                                        arguments={"content": chunk.content, "context": request.query}
                                    )
                                    
                                    self.active_conversations[conversation_id]["mcp_calls"] += 1
                                    
                                    yield StreamingChunk(
                                        chunk_id=str(uuid.uuid4()),
                                        conversation_id=conversation_id,
                                        content=f"MCP tool '{tool_name}' result: {result}",
                                        chunk_type="mcp_result",
                                        timestamp=datetime.now(),
                                        metadata={"tool": tool_name, "chunk_index": i}
                                    )
                                    
                                except Exception as e:
                                    error_msg = f"MCP tool '{tool_name}' failed: {str(e)}"
                                    logger.warning(error_msg)
                                    self.active_conversations[conversation_id]["errors"].append(error_msg)
                        
                        self.active_conversations[conversation_id]["processed_chunks"] += 1
                        
                        yield StreamingChunk(
                            chunk_id=str(uuid.uuid4()),
                            conversation_id=conversation_id,
                            content=chunk.content,
                            chunk_type="content",
                            timestamp=datetime.now(),
                            metadata={
                                "chunk_index": i,
                                "processed": True,
                                "stored_in_memory": True
                            }
                        )
                        
                    except Exception as e:
                        error_msg = f"Error processing chunk {i}: {str(e)}"
                        logger.error(error_msg)
                        self.active_conversations[conversation_id]["errors"].append(error_msg)
                        
                        yield StreamingChunk(
                            chunk_id=str(uuid.uuid4()),
                            conversation_id=conversation_id,
                            content=f"Error processing chunk {i}: {str(e)}",
                            chunk_type="error",
                            timestamp=datetime.now(),
                            metadata={"chunk_index": i, "error": str(e)}
                        )
            
            # Generate final response using enhanced Bedrock chat
            if self.chat_service:
                try:
                    # Build context from memory and processed content
                    context_parts = []
                    if request.use_memory and relevant_memories:
                        context_parts.append("Relevant memories:")
                        for memory in relevant_memories[:3]:  # Use top 3 memories
                            context_parts.append(f"- {memory.content[:200]}...")
                    
                    if request.message:
                        context_parts.append(f"Processed content with {len(chunks) if 'chunks' in locals() else 0} chunks")
                    
                    context = "\n".join(context_parts) if context_parts else None
                    
                    response = await self.chat_service.get_response(
                        message=request.message,
                        context=context
                    )
                    
                    yield StreamingChunk(
                        chunk_id=str(uuid.uuid4()),
                        conversation_id=conversation_id,
                        content=response,
                        chunk_type="ai_response",
                        timestamp=datetime.now(),
                        metadata={"model": self.chat_service.model_id, "has_context": context is not None}
                    )
                    
                except Exception as e:
                    error_msg = f"Chat service error: {str(e)}"
                    logger.error(error_msg)
                    yield StreamingChunk(
                        chunk_id=str(uuid.uuid4()),
                        conversation_id=conversation_id,
                        content=f"AI response generation failed: {str(e)}",
                        chunk_type="error",
                        timestamp=datetime.now(),
                        metadata={"error": str(e)}
                    )
            
            # Final status
            conversation_stats = self.active_conversations[conversation_id]
            duration = time.time() - conversation_stats["start_time"]
            
            yield StreamingChunk(
                chunk_id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                content="Enhanced workflow processing completed",
                chunk_type="status",
                is_final=True,
                timestamp=datetime.now(),
                metadata={
                    "status": "completed",
                    "duration": duration,
                    "total_chunks": conversation_stats["total_chunks"],
                    "processed_chunks": conversation_stats["processed_chunks"],
                    "mcp_calls": conversation_stats["mcp_calls"],
                    "errors": len(conversation_stats["errors"]),
                    "enhanced": True
                }
            )
            
        except Exception as e:
            logger.error(f"Enhanced conversation {conversation_id} failed: {e}")
            yield StreamingChunk(
                chunk_id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                content=f"Workflow processing failed: {str(e)}",
                chunk_type="error",
                timestamp=datetime.now(),
                metadata={"error": str(e), "conversation_id": conversation_id}
            )
        
        finally:
            # Cleanup conversation state
            if conversation_id in self.active_conversations:
                del self.active_conversations[conversation_id]
    
    async def process_mcp_request(self, request: MCPRequest) -> Dict[str, Any]:
        """Enhanced MCP request processing with multiple servers"""
        await self.initialize()
        
        try:
            # Get server status
            server_status = await self.mcp_client.get_server_status()
            
            # Try to call the tool on any available server
            result = await self.mcp_client.call_tool(
                tool_name=request.tool_name,
                arguments=request.arguments,
                preferred_server=request.metadata.get("preferred_server")
            )
            
            return {
                "success": True,
                "result": result,
                "metadata": {
                    "enhanced": True,
                    "server_status": server_status,
                    "tool": request.tool_name
                }
            }
            
        except Exception as e:
            logger.error(f"Enhanced MCP request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "enhanced": True,
                    "tool": request.tool_name
                }
            }
    
    async def get_mcp_server_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers"""
        await self.initialize()
        return await self.mcp_client.get_server_status()
    
    async def get_available_bedrock_models(self) -> Dict[str, Any]:
        """Get information about available Bedrock models"""
        await self.initialize()
        
        return {
            "embedding_models": self.bedrock_registry.get_embedding_models(),
            "chat_models": self.bedrock_registry.get_chat_models(),
            "image_models": self.bedrock_registry.get_image_models(),
            "current_embedding_model": self.embedding_service.model_id if self.embedding_service else None,
            "current_chat_model": self.chat_service.model_id if self.chat_service else None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of all system components"""
        await self.initialize()
        
        health_status = {
            "orchestrator": "healthy" if self._initialized else "unhealthy",
            "timestamp": datetime.now().isoformat()
        }
        
        # Check vector store
        try:
            if self.vector_store:
                stats = await self.vector_store.get_stats()
                health_status["vector_store"] = "healthy"
                health_status["vector_store_stats"] = stats
            else:
                health_status["vector_store"] = "not_initialized"
        except Exception as e:
            health_status["vector_store"] = f"error: {str(e)}"
        
        # Check memory service
        try:
            if self.memory_service:
                # Use a test user_id for health check
                stats = await self.memory_service.get_memory_stats("health_check_user")
                health_status["memory_service"] = "healthy"
                health_status["memory_stats"] = stats
            else:
                health_status["memory_service"] = "not_initialized"
        except Exception as e:
            health_status["memory_service"] = f"error: {str(e)}"
        
        # Check chunking service
        try:
            if self.chunking_service:
                health_status["chunking_service"] = "healthy"
            else:
                health_status["chunking_service"] = "not_initialized"
        except Exception as e:
            health_status["chunking_service"] = f"error: {str(e)}"
        
        # Check MCP client
        try:
            if self.mcp_client:
                server_status = await self.mcp_client.get_server_status()
                connected_servers = sum(1 for status in server_status.values() 
                                      if status.get('connected', False))
                health_status["mcp_client"] = "healthy"
                health_status["mcp_servers"] = {
                    "total": len(server_status),
                    "connected": connected_servers,
                    "status": server_status
                }
            else:
                health_status["mcp_client"] = "not_initialized"
        except Exception as e:
            health_status["mcp_client"] = f"error: {str(e)}"
        
        # Check chat service (may fail without AWS credentials)
        try:
            if self.chat_service:
                health_status["chat_service"] = "healthy"
                health_status["chat_model"] = self.chat_service.model_id
            else:
                health_status["chat_service"] = "not_initialized"
        except Exception as e:
            health_status["chat_service"] = f"error: {str(e)}"
        
        # Check embedding service (may fail without AWS credentials)
        try:
            if self.embedding_service:
                health_status["embedding_service"] = "healthy"
                health_status["embedding_model"] = self.embedding_service.model_id
            else:
                health_status["embedding_service"] = "not_initialized"
        except Exception as e:
            health_status["embedding_service"] = f"error: {str(e)}"
        
        return health_status

    async def get_conversation_stats(self, user_id: str) -> Dict[str, Any]:
        """Get conversation statistics for a user"""
        await self.initialize()
        
        try:
            # Get memory stats for user
            memory_stats = await self.memory_service.get_memory_stats(user_id)
            
            # Count active conversations for user
            user_conversations = [
                conv_id for conv_id, conv_data in self.active_conversations.items()
                if conv_data.get("user_id") == user_id
            ]
            
            # Get user-specific memory count
            user_memories = await self.memory_service.search_memory(
                MemoryQuery(
                    query="",  # Empty query to get all
                    user_id=user_id,
                    limit=100  # Max allowed limit
                )
            )
            
            return {
                "user_id": user_id,
                "active_conversations": len(user_conversations),
                "total_memories": len(user_memories.chunks),
                "global_memory_stats": memory_stats,
                "conversation_ids": user_conversations
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation stats for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "error": str(e),
                "active_conversations": 0,
                "total_memories": 0
            }

    async def cleanup(self):
        """Clean up all services"""
        logger.info("Cleaning up enhanced workflow orchestrator")
        
        cleanup_tasks = []
        
        if self.embedding_service:
            cleanup_tasks.append(self.embedding_service.cleanup())
        
        if self.chat_service:
            cleanup_tasks.append(self.chat_service.cleanup())
        
        if self.mcp_client:
            cleanup_tasks.append(self.mcp_client.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        # Clear conversation state
        self.active_conversations.clear()
        self._initialized = False
        
        logger.info("Enhanced workflow orchestrator cleanup completed")


# Global orchestrator instance
_orchestrator_instance = None


async def get_workflow_orchestrator(settings: Settings) -> WorkflowOrchestrator:
    """Get or create the global enhanced workflow orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = WorkflowOrchestrator(settings)
    return _orchestrator_instance


async def cleanup_workflow_orchestrator():
    """Clean up the global workflow orchestrator"""
    global _orchestrator_instance
    if _orchestrator_instance:
        await _orchestrator_instance.cleanup()
        _orchestrator_instance = None
