import time
import uuid
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from models.memory import MemoryChunk, ConversationMemory, MemoryQuery, MemoryResponse, MemoryType
from storage.vector_store import VectorStore
import logging

logger = logging.getLogger(__name__)

class MemoryService:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.conversations: Dict[str, ConversationMemory] = {}
        self.memory_chunks: Dict[str, MemoryChunk] = {}
        
    async def initialize(self):
        """Initialize the memory service"""
        await self.vector_store.initialize()
        logger.info("Memory service initialized")
    
    def _get_conversation_key(self, user_id: str, conversation_id: str) -> str:
        """Generate conversation key"""
        return f"{user_id}:{conversation_id}"
    
    async def add_memory(self, user_id: str, conversation_id: str, content: str, 
                        memory_type: MemoryType = MemoryType.SHORT_TERM,
                        metadata: Optional[Dict] = None) -> MemoryChunk:
        """Add a new memory chunk"""
        
        # Create memory chunk
        chunk = MemoryChunk(
            id=str(uuid.uuid4()),
            content=content,
            memory_type=memory_type,
            user_id=user_id,
            conversation_id=conversation_id,
            metadata=metadata or {},
            importance_score=self._calculate_importance(content)
        )
        
        # Generate embedding
        chunk.embedding = await self.vector_store.generate_embedding(content)
        
        # Store in vector store for long-term retrieval
        await self.vector_store.add_memory_chunk(chunk)
        
        # Store in memory chunks
        self.memory_chunks[chunk.id] = chunk
        
        # Update conversation memory
        conv_key = self._get_conversation_key(user_id, conversation_id)
        if conv_key not in self.conversations:
            self.conversations[conv_key] = ConversationMemory(
                user_id=user_id,
                conversation_id=conversation_id
            )
        
        conversation = self.conversations[conv_key]
        
        if memory_type == MemoryType.SHORT_TERM:
            conversation.short_term_memory.append(chunk)
            # Maintain short-term memory limit
            if len(conversation.short_term_memory) > conversation.max_short_term_chunks:
                # Move oldest to long-term
                oldest = conversation.short_term_memory.pop(0)
                oldest.memory_type = MemoryType.LONG_TERM
                conversation.long_term_memory.append(oldest.id)
        else:
            conversation.long_term_memory.append(chunk.id)
        
        logger.info(f"Added {memory_type} memory for user {user_id}")
        return chunk
    
    async def search_memory(self, query: MemoryQuery) -> MemoryResponse:
        """Search memory using vector similarity"""
        start_time = time.time()
        
        try:
            # Generate query embedding
            query_embedding = await self.vector_store.generate_embedding(query.query)
            
            # Search vector store
            similar_chunks = await self.vector_store.search_similar(
                query_embedding,
                limit=query.limit,
                threshold=query.similarity_threshold,
                user_id=query.user_id,
                conversation_id=query.conversation_id
            )
            
            # Filter by memory types
            filtered_chunks = [
                chunk for chunk in similar_chunks
                if chunk.memory_type in query.memory_types
            ]
            
            # Sort by relevance and recency
            filtered_chunks.sort(
                key=lambda x: (x.importance_score, x.timestamp),
                reverse=True
            )
            
            query_time = (time.time() - start_time) * 1000
            
            return MemoryResponse(
                chunks=filtered_chunks[:query.limit],
                total_found=len(filtered_chunks),
                query_time_ms=query_time
            )
            
        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            return MemoryResponse(
                chunks=[],
                total_found=0,
                query_time_ms=(time.time() - start_time) * 1000
            )
    
    async def get_conversation_context(self, user_id: str, conversation_id: str,
                                     max_tokens: int = 2000) -> List[MemoryChunk]:
        """Get conversation context within token limit"""
        conv_key = self._get_conversation_key(user_id, conversation_id)
        
        if conv_key not in self.conversations:
            return []
        
        conversation = self.conversations[conv_key]
        context_chunks = []
        current_tokens = 0
        
        # Start with most recent short-term memory
        for chunk in reversed(conversation.short_term_memory):
            chunk_tokens = len(chunk.content.split())  # Rough token estimate
            if current_tokens + chunk_tokens <= max_tokens:
                context_chunks.insert(0, chunk)
                current_tokens += chunk_tokens
            else:
                break
        
        return context_chunks
    
    async def get_relevant_long_term_memory(self, user_id: str, query: str,
                                          limit: int = 5) -> List[MemoryChunk]:
        """Get relevant long-term memories for a query"""
        memory_query = MemoryQuery(
            query=query,
            user_id=user_id,
            memory_types=[MemoryType.LONG_TERM, MemoryType.SEMANTIC],
            limit=limit
        )
        
        response = await self.search_memory(memory_query)
        return response.chunks
    
    def _calculate_importance(self, content: str) -> float:
        """Calculate importance score for content"""
        # Simple heuristic - can be made more sophisticated
        importance = 0.5
        
        # Longer content might be more important
        if len(content) > 100:
            importance += 0.1
        
        # Questions might be more important
        if '?' in content:
            importance += 0.1
        
        # Emotional words might be more important
        emotional_words = ['important', 'urgent', 'critical', 'remember', 'forget']
        for word in emotional_words:
            if word.lower() in content.lower():
                importance += 0.1
                break
        
        return min(importance, 1.0)
    
    async def consolidate_memory(self, user_id: str, conversation_id: str):
        """Consolidate short-term memory into long-term"""
        conv_key = self._get_conversation_key(user_id, conversation_id)
        
        if conv_key not in self.conversations:
            return
        
        conversation = self.conversations[conv_key]
        
        # Move old short-term memories to long-term
        cutoff_time = datetime.now() - timedelta(hours=1)  # 1 hour cutoff
        
        to_move = []
        for chunk in conversation.short_term_memory:
            if chunk.timestamp < cutoff_time:
                to_move.append(chunk)
        
        for chunk in to_move:
            chunk.memory_type = MemoryType.LONG_TERM
            conversation.short_term_memory.remove(chunk)
            conversation.long_term_memory.append(chunk.id)
            
            # Update in vector store
            await self.vector_store.update_chunk(chunk)
        
        logger.info(f"Consolidated {len(to_move)} memories to long-term for user {user_id}")
    
    async def delete_memory(self, chunk_id: str) -> bool:
        """Delete a memory chunk"""
        if chunk_id not in self.memory_chunks:
            return False
        
        chunk = self.memory_chunks[chunk_id]
        
        # Remove from vector store
        await self.vector_store.delete_chunk(chunk_id)
        
        # Remove from conversation memory
        conv_key = self._get_conversation_key(chunk.user_id, chunk.conversation_id)
        if conv_key in self.conversations:
            conversation = self.conversations[conv_key]
            
            # Remove from short-term
            conversation.short_term_memory = [
                c for c in conversation.short_term_memory if c.id != chunk_id
            ]
            
            # Remove from long-term
            if chunk_id in conversation.long_term_memory:
                conversation.long_term_memory.remove(chunk_id)
        
        # Remove from memory chunks
        del self.memory_chunks[chunk_id]
        
        return True
    
    async def get_memory_stats(self, user_id: str) -> Dict:
        """Get memory statistics for a user"""
        user_chunks = [
            chunk for chunk in self.memory_chunks.values()
            if chunk.user_id == user_id
        ]
        
        stats = {
            "total_memories": len(user_chunks),
            "short_term": len([c for c in user_chunks if c.memory_type == MemoryType.SHORT_TERM]),
            "long_term": len([c for c in user_chunks if c.memory_type == MemoryType.LONG_TERM]),
            "episodic": len([c for c in user_chunks if c.memory_type == MemoryType.EPISODIC]),
            "semantic": len([c for c in user_chunks if c.memory_type == MemoryType.SEMANTIC]),
            "conversations": len([
                conv for conv in self.conversations.values()
                if conv.user_id == user_id
            ])
        }
        
        return stats