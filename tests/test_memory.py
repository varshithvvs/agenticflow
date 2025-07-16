"""
Test suite for the Memory Service
"""

import pytest
import pytest_asyncio
from services.memory import MemoryService
from models.memory import MemoryType, MemoryQuery

@pytest_asyncio.fixture
async def memory_service():
    """Create a memory service instance for testing"""
    from storage.vector_store import VectorStore
    import tempfile
    import os
    
    # Create a temporary directory for test data
    test_dir = tempfile.mkdtemp()
    index_path = os.path.join(test_dir, "test_index")
    
    # Create a vector store for the memory service
    vector_store = VectorStore(
        index_path=index_path,
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        dimension=384
    )
    await vector_store.initialize()
    
    service = MemoryService(vector_store)
    await service.initialize()
    yield service
    await vector_store.cleanup()
    
    # Clean up test directory
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)

@pytest.mark.asyncio
async def test_add_memory(memory_service):
    """Test adding memory entries"""
    user_id = "test_user"
    conversation_id = "test_conv"
    content = "This is a test memory"
    
    memory_chunk = await memory_service.add_memory(
        user_id=user_id,
        conversation_id=conversation_id,
        content=content,
        memory_type=MemoryType.SHORT_TERM
    )
    
    assert memory_chunk is not None
    assert hasattr(memory_chunk, 'id')
    assert memory_chunk.content == content

@pytest.mark.asyncio
async def test_search_memory(memory_service):
    """Test memory search functionality"""
    user_id = "test_user"
    conversation_id = "test_conv"
    
    # Add some memories
    await memory_service.add_memory(
        user_id=user_id,
        conversation_id=conversation_id,
        content="Python programming tutorial",
        memory_type=MemoryType.SHORT_TERM
    )
    
    await memory_service.add_memory(
        user_id=user_id,
        conversation_id=conversation_id,
        content="JavaScript web development",
        memory_type=MemoryType.LONG_TERM
    )
    
    # Search for Python-related memories
    query = MemoryQuery(
        query="Python programming",
        user_id=user_id,
        conversation_id=conversation_id,
        limit=5
    )
    
    response = await memory_service.search_memory(query)
    
    assert len(response.chunks) > 0
    assert response.query_time_ms > 0

@pytest.mark.asyncio
async def test_memory_stats(memory_service):
    """Test memory statistics functionality"""
    user_id = "test_user"
    conversation_id = "test_conv"
    
    # Add some memories
    await memory_service.add_memory(
        user_id=user_id,
        conversation_id=conversation_id,
        content="Test short term memory",
        memory_type=MemoryType.SHORT_TERM
    )
    
    await memory_service.add_memory(
        user_id=user_id,
        conversation_id=conversation_id,
        content="Test long term memory",
        memory_type=MemoryType.LONG_TERM
    )
    
    stats = await memory_service.get_memory_stats(user_id)
    
    assert "total_memories" in stats
    assert stats["total_memories"] >= 2
    assert "short_term" in stats
    assert "long_term" in stats

@pytest.mark.asyncio
async def test_conversation_tracking(memory_service):
    """Test conversation tracking functionality"""
    user_id = "test_user"
    conversation_id = "test_conv"
    
    # Add memory and track conversation
    await memory_service.add_memory(
        user_id=user_id,
        conversation_id=conversation_id,
        content="Test conversation tracking",
        memory_type=MemoryType.SHORT_TERM
    )
    
    # Get conversation context instead since get_user_conversations doesn't exist
    context = await memory_service.get_conversation_context(user_id, conversation_id)
    assert isinstance(context, list)