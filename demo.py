#!/usr/bin/env python3
"""
PydanticAI Workflow System Demo
Showcases full Bedrock integration and dynamic MCP configuration
"""

import asyncio
import logging

from config.settings import get_settings
from services.workflow_orchestrator import get_workflow_orchestrator
from services.bedrock_registry import BedrockModelRegistry
from config.mcp_config import get_mcp_config_manager
from models.mcp_models import StreamingRequest

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_bedrock_models():
    """Demonstrate available Bedrock models"""
    print("\n🚀 Enhanced Bedrock Model Registry Demo")
    print("=" * 50)
    
    registry = BedrockModelRegistry()
    
    # Show embedding models
    embedding_models = registry.get_embedding_models()
    print(f"\n📊 Available Embedding Models ({len(embedding_models)}):")
    for model_id, config in embedding_models.items():
        print(f"  • {model_id}")
        print(f"    Provider: {config['provider'].value}")
        print(f"    Dimension: {config['dimension']}")
        print(f"    Description: {config['description']}")
    
    # Show chat models
    chat_models = registry.get_chat_models()
    print(f"\n💬 Available Chat Models ({len(chat_models)}):")
    for model_id, config in list(chat_models.items())[:5]:  # Show first 5
        print(f"  • {model_id}")
        print(f"    Provider: {config['provider'].value}")
        print(f"    Max Tokens: {config['max_tokens']}")
        print(f"    Description: {config['description']}")
    
    print(f"    ... and {len(chat_models) - 5} more chat models")
    
    # Show image models
    image_models = registry.get_image_models()
    print(f"\n🎨 Available Image Models ({len(image_models)}):")
    for model_id, config in image_models.items():
        print(f"  • {model_id}")
        print(f"    Provider: {config['provider'].value}")
        print(f"    Description: {config['description']}")


async def demo_mcp_configuration():
    """Demonstrate MCP server configuration management"""
    print("\n🔧 Dynamic MCP Configuration Demo")
    print("=" * 50)
    
    config_manager = get_mcp_config_manager()
    
    # Show current configuration
    config_summary = config_manager.get_config_summary()
    print(f"\n📋 Configuration Summary:")
    print(f"  Config File: {config_summary['config_path']}")
    print(f"  Total Servers: {config_summary['total_servers']}")
    print(f"  Enabled Servers: {config_summary['enabled_servers']}")
    print(f"  Disabled Servers: {config_summary['disabled_servers']}")
    
    print(f"\n📡 Server Details:")
    for name, info in config_summary['servers'].items():
        status = "✅ Enabled" if info['enabled'] else "❌ Disabled"
        print(f"  • {name}: {status}")
        print(f"    Description: {info['description']}")
    
    # Show enabled servers
    enabled_servers = config_manager.get_enabled_servers()
    print(f"\n🟢 Currently Enabled Servers:")
    for server in enabled_servers:
        print(f"  • {server.name}")
        print(f"    Command: {server.command} {' '.join(server.args)}")
        print(f"    Timeout: {server.timeout}s")


