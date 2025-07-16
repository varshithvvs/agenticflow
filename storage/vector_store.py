"""
Vector store implementation using FAISS for similarity search with Bedrock support
"""

import os
import pickle
import asyncio
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import faiss

from models.chunks import DataChunk
from models.memory import MemoryChunk
from services.bedrock_embedding import get_embedding_service
from config.settings import get_settings
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector storage and similarity search using FAISS with Bedrock embeddings"""
    
    def __init__(self, 
                 index_path: str = "./data/faiss_index",
                 embedding_model: str = "bedrock",
                 dimension: Optional[int] = None):
        self.index_path = index_path
        self.embedding_model_name = embedding_model
        self.settings = get_settings()
        
        # Dimension will be determined by embedding service
        self.dimension = dimension or self.settings.vector_dimension
        
        # Initialize components
        self.embedding_service = None
        self.index = None
        self.chunk_metadata: Dict[int, Dict[str, Any]] = {}
        self.id_to_index: Dict[str, int] = {}
        self.index_to_id: Dict[int, str] = {}
        self.next_index = 0
        
        # Thread pool for CPU-intensive operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def initialize(self):
        """Initialize the vector store"""
        try:
            # Initialize embedding service
            self.embedding_service = await get_embedding_service()
            
            # Update dimension based on actual embedding service
            self.dimension = self.embedding_service.get_embedding_dimension()
            logger.info(f"Using embedding dimension: {self.dimension}")
            
            # Get model info for logging
            model_info = self.embedding_service.get_model_info()
            logger.info(f"Embedding service info: {model_info}")
            
            # Create index directory
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            
            # Load or create FAISS index
            await self._load_or_create_index()
            
            logger.info(f"Vector store initialized with {self.index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    async def _load_or_create_index(self):
        """Load existing index or create new one"""
        index_file = f"{self.index_path}.index"
        metadata_file = f"{self.index_path}.metadata"
        
        if os.path.exists(index_file) and os.path.exists(metadata_file):
            # Load existing index
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._load_index_files,
                index_file,
                metadata_file
            )
            
            # Check if loaded index dimension matches current embedding service
            if self.index.d != self.dimension:
                logger.warning(f"Existing index dimension ({self.index.d}) doesn't match current embedding dimension ({self.dimension}). Creating new index.")
                self._create_new_index()
        else:
            # Create new index
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        self.chunk_metadata = {}
        self.id_to_index = {}
        self.index_to_id = {}
        self.next_index = 0
    
    def _load_index_files(self, index_file: str, metadata_file: str):
        """Load index and metadata files"""
        self.index = faiss.read_index(index_file)
        
        with open(metadata_file, 'rb') as f:
            data = pickle.load(f)
            self.chunk_metadata = data['metadata']
            self.id_to_index = data['id_to_index']
            self.index_to_id = data['index_to_id']
            self.next_index = data['next_index']
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Bedrock or fallback"""
        try:
            if not self.embedding_service:
                raise RuntimeError("Embedding service not initialized")
                
            embedding = await self.embedding_service.embed_text(text)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def add_chunk(self, chunk: DataChunk):
        """Add a data chunk to the vector store"""
        try:
            if chunk.embedding is None:
                chunk.embedding = await self.generate_embedding(chunk.content)
            
            # Add to FAISS index
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._add_to_index,
                chunk
            )
            
            logger.debug(f"Added chunk {chunk.id} to vector store")
            
        except Exception as e:
            logger.error(f"Error adding chunk to vector store: {e}")
            raise
    
    def _add_to_index(self, chunk: DataChunk):
        """Add chunk to FAISS index (thread-safe)"""
        embedding = np.array(chunk.embedding, dtype=np.float32).reshape(1, -1)
        
        # Add to index
        self.index.add(embedding)
        
        # Update metadata
        index_id = self.next_index
        self.chunk_metadata[index_id] = {
            'id': chunk.id,
            'content': chunk.content,
            'chunk_type': chunk.chunk_type,
            'source_id': chunk.source_id,
            'metadata': chunk.metadata,
            'created_at': chunk.created_at.isoformat(),
            'size': chunk.size
        }
        
        self.id_to_index[chunk.id] = index_id
        self.index_to_id[index_id] = chunk.id
        self.next_index += 1
    
    async def add_memory_chunk(self, chunk: MemoryChunk):
        """Add a memory chunk to the vector store"""
        try:
            if chunk.embedding is None:
                chunk.embedding = await self.generate_embedding(chunk.content)
            
            # Add to FAISS index
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._add_memory_to_index,
                chunk
            )
            
            logger.debug(f"Added memory chunk {chunk.id} to vector store")
            
        except Exception as e:
            logger.error(f"Error adding memory chunk to vector store: {e}")
            raise
    
    def _add_memory_to_index(self, chunk: MemoryChunk):
        """Add memory chunk to FAISS index (thread-safe)"""
        embedding = np.array(chunk.embedding, dtype=np.float32).reshape(1, -1)
        
        # Add to index
        self.index.add(embedding)
        
        # Update metadata
        index_id = self.next_index
        self.chunk_metadata[index_id] = {
            'id': chunk.id,
            'content': chunk.content,
            'memory_type': chunk.memory_type,
            'user_id': chunk.user_id,
            'conversation_id': chunk.conversation_id,
            'metadata': chunk.metadata,
            'timestamp': chunk.timestamp.isoformat(),
            'importance_score': chunk.importance_score,
            'is_memory': True
        }
        
        self.id_to_index[chunk.id] = index_id
        self.index_to_id[index_id] = chunk.id
        self.next_index += 1
    
    async def search_similar(self, 
                           query_embedding: List[float],
                           limit: int = 10,
                           threshold: float = 0.7,
                           user_id: Optional[str] = None,
                           conversation_id: Optional[str] = None) -> List[Any]:
        """Search for similar chunks"""
        try:
            # Run search in thread pool
            results = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._search_index,
                query_embedding,
                limit * 2,  # Get more results for filtering
                threshold
            )
            
            # Filter results
            filtered_results = []
            for similarity, metadata in results:
                # Apply filters
                if user_id and metadata.get('user_id') != user_id:
                    continue
                if conversation_id and metadata.get('conversation_id') != conversation_id:
                    continue
                
                # Convert back to appropriate object
                if metadata.get('is_memory'):
                    chunk = self._metadata_to_memory_chunk(metadata)
                else:
                    chunk = self._metadata_to_data_chunk(metadata)
                
                filtered_results.append(chunk)
                
                if len(filtered_results) >= limit:
                    break
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def _search_index(self, query_embedding: List[float], k: int, threshold: float):
        """Search FAISS index (thread-safe)"""
        if self.index.ntotal == 0:
            return []
        
        query_vector = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
        
        # Search
        similarities, indices = self.index.search(query_vector, min(k, self.index.ntotal))
        
        results = []
        for similarity, idx in zip(similarities[0], indices[0]):
            if similarity >= threshold:
                metadata = self.chunk_metadata.get(idx, {})
                results.append((similarity, metadata))
        
        return results
    
    def _metadata_to_data_chunk(self, metadata: Dict[str, Any]) -> DataChunk:
        """Convert metadata back to DataChunk"""
        from datetime import datetime
        return DataChunk(
            id=metadata['id'],
            content=metadata['content'],
            chunk_type=metadata['chunk_type'],
            size=metadata['size'],
            source_id=metadata.get('source_id'),
            chunk_index=0,  # Not stored in metadata
            metadata=metadata.get('metadata', {}),
            created_at=datetime.fromisoformat(metadata['created_at'])
        )
    
    def _metadata_to_memory_chunk(self, metadata: Dict[str, Any]) -> MemoryChunk:
        """Convert metadata back to MemoryChunk"""
        from datetime import datetime
        return MemoryChunk(
            id=metadata['id'],
            content=metadata['content'],
            memory_type=metadata['memory_type'],
            user_id=metadata['user_id'],
            conversation_id=metadata['conversation_id'],
            metadata=metadata.get('metadata', {}),
            timestamp=datetime.fromisoformat(metadata['timestamp']),
            importance_score=metadata['importance_score']
        )
    
    async def update_chunk(self, chunk: Any):
        """Update a chunk in the vector store"""
        # For simplicity, we'll delete and re-add
        # In production, you might want more sophisticated update logic
        await self.delete_chunk(chunk.id)
        if hasattr(chunk, 'memory_type'):
            await self.add_memory_chunk(chunk)
        else:
            await self.add_chunk(chunk)
    
    async def delete_chunk(self, chunk_id: str) -> bool:
        """Delete a chunk from the vector store"""
        try:
            if chunk_id not in self.id_to_index:
                return False
            
            index_id = self.id_to_index[chunk_id]
            
            # Remove from metadata
            del self.chunk_metadata[index_id]
            del self.id_to_index[chunk_id]
            del self.index_to_id[index_id]
            
            # Note: FAISS doesn't support individual deletion efficiently
            # In production, you might want to rebuild the index periodically
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting chunk: {e}")
            return False
    
    async def save_index(self):
        """Save the FAISS index and metadata to disk"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._save_index_files
            )
            logger.info("Vector store saved successfully")
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
    
    def _save_index_files(self):
        """Save index and metadata files"""
        index_file = f"{self.index_path}.index"
        metadata_file = f"{self.index_path}.metadata"
        
        # Save FAISS index
        faiss.write_index(self.index, index_file)
        
        # Save metadata
        with open(metadata_file, 'wb') as f:
            pickle.dump({
                'metadata': self.chunk_metadata,
                'id_to_index': self.id_to_index,
                'index_to_id': self.index_to_id,
                'next_index': self.next_index
            }, f)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        stats = {
            'total_vectors': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'memory_chunks': len([m for m in self.chunk_metadata.values() if m.get('is_memory')]),
            'data_chunks': len([m for m in self.chunk_metadata.values() if not m.get('is_memory')]),
        }
        
        # Add embedding service info
        if self.embedding_service:
            model_info = self.embedding_service.get_model_info()
            stats.update({
                'embedding_model': model_info.get('primary_model') or model_info.get('fallback_model'),
                'using_bedrock': model_info.get('using_bedrock', False),
                'bedrock_region': model_info.get('region'),
            })
        
        return stats
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.save_index()
        if self.executor:
            self.executor.shutdown(wait=True)
        if self.embedding_service:
            await self.embedding_service.cleanup()
