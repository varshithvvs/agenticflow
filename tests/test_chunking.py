"""
Test the chunking service
"""

import pytest
from services.chunking import ChunkingService
from models.chunks import ChunkRequest, ChunkType


@pytest.mark.asyncio
async def test_text_chunking():
    """Test basic text chunking functionality"""
    service = ChunkingService()
    
    # Create a test request
    content = "This is a test document. " * 100  # Create long text
    request = ChunkRequest(
        content=content,
        chunk_size=200,
        overlap=50,
        chunk_type=ChunkType.TEXT,
        source_id="test_doc_1"
    )
    
    # Create chunks
    response = await service.create_chunks(request)
    
    # Verify results
    assert len(response.chunks) > 1
    assert response.total_chunks == len(response.chunks)
    assert response.total_size > 0
    assert response.processing_time_ms > 0
    
    # Verify chunk properties
    for i, chunk in enumerate(response.chunks):
        assert chunk.id is not None
        assert chunk.content != ""
        assert chunk.chunk_type == ChunkType.TEXT
        assert chunk.source_id == "test_doc_1"
        assert chunk.chunk_index == i


@pytest.mark.asyncio
async def test_code_chunking():
    """Test code chunking functionality"""
    service = ChunkingService()
    
    # Create test code content
    code_content = '''
def function1():
    return "test1"

def function2():
    return "test2"

class TestClass:
    def method1(self):
        pass
    '''
    
    request = ChunkRequest(
        content=code_content,
        chunk_size=500,
        chunk_type=ChunkType.CODE,
        source_id="test_code_1"
    )
    
    # Create chunks
    response = await service.create_chunks(request)
    
    # Verify results
    assert len(response.chunks) > 0
    assert response.total_chunks == len(response.chunks)
    
    # Check that functions and classes are identified
    chunk_contents = [chunk.content for chunk in response.chunks]
    assert any("function1" in content for content in chunk_contents)
    assert any("TestClass" in content for content in chunk_contents)


@pytest.mark.asyncio
async def test_get_chunk():
    """Test retrieving a specific chunk"""
    service = ChunkingService()
    
    request = ChunkRequest(
        content="Test content for retrieval",
        chunk_size=100,
        chunk_type=ChunkType.TEXT,
        source_id="test_retrieval"
    )
    
    response = await service.create_chunks(request)
    chunk_id = response.chunks[0].id
    
    # Retrieve the chunk
    retrieved_chunk = await service.get_chunk(chunk_id)
    
    assert retrieved_chunk.id == chunk_id
    assert retrieved_chunk.content == response.chunks[0].content


@pytest.mark.asyncio
async def test_get_chunks_by_source():
    """Test retrieving chunks by source ID"""
    service = ChunkingService()
    
    request = ChunkRequest(
        content="Test content for source retrieval " * 50,
        chunk_size=100,
        chunk_type=ChunkType.TEXT,
        source_id="test_source_123"
    )
    
    response = await service.create_chunks(request)
    
    # Retrieve chunks by source
    source_chunks = await service.get_chunks_by_source("test_source_123")
    
    assert len(source_chunks) == len(response.chunks)
    assert all(chunk.source_id == "test_source_123" for chunk in source_chunks)
