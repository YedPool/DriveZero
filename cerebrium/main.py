#!/usr/bin/env python3
"""
Main orchestrator for the all-in-one Cerebrium voice agent deployment.
Manages LiveKit server, Ollama, and voice agent on the same infrastructure.
"""

import os
import asyncio
import logging
import signal
import sys
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from livekit_server import start_livekit_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app for token endpoints
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TokenRequest(BaseModel):
    room: str
    identity: str
    permissions: dict

@app.post("/token")
async def get_livekit_token(request: TokenRequest):
    """Generate LiveKit access token for frontend connection."""
    try:
        # Import livekit tokens inside function to avoid threading issues
        from livekit import api
        
        # Use our internal LiveKit configuration
        token = api.AccessToken(
            api_key=os.getenv("LIVEKIT_API_KEY", "devkey"),
            api_secret=os.getenv("LIVEKIT_API_SECRET", "secret")
        )
        
        # Set participant identity and room
        token.identity = request.identity
        token.name = request.identity
        
        # Add permissions
        grant = api.VideoGrant(
            room_join=True,
            room=request.room,
            can_publish=request.permissions.get("canPublish", True),
            can_subscribe=request.permissions.get("canSubscribe", True)
        )
        token.add_grant(grant)
        
        # Generate JWT token
        jwt_token = token.to_jwt()
        
        return {
            "token": jwt_token,
            "url": os.getenv("LIVEKIT_URL", "ws://localhost:7880")
        }
        
    except Exception as e:
        logger.error(f"Failed to generate token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "voice-agent"}

class VoiceAgentOrchestrator:
    def __init__(self):
        self.ollama_process = None
        self.livekit_server = None
        self.voice_agent_task = None
        
    async def start_all_services(self):
        """Start all services in the correct order."""
        try:
            logger.info("Starting All-in-One Voice Agent Deployment")
            
            # 1. Skip Ollama for now (using OpenAI GPT instead)
            logger.info("Using OpenAI GPT (skipping Ollama setup)...")
            
            # 2. Start LiveKit server
            logger.info("Starting LiveKit server...")
            self.livekit_server = await start_livekit_server()
            await asyncio.sleep(5)  # Wait for LiveKit to be ready
            
            # 3. Set internal URLs for voice agent
            os.environ["LIVEKIT_URL"] = "ws://localhost:7880"
            
            # 4. Start voice agent
            logger.info("Starting Voice Agent...")
            await self.start_voice_agent()
            
            logger.info("All services started successfully!")
            logger.info("Service URLs:")
            logger.info("   - LiveKit WebSocket: ws://localhost:7880")
            logger.info("   - Voice Agent: Running")
            logger.info("   - LLM: OpenAI GPT-4o-mini")
            
        except Exception as e:
            logger.error(f"Failed to start services: {e}")
            await self.shutdown()
            raise
    
    async def start_voice_agent(self):
        """Start the LiveKit voice agent."""
        try:
            # Create a task for the voice agent
            self.voice_agent_task = asyncio.create_task(
                self.run_voice_agent()
            )
            await asyncio.sleep(2)  # Let it initialize
            
        except Exception as e:
            logger.error(f"Failed to start voice agent: {e}")
            raise
    
    async def run_voice_agent(self):
        """Run the voice agent using LiveKit CLI."""
        try:
            # Import voice agent components inside function to avoid threading issues
            from voice_agent import cli, WorkerOptions, entrypoint
            
            # Run the voice agent
            cli.run_app(
                WorkerOptions(
                    entrypoint_fnc=entrypoint,
                    prewarm_fnc=None,
                ),
            )
        except Exception as e:
            logger.error(f"Voice agent error: {e}")
            raise
    
    async def health_check(self):
        """Check health of all services."""
        health = {
            "ollama": False,
            "livekit": False,
            "voice_agent": False
        }
        
        try:
            # Check Ollama
            if self.ollama_process and self.ollama_process.poll() is None:
                health["ollama"] = True
            
            # Check LiveKit
            if self.livekit_server and self.livekit_server.process and self.livekit_server.process.poll() is None:
                health["livekit"] = True
            
            # Check Voice Agent
            if self.voice_agent_task and not self.voice_agent_task.done():
                health["voice_agent"] = True
                
        except Exception as e:
            logger.error(f"Health check error: {e}")
        
        return health
    
    async def shutdown(self):
        """Gracefully shutdown all services."""
        logger.info("Shutting down all services...")
        
        # Stop voice agent
        if self.voice_agent_task:
            self.voice_agent_task.cancel()
            try:
                await self.voice_agent_task
            except asyncio.CancelledError:
                pass
        
        # Stop LiveKit server
        if self.livekit_server:
            self.livekit_server.stop()
        
        # Stop Ollama
        if self.ollama_process:
            self.ollama_process.terminate()
            self.ollama_process.wait()
        
        logger.info("All services shut down")

# Global orchestrator instance
orchestrator = VoiceAgentOrchestrator()

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal")
    asyncio.create_task(orchestrator.shutdown())
    sys.exit(0)

async def start_api_server():
    """Start the FastAPI server for token endpoints."""
    config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    """Main entry point."""
    try:
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start FastAPI server and voice services concurrently
        api_task = asyncio.create_task(start_api_server())
        
        # Start all voice services
        await orchestrator.start_all_services()
        
        # Keep running and monitor health
        while True:
            health = await orchestrator.health_check()
            logger.info(f"Health: {health}")
            
            # Restart failed services if needed
            if not all(health.values()):
                logger.warning("Some services are down, attempting restart...")
                await orchestrator.shutdown()
                await asyncio.sleep(5)
                await orchestrator.start_all_services()
            
            await asyncio.sleep(30)  # Health check every 30 seconds
            
    except KeyboardInterrupt:
        await orchestrator.shutdown()
    except Exception as e:
        logger.error(f"Main error: {e}")
        await orchestrator.shutdown()
        raise

if __name__ == "__main__":
    asyncio.run(main())