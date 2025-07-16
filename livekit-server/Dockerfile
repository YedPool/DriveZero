# LiveKit Server Docker Image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Download LiveKit server binary during build
RUN curl -L https://github.com/livekit/livekit/releases/latest/download/livekit-server_linux_amd64 \
    -o /usr/local/bin/livekit-server && \
    chmod +x /usr/local/bin/livekit-server

# Create directory for config files
RUN mkdir -p /tmp

# Expose LiveKit ports
EXPOSE 7880 7881 50000-60000/udp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:7880/ || exit 1

# Start LiveKit server
CMD ["python", "main.py"]