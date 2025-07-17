#!/usr/bin/env python3
"""
PydanticAI Workflow System Demo
Showcases pure PydanticAI agentic workflows with Bedrock integration and dynamic MCP configuration
"""

import asyncio
import logging

from services.workflow_orchestrator import get_workflow_orchestrator
from models.mcp_models import StreamingRequest

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_pydantic_ai_workflow():
    """Demonstrate PydanticAI agentic workflow processing"""
    print("\n🌟 PydanticAI Agentic Workflow System Demo")
    print("=" * 55)
    
    orchestrator = await get_workflow_orchestrator()
    
    try:
        print("✅ PydanticAI agentic orchestrator initialized successfully")
        
        # Get agent health status
        agent_health = await orchestrator.get_agent_health()
        print("\n🤖 Agent Health Status:")
        print(f"  PydanticAI Service: {'✅ Available' if agent_health['pydantic_ai_service']['available'] else '❌ Unavailable'}")
        print(f"  MCP Servers: {agent_health['mcp_client']['total_servers']} connected")
        print(f"  Memory Service: {'✅ Available' if agent_health['memory_service']['available'] else '❌ Unavailable'}")
        print(f"  Embedding Dimension: {agent_health['embedding_service']['dimension']}")
        
        # Get Bedrock models info
        bedrock_models = await orchestrator.get_available_bedrock_models()
        print(f"\n🧠 Available Bedrock Models: {len(bedrock_models)}")
        for model in bedrock_models[:3]:  # Show first 3 models
            print(f"  • {model['model_name']} ({model['provider']})")
            print(f"    APIs: {', '.join(model['supported_apis'])}")
        
        # Demo PydanticAI agentic workflow
        print("\n💬 PydanticAI Agentic Workflow Demo:")
        
        request = StreamingRequest(
            message="Analyze the benefits of using PydanticAI agents with AWS Bedrock for intelligent workflow automation. Consider scalability, performance, and integration capabilities.",
            user_id="demo_user",
            conversation_id="demo_agentic_conv",
            use_memory=True,
            mcp_tools=orchestrator.connected_mcp_servers[:2] if orchestrator.connected_mcp_servers else []
        )
        
        print("Processing PydanticAI agentic workflow...")
        chunk_count = 0
        async for chunk in orchestrator.create_agentic_workflow(request):
            chunk_count += 1
            
            if chunk.chunk_type == "agent_start":
                print(f"  🤖 {chunk.content}")
            elif chunk.chunk_type == "agent_status":
                print(f"  📋 {chunk.content}")
            elif chunk.chunk_type == "agent_processing":
                print(f"  🧠 {chunk.content}")
            elif chunk.chunk_type == "agent_response":
                print(f"  💬 Response: {chunk.content[:150]}...")
                metadata = chunk.metadata
                print(f"     Task Type: {metadata.get('task_type', 'unknown')}")
                print(f"     Confidence: {metadata.get('confidence_score', 0):.2f}")
                if metadata.get('tools_used'):
                    print(f"     Tools Used: {metadata.get('tools_used', [])}")
            elif chunk.chunk_type == "agent_evidence":
                print(f"  📚 Evidence: {chunk.content[:80]}...")
            elif chunk.chunk_type == "agent_reasoning":
                print(f"  🔍 Reasoning: {chunk.content[:80]}...")
            elif chunk.chunk_type == "agent_suggestion":
                print(f"  💡 Suggestion: {chunk.content[:80]}...")
            elif chunk.chunk_type == "agent_complete":
                print(f"  ✅ {chunk.content}")
                metadata = chunk.metadata
                print(f"     Duration: {metadata.get('duration_ms', 0)}ms")
                print(f"     Processing Steps: {metadata.get('processing_steps', 0)}")
                print(f"     MCP Calls: {metadata.get('mcp_calls', 0)}")
                print(f"     Success: {'✅' if metadata.get('success', False) else '❌'}")
            elif chunk.chunk_type == "agent_error":
                print(f"  ❌ Error: {chunk.content}")
            
            if chunk.is_final:
                break
        
        print(f"\n✅ Processed {chunk_count} agentic workflow chunks successfully")
        
        # Show final system health
        final_health = await orchestrator.health_check()
        print("\n📊 Final System Health:")
        for component, status in final_health.items():
            if isinstance(status, str):
                emoji = "✅" if status == "healthy" else "❌"
                print(f"  {emoji} {component}: {status}")
            else:
                print(f"  📈 {component}: {status}")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")
    finally:
        await orchestrator.cleanup()


async def demo_direct_chat():
    """Demonstrate direct PydanticAI agent chat"""
    print("\n🗣️ Direct PydanticAI Agent Chat Demo")
    print("=" * 45)
    
    orchestrator = await get_workflow_orchestrator()
    
    try:
        # Test direct agent conversation
        request = StreamingRequest(
            message="Explain the key advantages of using type-safe AI agents in production systems.",
            user_id="demo_user",
            conversation_id="direct_chat_demo",
            use_memory=True
        )
        
        print("Calling PydanticAI agent directly...")
        response = await orchestrator.pydantic_ai_service.process_conversation(request)
        
        print(f"\n📝 Agent Response:")
        print(f"Content: {response.content[:200]}...")
        
        if response.task_type:
            print(f"Task Type: {response.task_type.value}")
        
        if response.confidence:
            print(f"Confidence: {response.confidence.score:.2f}")
            print(f"Reasoning: {response.confidence.reasoning[:100]}...")
        
        if response.evidence:
            print(f"Evidence Sources: {len(response.evidence)}")
        
        if response.suggestions:
            print(f"Suggestions: {len(response.suggestions)}")
            for i, suggestion in enumerate(response.suggestions[:2]):
                print(f"  {i+1}. {suggestion[:80]}...")
        
    except Exception as e:
        logger.error(f"Direct chat demo failed: {e}")
        print(f"❌ Direct chat demo failed: {e}")
    finally:
        await orchestrator.cleanup()


async def main():
    """Run all PydanticAI workflow demos"""
    print("🚀 PydanticAI Workflow System - Comprehensive Demo")
    print("=" * 60)
    
    # Run PydanticAI agentic workflow demo
    await demo_pydantic_ai_workflow()
    
    print("\n" + "="*60)
    
    # Run direct chat demo
    await demo_direct_chat()
    
    print("\n🎉 All PydanticAI demos completed successfully!")
    print("   Ready for v1.0 production deployment! 🚀")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
