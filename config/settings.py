"""
Configuration management for PydanticAI Workflow System
"""

from functools import lru_cache
from typing import Optional, Literal
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    """Database configuration"""
    postgres_url: str = Field(default="postgresql://postgres:password@localhost:5432/pydantic_ai")
    redis_url: str = Field(default="redis://localhost:6379")
    max_connections: int = Field(default=10)
    connection_timeout: int = Field(default=30)


class AWSSettings(BaseModel):
    """AWS Bedrock configuration"""
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None
    region: str = Field(default="us-east-1")
    bedrock_model_id: str = Field(default="amazon.titan-embed-text-v1")
    bedrock_chat_model: str = Field(default="anthropic.claude-3-haiku-20240307-v1:0")
    bedrock_embedding_dimension: int = Field(default=1536)


class MCPSettings(BaseModel):
    """MCP Server configuration"""
    config_file: str = Field(default="./config/mcp_servers.yaml")
    auto_reload: bool = Field(default=True)
    connection_pool_size: int = Field(default=10)


class EmbeddingSettings(BaseModel):
    """Embedding model configuration"""
    # Bedrock settings
    bedrock_model: str = Field(default="amazon.titan-embed-text-v1")
    
    # Fallback settings  
    fallback_model: str = Field(default="all-MiniLM-L6-v2")
    fallback_dimension: int = Field(default=384)
    
    # Legacy settings for compatibility
    model_name: Literal["bedrock", "sentence-transformers", "openai"] = Field(default="bedrock")
    dimension: int = Field(default=1536)
    cache_embeddings: bool = Field(default=True)
    openai_api_key: Optional[str] = None


class ChunkingSettings(BaseModel):
    """Chunking configuration"""
    default_chunk_size: int = Field(default=1000)
    default_overlap: int = Field(default=100)
    max_chunk_size: int = Field(default=10000)
    min_chunk_size: int = Field(default=100)


class MemorySettings(BaseModel):
    """Memory configuration"""
    max_short_term_chunks: int = Field(default=50)
    max_context_tokens: int = Field(default=2000)
    consolidation_interval: int = Field(default=3600)  # seconds
    importance_threshold: float = Field(default=0.5)


class Settings(BaseSettings):
    """Main application settings"""
    
    # Application settings
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    aws: AWSSettings = Field(default_factory=AWSSettings)
    mcp: MCPSettings = Field(default_factory=MCPSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    chunking: ChunkingSettings = Field(default_factory=ChunkingSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    
    # Vector store settings
    faiss_index_path: str = Field(default="./data/faiss_index")
    vector_dimension: int = Field(default=1536)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )
@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
