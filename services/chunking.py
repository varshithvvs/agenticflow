import uuid
import time
from typing import List, Dict
from models.chunks import DataChunk, ChunkRequest, ChunkResponse, ChunkType
import re
import logging

logger = logging.getLogger(__name__)

class ChunkingService:
    def __init__(self):
        self.chunk_store: Dict[str, DataChunk] = {}
        
    async def create_chunks(self, request: ChunkRequest) -> ChunkResponse:
        """Create chunks from content based on request parameters"""
        start_time = time.time()
        
        try:
            chunks = []
            
            if request.chunk_type == ChunkType.TEXT:
                chunks = await self._chunk_text(request)
            elif request.chunk_type == ChunkType.CODE:
                chunks = await self._chunk_code(request)
            elif request.chunk_type == ChunkType.DOCUMENT:
                chunks = await self._chunk_document(request)
            else:
                chunks = await self._chunk_text(request)  # Default to text chunking
            
            # Store chunks
            for chunk in chunks:
                self.chunk_store[chunk.id] = chunk
            
            total_size = sum(chunk.size for chunk in chunks)
            processing_time = (time.time() - start_time) * 1000
            
            return ChunkResponse(
                chunks=chunks,
                total_chunks=len(chunks),
                total_size=total_size,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error creating chunks: {e}")
            raise
    
    async def _chunk_text(self, request: ChunkRequest) -> List[DataChunk]:
        """Chunk text content"""
        content = request.content
        chunk_size = request.chunk_size
        overlap = request.overlap
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = min(start + chunk_size, len(content))
            
            # Try to break at sentence boundaries
            if end < len(content):
                # Look for sentence endings within the last 100 characters
                sentence_end = self._find_sentence_boundary(content, start, end)
                if sentence_end > start:
                    end = sentence_end
            
            chunk_content = content[start:end].strip()
            
            if chunk_content:
                chunk = DataChunk(
                    id=str(uuid.uuid4()),
                    content=chunk_content,
                    chunk_type=request.chunk_type,
                    size=len(chunk_content.encode('utf-8')),
                    source_id=request.source_id,
                    chunk_index=chunk_index,
                    metadata={
                        **request.metadata,
                        "start_pos": start,
                        "end_pos": end,
                        "overlap": overlap
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Move start position with overlap
            start = max(start + chunk_size - overlap, end)
            
        return chunks
    
    async def _chunk_code(self, request: ChunkRequest) -> List[DataChunk]:
        """Chunk code content by functions/classes"""
        content = request.content
        chunks = []
        
        # Simple code chunking by functions (Python example)
        function_pattern = r'(def\\s+\\w+.*?(?=\\ndef\\s|\\nclass\\s|\\Z))'
        class_pattern = r'(class\\s+\\w+.*?(?=\\nclass\\s|\\ndef\\s|\\Z))'
        
        # Find functions and classes
        functions = re.findall(function_pattern, content, re.DOTALL)
        classes = re.findall(class_pattern, content, re.DOTALL)
        
        chunk_index = 0
        
        # Create chunks for functions
        for func in functions:
            chunk = DataChunk(
                id=str(uuid.uuid4()),
                content=func.strip(),
                chunk_type=request.chunk_type,
                size=len(func.encode('utf-8')),
                source_id=request.source_id,
                chunk_index=chunk_index,
                metadata={
                    **request.metadata,
                    "code_type": "function"
                }
            )
            chunks.append(chunk)
            chunk_index += 1
        
        # Create chunks for classes
        for cls in classes:
            chunk = DataChunk(
                id=str(uuid.uuid4()),
                content=cls.strip(),
                chunk_type=request.chunk_type,
                size=len(cls.encode('utf-8')),
                source_id=request.source_id,
                chunk_index=chunk_index,
                metadata={
                    **request.metadata,
                    "code_type": "class"
                }
            )
            chunks.append(chunk)
            chunk_index += 1
        
        # If no functions/classes found, fall back to text chunking
        if not chunks:
            return await self._chunk_text(request)
        
        return chunks
    
    async def _chunk_document(self, request: ChunkRequest) -> List[DataChunk]:
        """Chunk document content by paragraphs"""
        content = request.content
        
        # Split by paragraphs
        paragraphs = re.split(r'\\n\\s*\\n', content)
        chunks = []
        chunk_index = 0
        
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph would exceed chunk size, create a chunk
            if current_chunk and len(current_chunk + paragraph) > request.chunk_size:
                chunk = DataChunk(
                    id=str(uuid.uuid4()),
                    content=current_chunk.strip(),
                    chunk_type=request.chunk_type,
                    size=len(current_chunk.encode('utf-8')),
                    source_id=request.source_id,
                    chunk_index=chunk_index,
                    metadata={
                        **request.metadata,
                        "content_type": "paragraph_group"
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
                current_chunk = paragraph + "\\n\\n"
            else:
                current_chunk += paragraph + "\\n\\n"
        
        # Add the last chunk
        if current_chunk.strip():
            chunk = DataChunk(
                id=str(uuid.uuid4()),
                content=current_chunk.strip(),
                chunk_type=request.chunk_type,
                size=len(current_chunk.encode('utf-8')),
                source_id=request.source_id,
                chunk_index=chunk_index,
                metadata={
                    **request.metadata,
                    "content_type": "paragraph_group"
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _find_sentence_boundary(self, content: str, start: int, end: int) -> int:
        """Find the best sentence boundary near the end position"""
        # Look for sentence endings in the last portion
        search_start = max(start, end - 100)
        search_text = content[search_start:end]
        
        # Find sentence endings
        sentence_endings = ['.', '!', '?', '\\n']
        best_pos = start
        
        for i in range(len(search_text) - 1, -1, -1):
            if search_text[i] in sentence_endings:
                # Make sure it's not an abbreviation
                if search_text[i] == '.' and i > 0 and search_text[i-1].isupper():
                    continue
                best_pos = search_start + i + 1
                break
        
        return best_pos if best_pos > start else end
    
    async def get_chunk(self, chunk_id: str) -> DataChunk:
        """Get a specific chunk by ID"""
        if chunk_id not in self.chunk_store:
            raise ValueError(f"Chunk {chunk_id} not found")
        return self.chunk_store[chunk_id]
    
    async def get_chunks_by_source(self, source_id: str) -> List[DataChunk]:
        """Get all chunks for a specific source"""
        return [
            chunk for chunk in self.chunk_store.values()
            if chunk.source_id == source_id
        ]
    
    async def delete_chunk(self, chunk_id: str) -> bool:
        """Delete a chunk"""
        if chunk_id in self.chunk_store:
            del self.chunk_store[chunk_id]
            return True
        return False