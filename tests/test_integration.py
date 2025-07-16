"""
Integration tests for the Workflow Orchestrator
"""

import pytest
import pytest_asyncio
from services.workflow_orchestrator import WorkflowOrchestrator
from models.mcp_models import StreamingRequest
from models.chunks import ChunkRequest, ChunkType
from models.memory import MemoryQuery, MemoryType
from config.settings import get_settings

@pytest_asyncio.fixture
async def orchestrator():
    """Create a workflow orchestrator instance for testing"""
    settings = get_settings()
    orchestrator = WorkflowOrchestrator(settings)
    await orchestrator.initialize()
    yield orchestrator
    await orchestrator.cleanup()

@pytest.mark.asyncio
async def test_orchestrator_initialization(orchestrator):
    """Test that the orchestrator initializes all components"""
    assert orchestrator.chunking_service is not None
    assert orchestrator.memory_service is not None
    assert orchestrator.vector_store is not None
    assert orchestrator.mcp_client is not None
    # chat_service may be None if Bedrock is not configured
    assert hasattr(orchestrator, 'chat_service')

@pytest.mark.asyncio
async def test_health_check(orchestrator):
    """Test system health check"""
    health = await orchestrator.health_check()
    
    assert "orchestrator" in health
    assert "vector_store" in health
    assert "memory_service" in health
    assert "chunking_service" in health
    assert "mcp_client" in health
    assert "chat_service" in health
    
    # All required components should be healthy
    required_components = ["orchestrator", "vector_store", "memory_service", "chunking_service"]
    for component in required_components:
        if isinstance(health[component], str):
            assert health[component] == "healthy"

@pytest.mark.asyncio
async def test_stream_conversation(orchestrator):
    """Test streaming conversation functionality"""
    request = StreamingRequest(
        user_id="test_user",
        conversation_id="test_conv",
        message="Hello, this is a test message",
        use_memory=True,
        use_mcp=False,
        stream_chunks=True
    )
    
    chunks = []
    async for chunk in orchestrator.stream_conversation(request):
        chunks.append(chunk)
        if chunk.is_final:
            break
    
    assert len(chunks) > 0
    assert any(chunk.is_final for chunk in chunks)

@pytest.mark.asyncio
async def test_conversation_stats(orchestrator):
    """Test conversation statistics"""
    user_id = "test_user"
    
    # Add some memory to create statistics
    await orchestrator.memory_service.add_memory(
        user_id=user_id,
        conversation_id="test_conv",
        content="Test memory for stats",
        memory_type=MemoryType.SHORT_TERM
    )
    
    stats = await orchestrator.get_conversation_stats(user_id)
    
    assert "active_conversations" in stats
    assert "total_messages" in stats
    assert "memory_stats" in stats

@pytest.mark.asyncio
async def test_end_to_end_workflow(orchestrator):
    """Test complete end-to-end workflow"""
    user_id = "e2e_test_user"
    conversation_id = "e2e_test_conv"
    
    # 1. Create chunks
    chunk_request = ChunkRequest(
        content="This is a test document for end-to-end testing of the PydanticAI workflow system.",
        chunk_size=100,  # Minimum chunk size is 100
        overlap=10,
        chunk_type=ChunkType.TEXT,
        source_id="e2e_test_doc"
    )
    
    chunk_response = await orchestrator.chunking_service.create_chunks(chunk_request)
    assert chunk_response.total_chunks > 0
    
    # 2. Add memory
    memory_id = await orchestrator.memory_service.add_memory(
        user_id=user_id,
        conversation_id=conversation_id,
        content="User asked about workflow testing",
        memory_type=MemoryType.SHORT_TERM
    )
    assert memory_id is not None
    
    # 3. Search memory
    query = MemoryQuery(
        query="workflow testing",
        user_id=user_id,
        conversation_id=conversation_id,
        limit=5
    )
    
    search_response = await orchestrator.memory_service.search_memory(query)
    assert len(search_response.chunks) > 0
    
    # 4. Get MCP tools
    tools = await orchestrator.mcp_client.get_available_tools()
    assert len(tools) > 0
    
    # 5. Stream conversation with memory context
    stream_request = StreamingRequest(
        user_id=user_id,
        conversation_id=conversation_id,
        message="Tell me about the workflow system",
        use_memory=True,
        use_mcp=True,
        stream_chunks=True
    )
    
    chunks = []
    async for chunk in orchestrator.stream_conversation(stream_request):
        chunks.append(chunk)
        if chunk.is_final:
            break
    
    assert len(chunks) > 0
    
    # 6. Check final health
    health = await orchestrator.health_check()
    # Check that required components are healthy (chat service may be unavailable without AWS creds)
    required_healthy = ["orchestrator", "vector_store", "memory_service", "chunking_service"]
    for component in required_healthy:
        if component in health and isinstance(health[component], str):
            assert health[component] == "healthy", f"{component} should be healthy but is {health[component]}"
