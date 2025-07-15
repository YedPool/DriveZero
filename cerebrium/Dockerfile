# Custom Ollama + Voice Agent Docker Image
FROM ollama/ollama:latest

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-venv \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic links for python commands
RUN ln -s /usr/bin/python3.11 /usr/bin/python
RUN ln -s /usr/bin/pip3 /usr/bin/pip

# Set working directory
WORKDIR /app

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY *.py .

# Create startup script that runs both Ollama and our app
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting Ollama + Voice Agent Container"

# Start Ollama in background
echo "📦 Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama is ready!"
        break
    fi
    echo "   Attempt $i/30 - waiting..."
    sleep 2
done

# Download the model we need
echo "📥 Downloading llama3.2:1b model..."
ollama pull llama3.2:1b

# Start our voice agent
echo "🎤 Starting Voice Agent..."
python main.py

# Clean shutdown
trap 'kill $OLLAMA_PID' EXIT
wait
EOF

RUN chmod +x /app/start.sh

# Expose ports
EXPOSE 8600 11434

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:11434/api/tags || exit 1

# Start both services
CMD ["/app/start.sh"]