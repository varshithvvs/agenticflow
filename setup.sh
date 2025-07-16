#!/bin/bash

# PydanticAI Workflow System - UV Setup Script

echo "🚀 PydanticAI Workflow System - Setup with UV"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if Python 3.11+ is available
echo ""
print_info "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    echo "Python version: $PYTHON_VERSION"
    
    # Check if version is 3.11+
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
        print_status "Python 3.11+ detected"
    else
        print_warning "Python 3.11+ recommended (current: $PYTHON_VERSION)"
    fi
else
    print_error "Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check for UV package manager
echo ""
print_info "Checking for UV package manager..."
if command -v uv &> /dev/null; then
    UV_VERSION=$(uv --version | cut -d' ' -f2)
    print_status "UV found (version: $UV_VERSION)"
else
    print_error "UV not found. Please install UV first:"
    print_info "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Setup with UV
print_info "Using UV for fast package management..."

# Create and activate virtual environment
echo ""
print_info "Setting up virtual environment..."
if [ ! -d ".venv" ]; then
    print_info "Creating virtual environment with UV..."
    uv venv
    print_status "Virtual environment created with UV"
else
    print_status "Virtual environment already exists"
fi

# UV automatically manages the virtual environment
print_status "UV virtual environment ready"

# Install dependencies
echo ""
print_info "Installing dependencies..."
print_info "This may take a few minutes for ML libraries..."

print_info "Using UV for fast installation..."

# Install all dependencies at once with UV
uv sync
print_status "All dependencies installed with UV"

# Create necessary directories
echo ""
print_info "Creating project directories..."
mkdir -p data logs
print_status "Data and logs directories created"

# Setup environment file
echo ""
print_info "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_status "Environment file created from template"
    print_warning "Please edit .env file with your specific configuration"
else
    print_status "Environment file already exists"
fi

# Run installation test
echo ""
print_info "Running installation tests..."
uv run python test_installation.py

echo ""
print_status "Setup completed successfully!"
echo ""
echo "🎯 Next Steps:"
echo "  1. Edit .env file with your configuration"
if [ "$USE_UV" = true ]; then
    echo "  2. Run: uv run python demo.py (for a complete demo)"
    echo "  3. Run: uv run python main.py (to start the server)"
else
    echo "  2. Run: python3 demo.py (for a complete demo)"
    echo "  3. Run: python3 main.py (to start the server)"
fi
echo "  4. Visit: http://localhost:8000/docs (for API docs)"
echo ""
echo "🐳 Docker Alternative:"
echo "  Run: docker-compose up -d (starts all services)"
echo ""
echo "⚡ UV Commands (if using UV):"
if [ "$USE_UV" = true ]; then
    echo "  uv sync              # Install/update dependencies"
    echo "  uv sync --group dev  # Install dev dependencies"
    echo "  uv run <command>     # Run commands in virtual environment"
    echo "  uv add <package>     # Add new dependency"
    echo "  uv remove <package>  # Remove dependency"
    echo "  uv lock              # Update lock file"
else
    echo "  Install UV for faster package management:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
fi
echo ""
echo "📚 Documentation:"
echo "  See README.md for detailed usage instructions"
echo ""
print_status "Happy coding with PydanticAI Workflow System! 🚀"