async def demo_workflow():
    """Demonstrate enhanced workflow processing"""
    print("\n🌟 Enhanced Workflow Processing Demo")
    print("=" * 50)
    
    settings = get_settings()
    orchestrator = await get_workflow_orchestrator(settings)
    
    try:
        await orchestrator.initialize()
        print("✅ Enhanced orchestrator initialized successfully")
        
        # Get Bedrock models info
        bedrock_info = await orchestrator.get_available_bedrock_models()
        current_embedding = bedrock_info.get('current_embedding_model', 'Unknown')
        current_chat = bedrock_info.get('current_chat_model', 'Unknown')
        
        print(f"\n🧠 Current AI Models:")
        print(f"  Embedding Model: {current_embedding}")
        print(f"  Chat Model: {current_chat}")
        
        # Get MCP server status
        mcp_status = await orchestrator.get_mcp_server_status()
        connected_servers = [name for name, status in mcp_status.items() if status.get('connected', False)]
        
        print(f"\n🔗 MCP Server Status:")
        print(f"  Connected Servers: {len(connected_servers)}")
        for server_name in connected_servers:
            tools_count = mcp_status[server_name].get('tools_count', 0)
            print(f"    • {server_name}: {tools_count} tools available")
        
        # Demo enhanced streaming conversation
        print(f"\n💬 Enhanced Conversation Demo:")
        
        request = StreamingRequest(
            query="Analyze the benefits of using AWS Bedrock for AI workloads",
            content="""
            AWS Bedrock is a fully managed service that offers a choice of high-performing 
            foundation models (FMs) from leading AI companies like AI21 Labs, Anthropic, 
            Cohere, Meta, Stability AI, and Amazon via a single API, along with a broad 
            set of capabilities to build generative AI applications with security, privacy, 
            and responsible AI.
            """,
            use_memory=True,
            mcp_tools=["filesystem"] if "filesystem" in connected_servers else [],
            max_chunk_size=500,
            overlap_size=50
        )
        
        print("Processing enhanced workflow...")
        chunk_count = 0
        async for chunk in orchestrator.stream_conversation(request):
            chunk_count += 1
            if chunk.chunk_type == "status":
                print(f"  📋 Status: {chunk.content}")
            elif chunk.chunk_type == "ai_response":
                print(f"  🤖 AI Response: {chunk.content[:200]}...")
                print(f"     Model: {chunk.metadata.get('model', 'Unknown')}")
            elif chunk.chunk_type == "mcp_result":
                print(f"  🔧 MCP Result: {chunk.metadata.get('tool', 'Unknown')} executed")
            elif chunk.chunk_type == "error":
                print(f"  ❌ Error: {chunk.content}")
        
        print(f"\n✅ Processed {chunk_count} chunks successfully")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")
    finally:
        await orchestrator.cleanup()


async def demo_embedding_comparison():
    """Demonstrate embedding dimension comparison"""
    print("\n📊 Embedding Service Comparison Demo")
    print("=" * 50)
    
    from services.bedrock_embedding import get_embedding_service
    
    embedding_service = await get_embedding_service()
    await embedding_service.initialize()
    
    print(f"🔍 Testing embedding service:")
    print(f"  Model: {embedding_service.model_id}")
    print(f"  Bedrock Working: {embedding_service._bedrock_working}")
    print(f"  Embedding Dimension: {embedding_service.get_embedding_dimension()}")
    
    # Test embedding
    test_text = "This is a test for enhanced Bedrock embedding service"
    embedding = await embedding_service.embed_text(test_text)
    
    print(f"  Test Embedding Generated: {len(embedding)} dimensions")
    print(f"  Sample values: {embedding[:5]}...")
    
    await embedding_service.cleanup()


async def main():
    """Run all demos"""
    print("🚀 Enhanced PydanticAI Workflow System - Complete Demo")
    print("=" * 60)
    
    demos = [
        ("Bedrock Models", demo_bedrock_models),
        ("MCP Configuration", demo_mcp_configuration),
        ("Embedding Service", demo_embedding_comparison),
        ("Workflow Demo", demo_workflow),
    ]
    
    for demo_name, demo_func in demos:
        try:
            print(f"\n▶️  Running {demo_name} Demo...")
            await demo_func()
            print(f"✅ {demo_name} Demo completed successfully")
        except Exception as e:
            print(f"❌ {demo_name} Demo failed: {e}")
            logger.exception(f"Demo {demo_name} failed")
        
        # Small delay between demos
        await asyncio.sleep(1)
    
    print("\n🎉 All demos completed!")
    print("\n📝 Summary:")
    print("  • Enhanced Bedrock integration with 40+ models")
    print("  • Dynamic MCP server configuration via YAML")
    print("  • Automatic fallback for embedding and chat services")
    print("  • Real-time multi-server MCP tool execution")
    print("  • Advanced workflow orchestration with memory")


if __name__ == "__main__":
    asyncio.run(main())
