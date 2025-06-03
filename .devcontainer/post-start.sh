#!/bin/bash

# Market Analysis Post-Start Script
# This script runs every time the container starts

set -e

echo "🔄 Starting Market Analysis services..."

# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================

# Set up environment variables
export PYTHONPATH=/workspaces/market-analysis
export DATABASE_URL=postgresql+psycopg2://airflow:airflow@host.docker.internal:5432/market_analysis
export VAULT_ADDR=http://host.docker.internal:8200

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# =============================================================================
# SERVICE HEALTH CHECKS
# =============================================================================

echo "🏥 Performing service health checks..."

# Check PostgreSQL
if pg_isready -h host.docker.internal -p 5432 -U airflow >/dev/null 2>&1; then
    echo "✅ PostgreSQL is healthy"
else
    echo "⚠️  PostgreSQL is not responding"
fi

# Check Vault
if curl -s http://host.docker.internal:8200/v1/sys/health >/dev/null 2>&1; then
    echo "✅ Vault is healthy"
else
    echo "⚠️  Vault is not responding"
fi

# =============================================================================
# DATABASE SETUP
# =============================================================================

echo "🗄️ Setting up database..."

# Wait for PostgreSQL to be available
echo "⏳ Waiting for PostgreSQL..."
until pg_isready -h host.docker.internal -p 5432 -U airflow; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done

# Check if market_analysis database exists and create if needed
echo "📝 Checking market_analysis database..."
if ! psql -h host.docker.internal -U airflow -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='market_analysis'" | grep -q 1; then
    echo "🔧 Creating market_analysis database..."
    psql -h host.docker.internal -U airflow -d postgres -c "CREATE DATABASE market_analysis;"
    echo "✅ market_analysis database created"
else
    echo "✅ market_analysis database exists"
fi

# Run database migrations if alembic is configured
if [ -f "alembic.ini" ] && [ -d "alembic" ]; then
    echo "🔄 Running database migrations..."
    alembic upgrade head || echo "⚠️  Migration failed or no migrations to run"
fi

# =============================================================================
# VAULT INTEGRATION
# =============================================================================

echo "🔐 Setting up Vault integration..."

export VAULT_ADDR=http://host.docker.internal:8200
export VAULT_TOKEN=dev-token

# Wait for Vault to be ready
until curl -s $VAULT_ADDR/v1/sys/health > /dev/null; do
    echo "Vault is unavailable - sleeping"
    sleep 2
done

# Test Vault connectivity and setup secrets
if vault auth -method=token >/dev/null 2>&1; then
    echo "✅ Vault authentication successful"
    
    # Create market analysis secrets if they don't exist
    vault kv get secret/market-analysis >/dev/null 2>&1 || {
        echo "📝 Setting up market analysis secrets..."
        vault kv put secret/market-analysis \
            database_url="$DATABASE_URL" \
            secret_key="dev-secret-key-change-in-production" \
            alpha_vantage_api_key="" \
            finnhub_api_key="" \
            polygon_api_key=""
        echo "✅ Market analysis secrets created"
    }
else
    echo "⚠️  Vault authentication failed"
fi

# =============================================================================
# APPLICATION STARTUP
# =============================================================================

echo "🚀 Preparing application startup..."

# Install/update dependencies if requirements have changed
if [ -f "requirements-dev.txt" ]; then
    echo "📦 Checking Python dependencies..."
    pip install --user -q -r requirements-dev.txt
fi

# Run code quality checks
echo "🔍 Running code quality checks..."

# Check if main application files exist
if [ -f "main.py" ]; then
    echo "✅ Main application file found"
    
    # Validate Python syntax
    python -m py_compile main.py && echo "✅ main.py syntax OK" || echo "❌ main.py has syntax errors"
else
    echo "⚠️  main.py not found"
fi

# Check FastAPI application structure
if [ -d "app" ]; then
    echo "✅ Application directory structure found"
    
    # Validate app module syntax
    for py_file in $(find app -name "*.py" -type f); do
        python -m py_compile "$py_file" && echo "✅ $py_file syntax OK" || echo "❌ $py_file has syntax errors"
    done
