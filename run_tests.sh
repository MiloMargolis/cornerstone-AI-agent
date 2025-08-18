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
export SUPABASE_URL="https://test.supabase.co"
export SUPABASE_KEY="test_key"
export AGENT_PHONE_NUMBER="+1987654321"
export OPENAI_MODEL="gpt-4o-mini"
export MOCK_TELNX="1"

# OpenAI API Key setup
echo "🤖 Setting up OpenAI API key..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set in environment"
    echo "   To run integration tests with real OpenAI API, set your key:"
    echo "   export OPENAI_API_KEY='your_openai_api_key_here'"
    echo "   Or add it to your .env file"
    echo ""
    echo "   For now, using test key for mocked tests only..."
    export OPENAI_API_KEY="test_key"
    SKIP_INTEGRATION_TESTS=true
else
    echo "✅ OpenAI API key found in environment"
    SKIP_INTEGRATION_TESTS=false
fi

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

# Run unit tests (mocked)
echo "🧪 Running unit tests (mocked)..."
echo "  → Testing app.py (SMS Handler)..."
python -m pytest tests/test_app.py -v --cov=src.app --cov-report=term-missing

echo "  → Testing follow_up_handler.py..."
python -m pytest tests/test_follow_up_handler.py -v --cov=src.follow_up_handler --cov-report=term-missing

echo "  → Testing outreach_handler.py..."
python -m pytest tests/test_outreach_handler.py -v --cov=src.outreach_handler --cov-report=term-missing

echo "  → Testing utility modules..."
python -m pytest tests/test_utils/ -v --cov=src.utils --cov-report=term-missing

# Run integration tests (real OpenAI API)
if [ "$SKIP_INTEGRATION_TESTS" = false ]; then
    echo "🤖 Running OpenAI integration tests (real API)..."
    echo "  → Testing extract_lead_info function..."
    python -m pytest tests/test_openai_integration.py::TestOpenAIIntegration::test_extract_lead_info_complete_information -v -s
    
    echo "  → Testing generate_response function..."
    python -m pytest tests/test_openai_integration.py::TestOpenAIIntegration::test_generate_response_initial_contact -v -s
    
    echo "  → Testing robotic language detection..."
    python -m pytest tests/test_openai_integration.py::TestOpenAIIntegration::test_generate_response_no_robotic_confirmation -v -s
    
    echo "  → Running all integration tests..."
    python -m pytest tests/test_openai_integration.py -v -s --tb=short
else
    echo "⏭️  Skipping OpenAI integration tests (no API key)"
    echo "   To run integration tests, set OPENAI_API_KEY environment variable"
fi

# Generate overall coverage report
echo "📊 Generating coverage report..."
python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

echo ""
echo "✅ Tests completed!"
echo "📊 Check htmlcov/index.html for detailed coverage report."

if [ "$SKIP_INTEGRATION_TESTS" = true ]; then
    echo ""
    echo "🎉 To run integration tests with real OpenAI API:"
    echo "   1. Get your OpenAI API key from https://platform.openai.com/api-keys"
    echo "   2. Set the environment variable:"
    echo "      export OPENAI_API_KEY='your_key_here'"
    echo "   3. Run the script again"
    echo ""
    echo "   Or add it to your .env file:"
    echo "      OPENAI_API_KEY=your_key_here"
fi

echo "🎉 All done!"
