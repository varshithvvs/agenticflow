#!/bin/bash

# PydanticAI Workflow System Startup Script (UV Only)

echo "🚀 Starting PydanticAI Workflow System..."

# Check for UV
if ! command -v uv &> /dev/null; then
    echo "❌ UV is required but not installed."
    echo "📦 Please install UV: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "⚡ Using UV for package management..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# UV workflow
echo "🔧 Setting up UV environment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating UV virtual environment..."
    uv venv
fi

# Install dependencies
echo "📥 Installing dependencies with UV..."
uv sync

# Create necessary directories
mkdir -p data logs

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.example .env 2>/dev/null || true
    echo "✅ Please edit .env file with your configuration"
fi

# Run the application
echo "🎯 Starting the application with UV..."
uv run python main.py
