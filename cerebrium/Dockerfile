# Custom Ollama + Voice Agent Docker Image
FROM ollama/ollama:latest

# Install Python and system dependencies  
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /app/venv

# Activate virtual environment and upgrade pip
RUN /app/venv/bin/pip install --upgrade pip

# Set working directory
WORKDIR /app

# Copy Python requirements and install dependencies in virtual environment
COPY requirements.txt .
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Update PATH to use virtual environment
ENV PATH="/app/venv/bin:$PATH"

# Copy application code
COPY main.py .
COPY *.py .

# Create startup script that runs both Ollama and our app
RUN echo '#!/bin/bash' > /app/start.sh && \
    echo 'set -e' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo 'echo "🚀 Starting Ollama + Voice Agent Container"' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo '# Start Ollama in background' >> /app/start.sh && \
    echo 'echo "📦 Starting Ollama server..."' >> /app/start.sh && \
    echo 'ollama serve &' >> /app/start.sh && \
    echo 'OLLAMA_PID=$!' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo '# Wait for Ollama to be ready' >> /app/start.sh && \
    echo 'echo "⏳ Waiting for Ollama to be ready..."' >> /app/start.sh && \
    echo 'for i in {1..30}; do' >> /app/start.sh && \
    echo '    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then' >> /app/start.sh && \
    echo '        echo "✅ Ollama is ready!"' >> /app/start.sh && \
    echo '        break' >> /app/start.sh && \
    echo '    fi' >> /app/start.sh && \
    echo '    echo "   Attempt $i/30 - waiting..."' >> /app/start.sh && \
    echo '    sleep 2' >> /app/start.sh && \
    echo 'done' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo '# Download the model we need' >> /app/start.sh && \
    echo 'echo "📥 Downloading llama3.2:1b model..."' >> /app/start.sh && \
    echo 'ollama pull llama3.2:1b' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo '# Start our voice agent' >> /app/start.sh && \
    echo 'echo "🎤 Starting Voice Agent..."' >> /app/start.sh && \
    echo 'python main.py' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo '# Clean shutdown' >> /app/start.sh && \
    echo 'trap '"'"'kill $OLLAMA_PID'"'"' EXIT' >> /app/start.sh && \
    echo 'wait' >> /app/start.sh

RUN chmod +x /app/start.sh

# Expose ports
EXPOSE 8600 11434

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:11434/api/tags || exit 1

# Start both services
CMD ["/bin/bash", "/app/start.sh"]