from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MCPToolType(str, Enum):
    FUNCTION = "function"
    RESOURCE = "resource"
    PROMPT = "prompt"

class MCPRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the MCP tool to call")
    tool_type: MCPToolType = Field(default=MCPToolType.FUNCTION)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    user_id: str = Field(..., description="User making the request")
    conversation_id: Optional[str] = None
    timeout: int = Field(default=30, ge=1, le=300)

class MCPResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float
    tool_name: str
    timestamp: datetime = Field(default_factory=datetime.now)

class MCPTool(BaseModel):
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    tool_type: MCPToolType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    available: bool = Field(default=True)

class MCPServerConfig(BaseModel):
    server_url: str = Field(..., description="MCP server URL")
    api_key: Optional[str] = None
    timeout: int = Field(default=30)
    max_retries: int = Field(default=3)
    available_tools: List[MCPTool] = Field(default_factory=list)

class StreamingRequest(BaseModel):
    user_id: str
    conversation_id: str
    message: str
    use_memory: bool = Field(default=True)
    use_mcp: bool = Field(default=True)
    stream_chunks: bool = Field(default=True)
    max_tokens: int = Field(default=1000, ge=1, le=4000)
    max_chunk_size: Optional[int] = Field(default=1000, ge=100, le=10000)
    overlap_size: Optional[int] = Field(default=100, ge=0, le=500)

class StreamingChunk(BaseModel):
    chunk_id: str
    conversation_id: str
    content: str
    chunk_type: str = Field(default="content")
    is_final: bool = Field(default=False)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)