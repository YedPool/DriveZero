#!/usr/bin/env python3
"""
Embedded LiveKit server for Cerebrium deployment.
Runs LiveKit server alongside the voice agent on the same infrastructure.
"""

import os
import asyncio
import logging
import subprocess
import time
import signal
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiveKitServer:
    def __init__(self):
        self.process = None
        self.config_file = "/tmp/livekit.yaml"
        self.api_key = os.getenv("LIVEKIT_API_KEY", "devkey")
        self.api_secret = os.getenv("LIVEKIT_API_SECRET", "secret")
        
    def create_config(self):
        """Create LiveKit server configuration."""
        config = f"""
port: 7880
bind_addresses:
  - ""

rtc:
  tcp_port: 7881
  port_range_start: 50000
  port_range_end: 60000
  use_external_ip: false

redis: null

keys:
  {self.api_key}: {self.api_secret}

log_level: info

room:
  auto_create: true
  enable_recording: false

turn:
  enabled: false

webhook:
  api_key: {self.api_key}

development: true
"""
        
        with open(self.config_file, 'w') as f:
            f.write(config)
        
        logger.info(f"Created LiveKit config at {self.config_file}")
    
    def download_livekit_server(self):
        """Download LiveKit server binary."""
        try:
            # Download LiveKit server binary
            download_cmd = [
                "curl", "-L", 
                "https://github.com/livekit/livekit/releases/latest/download/livekit_linux_amd64",
                "-o", "/usr/local/bin/livekit-server"
            ]
            
            result = subprocess.run(download_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Failed to download LiveKit server: {result.stderr}")
            
            # Make executable
            os.chmod("/usr/local/bin/livekit-server", 0o755)
            logger.info("Downloaded and installed LiveKit server")
            
        except Exception as e:
            logger.error(f"Failed to setup LiveKit server: {e}")
            raise
    
    async def start(self):
        """Start LiveKit server."""
        try:
            # Create config file
            self.create_config()
            
            # Download server if not exists
            if not os.path.exists("/usr/local/bin/livekit-server"):
                self.download_livekit_server()
            
            # Start LiveKit server
            cmd = [
                "/usr/local/bin/livekit-server",
                "--config", self.config_file,
                "--bind", "0.0.0.0"
            ]
            
            logger.info("Starting LiveKit server...")
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            await asyncio.sleep(5)
            
            if self.process.poll() is None:
                logger.info("LiveKit server started successfully on port 7880")
                return True
            else:
                stdout, stderr = self.process.communicate()
                logger.error(f"LiveKit server failed to start: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start LiveKit server: {e}")
            return False
    
    def stop(self):
        """Stop LiveKit server."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            logger.info("LiveKit server stopped")
    
    def get_ws_url(self):
        """Get WebSocket URL for internal connections."""
        return "ws://localhost:7880"

# Global server instance
livekit_server = LiveKitServer()

async def start_livekit_server():
    """Start LiveKit server and return the instance."""
    success = await livekit_server.start()
    if not success:
        raise Exception("Failed to start LiveKit server")
    return livekit_server

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal")
    livekit_server.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start server
    asyncio.run(start_livekit_server())
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        livekit_server.stop()