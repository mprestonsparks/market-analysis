#!/bin/bash

# Market Analysis Post-Create Script
# This script runs after the container is created

set -e

echo "🚀 Setting up Market Analysis development environment..."

# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================

# Set up environment variables
export PYTHONPATH=/workspaces/market-analysis
export DATABASE_URL=postgresql+psycopg2://airflow:airflow@host.docker.internal:5432/market_analysis
export VAULT_ADDR=http://host.docker.internal:8200

# =============================================================================
# DIRECTORY STRUCTURE
# =============================================================================

echo "📁 Creating project directory structure..."

# Create main application directories
mkdir -p app
mkdir -p app/api
mkdir -p app/core
mkdir -p app/models
mkdir -p app/services
mkdir -p app/utils
mkdir -p app/schemas

# Create additional directories
mkdir -p tests
mkdir -p tests/api
mkdir -p tests/services
mkdir -p tests/utils
mkdir -p docs
mkdir -p scripts
mkdir -p data
mkdir -p notebooks
mkdir -p config

echo "✅ Directory structure created"

# =============================================================================
# PROJECT CONFIGURATION
# =============================================================================

echo "⚙️ Setting up project configuration..."

# Create pyproject.toml if it doesn't exist
if [ ! -f "pyproject.toml" ]; then
    echo "📝 Creating pyproject.toml..."
    cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "market-analysis"
version = "0.1.0"
description = "Financial market analysis and data processing API"
authors = [
    {name = "Market Analysis Team", email = "team@example.com"},
]
dependencies = [
    "fastapi[all]>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.0",
    "psycopg2-binary>=2.9.0",
    "alembic>=1.12.0",
    "pydantic>=2.4.0",
    "pydantic-settings>=2.0.0",
    "pandas>=2.1.0",
    "numpy>=1.24.0",
    "yfinance>=0.2.0",
    "alpha-vantage>=2.3.0",
    "finnhub-python>=2.4.0",
    "polygon-api-client>=1.12.0",
    "httpx>=0.25.0",
    "python-dotenv>=1.0.0",
    "hvac>=1.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
    "pytest-mock>=3.11.0",
    "black>=23.9.0",
    "ruff>=0.1.0",
    "mypy>=1.6.0",
    "pre-commit>=3.4.0",
    "bandit>=1.7.0",
    "safety>=2.3.0",
]
analysis = [
    "matplotlib>=3.7.0",
    "seaborn>=0.12.0",
    "plotly>=5.17.0",
    "scipy>=1.11.0",
    "scikit-learn>=1.3.0",
    "statsmodels>=0.14.0",
    "arch>=6.2.0",
    "jupyter>=1.0.0",
    "ipython>=8.15.0",
]

[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.ruff]
target-version = "py311"
line-length = 100
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long, handled by black
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]

