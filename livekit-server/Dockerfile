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

# Download LiveKit server binary during build with validation
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
    # Get latest version for proper filename
    latest_version=$(curl -s https://api.github.com/repos/livekit/livekit/releases/latest | grep '"tag_name"' | cut -d'"' -f4) && \
    echo "Latest LiveKit version: $latest_version" && \
    download_url="https://github.com/livekit/livekit/releases/download/${latest_version}/livekit_${latest_version#v}_linux_${binary_arch}.tar.gz" && \
    echo "Downloading LiveKit server from: $download_url" && \
    curl -L -f --retry 3 --retry-delay 2 "$download_url" -o /tmp/livekit.tar.gz && \
    echo "Download completed, extracting..." && \
    cd /tmp && \
    tar -xzf livekit.tar.gz && \
    ls -la /tmp/ && \
    # Find the livekit-server binary in extracted files
    find /tmp -name "livekit-server" -type f && \
    cp $(find /tmp -name "livekit-server" -type f) /usr/local/bin/livekit-server && \
    chmod +x /usr/local/bin/livekit-server && \
    echo "Binary installation completed, validating..." && \
    ls -la /usr/local/bin/livekit-server && \
    file_size=$(stat -c%s /usr/local/bin/livekit-server) && \
    echo "File size: $file_size bytes" && \
    file /usr/local/bin/livekit-server && \
    echo "Binary validation successful" && \
    ldd /usr/local/bin/livekit-server || echo "ldd failed - static binary or missing dependencies" && \
    rm -rf /tmp/livekit.tar.gz /tmp/livekit_*

# Create directory for config files
RUN mkdir -p /tmp

# Expose LiveKit ports
EXPOSE 7880 7881 50000-60000/udp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:7880/ || exit 1

# Start LiveKit server
CMD ["python", "main.py"]