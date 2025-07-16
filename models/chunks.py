from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ChunkType(str, Enum):
    TEXT = "text"
    CODE = "code"
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"

class DataChunk(BaseModel):
    id: str = Field(..., description="Unique identifier for the chunk")
    content: str = Field(..., description="The actual chunk content")
    chunk_type: ChunkType = Field(default=ChunkType.TEXT)
    size: int = Field(..., description="Size of the chunk in bytes")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    source_id: Optional[str] = Field(None, description="ID of the source document")
    chunk_index: int = Field(..., description="Index of this chunk in the source")
    
class ChunkRequest(BaseModel):
    content: str = Field(..., description="Content to be chunked")
    chunk_size: int = Field(default=1000, ge=100, le=10000)
    overlap: int = Field(default=100, ge=0, le=500)
    chunk_type: ChunkType = Field(default=ChunkType.TEXT)
    source_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChunkResponse(BaseModel):
    chunks: List[DataChunk]
    total_chunks: int
    total_size: int
    processing_time_ms: float

class ChunkQuery(BaseModel):
    query: str = Field(..., description="Search query")
    chunk_types: List[ChunkType] = Field(default_factory=lambda: [ChunkType.TEXT])
    limit: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    source_id: Optional[str] = None