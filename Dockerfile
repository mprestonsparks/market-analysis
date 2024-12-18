# Build stage for Python dependencies
FROM python:3.10-slim as python-base

WORKDIR /app
COPY pyproject.toml .

RUN pip install --no-cache-dir .[test,dev]

# Test stage for JavaScript tests
FROM node:18-slim as js-test

WORKDIR /app
COPY tests/infrastructure/package*.json ./
RUN npm install

COPY tests/infrastructure/ tests/infrastructure/
COPY tests/infrastructure/babel.config.js ./

CMD ["npm", "run", "test:infrastructure"]

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
