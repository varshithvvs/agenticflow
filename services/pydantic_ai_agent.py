"""
PydanticAI Agent Service - Core AI Agent Implementation
Integrates PydanticAI with AWS Bedrock and MCP tools for intelligent conversation handling
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.models.test import TestModel
from pydantic import BaseModel, Field

from config.settings import Settings
from models.mcp_models import StreamingRequest
from models.memory import MemoryQuery
from models.pydantic_ai_models import StructuredResponse, TaskType, Confidence, Evidence
from utils.logging_config import get_logger

logger = get_logger(__name__)


class AgentContext(BaseModel):
    """Context for PydanticAI agent with memory and MCP integration"""
    user_id: str
    conversation_id: str
    memory_chunks: List[str] = Field(default_factory=list)
    mcp_tools_available: List[str] = Field(default_factory=list)
    session_data: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Structured response from PydanticAI agent"""
    content: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PydanticAIService:
    """Enhanced PydanticAI service with Bedrock and MCP integration"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model: Optional[Union[BedrockConverseModel, TestModel]] = None
        self.agent: Optional[Agent] = None
        self.memory_service = None
        self.mcp_client = None
        self._initialized = False
    
    async def initialize(self, memory_service=None, mcp_client=None):
        """Initialize PydanticAI agent with integrated services"""
        if self._initialized:
            return
        
        logger.info("Initializing PydanticAI service with Bedrock integration")
        
        try:
            # Initialize Bedrock model
            self.model = BedrockConverseModel(
                model_name=self.settings.aws.bedrock_chat_model,
                region=self.settings.aws.region,
                access_key_id=self.settings.aws.access_key_id,
                secret_access_key=self.settings.aws.secret_access_key,
                session_token=self.settings.aws.session_token
            )
            
            # Store service references
            self.memory_service = memory_service
            self.mcp_client = mcp_client
            
            # Create PydanticAI agent with tools
            self.agent = Agent(
                model=self.model,
                output_type=StructuredResponse,
                system_prompt=self._get_system_prompt(),
                tools=[
                    self._create_memory_search_tool(),
                    self._create_mcp_tool_caller()
                ]
            )
            
            self._initialized = True
            logger.info("PydanticAI service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PydanticAI service: {e}")
            # Fallback to basic model without AWS credentials
            await self._initialize_fallback_model()
    
    async def _initialize_fallback_model(self):
        """Initialize fallback model when Bedrock is unavailable"""
        logger.warning("Initializing PydanticAI with fallback model (no Bedrock)")
        
        try:
            # Use a test model for testing/development
            self.model = TestModel()
            
            self.agent = Agent(
                model=self.model,
                output_type=StructuredResponse,
                system_prompt=self._get_system_prompt(),
                tools=[
                    self._create_memory_search_tool(),
                    self._create_mcp_tool_caller()
                ]
            )
            
            self._initialized = True
            logger.info("PydanticAI service initialized with fallback model")
            
        except Exception as e:
            logger.error(f"Failed to initialize fallback PydanticAI service: {e}")
            raise
    
    def _get_system_prompt(self) -> str:
        """Get enhanced system prompt for the AI agent"""
        return """
        You are an intelligent AI assistant in the PydanticAI Workflow System with advanced capabilities.

        CORE FEATURES:
        - Memory Integration: Search and retrieve relevant conversation history and documents
        - MCP Tool Access: Execute tools through the Model Context Protocol
        - Content Analysis: Analyze and chunk large documents intelligently
        - Workflow Orchestration: Coordinate multiple AI services seamlessly

        RESPONSE STRUCTURE:
        You must provide structured responses that include:
        - content: The main response content
        - task_type: The type of task being performed (analysis, summarization, etc.)
        - confidence: A confidence assessment with score and reasoning
        - evidence: Supporting evidence from memory, tools, or reasoning
        - tools_used: List of tools utilized in processing
        - reasoning_chain: Step-by-step reasoning process
        - suggestions: Follow-up suggestions for the user

        BEHAVIORAL GUIDELINES:
        - Always provide helpful, accurate, and contextually relevant responses
        - Use memory search to maintain conversation continuity
        - Leverage MCP tools when they can enhance your response
        - Be transparent about your reasoning and tool usage
        - Provide confidence scores with detailed reasoning
        - Include evidence and sources for all claims
        - Offer actionable suggestions for follow-up

        TASK TYPES:
        - analysis: Deep analysis of content, code, or data
        - summarization: Concise summaries of large content
        - code_review: Code analysis with suggestions
        - question_answering: Direct answers to questions
        - creative_writing: Creative content generation
        - workflow_orchestration: Process and workflow planning

        Remember: You are part of a larger workflow system designed to provide intelligent,
        context-aware assistance with full integration of memory, tools, and content processing.
        Always structure your responses according to the StructuredResponse format.
        """
    
    def _create_memory_search_tool(self) -> Tool:
        """Create tool for searching conversation memory"""
        async def search_memory(ctx: RunContext[AgentContext], query: str, limit: int = 5) -> str:
            """Search conversation memory for relevant information"""
            if not self.memory_service:
                return "Memory service not available"
            
            try:
                memory_query = MemoryQuery(
                    query=query,
                    user_id=ctx.deps.user_id,
                    conversation_id=ctx.deps.conversation_id,
                    limit=limit
                )
                
                results = await self.memory_service.search_memory(memory_query)
                
                if results.chunks:
                    memory_content = "\n".join([chunk.content for chunk in results.chunks[:limit]])
                    ctx.deps.memory_chunks.extend([chunk.content for chunk in results.chunks[:limit]])
                    return f"Found {len(results.chunks)} relevant memories:\n{memory_content}"
                else:
                    return "No relevant memories found"
                    
            except Exception as e:
                logger.error(f"Memory search failed: {e}")
                return f"Memory search error: {str(e)}"
        
        return search_memory
    
    def _create_mcp_tool_caller(self) -> Tool:
        """Create tool for calling MCP tools"""
        async def call_mcp_tool(ctx: RunContext[AgentContext], tool_name: str, arguments: Dict[str, Any]) -> str:
            """Execute MCP tools for enhanced functionality"""
            if not self.mcp_client:
                return "MCP client not available"
            
            try:
                result = await self.mcp_client.call_tool(
                    tool_name=tool_name,
                    arguments=arguments
                )
                
                ctx.deps.session_data['last_mcp_tool'] = tool_name
                
                return f"MCP tool '{tool_name}' executed successfully: {result}"
                
            except Exception as e:
                logger.error(f"MCP tool call failed: {e}")
                return f"MCP tool error: {str(e)}"
        
        return call_mcp_tool
    
    async def process_conversation(self, request: StreamingRequest) -> StructuredResponse:
        """Process conversation using PydanticAI agent with full context"""
        if not self._initialized:
            raise RuntimeError("PydanticAI service not initialized")
        
        # Create agent context
        context = AgentContext(
            user_id=request.user_id,
            conversation_id=request.conversation_id or f"conv_{datetime.now().isoformat()}",
            session_data={
                "use_memory": request.use_memory,
                "mcp_tools": request.mcp_tools or [],
                "message": request.message
            }
        )
        
        try:
            # Run the agent with context
            result = await self.agent.run(
                user_prompt=request.message,
                deps=context
            )
            
            # The result.output is already a StructuredResponse from PydanticAI
            structured_response = result.output
            
            # Enhance with additional context information
            structured_response.tools_used.extend([
                tool for tool in ["memory_search", "chunk_analysis", "mcp_tools"] 
                if tool in str(context.session_data)
            ])
            
            # Add evidence from memory chunks
            if context.memory_chunks:
                for chunk in context.memory_chunks:
                    evidence = Evidence(
                        source_type="memory",
                        content=chunk[:200] + "..." if len(chunk) > 200 else chunk,
                        relevance_score=0.8,  # Default relevance
                        metadata={"source": "conversation_memory"}
                    )
                    structured_response.evidence.append(evidence)
            
            return structured_response
            
        except Exception as e:
            logger.error(f"PydanticAI conversation processing failed: {e}")
            # Return structured error response
            return StructuredResponse(
                content=f"I encountered an error while processing your request: {str(e)}",
                task_type=TaskType.QUESTION_ANSWERING,
                confidence=Confidence(
                    score=0.0,
                    reasoning="Error occurred during processing",
                    factors=["system_error", "processing_failure"]
                ),
                evidence=[
                    Evidence(
                        source_type="reasoning",
                        content=f"Error details: {str(e)}",
                        relevance_score=1.0,
                        metadata={"error": True}
                    )
                ],
                reasoning_chain=[f"Error encountered: {str(e)}"],
                suggestions=["Please try rephrasing your request", "Check system logs for details"]
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of PydanticAI service"""
        health = {
            "service": "pydantic_ai",
            "initialized": self._initialized,
            "model_available": self.model is not None,
            "agent_available": self.agent is not None,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.model:
            health["model_type"] = type(self.model).__name__
            
        if hasattr(self.settings.aws, 'bedrock_chat_model'):
            health["configured_model"] = self.settings.aws.bedrock_chat_model
        
        return health
    
    async def cleanup(self):
        """Clean up PydanticAI service resources"""
        logger.info("Cleaning up PydanticAI service")
        
        if self.agent:
            # PydanticAI agents don't typically need explicit cleanup
            pass
        
        self.model = None
        self.agent = None
        self.memory_service = None
        self.mcp_client = None
        self._initialized = False
        
        logger.info("PydanticAI service cleanup completed")


# Global service instance
_pydantic_ai_service = None


async def get_pydantic_ai_service(settings: Settings = None) -> PydanticAIService:
    """Get or create PydanticAI service instance"""
    global _pydantic_ai_service
    
    if _pydantic_ai_service is None:
        if settings is None:
            from config.settings import get_settings
            settings = get_settings()
        
        _pydantic_ai_service = PydanticAIService(settings)
    
    return _pydantic_ai_service


async def cleanup_pydantic_ai_service():
    """Clean up global PydanticAI service instance"""
    global _pydantic_ai_service
    
    if _pydantic_ai_service:
        await _pydantic_ai_service.cleanup()
        _pydantic_ai_service = None
