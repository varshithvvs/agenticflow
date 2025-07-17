#!/usr/bin/env python3
"""
Start the PydanticAI Agentic Workflow System
Pure PydanticAI implementation with dynamic MCP servers and Bedrock integration
"""

import uvicorn
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Start the PydanticAI Agentic Workflow System server"""
    print("🚀 Starting PydanticAI Agentic Workflow System...")
    print("📍 Server will be available at: http://127.0.0.1:8000")
    print("📖 API Documentation: http://127.0.0.1:8000/docs")
    print("🎯 Pure PydanticAI agentic workflows with MCP and Bedrock integration")
    print("-" * 60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
