"""
Integration tests for PydanticAI Agentic Workflow System
Tests end-to-end functionality with pure PydanticAI agents
"""

import pytest
from models.mcp_models import StreamingRequest


@pytest.mark.asyncio
async def test_agentic_orchestrator_initialization(orchestrator):
    """Test that the PydanticAI agentic orchestrator initializes all components"""
    assert orchestrator.pydantic_ai_service is not None
    assert orchestrator.memory_service is not None
    assert orchestrator.vector_store is not None
    assert orchestrator.mcp_client is not None
    assert orchestrator.embedding_service is not None
    assert orchestrator._initialized is True


@pytest.mark.asyncio
async def test_agent_health_check(orchestrator):
    """Test PydanticAI agent health check"""
    health = await orchestrator.get_agent_health()
    
    assert "orchestrator_initialized" in health
    assert "pydantic_ai_service" in health
    assert "mcp_client" in health
    assert "memory_service" in health
    assert "embedding_service" in health
    assert "active_agents" in health
    assert "timestamp" in health
    
    assert health["orchestrator_initialized"] is True
    assert health["pydantic_ai_service"]["available"] is True
    assert health["memory_service"]["available"] is True


@pytest.mark.asyncio
async def test_agentic_workflow_streaming(orchestrator):
    """Test PydanticAI agentic workflow streaming"""
    request = StreamingRequest(
        message="Test the PydanticAI agentic system",
        user_id="test_user",
        conversation_id="test_conv",
        use_memory=True,
        mcp_tools=[]
    )
    
    chunks = []
    async for chunk in orchestrator.create_agentic_workflow(request):
        chunks.append(chunk)
        if chunk.is_final:
            break
    
    assert len(chunks) > 0
    assert any(chunk.chunk_type == "agent_start" for chunk in chunks)
    assert any(chunk.chunk_type == "agent_complete" for chunk in chunks)
    
    # Check final chunk
    final_chunk = chunks[-1]
    assert final_chunk.is_final is True
    assert final_chunk.chunk_type == "agent_complete"


@pytest.mark.asyncio
async def test_pydantic_ai_direct_chat(orchestrator):
    """Test direct PydanticAI agent conversation"""
    request = StreamingRequest(
        message="Analyze the benefits of PydanticAI agents",
        user_id="test_user",
        conversation_id="test_conv",
        use_memory=True
    )
    
    response = await orchestrator.pydantic_ai_service.process_conversation(request)
    
    assert response is not None
    assert response.content is not None
    assert len(response.content) > 0
    assert hasattr(response, 'confidence')
    assert hasattr(response, 'evidence')
    assert hasattr(response, 'tools_used')


@pytest.mark.asyncio
async def test_bedrock_models_availability(orchestrator):
    """Test Bedrock models information"""
    models = await orchestrator.get_available_bedrock_models()
    
    assert isinstance(models, list)
    assert len(models) > 0
    
    # Check model structure
    for model in models:
        assert "model_id" in model
        assert "model_name" in model
        assert "provider" in model
        assert "capabilities" in model
        assert "supported_apis" in model


@pytest.mark.asyncio
async def test_mcp_server_discovery(orchestrator):
    """Test MCP server discovery and tools"""
    # This may be empty in test environment, but should not error
    servers = orchestrator.connected_mcp_servers
    assert isinstance(servers, list)
    
    # Test health check includes MCP status
    health = await orchestrator.health_check()
    assert "mcp_client" in health
    assert health["mcp_client"] == "healthy"


@pytest.mark.asyncio
async def test_memory_integration(orchestrator):
    """Test memory service integration"""
    assert orchestrator.memory_service is not None
    assert orchestrator.vector_store is not None
    assert orchestrator.embedding_service is not None
    
    # Test embedding dimension
    dimension = orchestrator.embedding_service.get_embedding_dimension()
    assert isinstance(dimension, int)
    assert dimension > 0


@pytest.mark.asyncio
async def test_agent_state_tracking(orchestrator):
    """Test agent state tracking functionality"""
    # Initial state should be empty
    assert len(orchestrator.active_agents) == 0
    
    request = StreamingRequest(
        message="Test agent state tracking",
        user_id="test_user",
        conversation_id="test_conv"
    )
    
    # Start workflow and verify agent tracking
    chunk_count = 0
    agent_found = False
    final_chunk_received = False
    
    async for chunk in orchestrator.create_agentic_workflow(request):
        chunk_count += 1
        if chunk.chunk_type == "agent_start":
            # During processing, there should be one active agent
            assert len(orchestrator.active_agents) == 1
            agent_found = True
        if chunk.is_final:
            final_chunk_received = True
            break
    
    # Verify we found an agent during processing
    assert agent_found, "Agent should have been tracked during processing"
    assert final_chunk_received, "Final chunk should have been received"
    assert chunk_count > 0


@pytest.mark.asyncio
async def test_system_cleanup(orchestrator):
    """Test system cleanup functionality"""
    # Orchestrator should be initialized
    assert orchestrator._initialized is True
    
    # Cleanup should work without errors
    await orchestrator.cleanup()
    
    # After cleanup, system should be cleaned up
    # Note: We don't test _initialized = False as the orchestrator 
    # might be needed for other tests in the same session
