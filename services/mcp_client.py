"""
Enhanced MCP client with support for multiple servers and dynamic configuration
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Set
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config.mcp_config import get_mcp_config_manager, MCPServerConfig

logger = logging.getLogger(__name__)


class MCPServerConnection:
    """Manages connection to a single MCP server"""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.session: Optional[ClientSession] = None
        self.is_connected = False
        self.available_tools: Set[str] = set()
        self._connection_lock = asyncio.Lock()
    
    async def connect(self) -> bool:
        """Connect to the MCP server"""
        async with self._connection_lock:
            if self.is_connected:
                return True
            
            try:
                server_params = StdioServerParameters(
                    command=self.config.command,
                    args=self.config.args,
                    env=self.config.env
                )
                
                # Connect with timeout
                stdio_transport = await asyncio.wait_for(
                    stdio_client(server_params),
                    timeout=self.config.timeout
                )
                
                read, write = stdio_transport
                self.session = ClientSession(read, write)
                
                # Initialize the session
                await self.session.initialize()
                
                # Get available tools
                await self._update_available_tools()
                
                self.is_connected = True
                logger.info(f"Connected to MCP server: {self.config.name}")
                logger.debug(f"Available tools: {list(self.available_tools)}")
                return True
                
            except asyncio.TimeoutError:
                logger.error(f"Timeout connecting to MCP server: {self.config.name}")
                return False
            except Exception as e:
                logger.error(f"Failed to connect to MCP server {self.config.name}: {e}")
                return False
    
    async def _update_available_tools(self):
        """Update the list of available tools from the server"""
        if not self.session:
            return
        
        try:
            tools_response = await self.session.list_tools()
            self.available_tools = {tool.name for tool in tools_response.tools}
        except Exception as e:
            logger.warning(f"Failed to get tools from {self.config.name}: {e}")
            self.available_tools = set()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on this server"""
        if not self.is_connected or not self.session:
            raise RuntimeError(f"Server {self.config.name} is not connected")
        
        if tool_name not in self.available_tools:
            raise ValueError(f"Tool {tool_name} not available on server {self.config.name}")
        
        try:
            result = await self.session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else {}
        except Exception as e:
            logger.error(f"Tool call failed on {self.config.name}: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from the server"""
        async with self._connection_lock:
            if self.session:
                try:
                    await self.session.close()
                except Exception as e:
                    logger.warning(f"Error closing session for {self.config.name}: {e}")
                finally:
                    self.session = None
                    self.is_connected = False
                    self.available_tools.clear()
                    logger.info(f"Disconnected from MCP server: {self.config.name}")


class EnhancedMCPClient:
    """Enhanced MCP client supporting multiple servers"""
    
    def __init__(self):
        self.config_manager = get_mcp_config_manager()
        self.connections: Dict[str, MCPServerConnection] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize connections to all enabled servers"""
        if self._initialized:
            return
        
        enabled_servers = self.config_manager.get_enabled_servers()
        logger.info(f"Initializing {len(enabled_servers)} MCP servers")
        
        # Create connections for all enabled servers
        for server_config in enabled_servers:
            connection = MCPServerConnection(server_config)
            self.connections[server_config.name] = connection
        
        # Connect to all servers concurrently
        connection_tasks = []
        for name, connection in self.connections.items():
            task = asyncio.create_task(self._connect_with_retry(connection))
            connection_tasks.append((name, task))
        
        # Wait for all connections to complete
        successful_connections = 0
        for name, task in connection_tasks:
            try:
                success = await task
                if success:
                    successful_connections += 1
                else:
                    logger.warning(f"Failed to connect to MCP server: {name}")
            except Exception as e:
                logger.error(f"Error connecting to MCP server {name}: {e}")
        
        logger.info(f"Successfully connected to {successful_connections}/{len(enabled_servers)} MCP servers")
        self._initialized = True
    
    async def _connect_with_retry(self, connection: MCPServerConnection) -> bool:
        """Connect to a server with retry logic"""
        for attempt in range(connection.config.retry_attempts):
            try:
                success = await connection.connect()
                if success:
                    return True
                
                if attempt < connection.config.retry_attempts - 1:
                    logger.info(f"Retrying connection to {connection.config.name} in {connection.config.retry_delay}s")
                    await asyncio.sleep(connection.config.retry_delay)
                    
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed for {connection.config.name}: {e}")
                if attempt < connection.config.retry_attempts - 1:
                    await asyncio.sleep(connection.config.retry_delay)
        
        return False
    
    async def get_available_tools(self) -> Dict[str, List[str]]:
        """Get available tools from all connected servers"""
        await self.initialize()
        
        tools_by_server = {}
        for name, connection in self.connections.items():
            if connection.is_connected:
                tools_by_server[name] = list(connection.available_tools)
        
        return tools_by_server
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], preferred_server: Optional[str] = None) -> Dict[str, Any]:
        """Call a tool, optionally specifying a preferred server"""
        await self.initialize()
        
        # If preferred server is specified and available, use it
        if preferred_server and preferred_server in self.connections:
            connection = self.connections[preferred_server]
            if connection.is_connected and tool_name in connection.available_tools:
                try:
                    return await connection.call_tool(tool_name, arguments)
                except Exception as e:
                    logger.warning(f"Tool call failed on preferred server {preferred_server}: {e}")
        
        # Find any server that has this tool
        for name, connection in self.connections.items():
            if connection.is_connected and tool_name in connection.available_tools:
                try:
                    result = await connection.call_tool(tool_name, arguments)
                    logger.debug(f"Tool {tool_name} executed on server {name}")
                    return result
                except Exception as e:
                    logger.warning(f"Tool call failed on server {name}: {e}")
                    continue
        
        raise ValueError(f"Tool {tool_name} not available on any connected server")
    
    async def add_server(self, server_config: MCPServerConfig) -> bool:
        """Add a new server dynamically"""
        if self.config_manager.add_server(server_config):
            # Create and connect to the new server
            connection = MCPServerConnection(server_config)
            success = await self._connect_with_retry(connection)
            
            if success:
                self.connections[server_config.name] = connection
                logger.info(f"Dynamically added MCP server: {server_config.name}")
                return True
            else:
                # Remove from config if connection failed
                self.config_manager.remove_server(server_config.name)
                logger.error(f"Failed to connect to new server {server_config.name}, removed from config")
                return False
        
        return False
    
    async def remove_server(self, name: str) -> bool:
        """Remove a server dynamically"""
        # Disconnect first
        if name in self.connections:
            await self.connections[name].disconnect()
            del self.connections[name]
        
        # Remove from config
        success = self.config_manager.remove_server(name)
        if success:
            logger.info(f"Dynamically removed MCP server: {name}")
        
        return success
    
    async def reload_config(self):
        """Reload configuration and reconnect to servers"""
        logger.info("Reloading MCP configuration")
        
        # Disconnect all current connections
        await self.disconnect_all()
        
        # Reload config
        self.config_manager.reload_config()
        
        # Reinitialize
        self._initialized = False
        await self.initialize()
    
    async def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all servers"""
        status = {}
        
        for name, connection in self.connections.items():
            status[name] = {
                "connected": connection.is_connected,
                "tools_count": len(connection.available_tools),
                "tools": list(connection.available_tools),
                "config": connection.config.to_dict()
            }
        
        # Add configured but not connected servers
        for name in self.config_manager.list_servers():
            if name not in status:
                server_config = self.config_manager.get_server(name)
                status[name] = {
                    "connected": False,
                    "tools_count": 0,
                    "tools": [],
                    "config": server_config.to_dict() if server_config else {}
                }
        
        return status
    
    async def disconnect_all(self):
        """Disconnect from all servers"""
        disconnect_tasks = []
        for connection in self.connections.values():
            task = asyncio.create_task(connection.disconnect())
            disconnect_tasks.append(task)
        
        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        
        self.connections.clear()
        logger.info("Disconnected from all MCP servers")
    
    async def cleanup(self):
        """Clean up all connections"""
        await self.disconnect_all()
        self._initialized = False


# Global client instance
_mcp_client = None


async def get_mcp_client() -> EnhancedMCPClient:
    """Get or create the global MCP client instance"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = EnhancedMCPClient()
    return _mcp_client


async def cleanup_mcp_client():
    """Clean up the global MCP client"""
    global _mcp_client
    if _mcp_client:
        await _mcp_client.cleanup()
        _mcp_client = None
