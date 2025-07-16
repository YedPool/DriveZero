#!/usr/bin/env python3
"""
LiveKit Server deployment for Cerebrium.
Runs a standalone LiveKit server that agents can connect to.
"""

import os
import subprocess
import logging
import time
import signal
import sys
import asyncio
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiveKitServer:
    def __init__(self):
        self.process = None
        self.config_file = "/tmp/livekit.yaml"
        
        # LiveKit server configuration
        self.api_key = os.getenv("LIVEKIT_API_KEY")
        self.api_secret = os.getenv("LIVEKIT_API_SECRET")
        
        # Validate required credentials
        if not self.api_key or not self.api_secret:
            missing = []
            if not self.api_key: missing.append("LIVEKIT_API_KEY")
            if not self.api_secret: missing.append("LIVEKIT_API_SECRET")
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}. Set these in Cerebrium dashboard secrets.")
        self.port = int(os.getenv("LIVEKIT_PORT", "7880"))
        
        # Service discovery: Build external URL from Cerebrium environment
        cerebrium_project_id = os.getenv("CEREBRIUM_PROJECT_ID")
        deployment_name = os.getenv("LIVEKIT_DEPLOYMENT_NAME", "gmail-livekit-server")
        
        if cerebrium_project_id:
            # Production: Use Cerebrium service URL
            self.external_url = f"wss://api.aws.us-east-1.cerebrium.ai/v4/p-{cerebrium_project_id}/{deployment_name}:{self.port}"
            logger.info(f"Using Cerebrium external URL: {self.external_url}")
        else:
            # Fallback: Use explicit LIVEKIT_EXTERNAL_URL or development default
            self.external_url = os.getenv("LIVEKIT_EXTERNAL_URL", f"ws://localhost:{self.port}")
            logger.warning(f"CEREBRIUM_PROJECT_ID not set, using fallback: {self.external_url}")
        
    def create_config(self):
        """Create LiveKit server configuration file."""
        config = f"""
port: {self.port}
bind_addresses:
  - ""

rtc:
  tcp_port: {self.port + 1}
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
        logger.info(f"Server will run on port {self.port}")
        logger.info(f"API Key: {self.api_key}")
    
    def download_livekit_server(self):
        """Download LiveKit server binary."""
        try:
            import requests
            import platform
            
            # Detect architecture
            arch = platform.machine()
            logger.info(f"Detected architecture: {arch}")
            
            if arch == "x86_64":
                binary_arch = "amd64"
            elif arch == "aarch64":
                binary_arch = "arm64"
            else:
                logger.error(f"Unsupported architecture: {arch}")
                raise ValueError(f"Unsupported architecture: {arch}")
            
            # Download LiveKit server binary for Linux
            url = f"https://github.com/livekit/livekit/releases/latest/download/livekit-server_linux_{binary_arch}"
            logger.info(f"Downloading LiveKit server from {url}")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            logger.info(f"Download response status: {response.status_code}")
            logger.info(f"Content-Length: {response.headers.get('content-length', 'unknown')}")
            
            # Create directory and write binary
            os.makedirs("/usr/local/bin", exist_ok=True)
            
            total_size = 0
            with open("/usr/local/bin/livekit-server", "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    total_size += len(chunk)
            
            logger.info(f"Downloaded {total_size} bytes")
            
            # Check file info before making executable
            logger.info("File info before chmod:")
            logger.info(f"  Size: {os.path.getsize('/usr/local/bin/livekit-server')} bytes")
            logger.info(f"  Exists: {os.path.exists('/usr/local/bin/livekit-server')}")
            
            # Make executable
            os.chmod("/usr/local/bin/livekit-server", 0o755)
            
            # Check file info after chmod
            logger.info("File info after chmod:")
            stat_info = os.stat("/usr/local/bin/livekit-server")
            logger.info(f"  Mode: {oct(stat_info.st_mode)}")
            logger.info(f"  Size: {stat_info.st_size} bytes")
            
            # Try to get file type if 'file' command is available
            try:
                import subprocess
                result = subprocess.run(['file', '/usr/local/bin/livekit-server'], 
                                      capture_output=True, text=True)
                logger.info(f"File type: {result.stdout.strip()}")
            except:
                logger.info("Could not determine file type")
            
            logger.info("✓ Downloaded and installed LiveKit server")
            
        except Exception as e:
            logger.error(f"Failed to download LiveKit server: {e}")
            raise
    
    def start(self):
        """Start LiveKit server."""
        try:
            # Create config file
            self.create_config()
            
            # Download server if not exists
            if not os.path.exists("/usr/local/bin/livekit-server"):
                logger.info("LiveKit server not found, downloading...")
                self.download_livekit_server()
            
            # Start LiveKit server
            cmd = [
                "/usr/local/bin/livekit-server",
                "--config", self.config_file,
                "--bind", "0.0.0.0"
            ]
            
            logger.info("Starting LiveKit server...")
            logger.info(f"Command: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitor server output
            return self.monitor_server()
            
        except Exception as e:
            logger.error(f"Failed to start LiveKit server: {e}")
            return False
    
    def monitor_server(self):
        """Monitor server startup and log output."""
        startup_timeout = 30
        start_time = time.time()
        
        logger.info("Monitoring LiveKit server startup...")
        
        while time.time() - start_time < startup_timeout:
            if self.process.poll() is not None:
                # Process has terminated
                stdout, stderr = self.process.communicate()
                logger.error(f"LiveKit server exited early:")
                logger.error(f"Output: {stdout}")
                return False
            
            # Read any available output
            try:
                line = self.process.stdout.readline()
                if line:
                    logger.info(f"LiveKit: {line.strip()}")
                    
                    # Check for successful startup indicators
                    if "starting rtc server" in line.lower() or "server listening" in line.lower():
                        logger.info("✓ LiveKit server started successfully!")
                        return True
            except:
                pass
            
            time.sleep(0.5)
        
        logger.info("✓ LiveKit server startup completed (timeout reached)")
        return True
    
    def stop(self):
        """Stop LiveKit server."""
        if self.process:
            logger.info("Stopping LiveKit server...")
            self.process.terminate()
            self.process.wait()
            logger.info("✓ LiveKit server stopped")
    
    def get_connection_info(self):
        """Get connection information for clients."""
        return {
            "url": self.external_url,
            "api_key": self.api_key,
            "api_secret": self.api_secret
        }

# Global server instance
livekit_server = LiveKitServer()

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal")
    livekit_server.stop()
    sys.exit(0)

def main():
    """Main function to start LiveKit server."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 Starting LiveKit Server on Cerebrium")
    
    # Start server
    success = livekit_server.start()
    
    if not success:
        logger.error("❌ Failed to start LiveKit server")
        sys.exit(1)
    
    # Print connection info
    info = livekit_server.get_connection_info()
    logger.info("📡 LiveKit Server Ready!")
    logger.info(f"   URL: {info['url']}")
    logger.info(f"   API Key: {info['api_key']}")
    
    # Keep running and log output
    try:
        while True:
            if livekit_server.process.poll() is not None:
                logger.error("LiveKit server process died")
                break
                
            # Continue reading and logging output
            try:
                line = livekit_server.process.stdout.readline()
                if line:
                    logger.info(f"LiveKit: {line.strip()}")
            except:
                pass
                
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        livekit_server.stop()

if __name__ == "__main__":
    main()