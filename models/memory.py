from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MemoryType(str, Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"

class MemoryChunk(BaseModel):
    id: str = Field(..., description="Unique identifier for the memory chunk")
    content: str = Field(..., description="The actual memory content")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding of the content")
    timestamp: datetime = Field(default_factory=datetime.now)
    memory_type: MemoryType = Field(default=MemoryType.SHORT_TERM)
    user_id: str = Field(..., description="User identifier")
    conversation_id: str = Field(..., description="Conversation identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    importance_score: float = Field(default=1.0, ge=0.0, le=1.0)

class ConversationMemory(BaseModel):
    user_id: str
    conversation_id: str
    short_term_memory: List[MemoryChunk] = Field(default_factory=list)
    long_term_memory: List[str] = Field(default_factory=list)  # References to vector store
    context_window: int = Field(default=4096)
    max_short_term_chunks: int = Field(default=50)

class MemoryQuery(BaseModel):
    query: str = Field(..., description="Query to search memory")
    user_id: str
    conversation_id: Optional[str] = None
    memory_types: List[MemoryType] = Field(default_factory=lambda: [MemoryType.SHORT_TERM, MemoryType.LONG_TERM])
    limit: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

class MemoryResponse(BaseModel):
    chunks: List[MemoryChunk]
    total_found: int
    query_time_ms: float