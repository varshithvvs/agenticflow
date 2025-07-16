"""
Enhanced AWS Bedrock embedding service with full model support
"""

import asyncio
import json
import logging
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

import boto3
import numpy as np
from botocore.exceptions import ClientError, NoCredentialsError
from sentence_transformers import SentenceTransformer

from config.settings import get_settings
from services.bedrock_registry import BedrockModelRegistry, BedrockModelType

logger = logging.getLogger(__name__)


class EnhancedBedrockEmbeddingService:
    """Enhanced AWS Bedrock embedding service with full model support"""
    
    def __init__(self, model_id: Optional[str] = None):
        self.settings = get_settings()
        self.model_id = model_id or self.settings.embedding.bedrock_model
        self.bedrock_client = None
        self.fallback_model = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._initialized = False
        self._bedrock_working = False
        self.registry = BedrockModelRegistry()
        
        # Get model configuration
        self.model_config = self.registry.get_model_config(self.model_id)
        if not self.model_config or self.model_config["type"] != BedrockModelType.EMBEDDING:
            raise ValueError(f"Model {self.model_id} is not a supported embedding model")
    
    async def initialize(self):
        """Initialize Bedrock client and fallback model"""
        if self._initialized:
            return
            
        try:
            # Initialize Bedrock client
            session = boto3.Session(
                aws_access_key_id=self.settings.aws.access_key_id,
                aws_secret_access_key=self.settings.aws.secret_access_key,
                aws_session_token=self.settings.aws.session_token,
                region_name=self.settings.aws.region
            )
            
            self.bedrock_client = session.client(
                service_name='bedrock-runtime',
                region_name=self.settings.aws.region
            )
            
            # Test Bedrock connection
            if await self._test_bedrock_connection():
                self._bedrock_working = True
                logger.info(f"Bedrock client initialized with {self.model_id} in region {self.settings.aws.region}")
            else:
                self._bedrock_working = False
                self.bedrock_client = None
                logger.info("Bedrock connection failed, using fallback only")
            
        except (NoCredentialsError, ClientError) as e:
            logger.warning(f"Failed to initialize Bedrock client: {e}")
            logger.info("Falling back to sentence-transformers model")
            self.bedrock_client = None
            self._bedrock_working = False
            
        # Initialize fallback model
        try:
            self._ensure_executor()
            self.fallback_model = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._load_fallback_model
            )
            logger.info(f"Fallback model {self.settings.embedding.fallback_model} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load fallback model: {e}")
            raise
            
        self._initialized = True
    
    def _load_fallback_model(self) -> SentenceTransformer:
        """Load sentence-transformers model in thread pool"""
        return SentenceTransformer(self.settings.embedding.fallback_model)
    
    async def _test_bedrock_connection(self):
        """Test Bedrock connection with a simple embedding request"""
        if not self.bedrock_client:
            return False
            
        try:
            test_text = "test connection"
            await self._get_bedrock_embedding(test_text)
            return True
        except Exception as e:
            logger.warning(f"Bedrock connection test failed: {e}")
            return False
    
    def _ensure_executor(self):
        """Ensure we have a working executor"""
        if not self.executor or self.executor._shutdown:
            self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def _get_bedrock_embedding(self, text: str) -> List[float]:
        """Get embedding from Bedrock using model-specific format"""
        if not self.bedrock_client:
            raise RuntimeError("Bedrock client not initialized")
        
        # Build request based on model format
        request_format = self.model_config["request_format"]
        request_body = self._build_embedding_request(text, request_format)
        
        def _invoke_bedrock():
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            response_body = json.loads(response['body'].read())
            return self._parse_embedding_response(response_body, request_format)
        
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, _invoke_bedrock
        )
    
    def _build_embedding_request(self, text: str, request_format: str) -> Dict[str, Any]:
        """Build request body based on model format"""
        if request_format == "titan_embed":
            return {"inputText": text}
        elif request_format == "titan_embed_v2":
            return {
                "inputText": text,
                "dimensions": self.model_config["dimension"],
                "normalize": True
            }
        elif request_format == "cohere_embed":
            return {
                "texts": [text],
                "input_type": "search_document"
            }
        else:
            raise ValueError(f"Unsupported request format: {request_format}")
    
    def _parse_embedding_response(self, response: Dict[str, Any], request_format: str) -> List[float]:
        """Parse embedding response based on model format"""
        if request_format in ["titan_embed", "titan_embed_v2"]:
            return response["embedding"]
        elif request_format == "cohere_embed":
            return response["embeddings"][0]
        else:
            raise ValueError(f"Unsupported response format: {request_format}")
    
    async def _get_fallback_embedding(self, text: str) -> List[float]:
        """Get embedding from fallback model"""
        if not self.fallback_model:
            raise RuntimeError("Fallback model not initialized")
        
        self._ensure_executor()
        
        def _encode_text():
            embedding = self.fallback_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, _encode_text
        )
    
    async def embed_text(self, text: str) -> List[float]:
        """Get embedding for a single text"""
        await self.initialize()
        
        # Try Bedrock first
        if self._bedrock_working:
            try:
                embedding = await self._get_bedrock_embedding(text)
                logger.debug(f"Generated Bedrock embedding with {len(embedding)} dimensions")
                return embedding
            except Exception as e:
                logger.warning(f"Bedrock embedding failed: {e}, falling back to local model")
                self._bedrock_working = False  # Mark as not working for subsequent calls
        
        # Fallback to sentence-transformers
        embedding = await self._get_fallback_embedding(text)
        logger.debug(f"Generated fallback embedding with {len(embedding)} dimensions")
        return embedding
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this service"""
        if self._bedrock_working and self.model_config:
            return self.model_config["dimension"]
        else:
            # Return fallback model dimension
            return self.settings.embedding.fallback_dimension
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current embedding model"""
        if self._bedrock_working and self.model_config:
            return {
                "provider": "bedrock",
                "model_id": self.model_id,
                "dimension": self.model_config["dimension"],
                "provider_name": self.model_config.get("provider", "amazon"),
                "working": True
            }
        else:
            return {
                "provider": "sentence-transformers",
                "model_id": self.settings.embedding.fallback_model,
                "dimension": self.settings.embedding.fallback_dimension,
                "provider_name": "huggingface",
                "working": False,
                "fallback": True
            }

    async def cleanup(self):
        """Clean up resources"""
        if self.executor and not self.executor._shutdown:
            self.executor.shutdown(wait=True)
            logger.debug("Embedding service executor shut down")
    
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'executor') and self.executor and not self.executor._shutdown:
            try:
                self.executor.shutdown(wait=False)
            except Exception:
                pass  # Ignore cleanup errors in destructor


# Global service instance
_service_instance = None


async def get_embedding_service() -> EnhancedBedrockEmbeddingService:
    """Get or create the global embedding service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = EnhancedBedrockEmbeddingService()
    return _service_instance


async def cleanup_embedding_service():
    """Clean up the global embedding service"""
    global _service_instance
    if _service_instance:
        await _service_instance.cleanup()
        _service_instance = None
