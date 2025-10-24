#!/bin/bash
set -e

echo "🔧 Setting up DAA Chatbot Backend..."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

# Display Python version
PYTHON_VERSION=$(python3 --version)
echo "✓ Found $PYTHON_VERSION"

# Navigate to backend directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$BACKEND_DIR"

echo ""
echo "📦 Setting up virtual environment..."

# Create venv if doesn't exist
if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
    echo "  ✓ Virtual environment created"
else
    echo "  ✓ Virtual environment already exists"
fi

# Activate venv
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "  ✓ Dependencies installed"

# Create .env if doesn't exist
echo ""
echo "⚙️  Configuring environment..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "  Creating .env file from .env.example..."
        cp .env.example .env
        echo "  ✓ .env file created - please review and update if needed"
    else
        echo "  ⚠️  No .env.example found - skipping .env creation"
    fi
else
    echo "  ✓ .env file already exists"
fi

# Create storage directories
echo ""
echo "📁 Creating storage directories..."
mkdir -p storage/sqlite
mkdir -p storage/chroma
mkdir -p storage/documents
echo "  ✓ Storage directories created"

# Run database migrations
echo ""
echo "🗄️  Running database migrations..."
alembic upgrade head
echo "  ✓ Database migrations applied"

# Initialize database with default data
echo ""
echo "🔧 Initializing database..."
if [ -f "scripts/init_db.py" ]; then
    python scripts/init_db.py
    echo "  ✓ Database initialized"
else
    echo "  ⚠️  init_db.py not found - skipping database initialization"
fi

# Run setup verification
echo ""
echo "🔍 Verifying setup..."
if [ -f "scripts/check_setup.py" ]; then
    python scripts/check_setup.py
else
    echo "  ⚠️  check_setup.py not found - skipping verification"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the backend server, run:"
echo "  cd $BACKEND_DIR"
echo "  source venv/bin/activate"
echo "  uvicorn api.main:socket_app --reload"
echo ""
