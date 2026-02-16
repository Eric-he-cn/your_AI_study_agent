#!/bin/bash
# Quick start script for Course Learning Agent

echo "================================================"
echo "Course Learning Agent - Quick Start"
echo "================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file and add your API keys:"
    echo "   - OPENAI_API_KEY=your_api_key_here"
    echo ""
    read -p "Press Enter to continue after editing .env file..."
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"
echo ""

# Create data directory
mkdir -p data/workspaces
echo "✅ Created data directory"
echo ""

echo "================================================"
echo "Setup Complete! 🎉"
echo "================================================"
echo ""
echo "To start the application:"
echo ""
echo "1. Start the backend (in one terminal):"
echo "   python backend/api.py"
echo ""
echo "2. Start the frontend (in another terminal):"
echo "   streamlit run frontend/streamlit_app.py"
echo ""
echo "3. Open your browser and go to:"
echo "   http://localhost:8501"
echo ""
echo "For detailed usage instructions, see USAGE.md"
echo "================================================"
