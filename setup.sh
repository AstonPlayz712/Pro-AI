#!/bin/bash
# Quick Start Script for Private AI Assistant

echo "======================================"
echo "Private AI Assistant - Quick Start"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python..."
python_version=$(python --version 2>&1)
if [[ $? -eq 0 ]]; then
    echo "✓ $python_version"
else
    echo "✗ Python not found. Please install Python 3.10+"
    exit 1
fi

echo ""
echo "Step 1: Creating virtual environment..."
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

echo ""
echo "Step 2: Activating virtual environment..."
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null
if [[ $? -eq 0 ]]; then
    echo "✓ Virtual environment activated"
else
    echo "✗ Failed to activate virtual environment"
    exit 1
fi

echo ""
echo "Step 3: Installing dependencies..."
pip install -q -r requirements.txt
if [[ $? -eq 0 ]]; then
    echo "✓ Dependencies installed"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

echo ""
echo "Step 4: Checking configuration..."
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠ .env created. Please edit it with your API keys:"
    echo "  - OPENAI_API_KEY"
    echo "  - ANTHROPIC_API_KEY"
    echo "  - GOOGLE_API_KEY"
else
    echo "✓ .env file exists"
fi

echo ""
echo "Step 5: Verifying setup..."
python verify_setup.py
if [[ $? -ne 0 ]]; then
    echo "✗ Verification failed"
    exit 1
fi

echo ""
echo "======================================"
echo "✓ Setup Complete!"
echo "======================================"
echo ""
echo "To start the server, run:"
echo "  python main.py"
echo ""
echo "The API will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
