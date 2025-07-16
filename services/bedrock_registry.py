"""
Enhanced AWS Bedrock model registry and configuration
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import json


class BedrockModelType(Enum):
    """Bedrock model types"""
    EMBEDDING = "embedding"
    CHAT = "chat"
    IMAGE = "image"
    MULTIMODAL = "multimodal"


class BedrockProvider(Enum):
    """Bedrock model providers"""
    AMAZON = "amazon"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    AI21 = "ai21"
    META = "meta"
    MISTRAL = "mistral"
    STABILITY = "stability"


class BedrockModelRegistry:
    """Registry of supported Bedrock models with their configurations"""
    
    EMBEDDING_MODELS = {
        # Amazon Titan Embeddings
        "amazon.titan-embed-text-v1": {
            "provider": BedrockProvider.AMAZON,
            "type": BedrockModelType.EMBEDDING,
            "dimension": 1536,
            "max_tokens": 8000,
            "request_format": "titan_embed",
            "description": "Amazon Titan Text Embeddings v1"
        },
        "amazon.titan-embed-text-v2:0": {
            "provider": BedrockProvider.AMAZON,
            "type": BedrockModelType.EMBEDDING,
            "dimension": 1024,
            "max_tokens": 8000,
            "request_format": "titan_embed_v2",
            "description": "Amazon Titan Text Embeddings v2"
        },
        "amazon.titan-embed-image-v1": {
            "provider": BedrockProvider.AMAZON,
            "type": BedrockModelType.EMBEDDING,
            "dimension": 1024,
            "max_tokens": None,
            "request_format": "titan_embed_image",
            "description": "Amazon Titan Multimodal Embeddings"
        },
        
        # Cohere Embeddings
        "cohere.embed-english-v3": {
            "provider": BedrockProvider.COHERE,
            "type": BedrockModelType.EMBEDDING,
            "dimension": 1024,
            "max_tokens": 512,
            "request_format": "cohere_embed",
            "description": "Cohere Embed English v3"
        },
        "cohere.embed-multilingual-v3": {
            "provider": BedrockProvider.COHERE,
            "type": BedrockModelType.EMBEDDING,
            "dimension": 1024,
            "max_tokens": 512,
            "request_format": "cohere_embed",
            "description": "Cohere Embed Multilingual v3"
        }
    }
    
    CHAT_MODELS = {
        # Anthropic Claude
        "anthropic.claude-3-sonnet-20240229-v1:0": {
            "provider": BedrockProvider.ANTHROPIC,
            "type": BedrockModelType.CHAT,
            "max_tokens": 4096,
            "context_window": 200000,
            "request_format": "claude_v3",
            "supports_streaming": True,
            "supports_multimodal": True,
            "description": "Claude 3 Sonnet"
        },
        "anthropic.claude-3-haiku-20240307-v1:0": {
            "provider": BedrockProvider.ANTHROPIC,
            "type": BedrockModelType.CHAT,
            "max_tokens": 4096,
            "context_window": 200000,
            "request_format": "claude_v3",
            "supports_streaming": True,
            "supports_multimodal": True,
            "description": "Claude 3 Haiku"
        },
        "anthropic.claude-3-opus-20240229-v1:0": {
            "provider": BedrockProvider.ANTHROPIC,
            "type": BedrockModelType.CHAT,
            "max_tokens": 4096,
            "context_window": 200000,
            "request_format": "claude_v3",
            "supports_streaming": True,
            "supports_multimodal": True,
            "description": "Claude 3 Opus"
        },
        "anthropic.claude-3-5-sonnet-20241022-v2:0": {
            "provider": BedrockProvider.ANTHROPIC,
            "type": BedrockModelType.CHAT,
            "max_tokens": 8192,
            "context_window": 200000,
            "request_format": "claude_v3",
            "supports_streaming": True,
            "supports_multimodal": True,
            "description": "Claude 3.5 Sonnet"
        },
        
        # Amazon Titan
        "amazon.titan-text-lite-v1": {
            "provider": BedrockProvider.AMAZON,
            "type": BedrockModelType.CHAT,
            "max_tokens": 4096,
            "context_window": 4096,
            "request_format": "titan_text",
            "supports_streaming": True,
            "description": "Amazon Titan Text Lite"
        },
        "amazon.titan-text-express-v1": {
            "provider": BedrockProvider.AMAZON,
            "type": BedrockModelType.CHAT,
            "max_tokens": 8192,
            "context_window": 8192,
            "request_format": "titan_text",
            "supports_streaming": True,
            "description": "Amazon Titan Text Express"
        },
        "amazon.nova-micro-v1:0": {
            "provider": BedrockProvider.AMAZON,
            "type": BedrockModelType.CHAT,
            "max_tokens": 4096,
            "context_window": 128000,
            "request_format": "nova",
            "supports_streaming": True,
            "description": "Amazon Nova Micro"
        },
        "amazon.nova-lite-v1:0": {
            "provider": BedrockProvider.AMAZON,
            "type": BedrockModelType.CHAT,
            "max_tokens": 4096,
            "context_window": 300000,
            "request_format": "nova",
            "supports_streaming": True,
            "supports_multimodal": True,
            "description": "Amazon Nova Lite"
        },
        "amazon.nova-pro-v1:0": {
            "provider": BedrockProvider.AMAZON,
            "type": BedrockModelType.CHAT,
            "max_tokens": 4096,
            "context_window": 300000,
            "request_format": "nova",
            "supports_streaming": True,
            "supports_multimodal": True,
            "description": "Amazon Nova Pro"
        },
        
        # Meta Llama
        "meta.llama3-2-1b-instruct-v1:0": {
            "provider": BedrockProvider.META,
            "type": BedrockModelType.CHAT,
            "max_tokens": 2048,
            "context_window": 131072,
            "request_format": "llama",
            "supports_streaming": True,
            "description": "Llama 3.2 1B Instruct"
        },
        "meta.llama3-2-3b-instruct-v1:0": {
            "provider": BedrockProvider.META,
            "type": BedrockModelType.CHAT,
            "max_tokens": 2048,
            "context_window": 131072,
            "request_format": "llama",
            "supports_streaming": True,
            "description": "Llama 3.2 3B Instruct"
        },
        "meta.llama3-2-11b-instruct-v1:0": {
            "provider": BedrockProvider.META,
            "type": BedrockModelType.CHAT,
            "max_tokens": 2048,
            "context_window": 131072,
            "request_format": "llama",
            "supports_streaming": True,
            "supports_multimodal": True,
            "description": "Llama 3.2 11B Instruct Vision"
        },
        "meta.llama3-2-90b-instruct-v1:0": {
            "provider": BedrockProvider.META,
            "type": BedrockModelType.CHAT,
            "max_tokens": 2048,
            "context_window": 131072,
            "request_format": "llama",
            "supports_streaming": True,
            "supports_multimodal": True,
            "description": "Llama 3.2 90B Instruct Vision"
        },
        "meta.llama3-1-8b-instruct-v1:0": {
            "provider": BedrockProvider.META,
            "type": BedrockModelType.CHAT,
            "max_tokens": 2048,
            "context_window": 131072,
            "request_format": "llama",
            "supports_streaming": True,
            "description": "Llama 3.1 8B Instruct"
        },
        "meta.llama3-1-70b-instruct-v1:0": {
            "provider": BedrockProvider.META,
            "type": BedrockModelType.CHAT,
            "max_tokens": 2048,
            "context_window": 131072,
            "request_format": "llama",
            "supports_streaming": True,
            "description": "Llama 3.1 70B Instruct"
        },
        "meta.llama3-1-405b-instruct-v1:0": {
            "provider": BedrockProvider.META,
            "type": BedrockModelType.CHAT,
            "max_tokens": 2048,
            "context_window": 131072,
            "request_format": "llama",
            "supports_streaming": True,
            "description": "Llama 3.1 405B Instruct"
        },
        
        # Mistral AI
        "mistral.mistral-7b-instruct-v0:2": {
            "provider": BedrockProvider.MISTRAL,
            "type": BedrockModelType.CHAT,
            "max_tokens": 4096,
            "context_window": 32768,
            "request_format": "mistral",
            "supports_streaming": True,
            "description": "Mistral 7B Instruct"
        },
        "mistral.mixtral-8x7b-instruct-v0:1": {
            "provider": BedrockProvider.MISTRAL,
            "type": BedrockModelType.CHAT,
            "max_tokens": 4096,
            "context_window": 32768,
            "request_format": "mistral",
            "supports_streaming": True,
            "description": "Mixtral 8x7B Instruct"
        },
        "mistral.mistral-large-2402-v1:0": {
            "provider": BedrockProvider.MISTRAL,
            "type": BedrockModelType.CHAT,
            "max_tokens": 4096,
            "context_window": 32768,
            "request_format": "mistral",
            "supports_streaming": True,
            "description": "Mistral Large"
        },
        "mistral.mistral-large-2407-v1:0": {
            "provider": BedrockProvider.MISTRAL,
            "type": BedrockModelType.CHAT,
            "max_tokens": 4096,
            "context_window": 128000,
            "request_format": "mistral",
            "supports_streaming": True,
            "description": "Mistral Large 2"
        },
        
        # AI21 Labs
        "ai21.jamba-1-5-mini-v1:0": {
            "provider": BedrockProvider.AI21,
            "type": BedrockModelType.CHAT,
            "max_tokens": 4096,
            "context_window": 256000,
            "request_format": "ai21",
            "supports_streaming": True,
            "description": "AI21 Jamba 1.5 Mini"
        },
        "ai21.jamba-1-5-large-v1:0": {
            "provider": BedrockProvider.AI21,
            "type": BedrockModelType.CHAT,
            "max_tokens": 4096,
            "context_window": 256000,
            "request_format": "ai21",
            "supports_streaming": True,
            "description": "AI21 Jamba 1.5 Large"
        },
        
        # Cohere Command
        "cohere.command-r-v1:0": {
            "provider": BedrockProvider.COHERE,
            "type": BedrockModelType.CHAT,
            "max_tokens": 4000,
            "context_window": 128000,
            "request_format": "cohere_command",
            "supports_streaming": True,
            "description": "Cohere Command R"
        },
        "cohere.command-r-plus-v1:0": {
            "provider": BedrockProvider.COHERE,
            "type": BedrockModelType.CHAT,
            "max_tokens": 4000,
            "context_window": 128000,
            "request_format": "cohere_command",
            "supports_streaming": True,
            "description": "Cohere Command R+"
        }
    }
    
    IMAGE_MODELS = {
        # Stability AI
        "stability.stable-diffusion-xl-v1": {
            "provider": BedrockProvider.STABILITY,
            "type": BedrockModelType.IMAGE,
            "request_format": "stability_xl",
            "description": "Stable Diffusion XL"
        },
        "stability.sd3-large-v1:0": {
            "provider": BedrockProvider.STABILITY,
            "type": BedrockModelType.IMAGE,
            "request_format": "stability_sd3",
            "description": "Stable Diffusion 3 Large"
        },
        "stability.stable-image-ultra-v1:0": {
            "provider": BedrockProvider.STABILITY,
            "type": BedrockModelType.IMAGE,
            "request_format": "stability_ultra",
            "description": "Stable Image Ultra"
        },
        "stability.stable-image-core-v1:0": {
            "provider": BedrockProvider.STABILITY,
            "type": BedrockModelType.IMAGE,
            "request_format": "stability_core",
            "description": "Stable Image Core"
        },
        
        # Amazon Titan Image
        "amazon.titan-image-generator-v1": {
            "provider": BedrockProvider.AMAZON,
            "type": BedrockModelType.IMAGE,
            "request_format": "titan_image",
            "description": "Amazon Titan Image Generator"
        },
        "amazon.titan-image-generator-v2:0": {
            "provider": BedrockProvider.AMAZON,
            "type": BedrockModelType.IMAGE,
            "request_format": "titan_image_v2",
            "description": "Amazon Titan Image Generator v2"
        }
    }
    
    @classmethod
    def get_all_models(cls) -> Dict[str, Dict[str, Any]]:
        """Get all supported models"""
        all_models = {}
        all_models.update(cls.EMBEDDING_MODELS)
        all_models.update(cls.CHAT_MODELS)
        all_models.update(cls.IMAGE_MODELS)
        return all_models
    
    @classmethod
    def get_model_info(cls, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model"""
        all_models = cls.get_all_models()
        return all_models.get(model_id)
    
    @classmethod
    def get_embedding_models(cls) -> Dict[str, Dict[str, Any]]:
        """Get all embedding models"""
        return {k: v for k, v in cls.EMBEDDING_MODELS.items()}
    
    @classmethod
    def get_chat_models(cls) -> Dict[str, Dict[str, Any]]:
        """Get all chat models"""
        return {k: v for k, v in cls.CHAT_MODELS.items()}
    
    @classmethod
    def get_image_models(cls) -> Dict[str, Dict[str, Any]]:
        """Get all image generation models"""
        return {k: v for k, v in cls.IMAGE_MODELS.items()}
    
    @classmethod
    def get_models_by_provider(cls, provider: BedrockProvider) -> Dict[str, Dict[str, Any]]:
        """Get all models from a specific provider"""
        all_models = {**cls.EMBEDDING_MODELS, **cls.CHAT_MODELS, **cls.IMAGE_MODELS}
        return {k: v for k, v in all_models.items() if v["provider"] == provider}
    
    @classmethod
    def get_models_by_type(cls, model_type: BedrockModelType) -> Dict[str, Dict[str, Any]]:
        """Get all models of a specific type"""
        all_models = {**cls.EMBEDDING_MODELS, **cls.CHAT_MODELS, **cls.IMAGE_MODELS}
        return {k: v for k, v in all_models.items() if v["type"] == model_type}
    
    @classmethod
    def list_all_models(cls) -> List[str]:
        """Get list of all available model IDs"""
        return list(cls.EMBEDDING_MODELS.keys()) + list(cls.CHAT_MODELS.keys()) + list(cls.IMAGE_MODELS.keys())
    
    @classmethod
    def get_model_config(cls, model_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific model"""
        all_models = {**cls.EMBEDDING_MODELS, **cls.CHAT_MODELS, **cls.IMAGE_MODELS}
        return all_models.get(model_id)
    
    @classmethod
    def is_model_supported(cls, model_id: str) -> bool:
        """Check if a model is supported"""
        return model_id in cls.list_all_models()
    
    @classmethod
    def get_embedding_dimension(cls, model_id: str) -> Optional[int]:
        """Get embedding dimension for a specific embedding model"""
        model_config = cls.EMBEDDING_MODELS.get(model_id)
        return model_config.get("dimension") if model_config else None


class BedrockRequestBuilder:
    """Helper class to build requests for different Bedrock models"""
    
    @staticmethod
    def build_embedding_request(model_id: str, text: str, **kwargs) -> Dict[str, Any]:
        """Build embedding request based on model format"""
        model_info = BedrockModelRegistry.get_model_info(model_id)
        if not model_info:
            raise ValueError(f"Unsupported model: {model_id}")
        
        request_format = model_info["request_format"]
        
        if request_format == "titan_embed":
            return {"inputText": text}
        
        elif request_format == "titan_embed_v2":
            return {
                "inputText": text,
                "dimensions": model_info["dimension"],
                "normalize": True
            }
        
        elif request_format == "titan_embed_image":
            return {"inputText": text, "embeddingConfig": {"outputEmbeddingLength": 1024}}
        
        elif request_format == "cohere_embed":
            return {
                "texts": [text],
                "input_type": kwargs.get("input_type", "search_document"),
                "embedding_types": ["float"]
            }
        
        else:
            raise ValueError(f"Unknown request format: {request_format}")
    
    @staticmethod
    def build_chat_request(
        model_id: str, 
        prompt: str, 
        max_tokens: int = 1000, 
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Build chat request based on model format"""
        model_info = BedrockModelRegistry.get_model_info(model_id)
        if not model_info:
            raise ValueError(f"Unsupported model: {model_id}")
        
        request_format = model_info["request_format"]
        
        if request_format == "claude_v3":
            return {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": min(max_tokens, model_info["max_tokens"]),
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
                "stop_sequences": kwargs.get("stop_sequences", [])
            }
        
        elif request_format in ["titan_text", "nova"]:
            return {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": min(max_tokens, model_info["max_tokens"]),
                    "temperature": temperature,
                    "stopSequences": kwargs.get("stop_sequences", [])
                }
            }
        
        elif request_format == "llama":
            return {
                "prompt": prompt,
                "max_gen_len": min(max_tokens, model_info["max_tokens"]),
                "temperature": temperature,
                "top_p": kwargs.get("top_p", 0.9)
            }
        
        elif request_format == "mistral":
            return {
                "prompt": prompt,
                "max_tokens": min(max_tokens, model_info["max_tokens"]),
                "temperature": temperature,
                "top_p": kwargs.get("top_p", 0.7),
                "top_k": kwargs.get("top_k", 50)
            }
        
        elif request_format == "ai21":
            return {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": min(max_tokens, model_info["max_tokens"]),
                "temperature": temperature,
                "top_p": kwargs.get("top_p", 1.0)
            }
        
        elif request_format == "cohere_command":
            return {
                "message": prompt,
                "max_tokens": min(max_tokens, model_info["max_tokens"]),
                "temperature": temperature,
                "p": kwargs.get("top_p", 0.75),
                "k": kwargs.get("top_k", 0)
            }
        
        else:
            raise ValueError(f"Unknown request format: {request_format}")