[tool.mypy]
python_version = "3.11"
check_untyped_defs = true
disallow_any_generics = true
disallow_incomplete_defs = true
disallow_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_return_any = true
strict_equality = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov",
    "--cov-fail-under=80",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow running tests",
    "external: Tests that require external APIs",
]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["app"]
omit = [
    "*/tests/*",
    "*/venv/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
EOF
fi

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    echo "📝 Creating requirements.txt..."
    cat > requirements.txt << 'EOF'
# Core FastAPI dependencies
fastapi[all]>=0.104.0
uvicorn[standard]>=0.24.0

# Database
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
alembic>=1.12.0

# Data validation
pydantic>=2.4.0
pydantic-settings>=2.0.0

# Data processing
pandas>=2.1.0
numpy>=1.24.0

# Financial data APIs
yfinance>=0.2.0
alpha-vantage>=2.3.0
finnhub-python>=2.4.0
polygon-api-client>=1.12.0

# HTTP client
httpx>=0.25.0

# Configuration
python-dotenv>=1.0.0

# Vault integration
hvac>=1.2.0
EOF
fi

# Create requirements-dev.txt if it doesn't exist
if [ ! -f "requirements-dev.txt" ]; then
    echo "📝 Creating requirements-dev.txt..."
    cat > requirements-dev.txt << 'EOF'
# Include base requirements
-r requirements.txt

# Development tools
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
pytest-mock>=3.11.0
black>=23.9.0
ruff>=0.1.0
mypy>=1.6.0
pre-commit>=3.4.0
bandit>=1.7.0
safety>=2.3.0

# Analysis tools
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.17.0
scipy>=1.11.0
scikit-learn>=1.3.0
statsmodels>=0.14.0
arch>=6.2.0
jupyter>=1.0.0
ipython>=8.15.0
EOF
fi

# Install requirements
if [ -f "requirements-dev.txt" ]; then
    echo "📦 Installing Python dependencies..."
    pip install --user -r requirements-dev.txt
fi

echo "✅ Project configuration complete"

# =============================================================================
# FASTAPI APPLICATION SETUP
# =============================================================================

echo "🌐 Setting up FastAPI application..."

# Create main application file
if [ ! -f "main.py" ]; then
    cat > main.py << 'EOF'
"""
Market Analysis API
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title="Market Analysis API",
    description="Financial market analysis and data processing API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Market Analysis API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
fi

# Create core configuration
if [ ! -f "app/core/config.py" ]; then
    mkdir -p app/core
    cat > app/core/config.py << 'EOF'
"""
Application configuration
"""
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Market Analysis API"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database Configuration
    DATABASE_URL: str = "postgresql+psycopg2://airflow:airflow@host.docker.internal:5432/market_analysis"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # External APIs
    ALPHA_VANTAGE_API_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    POLYGON_API_KEY: str = ""
    
    # Vault Configuration
    VAULT_ADDR: str = "http://host.docker.internal:8200"
    VAULT_TOKEN: str = "dev-token"
    
    class Config:
        env_file = ".env"

settings = Settings()
EOF
fi

# Create API routes
if [ ! -f "app/api/routes.py" ]; then
    mkdir -p app/api
    cat > app/api/routes.py << 'EOF'
"""
API routes
"""
from fastapi import APIRouter
from app.api.endpoints import market_data, analysis

router = APIRouter()

router.include_router(market_data.router, prefix="/market", tags=["market-data"])
router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
EOF
fi

# Create sample endpoints
mkdir -p app/api/endpoints
if [ ! -f "app/api/endpoints/market_data.py" ]; then
    cat > app/api/endpoints/market_data.py << 'EOF'
"""
Market data endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import yfinance as yf

router = APIRouter()

@router.get("/quote/{symbol}")
async def get_quote(symbol: str) -> Dict[str, Any]:
    """Get current quote for a symbol"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "symbol": symbol,
            "price": info.get("currentPrice"),
            "change": info.get("regularMarketChange"),
            "change_percent": info.get("regularMarketChangePercent"),
            "volume": info.get("volume"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching data: {str(e)}")

@router.get("/history/{symbol}")
async def get_history(symbol: str, period: str = "1mo") -> Dict[str, Any]:
    """Get historical data for a symbol"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        return {
            "symbol": symbol,
            "period": period,
            "data": hist.to_dict("records")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching data: {str(e)}")
EOF
fi

if [ ! -f "app/api/endpoints/analysis.py" ]; then
    cat > app/api/endpoints/analysis.py << 'EOF'
"""
Analysis endpoints
"""
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

@router.get("/summary/{symbol}")
async def get_analysis_summary(symbol: str) -> Dict[str, Any]:
    """Get analysis summary for a symbol"""
    return {
        "symbol": symbol,
        "analysis": "Sample analysis data",
        "recommendation": "HOLD",
        "confidence": 0.75
    }
EOF
fi

# Create __init__.py files
touch app/__init__.py
touch app/api/__init__.py
touch app/api/endpoints/__init__.py
touch app/core/__init__.py
touch app/models/__init__.py
touch app/services/__init__.py
touch app/utils/__init__.py
touch app/schemas/__init__.py

echo "✅ FastAPI application setup complete"

# =============================================================================
# DATABASE SETUP
# =============================================================================

echo "🗄️ Setting up database configuration..."

# Create Alembic configuration
if [ ! -f "alembic.ini" ]; then
    alembic init alembic
    
    # Update alembic.ini with correct database URL
    sed -i 's|sqlalchemy.url = driver://user:pass@localhost/dbname|sqlalchemy.url = postgresql+psycopg2://airflow:airflow@host.docker.internal:5432/market_analysis|g' alembic.ini
fi

echo "✅ Database configuration complete"

# =============================================================================
# TESTING SETUP
# =============================================================================

echo "🧪 Setting up testing framework..."

# Create pytest configuration (already in pyproject.toml)

# Create sample tests
if [ ! -f "tests/test_main.py" ]; then
    cat > tests/test_main.py << 'EOF'
"""
Tests for main application
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Market Analysis API"
    assert data["version"] == "0.1.0"

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
EOF
fi

# Create __init__.py files for tests
touch tests/__init__.py
touch tests/api/__init__.py
touch tests/services/__init__.py
touch tests/utils/__init__.py

echo "✅ Testing framework setup complete"

# =============================================================================
# DEVELOPMENT TOOLS
# =============================================================================

echo "🛠️ Setting up development tools..."

# Create Makefile
if [ ! -f "Makefile" ]; then
    cat > Makefile << 'EOF'
.PHONY: help install dev test lint format check run clean

help:
	@echo "Available commands:"
	@echo "  install       - Install dependencies"
	@echo "  dev           - Install development dependencies"
	@echo "  test          - Run tests"
	@echo "  lint          - Run linting"
	@echo "  format        - Format code"
	@echo "  check         - Run all checks (lint + test)"
	@echo "  run           - Run the development server"
	@echo "  clean         - Clean cache files"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements-dev.txt

test:
	pytest

lint:
	ruff check .
	mypy .
	bandit -r app/

format:
	black .
	ruff check --fix .

check: lint test

run:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -name "*.pyc" -delete
EOF
fi

# Create .gitignore
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.tox/
.coverage
.coverage.*
.cache
.pytest_cache/
htmlcov/
.hypothesis/

# MyPy
.mypy_cache/
.dmypy.json
dmypy.json

# Ruff
.ruff_cache/

# Environment variables
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite3

# Logs
*.log
logs/

# Data files
data/*.csv
data/*.json
data/*.parquet

# Jupyter Notebooks
.ipynb_checkpoints/
*.ipynb

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
EOF
fi

# Create .env.example
if [ ! -f ".env.example" ]; then
    cat > .env.example << 'EOF'
# Database Configuration
DATABASE_URL=postgresql+psycopg2://airflow:airflow@host.docker.internal:5432/market_analysis

# API Keys (set these for external services)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FINNHUB_API_KEY=your_finnhub_key
POLYGON_API_KEY=your_polygon_key

# Security
SECRET_KEY=your-secret-key-here

# Vault Configuration
VAULT_ADDR=http://host.docker.internal:8200
VAULT_TOKEN=dev-token
EOF
fi

echo "✅ Development tools setup complete"

# =============================================================================
# COMPLETION
# =============================================================================

echo ""
echo "🎉 Market Analysis setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Customize the .env file with your API keys"
echo "   2. Wait for PostgreSQL to be available"
echo "   3. Run 'make run' to start the development server"
echo "   4. Access the API at http://localhost:8000"
echo "   5. View API docs at http://localhost:8000/docs"
echo ""
echo "🔧 Available commands:"
echo "   - 'make help' to see all available commands"
echo "   - 'make test' to run tests"
echo "   - 'make lint' to run linting"
echo "   - 'make format' to format code"
echo "   - 'make run' to start the development server"
echo ""
echo "Happy financial analysis! 📈"