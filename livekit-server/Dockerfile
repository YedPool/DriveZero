# LiveKit Server Docker Image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    file \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Download LiveKit server binary during build with better debugging
RUN echo "System info:" && \
    uname -a && \
    dpkg --print-architecture && \
    arch=$(uname -m) && \
    echo "Detected architecture: $arch" && \
    if [ "$arch" = "x86_64" ]; then \
        binary_arch="amd64"; \
    elif [ "$arch" = "aarch64" ]; then \
        binary_arch="arm64"; \
    else \
        echo "Unsupported architecture: $arch"; exit 1; \
    fi && \
    download_url="https://github.com/livekit/livekit/releases/latest/download/livekit-server_linux_${binary_arch}" && \
    echo "Downloading LiveKit server from: $download_url" && \
    curl -L "$download_url" -o /usr/local/bin/livekit-server && \
    echo "Download completed, file info:" && \
    ls -la /usr/local/bin/livekit-server && \
    file /usr/local/bin/livekit-server && \
    chmod +x /usr/local/bin/livekit-server && \
    echo "Final binary info:" && \
    file /usr/local/bin/livekit-server && \
    ldd /usr/local/bin/livekit-server || echo "ldd failed - static binary or missing dependencies"

# Create directory for config files
RUN mkdir -p /tmp

# Expose LiveKit ports
EXPOSE 7880 7881 50000-60000/udp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:7880/ || exit 1

# Start LiveKit server
CMD ["python", "main.py"]