# Build stage for Python dependencies
FROM python:3.10-slim as python-base

WORKDIR /app

# Copy dependency files
COPY pyproject.toml .
COPY requirements*.txt ./

# Install dependencies
RUN pip install --no-cache-dir .[test,dev]

# JavaScript test base
FROM node:18-slim as js-test-base

WORKDIR /app/tests/infrastructure

# Install JavaScript test dependencies
COPY tests/infrastructure/package*.json ./
RUN npm ci

# Python test stage
FROM python:3.10-slim as python-test

WORKDIR /app

# Copy Python dependencies
COPY --from=python-base /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/

# Default command (can be overridden by docker-compose)
CMD ["pytest"]

# JavaScript test stage
FROM js-test-base as js-test

WORKDIR /app/tests/infrastructure

# Default command (can be overridden by docker-compose)
CMD ["npm", "run", "test:infrastructure"]

# Combined test base (for running all tests)
FROM python:3.10-slim as test-base

WORKDIR /app

# Copy Python dependencies
COPY --from=python-base /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/

# Install Node.js
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install JavaScript test dependencies
COPY tests/infrastructure/.github/package*.json /app/tests/infrastructure/.github/
WORKDIR /app/tests/infrastructure/.github
RUN npm ci
WORKDIR /app

# Default command (can be overridden by docker-compose)
CMD ["sh", "-c", "python -m pytest tests/ && cd tests/infrastructure/.github && npm run test:infrastructure"]

# Production stage
FROM python:3.10-slim

WORKDIR /app

# Copy Python dependencies from base
COPY --from=python-base /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/

# Copy application code
COPY src/ src/
COPY pyproject.toml .

# Create non-root user
RUN useradd -m -r -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
