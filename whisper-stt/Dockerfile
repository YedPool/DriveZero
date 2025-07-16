# Whisper STT Docker Image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Set environment variables
ENV WHISPER_MODEL=base
ENV TRANSFORMERS_CACHE=/app/.cache
ENV XDG_CACHE_HOME=/app/.cache

# Create cache directory
RUN mkdir -p /app/.cache

# Expose FastAPI port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Start FastAPI server
CMD ["python", "main.py"]