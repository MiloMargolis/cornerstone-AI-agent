#!/bin/bash

# Local test runner script for CornerStone AI Agent
# This script sets up the environment and runs tests locally

set -e

echo "🧪 Running CornerStone AI Agent Tests Locally"
echo "============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please create one first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r src/requirements.txt"
    echo "   pip install -r requirements-dev.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r src/requirements.txt
pip install -r requirements-dev.txt

# Set up test environment variables
echo "🌍 Setting up test environment variables..."
export TELNYX_API_KEY="test_key"
export TELNYX_PHONE_NUMBER="+1234567890"
export OPENAI_API_KEY="test_key"
export SUPABASE_URL="https://test.supabase.co"
export SUPABASE_KEY="test_key"
export AGENT_PHONE_NUMBER="+1987654321"
export OPENAI_MODEL="gpt-4o-mini"
export MOCK_TELNX="1"

# Run linting first
echo "🔍 Running code linting..."
echo "  → Black formatting check..."
black --check --diff src/ || echo "❌ Black formatting issues found"

echo "  → isort import sorting check..."
isort --check-only --diff src/ || echo "❌ Import sorting issues found"

echo "  → Flake8 linting..."
flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 src/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Run security checks
echo "🔒 Running security checks..."
echo "  → Bandit security linting..."
bandit -r src/ || echo "⚠️  Security issues found"

echo "  → Safety dependency vulnerability check..."
safety scan --file src/requirements.txt || echo "⚠️  Vulnerable dependencies found"

# Run tests
echo "🧪 Running unit tests..."
echo "  → Testing app.py (SMS Handler)..."
python -m pytest tests/test_app.py -v --cov=src.app --cov-report=term-missing

echo "  → Testing follow_up_handler.py..."
python -m pytest tests/test_follow_up_handler.py -v --cov=src.follow_up_handler --cov-report=term-missing

echo "  → Testing outreach_handler.py..."
python -m pytest tests/test_outreach_handler.py -v --cov=src.outreach_handler --cov-report=term-missing

echo "  → Testing utility modules..."
python -m pytest tests/test_utils/ -v --cov=src.utils --cov-report=term-missing

# Generate overall coverage report
echo "📊 Generating coverage report..."
python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

echo ""
echo "✅ Tests completed! Check htmlcov/index.html for detailed coverage report."
echo "🎉 All done!"
