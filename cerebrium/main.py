#!/usr/bin/env python3
"""
LiveKit Agent for Gmail voice assistant following Cerebrium GitHub example.
"""

import os
import sys
import logging
import subprocess
import time
import asyncio
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, cli, WorkerOptions, WorkerType
from livekit.plugins import openai, deepgram, silero
from livekit.plugins.turn_detector.english import EnglishModel
from livekit.agents import metrics, MetricsCollectedEvent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Usage metrics collector
usage_collector = metrics.UsageCollector()

# Set cache directory for models
os.environ["HF_HOME"] = "/cortex/.cache/"

def setup_ollama():
    """Start Ollama service (binary installed during build)."""
    try:
        logger.info("Starting Ollama service...")
        
        # Start Ollama service in background (binary pre-installed)
        ollama_process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info("✓ Ollama service started")
        return ollama_process
        
    except Exception as e:
        logger.error(f"Failed to start Ollama: {e}")
        return None

def wait_for_ollama():
    """Wait for Ollama to be ready."""
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            result = subprocess.run(
                ["curl", "-s", "http://127.0.0.1:11434/api/tags"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info("✓ Ollama is ready")
                return True
        except:
            pass
        
        logger.info(f"Waiting for Ollama... ({attempt + 1}/{max_attempts})")
        time.sleep(2)
    
    logger.error("✗ Ollama failed to start within timeout")
    return False

class GmailAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful Gmail voice assistant. Help users manage their emails, compose messages, and organize their inbox.")

def get_livekit_connection_url():
    """Service discovery for LiveKit server connection."""
    cerebrium_project_id = os.getenv("CEREBRIUM_PROJECT_ID")
    livekit_deployment_name = os.getenv("LIVEKIT_DEPLOYMENT_NAME", "gmail-livekit-server")
    
    if cerebrium_project_id:
        # Production: Use Cerebrium service URL  
        url = f"wss://api.aws.us-east-1.cerebrium.ai/v4/p-{cerebrium_project_id}/{livekit_deployment_name}:7880"
        logger.info(f"Agent connecting to Cerebrium LiveKit: {url}")
        return url
    else:
        # Fallback: Use explicit LIVEKIT_URL or development default
        url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
        logger.warning(f"CEREBRIUM_PROJECT_ID not set, using fallback: {url}")
        return url

async def entrypoint(ctx: agents.JobContext):
    """
    Main entrypoint for the LiveKit agent.
    This function is called when a participant joins a room.
    """
    # Log service discovery information
    livekit_url = get_livekit_connection_url()
    logger.info(f"Agent starting with LiveKit URL: {livekit_url}")
    
    await ctx.connect()
    
    # Configure the agent session with required services
    session = AgentSession(
        # Speech-to-Text: Deepgram Nova-2
        stt=deepgram.STT(
            model="nova-2",
            language="en-US",
            smart_format=True,
            profanity_filter=False,
            punctuate=True,
        ),
        
        # Large Language Model: Local Ollama
        llm=openai.LLM(
            base_url="http://127.0.0.1:11434/v1",
            api_key="ollama",  # Ollama doesn't need real API key
            model="llama3.2:1b",
            temperature=0.7,
        ),
        
        # Text-to-Speech: Deepgram Rime
        tts=deepgram.TTS(
            model="aura-asteria-en",
            encoding="linear16",
            sample_rate=24000,
        ),
        
        # Voice Activity Detection
        vad=silero.VAD.load(),
        
        # Turn detection for natural conversation flow
        turn_detection=EnglishModel(),
    )
    
    # Start the agent session
    await session.start(
        room=ctx.room,
        agent=GmailAssistant(),
    )
    
    # Generate initial greeting when agent joins
    await session.generate_reply(
        instructions="Greet the user warmly and ask how you can help them with their Gmail today."
    )
    
    # Metrics collection for usage tracking
    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        usage_collector.collect(ev.metrics)
        metrics.log_metrics(ev.metrics)
    
    async def log_usage():
        """Log usage summary when session ends"""
        summary = usage_collector.get_summary()
        print(f"Usage: {summary}")
    
    # Register cleanup callback
    ctx.add_shutdown_callback(log_usage)

if __name__ == '__main__':
    # Add 'dev' as default argument if none provided (following GitHub example)
    if len(sys.argv) == 1:
        sys.argv.append('dev')
    
    # Check for download command
    if len(sys.argv) > 1 and sys.argv[1] == 'download-files':
        # Download required models during build phase
        logger.info("Downloading required models...")
        try:
            # Download LiveKit models
            from livekit.plugins.turn_detector.english import EnglishModel
            model = EnglishModel()
            logger.info("✓ LiveKit models downloaded successfully")
        except Exception as e:
            logger.warning(f"LiveKit model download failed: {e}")
            
        # Download Ollama models during build
        try:
            logger.info("Starting Ollama and downloading models...")
            
            # Start Ollama in background
            ollama_proc = subprocess.Popen(["ollama", "serve"])
            time.sleep(10)  # Wait for startup
            
            # Pull small model
            logger.info("Pulling llama3.2:1b model...")
            result = subprocess.run(["ollama", "pull", "llama3.2:1b"], timeout=600)
            
            if result.returncode == 0:
                logger.info("✓ Ollama model downloaded successfully")
            else:
                logger.warning("Ollama model download failed, will retry at runtime")
                
            # Stop Ollama
            ollama_proc.terminate()
            
        except Exception as e:
            logger.warning(f"Ollama setup during build failed: {e}")
            
        logger.info("✓ Build phase complete")
        
    else:
        # Start Ollama service first
        logger.info("🚀 Starting Gmail Voice Assistant Agent...")
        logger.info("Setting up Ollama...")
        
        ollama_process = setup_ollama()
        
        if ollama_process and wait_for_ollama():
            logger.info("✓ Ollama is ready, starting LiveKit agent worker")
        else:
            logger.error("❌ Ollama setup failed - agent cannot function without LLM")
            logger.error("Please check Ollama installation and model availability")
            # Don't start agent if Ollama failed - it will definitely fail
            sys.exit(1)
        
        # Start the LiveKit agent worker
        logger.info("Starting LiveKit agent worker on port 8600...")
        try:
            cli.run_app(WorkerOptions(
                entrypoint_fnc=entrypoint,
                worker_type=WorkerType.ROOM,
                port=8600
            ))
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            if ollama_process:
                ollama_process.terminate()
        except Exception as e:
            logger.error(f"Agent failed: {e}")
            if ollama_process:
                ollama_process.terminate()
            raise