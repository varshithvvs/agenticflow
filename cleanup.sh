#!/usr/bin/env bash
# PydanticAI Agentic Workflow System v1.0.0 - Pre-shipping Cleanup Script
# This script prepares the repository for production deployment

set -e

echo "🧹 PydanticAI Agentic Workflow System - Pre-shipping Cleanup"
echo "============================================================"

# Step 1: Remove Python cache files
echo "🗑️ Removing Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
echo "✅ Python cache files removed"

# Step 2: Remove log files
echo "🗑️ Removing development log files..."
rm -f logs/*.log 2>/dev/null || true
echo "✅ Log files removed"

# Step 3: Remove temporary and backup files
echo "🗑️ Removing temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.bak" -delete 2>/dev/null || true
find . -name "*~" -delete 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true
echo "✅ Temporary files removed"

# Step 4: Remove development vector store data
echo "🗑️ Removing development vector store data..."
rm -f data/faiss_index.index data/faiss_index.metadata 2>/dev/null || true
echo "✅ Development vector store removed"

# Step 5: Remove test cache
echo "🗑️ Removing test cache..."
rm -rf .pytest_cache 2>/dev/null || true
echo "✅ Test cache removed"

# Step 6: File count summary
echo ""
echo "📊 Final repository statistics:"
total_files=$(find . -type f ! -path "./.git/*" ! -path "./.venv/*" | wc -l)
python_files=$(find . -name "*.py" ! -path "./.venv/*" | wc -l)
doc_files=$(find . -name "*.md" | wc -l)
config_files=$(find . -name "*.yaml" -o -name "*.toml" -o -name "*.yml" | wc -l)

echo "  📄 Total files: $total_files"
echo "  🐍 Python files: $python_files"
echo "  📋 Documentation: $doc_files"
echo "  ⚙️ Configuration: $config_files"

echo ""
echo "✅ Repository cleaned and ready for production shipping!"
echo "🚀 PydanticAI Agentic Workflow System v1.0.0 is production-ready"
