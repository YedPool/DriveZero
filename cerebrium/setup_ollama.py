#!/usr/bin/env python3
"""
Setup script to initialize Ollama with Llama model on Cerebrium deployment.
This runs during container initialization to download and configure the model.
"""

import os
import subprocess
import sys
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_ollama():
    """Initialize Ollama server and download Llama model."""
    try:
        # Start Ollama server in background
        logger.info("Starting Ollama server...")
        ollama_process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        time.sleep(10)
        
        # Download Llama model
        model_name = os.getenv("LLM_MODEL", "llama3.1:8b")
        logger.info(f"Pulling {model_name} model...")
        
        result = subprocess.run(
            ["ollama", "pull", model_name],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout for model download
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully pulled {model_name}")
        else:
            logger.error(f"Failed to pull model: {result.stderr}")
            sys.exit(1)
            
        # Test model is working
        logger.info("Testing model inference...")
        test_result = subprocess.run(
            ["ollama", "run", model_name, "Hello, respond with just 'OK'"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if test_result.returncode == 0:
            logger.info("Model test successful!")
        else:
            logger.error(f"Model test failed: {test_result.stderr}")
            
        return ollama_process
        
    except Exception as e:
        logger.error(f"Failed to setup Ollama: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_ollama()