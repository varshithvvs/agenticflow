"""
Test suite for the Vector Store
"""

import pytest
import pytest_asyncio
from storage.vector_store import VectorStore
from models.chunks import DataChunk
from models.memory import MemoryChunk, MemoryType

@pytest_asyncio.fixture
async def vector_store():
    """Create a vector store instance for testing"""
    import tempfile
    import os
    
    # Create a temporary directory for test data
    test_dir = tempfile.mkdtemp()
    index_path = os.path.join(test_dir, "test_vector_index")
    
    # Use fallback model for testing to avoid AWS dependency
    store = VectorStore(
        index_path=index_path,
        embedding_model="sentence-transformers"  # Will use fallback
    )
    await store.initialize()
    yield store
    await store.cleanup()
    
    # Clean up test directory
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)

@pytest.mark.asyncio
async def test_add_vectors(vector_store):
    """Test adding vectors to the store"""
    texts = ["Hello world", "Python programming", "Machine learning"]
    
    for i, text in enumerate(texts):
        chunk = DataChunk(
            id=f"test_chunk_{i}",
            content=text,
            chunk_type="text",
            size=len(text),
            source_id="test_source",
            chunk_index=i
        )
        await vector_store.add_chunk(chunk)
    
    # Verify chunks were added
    stats = await vector_store.get_stats()
    assert stats["total_vectors"] == 3

@pytest.mark.asyncio
async def test_search_vectors(vector_store):
    """Test vector similarity search"""
    # Add some test chunks
    texts = [
        "Python is a programming language",
        "JavaScript is used for web development", 
        "Machine learning with Python",
        "Web development with React"
    ]
    
    for i, text in enumerate(texts):
        chunk = DataChunk(
            id=f"search_test_{i}",
            content=text,
            chunk_type="text",
            size=len(text),
            source_id="test_source",
            chunk_index=i
        )
        await vector_store.add_chunk(chunk)
    
    # Search for Python-related content
    query_embedding = await vector_store.generate_embedding("Python programming")
    results = await vector_store.search_similar(query_embedding, limit=2)
    
    assert len(results) <= 2
    assert all(hasattr(result, 'content') for result in results)

@pytest.mark.asyncio
async def test_get_vector_count(vector_store):
    """Test getting vector count"""
    initial_stats = await vector_store.get_stats()
    initial_count = initial_stats["total_vectors"]
    
    # Add a chunk
    chunk = DataChunk(
        id="count_test",
        content="Test vector for counting",
        chunk_type="text",
        size=25,
        source_id="test_source",
        chunk_index=0
    )
    await vector_store.add_chunk(chunk)
    
    new_stats = await vector_store.get_stats()
    new_count = new_stats["total_vectors"]
    assert new_count == initial_count + 1

@pytest.mark.asyncio
async def test_delete_vector(vector_store):
    """Test deleting vectors"""
    # Add a chunk
    chunk = DataChunk(
        id="delete_test",
        content="Vector to be deleted",
        chunk_type="text",
        size=20,
        source_id="test_source",
        chunk_index=0
    )
    await vector_store.add_chunk(chunk)
    
    # Delete the chunk
    result = await vector_store.delete_chunk("delete_test")
    assert result is True

@pytest.mark.asyncio
async def test_embedding_dimensions(vector_store):
    """Test that embeddings have consistent dimensions"""
    texts = ["Short text", "This is a longer text with more words"]
    
    embeddings = []
    for text in texts:
        embedding = await vector_store.generate_embedding(text)
        embeddings.append(embedding)
    
    assert len(embeddings) == 2
    assert len(embeddings[0]) == len(embeddings[1])
    
    # Should be using sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
    expected_dim = 384
    assert len(embeddings[0]) == expected_dim

@pytest.mark.asyncio
async def test_memory_chunk_operations(vector_store):
    """Test adding and searching memory chunks"""
    memory_chunk = MemoryChunk(
        id="memory_test",
        content="This is a test memory",
        memory_type=MemoryType.SHORT_TERM,
        user_id="test_user",
        conversation_id="test_conv",
        importance_score=0.8
    )
    
    await vector_store.add_memory_chunk(memory_chunk)
    
    # Search for the memory chunk
    query_embedding = await vector_store.generate_embedding("test memory")
    results = await vector_store.search_similar(
        query_embedding, 
        limit=5, 
        user_id="test_user"
    )
    
    assert len(results) > 0
    assert any(result.id == "memory_test" for result in results)
