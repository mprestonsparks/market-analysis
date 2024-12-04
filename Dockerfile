# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies including tkinter
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Add the src directory to Python path
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Create mount point for local volume
VOLUME /app

# Environment variables for API
ENV API_PORT=8000
ENV API_HOST=0.0.0.0

# Expose API port
EXPOSE 8000

# Set the default command to run the API server
CMD ["python", "src/run_api.py"]
