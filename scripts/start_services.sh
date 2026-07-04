#!/bin/bash

# Multi-Agent Loan Application System - Startup Script

set -e

echo "================================================"
echo "Multi-Agent Agentic AI Loan Application System"
echo "================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your ANTHROPIC_API_KEY"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "🚀 Starting services..."
echo ""

# Create necessary directories
mkdir -p data/applications

# Load environment variables
set -a
source .env
set +a

# Start API server in background
echo "Starting FastAPI server on port 8000..."
python -m uvicorn api.app:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!
echo "✓ API Server PID: $API_PID"

# Wait for API to start
sleep 3

# Start Streamlit UI
echo ""
echo "Starting Streamlit UI on port 8501..."
streamlit run ui/streamlit_app.py --server.port=8501

# Cleanup on exit
trap "kill $API_PID" EXIT
