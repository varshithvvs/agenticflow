"""
PydanticAI Agentic Workflow Orchestrator
Pure PydanticAI implementation with dynamic MCP servers and Bedrock integration
"""

import uuid
import time
from typing import AsyncGenerator, Dict, Any, List
from datetime import datetime

from config.settings import Settings
from services.memory import MemoryService
from services.mcp_client import get_mcp_client
from services.bedrock_embedding import get_embedding_service
from services.pydantic_ai_agent import get_pydantic_ai_service
from storage.vector_store import VectorStore
from models.mcp_models import StreamingRequest, StreamingChunk
from models.pydantic_ai_models import StructuredResponse
from utils.logging_config import get_logger

logger = get_logger(__name__)


class PydanticAIWorkflowOrchestrator:
    """
    Pure PydanticAI Agentic Workflow Orchestrator
    All workflows are handled by PydanticAI agents with dynamic MCP server integration
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Core PydanticAI services
        self.vector_store = None
        self.memory_service = None
        self.mcp_client = None
        self.embedding_service = None
        self.pydantic_ai_service = None
        
        # Agent state tracking
        self._initialized = False
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.connected_mcp_servers: List[str] = []
    
    async def initialize(self):
        """Initialize PydanticAI agentic services"""
        if self._initialized:
            return
        
        logger.info("Initializing PydanticAI agentic workflow orchestrator")
        
        try:
            # Initialize embedding service for memory
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
            
            # Initialize memory service for agent context
            self.memory_service = MemoryService(self.vector_store)
            await self.memory_service.initialize()
            
            # Initialize dynamic MCP client for tool integration
            self.mcp_client = await get_mcp_client()
            await self.mcp_client.initialize()
            
            # Discover connected MCP servers
            available_tools = await self.mcp_client.get_available_tools()
            self.connected_mcp_servers = list(available_tools.keys())
            total_tools = sum(len(tools) for tools in available_tools.values())
            
            logger.info(f"Connected to {len(self.connected_mcp_servers)} MCP servers with {total_tools} tools")
            
            # Initialize core PydanticAI service with all integrations
            self.pydantic_ai_service = await get_pydantic_ai_service(self.settings)
            await self.pydantic_ai_service.initialize(
                memory_service=self.memory_service,
                mcp_client=self.mcp_client
            )
            
            self._initialized = True
            logger.info("PydanticAI agentic workflow orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PydanticAI agentic orchestrator: {e}")
            raise

    async def create_agentic_workflow(self, request: StreamingRequest) -> AsyncGenerator[StreamingChunk, None]:
        """
        Create a pure PydanticAI agentic workflow with dynamic MCP server integration
        All processing is handled by PydanticAI agents with Bedrock APIs
        """
        await self.initialize()
        
        agent_id = str(uuid.uuid4())
        logger.info(f"Starting PydanticAI agentic workflow {agent_id}")
        
        # Initialize agent state
        self.active_agents[agent_id] = {
            "start_time": time.time(),
            "user_id": request.user_id,
            "conversation_id": request.conversation_id,
            "mcp_calls": 0,
            "processing_steps": 0,
            "errors": []
        }
        
        try:
            # Yield start notification
            yield StreamingChunk(
                chunk_id=str(uuid.uuid4()),
                conversation_id=request.conversation_id,
                content="🤖 Initializing PydanticAI agent workflow...",
                chunk_type="agent_start",
                timestamp=datetime.now(),
                metadata={
                    "agent_id": agent_id,
                    "status": "initializing",
                    "mcp_servers": self.connected_mcp_servers,
                    "total_servers": len(self.connected_mcp_servers)
                }
            )
            
            # Agent discovery and tool preparation
            yield StreamingChunk(
                chunk_id=str(uuid.uuid4()),
                conversation_id=request.conversation_id,
                content=f"🔧 Agent connected to {len(self.connected_mcp_servers)} MCP servers",
                chunk_type="agent_status",
                timestamp=datetime.now(),
                metadata={
                    "connected_servers": self.connected_mcp_servers,
                    "agent_capabilities": ["bedrock_chat", "memory_search", "tool_execution"]
                }
            )
            
            # Process request through PydanticAI agent
            if self.pydantic_ai_service and self.pydantic_ai_service._initialized:
                self.active_agents[agent_id]["processing_steps"] += 1
                
                yield StreamingChunk(
                    chunk_id=str(uuid.uuid4()),
                    conversation_id=request.conversation_id,
                    content="🧠 PydanticAI agent processing request with Bedrock integration...",
                    chunk_type="agent_processing",
                    timestamp=datetime.now(),
                    metadata={"step": "pydantic_ai_processing"}
                )
                
                try:
                    # Get structured response from PydanticAI agent
                    agent_response: StructuredResponse = await self.pydantic_ai_service.process_conversation(request)
                    
                    # Update agent state
                    self.active_agents[agent_id]["mcp_calls"] = len(agent_response.tools_used) if agent_response.tools_used else 0
                    self.active_agents[agent_id]["processing_steps"] += 1
                    
                    # Stream the agent's structured response
                    yield StreamingChunk(
                        chunk_id=str(uuid.uuid4()),
                        conversation_id=request.conversation_id,
                        content=agent_response.content,
                        chunk_type="agent_response",
                        timestamp=datetime.now(),
                        metadata={
                            "agent_id": agent_id,
                            "task_type": agent_response.task_type.value if agent_response.task_type else "unknown",
                            "confidence_score": agent_response.confidence.score if agent_response.confidence else 0.0,
                            "confidence_reasoning": agent_response.confidence.reasoning if agent_response.confidence else "",
                            "evidence_count": len(agent_response.evidence) if agent_response.evidence else 0,
                            "tools_used": agent_response.tools_used or [],
                            "reasoning_steps": len(agent_response.reasoning_chain) if agent_response.reasoning_chain else 0,
                            "suggestions": agent_response.suggestions or []
                        }
                    )
                    
                    # Stream evidence if available
                    if agent_response.evidence:
                        for i, evidence in enumerate(agent_response.evidence):
                            yield StreamingChunk(
                                chunk_id=str(uuid.uuid4()),
                                conversation_id=request.conversation_id,
                                content=f"📚 Evidence {i+1}: {evidence.content[:200]}...",
                                chunk_type="agent_evidence",
                                timestamp=datetime.now(),
                                metadata={
                                    "evidence_source": evidence.source,
                                    "relevance_score": evidence.relevance_score,
                                    "evidence_index": i
                                }
                            )
                    
                    # Stream reasoning steps if available
                    if agent_response.reasoning_chain:
                        for step in agent_response.reasoning_chain:
                            yield StreamingChunk(
                                chunk_id=str(uuid.uuid4()),
                                conversation_id=request.conversation_id,
                                content=f"🔍 Step {step.step_number}: {step.description}",
                                chunk_type="agent_reasoning",
                                timestamp=datetime.now(),
                                metadata={
                                    "step_confidence": step.confidence,
                                    "step_number": step.step_number
                                }
                            )
                    
                    # Stream suggestions if available
                    if agent_response.suggestions:
                        for i, suggestion in enumerate(agent_response.suggestions):
                            yield StreamingChunk(
                                chunk_id=str(uuid.uuid4()),
                                conversation_id=request.conversation_id,
                                content=f"💡 Suggestion {i+1}: {suggestion}",
                                chunk_type="agent_suggestion",
                                timestamp=datetime.now(),
                                metadata={"suggestion_index": i}
                            )
                    
                except Exception as e:
                    error_msg = f"PydanticAI agent processing failed: {str(e)}"
                    logger.error(error_msg)
                    self.active_agents[agent_id]["errors"].append(error_msg)
                    
                    yield StreamingChunk(
                        chunk_id=str(uuid.uuid4()),
                        conversation_id=request.conversation_id,
                        content=f"❌ Agent processing error: {str(e)}",
                        chunk_type="agent_error",
                        timestamp=datetime.now(),
                        metadata={"error": str(e), "agent_id": agent_id}
                    )
            else:
                error_msg = "PydanticAI service not available"
                self.active_agents[agent_id]["errors"].append(error_msg)
                
                yield StreamingChunk(
                    chunk_id=str(uuid.uuid4()),
                    conversation_id=request.conversation_id,
                    content="❌ PydanticAI service not available",
                    chunk_type="agent_error",
                    timestamp=datetime.now(),
                    metadata={"error": error_msg}
                )
            
            # Final agent status
            agent_stats = self.active_agents[agent_id]
            duration = time.time() - agent_stats["start_time"]
            
            yield StreamingChunk(
                chunk_id=str(uuid.uuid4()),
                conversation_id=request.conversation_id,
                content="✅ PydanticAI agentic workflow completed",
                chunk_type="agent_complete",
                is_final=True,
                timestamp=datetime.now(),
                metadata={
                    "agent_id": agent_id,
                    "status": "completed",
                    "duration_ms": int(duration * 1000),
                    "processing_steps": agent_stats["processing_steps"],
                    "mcp_calls": agent_stats["mcp_calls"],
                    "errors": len(agent_stats["errors"]),
                    "success": len(agent_stats["errors"]) == 0
                }
            )
            
        except Exception as e:
            logger.error(f"PydanticAI agentic workflow {agent_id} failed: {e}")
            yield StreamingChunk(
                chunk_id=str(uuid.uuid4()),
                conversation_id=request.conversation_id,
                content=f"💥 Agentic workflow failed: {str(e)}",
                chunk_type="agent_error",
                timestamp=datetime.now(),
                metadata={"error": str(e), "agent_id": agent_id}
            )
        
        finally:
            # Cleanup agent state
            if agent_id in self.active_agents:
                del self.active_agents[agent_id]

    async def get_agent_health(self) -> Dict[str, Any]:
        """Get health status of all PydanticAI agentic services"""
        await self.initialize()
        
        return {
            "orchestrator_initialized": self._initialized,
            "pydantic_ai_service": {
                "available": self.pydantic_ai_service is not None,
                "initialized": self.pydantic_ai_service._initialized if self.pydantic_ai_service else False
            },
            "mcp_client": {
                "available": self.mcp_client is not None,
                "connected_servers": self.connected_mcp_servers,
                "total_servers": len(self.connected_mcp_servers)
            },
            "memory_service": {
                "available": self.memory_service is not None,
                "vector_store_initialized": self.vector_store is not None
            },
            "embedding_service": {
                "available": self.embedding_service is not None,
                "dimension": self.embedding_service.get_embedding_dimension() if self.embedding_service else None
            },
            "active_agents": len(self.active_agents),
            "timestamp": datetime.now().isoformat()
        }

    async def health_check(self) -> Dict[str, Any]:
        """Basic health check for the orchestrator"""
        await self.initialize()
        
        return {
            "orchestrator": "healthy" if self._initialized else "unhealthy",
            "pydantic_ai_service": "healthy" if (self.pydantic_ai_service and self.pydantic_ai_service._initialized) else "unhealthy",
            "mcp_client": "healthy" if self.mcp_client else "unhealthy",
            "memory_service": "healthy" if self.memory_service else "unhealthy",
            "embedding_service": "healthy" if self.embedding_service else "unhealthy",
            "connected_servers": len(self.connected_mcp_servers),
            "active_agents": len(self.active_agents)
        }
    
    async def get_available_bedrock_models(self) -> List[Dict[str, Any]]:
        """Get available Bedrock models information"""
        await self.initialize()
        
        if not self.pydantic_ai_service:
            raise RuntimeError("PydanticAI service not available")
        
        # Return information about available Bedrock models
        # This would typically come from the Bedrock service or PydanticAI service
        return [
            {
                "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                "model_name": "Claude 3.5 Sonnet",
                "provider": "Anthropic",
                "capabilities": ["text", "chat", "reasoning"],
                "max_tokens": 200000,
                "supported_apis": ["invoke", "converse"]
            },
            {
                "model_id": "anthropic.claude-3-5-haiku-20241022-v1:0",
                "model_name": "Claude 3.5 Haiku",
                "provider": "Anthropic",
                "capabilities": ["text", "chat", "fast_reasoning"],
                "max_tokens": 200000,
                "supported_apis": ["invoke", "converse"]
            },
            {
                "model_id": "anthropic.claude-3-opus-20240229-v1:0",
                "model_name": "Claude 3 Opus",
                "provider": "Anthropic",
                "capabilities": ["text", "chat", "advanced_reasoning"],
                "max_tokens": 200000,
                "supported_apis": ["invoke", "converse"]
            }
        ]

    async def cleanup(self):
        """Cleanup all PydanticAI agentic services and resources"""
        try:
            logger.info("Cleaning up PydanticAI agentic workflow orchestrator resources")
            
            # Cleanup active agents
            self.active_agents.clear()
            
            # Cleanup services
            if self.mcp_client:
                await self.mcp_client.cleanup()
            
            if self.pydantic_ai_service:
                await self.pydantic_ai_service.cleanup()
                
            if self.memory_service:
                await self.memory_service.cleanup()
                
            if self.vector_store:
                await self.vector_store.cleanup()
                
            logger.info("PydanticAI agentic workflow orchestrator cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during PydanticAI agentic orchestrator cleanup: {e}")


# Factory function (updated for new class name)
async def get_workflow_orchestrator() -> PydanticAIWorkflowOrchestrator:
    """Factory function to create and initialize a PydanticAI Workflow Orchestrator instance"""
    settings = Settings()
    orchestrator = PydanticAIWorkflowOrchestrator(settings)
    await orchestrator.initialize()
    return orchestrator

# Backward compatibility alias
WorkflowOrchestrator = PydanticAIWorkflowOrchestrator
