# Base image - Python 3.11 slim
FROM python:3.11-slim

# Prevents Python from writing .pyc files and buffering output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create necessary directories
RUN mkdir -p data logs images

# Expose port 8000 (FastAPI default)
EXPOSE 8000

# Run FastAPI application
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}