#!/bin/bash

# Release Preparation Script for PydanticAI Workflow System v1.0.0
# This script performs final checks and preparations for the first release

echo "🚀 Preparing PydanticAI Workflow System for Release v1.0.0"
echo "=" * 60

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $2 -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
    fi
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Must be run from project root directory${NC}"
    exit 1
fi

echo "📋 Pre-release Checklist:"
echo "------------------------"

# 1. Check project structure
echo "1. Checking project structure..."
required_files=(
    "pyproject.toml"
    "README.md"
    "LICENSE"
    "CHANGELOG.md"
    ".env.example"
    "main.py"
    "demo.py"
    "config/settings.py"
    "config/mcp_servers.yaml"
    "services/workflow_orchestrator.py"
    "services/bedrock_chat.py"
    "services/bedrock_embedding.py"
    "services/mcp_client.py"
)

missing_files=0
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✅${NC} $file"
    else
        echo -e "  ${RED}❌${NC} $file (missing)"
        missing_files=$((missing_files + 1))
    fi
done

print_status "Project structure" $missing_files

# 2. Check for leftover development files
echo "2. Checking for leftover development files..."
dev_files=(
    "**/workflow_orchestrator_enhanced.py"
    "**/bedrock_chat_enhanced.py"
    "**/bedrock_embedding_enhanced.py"
    "**/mcp_client_enhanced.py"
    "**/demo_enhanced.py"
    "**/*_enhanced.py"
    "**/BEDROCK_INTEGRATION_COMPLETE.md"
    "**/CLEANUP_SUCCESS.md"
    "**/TRANSFORMATION_SUCCESS.md"
)

leftover_count=0
for pattern in "${dev_files[@]}"; do
    if find . -name "$pattern" -type f 2>/dev/null | grep -q .; then
        echo -e "  ${RED}❌${NC} Found leftover files: $pattern"
        leftover_count=$((leftover_count + 1))
    fi
done

if [ $leftover_count -eq 0 ]; then
    echo -e "  ${GREEN}✅${NC} No leftover development files found"
fi

print_status "Development cleanup" $leftover_count

# 3. Check version consistency
echo "3. Checking version consistency..."
version_issues=0

# Check pyproject.toml version
pyproject_version=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
echo "  pyproject.toml version: $pyproject_version"

# Check __init__.py version
init_version=$(grep '__version__ = ' config/__init__.py | cut -d'"' -f2)
echo "  config/__init__.py version: $init_version"

if [ "$pyproject_version" != "$init_version" ]; then
    echo -e "  ${RED}❌${NC} Version mismatch between pyproject.toml and config/__init__.py"
    version_issues=1
else
    echo -e "  ${GREEN}✅${NC} Versions are consistent: $pyproject_version"
fi

print_status "Version consistency" $version_issues

# 4. Check for clean codebase
echo "4. Checking for clean codebase..."
code_issues=0

# Check for TODO/FIXME comments
todo_count=$(find . -name "*.py" -exec grep -l "TODO\|FIXME" {} \; | wc -l)
if [ $todo_count -gt 0 ]; then
    echo -e "  ${YELLOW}⚠️${NC} Found $todo_count files with TODO/FIXME comments"
fi

# Check for import issues
echo "  Checking imports..."
python -c "
import sys
sys.path.append('.')
try:
    from config.settings import get_settings
    from services.workflow_orchestrator import WorkflowOrchestrator
    from services.bedrock_chat import get_chat_service
    from services.bedrock_embedding import get_embedding_service
    from services.mcp_client import get_mcp_client
    print('  ✅ All core imports successful')
except Exception as e:
    print(f'  ❌ Import error: {e}')
    exit(1)
"

import_result=$?
if [ $import_result -ne 0 ]; then
    code_issues=1
fi

print_status "Code quality" $code_issues

# 5. Check configuration files
echo "5. Checking configuration files..."
config_issues=0

# Check .env.example
if grep -q "MCP__SERVER_URL" .env.example; then
    echo -e "  ${RED}❌${NC} .env.example contains legacy MCP settings"
    config_issues=1
fi

# Check mcp_servers.yaml is not empty
if [ ! -s "config/mcp_servers.yaml" ]; then
    echo -e "  ${RED}❌${NC} config/mcp_servers.yaml is empty"
    config_issues=1
else
    echo -e "  ${GREEN}✅${NC} config/mcp_servers.yaml has content"
fi

print_status "Configuration files" $config_issues

# 6. Check documentation
echo "6. Checking documentation..."
doc_issues=0

# Check README.md has proper title
if ! grep -q "PydanticAI Workflow System" README.md; then
    echo -e "  ${RED}❌${NC} README.md missing proper title"
    doc_issues=1
fi

# Check CHANGELOG.md exists and has v1.0.0
if ! grep -q "\[1.0.0\]" CHANGELOG.md; then
    echo -e "  ${RED}❌${NC} CHANGELOG.md missing v1.0.0 entry"
    doc_issues=1
fi

print_status "Documentation" $doc_issues

# Final summary
echo ""
echo "🎯 Release Readiness Summary:"
echo "=============================="

total_issues=$((missing_files + leftover_count + version_issues + code_issues + config_issues + doc_issues))

if [ $total_issues -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed! Ready for release v1.0.0${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run final tests: python -m pytest"
    echo "2. Build package: python -m build"
    echo "3. Create git tag: git tag v1.0.0"
    echo "4. Push to repository: git push origin v1.0.0"
    exit 0
else
    echo -e "${RED}❌ Found $total_issues issues that need to be resolved before release${NC}"
    exit 1
fi