class BedrockResponseParser:
    """Helper class to parse responses from different Bedrock models"""
    
    @staticmethod
    def parse_embedding_response(model_id: str, response_body: Dict[str, Any]) -> List[float]:
        """Parse embedding response based on model format"""
        model_info = BedrockModelRegistry.get_model_info(model_id)
        if not model_info:
            raise ValueError(f"Unsupported model: {model_id}")
        
        request_format = model_info["request_format"]
        
        if request_format in ["titan_embed", "titan_embed_v2", "titan_embed_image"]:
            return response_body.get("embedding", [])
        
        elif request_format == "cohere_embed":
            embeddings = response_body.get("embeddings", [])
            return embeddings[0] if embeddings else []
        
        else:
            raise ValueError(f"Unknown request format: {request_format}")
    
    @staticmethod
    def parse_chat_response(model_id: str, response_body: Dict[str, Any]) -> str:
        """Parse chat response based on model format"""
        model_info = BedrockModelRegistry.get_model_info(model_id)
        if not model_info:
            raise ValueError(f"Unsupported model: {model_id}")
        
        request_format = model_info["request_format"]
        
        if request_format == "claude_v3":
            content = response_body.get("content", [])
            if content and content[0].get("type") == "text":
                return content[0].get("text", "")
            return ""
        
        elif request_format in ["titan_text", "nova"]:
            results = response_body.get("results", [])
            if results:
                return results[0].get("outputText", "")
            return ""
        
        elif request_format == "llama":
            return response_body.get("generation", "")
        
        elif request_format == "mistral":
            outputs = response_body.get("outputs", [])
            if outputs:
                return outputs[0].get("text", "")
            return ""
        
        elif request_format == "ai21":
            choices = response_body.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return ""
        
        elif request_format == "cohere_command":
            return response_body.get("text", "")
        
        else:
            raise ValueError(f"Unknown request format: {request_format}")
    
    @staticmethod
    def parse_streaming_chunk(model_id: str, chunk_data: Dict[str, Any]) -> Optional[str]:
        """Parse streaming chunk based on model format"""
        model_info = BedrockModelRegistry.get_model_info(model_id)
        if not model_info:
            return None
        
        request_format = model_info["request_format"]
        
        if request_format == "claude_v3":
            if chunk_data.get("type") == "content_block_delta":
                delta = chunk_data.get("delta", {})
                return delta.get("text", "")
        
        elif request_format in ["titan_text", "nova"]:
            return chunk_data.get("outputText", "")
        
        elif request_format == "llama":
            return chunk_data.get("generation", "")
        
        elif request_format == "mistral":
            outputs = chunk_data.get("outputs", [])
            if outputs:
                return outputs[0].get("text", "")
        
        elif request_format == "ai21":
            return chunk_data.get("text", "")
        
        elif request_format == "cohere_command":
            return chunk_data.get("text", "")
        
        return None
