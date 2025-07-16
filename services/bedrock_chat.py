"""
Enhanced AWS Bedrock chat service with full model support
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from config.settings import get_settings
from services.bedrock_registry import BedrockModelRegistry, BedrockModelType

logger = logging.getLogger(__name__)


class EnhancedBedrockChatService:
    """Enhanced AWS Bedrock chat service with full model support"""
    
    def __init__(self, model_id: Optional[str] = None):
        self.settings = get_settings()
        self.model_id = model_id or self.settings.aws.bedrock_chat_model
        self.bedrock_client = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._initialized = False
        self._bedrock_working = False
        self.registry = BedrockModelRegistry()
        
        # Get model configuration
        self.model_config = self.registry.get_model_config(self.model_id)
        if not self.model_config or self.model_config["type"] != BedrockModelType.CHAT:
            raise ValueError(f"Model {self.model_id} is not a supported chat model")
    
    async def initialize(self):
        """Initialize Bedrock client"""
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
                logger.info(f"Bedrock chat client initialized with {self.model_id} in region {self.settings.aws.region}")
            else:
                self._bedrock_working = False
                self.bedrock_client = None
                logger.info("Bedrock chat connection failed")
            
        except (NoCredentialsError, ClientError) as e:
            logger.warning(f"Failed to initialize Bedrock chat client: {e}")
            self.bedrock_client = None
            self._bedrock_working = False
            
        self._initialized = True
    
    async def _test_bedrock_connection(self):
        """Test Bedrock connection with a simple chat request"""
        if not self.bedrock_client:
            return False
            
        try:
            test_message = "Hello"
            await self._get_bedrock_response(test_message)
            return True
        except Exception as e:
            logger.warning(f"Bedrock chat connection test failed: {e}")
            return False
    
    def _ensure_executor(self):
        """Ensure we have a working executor"""
        if not self.executor or self.executor._shutdown:
            self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def _get_bedrock_response(self, message: str, context: Optional[str] = None) -> str:
        """Get response from Bedrock using model-specific format"""
        if not self.bedrock_client:
            raise RuntimeError("Bedrock client not initialized")
        
        # Build request based on model format
        request_format = self.model_config["request_format"]
        request_body = self._build_chat_request(message, context, request_format)
        
        def _invoke_bedrock():
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            response_body = json.loads(response['body'].read())
            return self._parse_chat_response(response_body, request_format)
        
        self._ensure_executor()
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, _invoke_bedrock
        )
    
    def _build_chat_request(self, message: str, context: Optional[str], request_format: str) -> Dict[str, Any]:
        """Build request body based on model format"""
        full_message = f"{context}\n\n{message}" if context else message
        
        if request_format == "claude":
            return {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.model_config.get("max_tokens", 4096),
                "messages": [
                    {
                        "role": "user",
                        "content": full_message
                    }
                ],
                "temperature": 0.7
            }
        elif request_format == "titan":
            return {
                "inputText": full_message,
                "textGenerationConfig": {
                    "maxTokenCount": self.model_config.get("max_tokens", 4096),
                    "temperature": 0.7,
                    "topP": 0.9
                }
            }
        elif request_format == "ai21":
            return {
                "prompt": full_message,
                "maxTokens": self.model_config.get("max_tokens", 4096),
                "temperature": 0.7,
                "topP": 0.9
            }
        elif request_format == "cohere":
            return {
                "message": full_message,
                "max_tokens": self.model_config.get("max_tokens", 4096),
                "temperature": 0.7,
                "p": 0.9
            }
        elif request_format == "llama":
            return {
                "prompt": full_message,
                "max_gen_len": self.model_config.get("max_tokens", 4096),
                "temperature": 0.7,
                "top_p": 0.9
            }
        elif request_format == "mistral":
            return {
                "prompt": full_message,
                "max_tokens": self.model_config.get("max_tokens", 4096),
                "temperature": 0.7,
                "top_p": 0.9
            }
        elif request_format == "nova":
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": full_message}]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": self.model_config.get("max_tokens", 4096),
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
        else:
            raise ValueError(f"Unsupported request format: {request_format}")
    
    def _parse_chat_response(self, response: Dict[str, Any], request_format: str) -> str:
        """Parse chat response based on model format"""
        if request_format == "claude":
            return response["content"][0]["text"]
        elif request_format == "titan":
            return response["results"][0]["outputText"]
        elif request_format == "ai21":
            return response["completions"][0]["data"]["text"]
        elif request_format == "cohere":
            return response["text"]
        elif request_format == "llama":
            return response["generation"]
        elif request_format == "mistral":
            return response["outputs"][0]["text"]
        elif request_format == "nova":
            return response["output"]["message"]["content"][0]["text"]
        else:
            raise ValueError(f"Unsupported response format: {request_format}")
    
    async def get_response(self, message: str, context: Optional[str] = None) -> str:
        """Get chat response"""
        await self.initialize()
        
        if not self._bedrock_working:
            return "I apologize, but the AI chat service is currently unavailable. Please try again later."
        
        try:
            response = await self._get_bedrock_response(message, context)
            logger.debug(f"Generated Bedrock chat response using {self.model_id}")
            return response
        except Exception as e:
            logger.error(f"Bedrock chat failed: {e}")
            return f"I encountered an error while processing your request: {str(e)}"
    
    async def cleanup(self):
        """Clean up resources"""
        if self.executor and not self.executor._shutdown:
            self.executor.shutdown(wait=True)
            logger.debug("Chat service executor shut down")
    
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'executor') and self.executor and not self.executor._shutdown:
            try:
                self.executor.shutdown(wait=False)
            except Exception:
                pass  # Ignore cleanup errors in destructor


# Global service instance
_chat_service_instance = None


async def get_chat_service() -> EnhancedBedrockChatService:
    """Get or create the global chat service instance"""
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = EnhancedBedrockChatService()
    return _chat_service_instance


async def cleanup_chat_service():
    """Clean up the global chat service"""
    global _chat_service_instance
    if _chat_service_instance:
        await _chat_service_instance.cleanup()
        _chat_service_instance = None
