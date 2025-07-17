# filepath: /Users/saivarshithvv/Documents/projects/agenticflow/main.py
"""
PydanticAI Agentic Workflow System - Main Application Entry Point
Pure PydanticAI implementation with dynamic MCP servers and Bedrock integration
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from services.workflow_orchestrator import get_workflow_orchestrator
from models.mcp_models import StreamingRequest
from utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """PydanticAI agentic application lifespan manager"""
    global orchestrator
    
    logger.info("Starting PydanticAI Agentic Workflow System...")
    
    try:
        # Initialize PydanticAI agentic workflow orchestrator
        orchestrator = await get_workflow_orchestrator()
        
        logger.info("PydanticAI agentic system initialization completed successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize PydanticAI agentic system: {e}")
        raise
    finally:
        # PydanticAI agentic cleanup
        if orchestrator:
            await orchestrator.cleanup()
        logger.info("PydanticAI agentic system cleanup completed")

# Create FastAPI app
app = FastAPI(
    title="PydanticAI Agentic Workflow System",
    description="Pure PydanticAI agentic workflow system with MCP integration and Bedrock APIs",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Core Application Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PydanticAI Agentic Workflow System",
        "version": "1.0.0",
        "status": "running",
        "description": "Pure PydanticAI agentic workflows with dynamic MCP integration"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if orchestrator:
        return {"status": "healthy", "components": await orchestrator.health_check()}
    return {"status": "unhealthy", "error": "PydanticAI agentic system not initialized"}

# ============================================================================
# PydanticAI Agentic Workflow Endpoints
# ============================================================================

@app.post("/api/v1/agentic-workflow")
async def create_agentic_workflow(request: StreamingRequest):
    """Create a pure PydanticAI agentic workflow with dynamic MCP integration"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="PydanticAI agentic system not initialized")
    
    async def generate_agentic_stream():
        try:
            async for chunk in orchestrator.create_agentic_workflow(request):
                yield f"data: {chunk.model_dump_json()}\n\n"
        except Exception as e:
            logger.error(f"Agentic workflow error: {e}")
            error_chunk = {
                "chunk_id": "error",
                "conversation_id": request.conversation_id,
                "content": f"Agentic workflow error: {str(e)}",
                "chunk_type": "agent_error",
                "is_final": True,
                "metadata": {"error": True, "agent_error": str(e)}
            }
            yield f"data: {error_chunk}\n\n"
    
    return StreamingResponse(
        generate_agentic_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.post("/api/v1/pydantic-ai/chat")
async def pydantic_ai_chat(request: StreamingRequest):
    """Direct PydanticAI agent chat with structured responses"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="PydanticAI agentic system not initialized")
    
    if not orchestrator.pydantic_ai_service or not orchestrator.pydantic_ai_service._initialized:
        raise HTTPException(status_code=503, detail="PydanticAI service not available")
    
    try:
        response = await orchestrator.pydantic_ai_service.process_conversation(request)
        return {
            "content": response.content,
            "task_type": response.task_type.value if response.task_type else None,
            "confidence": {
                "score": response.confidence.score if response.confidence else 0.0,
                "reasoning": response.confidence.reasoning if response.confidence else "",
                "factors": response.confidence.factors if response.confidence else []
            } if response.confidence else None,
            "evidence": [
                {
                    "source": evidence.source,
                    "content": evidence.content,
                    "relevance_score": evidence.relevance_score,
                    "metadata": evidence.metadata
                } for evidence in response.evidence
            ] if response.evidence else [],
            "tools_used": response.tools_used or [],
            "reasoning_chain": [
                {
                    "step_number": step.step_number,
                    "description": step.description,
                    "confidence": step.confidence
                } for step in response.reasoning_chain
            ] if response.reasoning_chain else [],
            "suggestions": response.suggestions or [],
            "metadata": response.metadata or {}
        }
    except Exception as e:
        logger.error(f"PydanticAI chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Agent and MCP Server Management Endpoints
# ============================================================================

@app.get("/api/v1/agent/health")
async def get_agent_health():
    """Get comprehensive health status of PydanticAI agentic services"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="PydanticAI agentic system not initialized")
    
    try:
        health_status = await orchestrator.get_agent_health()
        return health_status
    except Exception as e:
        logger.error(f"Agent health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/mcp/servers")
async def get_connected_mcp_servers():
    """Get list of connected MCP servers"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="PydanticAI agentic system not initialized")
    
    try:
        return {
            "connected_servers": orchestrator.connected_mcp_servers,
            "total_servers": len(orchestrator.connected_mcp_servers),
            "active_agents": len(orchestrator.active_agents)
        }
    except Exception as e:
        logger.error(f"MCP servers query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/mcp/tools")
async def get_available_tools():
    """Get available tools from all connected MCP servers"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="PydanticAI agentic system not initialized")
    
    try:
        tools = await orchestrator.mcp_client.get_available_tools()
        return {
            "success": True,
            "tools": tools,
            "message": "Available tools retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to get available tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/mcp/servers/reload")
async def reload_mcp_config():
    """Reload MCP server configuration"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="PydanticAI agentic system not initialized")
    
    try:
        await orchestrator.mcp_client.reload_config()
        return {
            "success": True,
            "message": "MCP configuration reloaded successfully"
        }
    except Exception as e:
        logger.error(f"Failed to reload MCP config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Bedrock Integration Endpoints
# ============================================================================

@app.get("/api/v1/bedrock/models")
async def get_bedrock_models():
    """Get available Bedrock models information"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="PydanticAI agentic system not initialized")
    
    try:
        models_info = await orchestrator.get_available_bedrock_models()
        return {
            "success": True,
            "models": models_info,
            "message": "Bedrock models retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to get Bedrock models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Application Startup
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
