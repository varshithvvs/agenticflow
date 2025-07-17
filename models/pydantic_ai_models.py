"""
Enhanced PydanticAI Models - Structured AI responses with validation
"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class TaskType(str, Enum):
    """Types of tasks that can be performed"""
    ANALYSIS = "analysis"
    SUMMARIZATION = "summarization"
    CODE_REVIEW = "code_review"
    QUESTION_ANSWERING = "question_answering"
    CREATIVE_WRITING = "creative_writing"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"


class Confidence(BaseModel):
    """Confidence scoring for AI responses"""
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    reasoning: str = Field(..., description="Explanation for the confidence level")
    factors: List[str] = Field(default_factory=list, description="Factors affecting confidence")


class Evidence(BaseModel):
    """Evidence or source information supporting a response"""
    source_type: Literal["memory", "mcp_tool", "knowledge_base", "reasoning"] = Field(
        ..., description="Type of evidence source"
    )
    content: str = Field(..., description="Content of the evidence")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance to the query")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class StructuredResponse(BaseModel):
    """Structured AI response with rich metadata"""
    content: str = Field(..., description="Main response content")
    task_type: TaskType = Field(..., description="Type of task performed")
    confidence: Confidence = Field(..., description="Confidence assessment")
    evidence: List[Evidence] = Field(default_factory=list, description="Supporting evidence")
    tools_used: List[str] = Field(default_factory=list, description="Tools used in processing")
    reasoning_chain: List[str] = Field(default_factory=list, description="Step-by-step reasoning")
    suggestions: List[str] = Field(default_factory=list, description="Follow-up suggestions")
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")


class CodeAnalysis(BaseModel):
    """Structured code analysis response"""
    language: str = Field(..., description="Programming language detected")
    complexity_score: float = Field(..., ge=0.0, le=10.0, description="Code complexity (0-10)")
    issues: List[str] = Field(default_factory=list, description="Identified issues")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    strengths: List[str] = Field(default_factory=list, description="Code strengths")
    security_concerns: List[str] = Field(default_factory=list, description="Security issues")
    performance_notes: List[str] = Field(default_factory=list, description="Performance considerations")
    
    @field_validator('complexity_score')
    @classmethod
    def validate_complexity(cls, v):
        if not 0 <= v <= 10:
            raise ValueError('Complexity score must be between 0 and 10')
        return v


class DocumentSummary(BaseModel):
    """Structured document summary"""
    main_points: List[str] = Field(..., description="Key points from the document")
    abstract: str = Field(..., description="Brief abstract of the content")
    keywords: List[str] = Field(default_factory=list, description="Important keywords")
    sentiment: Literal["positive", "negative", "neutral", "mixed"] = Field(
        ..., description="Overall sentiment"
    )
    word_count: int = Field(..., ge=0, description="Original document word count")
    compression_ratio: float = Field(..., ge=0.0, le=1.0, description="Summary compression ratio")


class WorkflowStep(BaseModel):
    """Individual step in a workflow"""
    step_id: str = Field(..., description="Unique step identifier")
    description: str = Field(..., description="Step description")
    tool_required: Optional[str] = Field(None, description="Tool needed for this step")
    estimated_time: Optional[int] = Field(None, description="Estimated time in seconds")
    dependencies: List[str] = Field(default_factory=list, description="Dependent step IDs")
    status: Literal["pending", "in_progress", "completed", "failed"] = Field(
        default="pending", description="Step status"
    )


class WorkflowPlan(BaseModel):
    """Structured workflow orchestration plan"""
    workflow_id: str = Field(..., description="Unique workflow identifier")
    title: str = Field(..., description="Workflow title")
    description: str = Field(..., description="Workflow description")
    steps: List[WorkflowStep] = Field(..., description="Workflow steps")
    estimated_total_time: int = Field(..., ge=0, description="Total estimated time in seconds")
    complexity: Literal["simple", "moderate", "complex"] = Field(..., description="Workflow complexity")
    success_criteria: List[str] = Field(default_factory=list, description="Success criteria")
    risk_factors: List[str] = Field(default_factory=list, description="Potential risks")


class EnhancedStreamingRequest(BaseModel):
    """Enhanced streaming request with PydanticAI structure"""
    user_id: str = Field(..., description="User identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    message: str = Field(..., description="User message")
    task_type: TaskType = Field(default=TaskType.QUESTION_ANSWERING, description="Type of task")
    expected_format: Literal["text", "structured", "code_analysis", "summary", "workflow"] = Field(
        default="text", description="Expected response format"
    )
    use_memory: bool = Field(default=True, description="Use conversation memory")
    use_mcp: bool = Field(default=True, description="Use MCP tools")
    mcp_tools: Optional[List[str]] = Field(None, description="Specific MCP tools to use")
    max_chunk_size: Optional[int] = Field(1000, description="Maximum chunk size for processing")
    overlap_size: Optional[int] = Field(100, description="Overlap size for chunking")
    require_evidence: bool = Field(default=True, description="Require evidence for claims")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence")


class PydanticAIStreamingChunk(BaseModel):
    """Enhanced streaming chunk with PydanticAI metadata"""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    conversation_id: str = Field(..., description="Conversation identifier")
    content: str = Field(..., description="Chunk content")
    chunk_type: Literal[
        "status", "memory", "content", "mcp_result", "ai_response", 
        "pydantic_ai_response", "structured_response", "error"
    ] = Field(..., description="Type of chunk")
    task_type: Optional[TaskType] = Field(None, description="Task type if applicable")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")
    tools_used: List[str] = Field(default_factory=list, description="Tools used for this chunk")
    evidence_count: int = Field(default=0, ge=0, description="Number of evidence pieces")
    is_final: bool = Field(default=False, description="Whether this is the final chunk")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MultiModalRequest(BaseModel):
    """Multi-modal request supporting text, images, and files"""
    user_id: str = Field(..., description="User identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    text_content: Optional[str] = Field(None, description="Text content")
    image_urls: List[str] = Field(default_factory=list, description="Image URLs to analyze")
    file_paths: List[str] = Field(default_factory=list, description="File paths to process")
    task_type: TaskType = Field(default=TaskType.ANALYSIS, description="Type of task")
    processing_instructions: Optional[str] = Field(None, description="Special processing instructions")
    output_format: Literal["text", "structured", "json", "markdown"] = Field(
        default="structured", description="Desired output format"
    )


class SystemInsight(BaseModel):
    """System-level insights and recommendations"""
    insight_type: Literal["performance", "usage", "error", "optimization", "security"] = Field(
        ..., description="Type of insight"
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="Insight severity")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed description")
    recommendations: List[str] = Field(default_factory=list, description="Recommended actions")
    affected_components: List[str] = Field(default_factory=list, description="Affected system components")
    estimated_impact: str = Field(..., description="Estimated impact if addressed")
    priority_score: float = Field(..., ge=0.0, le=10.0, description="Priority score (0-10)")


class AgentCapability(BaseModel):
    """PydanticAI agent capability description"""
    name: str = Field(..., description="Capability name")
    description: str = Field(..., description="Capability description")
    tools_required: List[str] = Field(default_factory=list, description="Required tools")
    complexity_level: Literal["basic", "intermediate", "advanced", "expert"] = Field(
        ..., description="Complexity level"
    )
    use_cases: List[str] = Field(default_factory=list, description="Common use cases")
    limitations: List[str] = Field(default_factory=list, description="Known limitations")
    performance_metrics: Dict[str, float] = Field(
        default_factory=dict, description="Performance metrics"
    )


class AgentProfile(BaseModel):
    """Complete PydanticAI agent profile"""
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent name")
    version: str = Field(..., description="Agent version")
    description: str = Field(..., description="Agent description")
    capabilities: List[AgentCapability] = Field(default_factory=list, description="Agent capabilities")
    supported_models: List[str] = Field(default_factory=list, description="Supported AI models")
    memory_integration: bool = Field(default=True, description="Memory integration support")
    mcp_integration: bool = Field(default=True, description="MCP integration support")
    max_context_length: int = Field(default=32000, description="Maximum context length")
    specializations: List[str] = Field(default_factory=list, description="Agent specializations")
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