else
    echo "⚠️  Application directory not found"
fi

# =============================================================================
# API SERVICE MANAGEMENT
# =============================================================================

echo "🌐 Managing API service..."

# Function to check if the API is running
is_api_running() {
    curl -s http://localhost:8000/health >/dev/null 2>&1
}

# Check if API is already running
if is_api_running; then
    echo "✅ Market Analysis API is already running"
else
    echo "🔄 Starting Market Analysis API..."
    
    # Start the API in the background
    if [ -f "main.py" ]; then
        nohup uvicorn main:app --reload --host 0.0.0.0 --port 8000 > /logs/market-analysis-api.log 2>&1 &
        
        # Wait for API to start
        echo "⏳ Waiting for API to start..."
        for i in {1..30}; do
            if is_api_running; then
                echo "✅ Market Analysis API started successfully"
                break
            fi
            if [ $i -eq 30 ]; then
                echo "⚠️  API startup timeout"
            fi
            sleep 2
        done
    else
        echo "⚠️  Cannot start API - main.py not found"
    fi
fi

# =============================================================================
# JUPYTER NOTEBOOK SETUP
# =============================================================================

echo "📓 Setting up Jupyter environment..."

# Start Jupyter Lab if not already running
if ! pgrep -f "jupyter-lab" > /dev/null; then
    echo "🚀 Starting Jupyter Lab..."
    nohup jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --notebook-dir=/workspaces/market-analysis > /logs/jupyter-market.log 2>&1 &
    echo "✅ Jupyter Lab started on port 8888"
else
    echo "✅ Jupyter Lab is already running"
fi

# =============================================================================
# DEVELOPMENT ENVIRONMENT STATUS
# =============================================================================

echo ""
echo "📊 Market Analysis Status Summary:"
echo "=================================="

# Service status
echo "🔧 Services:"
echo "   - PostgreSQL: $(pg_isready -h host.docker.internal -p 5432 -U airflow >/dev/null 2>&1 && echo "✅ Connected" || echo "❌ Disconnected")"
echo "   - Vault: $(curl -s http://host.docker.internal:8200/v1/sys/health >/dev/null 2>&1 && echo "✅ Connected" || echo "❌ Disconnected")"
echo "   - Market Analysis API: $(is_api_running && echo "✅ Running" || echo "❌ Stopped")"
echo "   - Jupyter Lab: $(pgrep -f "jupyter-lab" >/dev/null && echo "✅ Running on port 8888" || echo "❌ Not running")"

# Database status
echo ""
echo "🗄️ Database:"
if psql -h host.docker.internal -U airflow -d market_analysis -c '\q' >/dev/null 2>&1; then
    echo "   - market_analysis database: ✅ Accessible"
else
    echo "   - market_analysis database: ❌ Not accessible"
fi

# Application status
echo ""
echo "📱 Application:"
echo "   - Main module: $([ -f "main.py" ] && echo "✅ Found" || echo "❌ Missing")"
echo "   - App directory: $([ -d "app" ] && echo "✅ Found" || echo "❌ Missing")"
echo "   - Tests directory: $([ -d "tests" ] && echo "✅ Found" || echo "❌ Missing")"

# Access information
echo ""
echo "🌐 Access Information:"
echo "   - API Base URL: http://localhost:8000"
echo "   - API Documentation: http://localhost:8000/docs"
echo "   - ReDoc Documentation: http://localhost:8000/redoc"
echo "   - Health Check: http://localhost:8000/health"
echo "   - Jupyter Lab: http://localhost:8888"

# Log locations
echo ""
echo "📝 Log Locations:"
echo "   - API Logs: /logs/market-analysis-api.log"
echo "   - Jupyter Logs: /logs/jupyter-market.log"

echo ""
echo "💡 Quick commands:"
echo "   - 'make help' - Show available commands"
echo "   - 'make run' - Start the development server"
echo "   - 'make test' - Run tests"
echo "   - 'make lint' - Run code quality checks"
echo "   - 'curl http://localhost:8000/health' - Test API health"

echo ""
echo "🎉 Market Analysis environment is ready for development!"