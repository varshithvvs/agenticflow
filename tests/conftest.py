"""
Test configuration and fixtures for enhanced system
"""

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
import tempfile
import shutil

from config.settings import Settings
from services.workflow_orchestrator import WorkflowOrchestrator
from storage.vector_store import VectorStore


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def cleanup_global_services():
    """Clean up global enhanced services between tests"""
    # Clear global embedding service
    import services.bedrock_embedding
    if hasattr(services.bedrock_embedding, '_service_instance') and services.bedrock_embedding._service_instance:
        await services.bedrock_embedding._service_instance.cleanup()
        services.bedrock_embedding._service_instance = None
    
    # Clear global chat service  
    import services.bedrock_chat
    if hasattr(services.bedrock_chat, '_chat_service_instance') and services.bedrock_chat._chat_service_instance:
        await services.bedrock_chat._chat_service_instance.cleanup()
        services.bedrock_chat._chat_service_instance = None
    
    # Clear global MCP client
    import services.mcp_client
    if hasattr(services.mcp_client, '_mcp_client') and services.mcp_client._mcp_client:
        await services.mcp_client._mcp_client.cleanup()
        services.mcp_client._mcp_client = None
    
    yield
    
    # Cleanup after test
    if hasattr(services.bedrock_embedding, '_service_instance') and services.bedrock_embedding._service_instance:
        await services.bedrock_embedding._service_instance.cleanup()
        services.bedrock_embedding._service_instance = None
    
    if hasattr(services.bedrock_chat, '_chat_service_instance') and services.bedrock_chat._chat_service_instance:
        await services.bedrock_chat._chat_service_instance.cleanup()
        services.bedrock_chat._chat_service_instance = None
        
    if hasattr(services.mcp_client, '_mcp_client') and services.mcp_client._mcp_client:
        await services.mcp_client._mcp_client.cleanup()
        services.mcp_client._mcp_client = None


@pytest.fixture
async def temp_dir():
    """Create a temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
async def test_settings(temp_dir) -> Settings:
    """Create test settings"""
    settings = Settings()
    settings.faiss_index_path = f"{temp_dir}/test_faiss_index"
    settings.debug = True
    settings.log_level = "DEBUG"
    return settings


@pytest.fixture
async def vector_store(test_settings) -> AsyncGenerator[VectorStore, None]:
    """Create test vector store"""
    store = VectorStore(
        index_path=test_settings.faiss_index_path,
        embedding_model=test_settings.embedding.model_name,
        dimension=test_settings.vector_dimension
    )
    await store.initialize()
    yield store
    await store.cleanup()


@pytest.fixture
async def orchestrator(test_settings) -> AsyncGenerator[WorkflowOrchestrator, None]:
    """Create test enhanced orchestrator"""
    orch = WorkflowOrchestrator(test_settings)
    await orch.initialize()
    yield orch
    await orch.cleanup()
