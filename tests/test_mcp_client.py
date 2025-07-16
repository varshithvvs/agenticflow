"""Test suite for the MCP Client Service"""

import pytest
import pytest_asyncio
from services.mcp_client import EnhancedMCPClient


@pytest_asyncio.fixture
async def mcp_client():
    """Create an MCP client instance for testing"""
    client = EnhancedMCPClient()
    await client.initialize()
    yield client
    await client.cleanup()


@pytest.mark.asyncio
async def test_get_available_tools(mcp_client):
    """Test getting available MCP tools"""
    tools = await mcp_client.get_available_tools()
    
    assert isinstance(tools, dict)
    # Note: May be empty if no MCP servers are configured for testing


@pytest.mark.asyncio
async def test_get_server_status(mcp_client):
    """Test getting MCP server status"""
    status = await mcp_client.get_server_status()
    
    assert isinstance(status, dict)


@pytest.mark.asyncio
async def test_reload_configuration():
    """Test reloading MCP configuration"""
    client = EnhancedMCPClient()
    await client.initialize()
    
    try:
        # This should complete without error
        await client.reload_config()
        assert True  # If we get here, the reload worked
    finally:
        await client.cleanup()