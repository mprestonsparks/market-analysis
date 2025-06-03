# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies including tkinter and curl for healthcheck
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    python3-tk \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements directory first for better caching
COPY requirements/ requirements/

# Install dependencies
RUN pip install --no-cache-dir -r requirements/requirements-core.txt \
    && pip install --no-cache-dir -r requirements/requirements-binance.txt \
    && pip install --no-cache-dir -r requirements/requirements-ibrokers.txt

# Copy the rest of the application
COPY . .

# Add the src directory to Python path
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Create mount point for local volume
VOLUME /app

# Environment variables for API
ARG API_PORT
ENV API_PORT=${API_PORT}
ENV API_HOST=0.0.0.0

# Expose API port
EXPOSE ${API_PORT}

# Set the default command to run the API server
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
