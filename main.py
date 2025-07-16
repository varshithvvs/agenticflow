"""
PydanticAI Workflow System - Main Application Entry Point
Complete system with full Bedrock integration and dynamic MCP support
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from config.settings import get_settings
from services.workflow_orchestrator import get_workflow_orchestrator, cleanup_workflow_orchestrator
from models.mcp_models import StreamingRequest, MCPRequest
from models.chunks import ChunkRequest
from models.memory import MemoryQuery
from utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Enhanced application lifespan manager"""
    global orchestrator
    
    logger.info("Starting Enhanced PydanticAI Workflow System...")
    
    try:
        # Initialize settings
        settings = get_settings()
        
        # Initialize enhanced workflow orchestrator
        orchestrator = await get_workflow_orchestrator(settings)
        await orchestrator.initialize()
        
        logger.info("Enhanced system initialization completed successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize enhanced system: {e}")
        raise
    finally:
        # Enhanced cleanup
        await cleanup_workflow_orchestrator()
        logger.info("Enhanced system cleanup completed")
        logger.info("System shutdown completed")

# Create FastAPI app
app = FastAPI(
    title="PydanticAI Workflow System",
    description="Complete workflow system with MCP integration, chunking, and conversation-aware memory",
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

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PydanticAI Workflow System",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if orchestrator:
        return {"status": "healthy", "components": await orchestrator.health_check()}
    return {"status": "unhealthy", "error": "System not initialized"}

@app.post("/api/v1/stream")
async def stream_conversation(request: StreamingRequest):
    """Stream conversation responses with memory and MCP integration"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    async def generate_stream():
        try:
            async for chunk in orchestrator.stream_conversation(request):
                yield f"data: {chunk.model_dump_json()}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            error_chunk = {
                "chunk_id": "error",
                "content": f"Error: {str(e)}",
                "is_final": True,
                "metadata": {"error": True}
            }
            yield f"data: {error_chunk}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@app.post("/api/v1/chunks")
async def create_chunks(request: ChunkRequest):
    """Create chunks from content"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    try:
        response = await orchestrator.chunking_service.create_chunks(request)
        return response
    except Exception as e:
        logger.error(f"Chunking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/mcp/call")
async def call_mcp_tool(request: MCPRequest):
    """Call an MCP tool"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    try:
        response = await orchestrator.mcp_client.call_tool(request)
        return response
    except Exception as e:
        logger.error(f"MCP call error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/mcp/tools")
async def get_mcp_tools():
    """Get available MCP tools"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    try:
        tools = await orchestrator.mcp_client.get_available_tools()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"MCP tools error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/memory/search")
async def search_memory(query: MemoryQuery):
    """Search memory"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    try:
        response = await orchestrator.memory_service.search_memory(query)
        return response
    except Exception as e:
        logger.error(f"Memory search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/memory/stats/{user_id}")
async def get_memory_stats(user_id: str):
    """Get memory statistics for a user"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    try:
        stats = await orchestrator.memory_service.get_memory_stats(user_id)
        return stats
    except Exception as e:
        logger.error(f"Memory stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/memory/consolidate/{user_id}/{conversation_id}")
async def consolidate_memory(user_id: str, conversation_id: str, background_tasks: BackgroundTasks):
    """Consolidate memory in background"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    background_tasks.add_task(
        orchestrator.memory_service.consolidate_memory,
        user_id,
        conversation_id
    )
    
    return {"message": "Memory consolidation started"}

@app.get("/api/v1/chunks/{chunk_id}")
async def get_chunk(chunk_id: str):
    """Get a specific chunk"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    try:
        chunk = await orchestrator.chunking_service.get_chunk(chunk_id)
        return chunk
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Get chunk error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/chunks/source/{source_id}")
async def get_chunks_by_source(source_id: str):
    """Get all chunks for a source"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    try:
        chunks = await orchestrator.chunking_service.get_chunks_by_source(source_id)
        return {"chunks": chunks, "count": len(chunks)}
    except Exception as e:
        logger.error(f"Get chunks by source error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Bedrock and MCP management endpoints

@app.get("/api/v1/bedrock/models")
async def get_bedrock_models():
    """Get available Bedrock models information"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="System not initialized")
    
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

@app.get("/api/v1/mcp/servers")
async def get_mcp_servers():
    """Get status of all MCP servers"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    try:
        server_status = await orchestrator.get_mcp_server_status()
        return {
            "success": True,
            "servers": server_status,
            "message": "MCP server status retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to get MCP server status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/mcp/tools")
async def get_available_tools():
    """Get available tools from all connected MCP servers"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="System not initialized")
    
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
        raise HTTPException(status_code=500, detail="System not initialized")
    
    try:
        await orchestrator.mcp_client.reload_config()
        return {
            "success": True,
            "message": "MCP configuration reloaded successfully"
        }
    except Exception as e:
        logger.error(f"Failed to reload MCP config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
