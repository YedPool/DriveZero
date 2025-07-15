#!/usr/bin/env python3
"""
LiveKit Token Generation Server for Gmail Voice Assistant.
Generates secure JWT tokens for LiveKit connections.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from livekit import api
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LiveKit Token Server",
    description="Secure token generation for Gmail Voice Assistant LiveKit connections",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://localhost:5173",  # Vite dev server
        "http://localhost:5174",  # Alternative Vite port
        "https://*.cerebrium.ai", # Cerebrium domains
        "https://*.vercel.app",   # Vercel deployments
        "https://*.netlify.app",  # Netlify deployments
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class TokenRequest(BaseModel):
    room: str
    identity: str
    name: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None
    
    @validator('room')
    def validate_room(cls, v):
        if not v or len(v) < 1 or len(v) > 100:
            raise ValueError('Room name must be between 1 and 100 characters')
        # Allow alphanumeric, hyphens, underscores
        if not all(c.isalnum() or c in '-_' for c in v):
            raise ValueError('Room name contains invalid characters')
        return v
    
    @validator('identity')
    def validate_identity(cls, v):
        if not v or len(v) < 1 or len(v) > 100:
            raise ValueError('Identity must be between 1 and 100 characters')
        return v

class TokenResponse(BaseModel):
    token: str
    url: str
    room: str
    identity: str
    expires_at: str

def generate_livekit_token(
    room: str, 
    identity: str, 
    name: Optional[str] = None,
    permissions: Optional[Dict[str, bool]] = None
) -> Dict[str, Any]:
    """Generate a secure LiveKit access token."""
    try:
        # Get environment variables
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")
        
        # Service discovery: Build LiveKit URL from Cerebrium environment
        cerebrium_project_id = os.getenv("CEREBRIUM_PROJECT_ID")
        livekit_deployment_name = os.getenv("LIVEKIT_DEPLOYMENT_NAME", "gmail-livekit-server")
        
        if cerebrium_project_id:
            # Production: Use Cerebrium service URL
            livekit_url = f"wss://api.aws.us-east-1.cerebrium.ai/v4/p-{cerebrium_project_id}/{livekit_deployment_name}:7880"
            logger.info(f"Using Cerebrium LiveKit service: {livekit_url}")
        else:
            # Fallback: Use explicit LIVEKIT_URL or development default
            livekit_url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
            logger.warning(f"CEREBRIUM_PROJECT_ID not set, using fallback: {livekit_url}")
        
        # Validate LiveKit connection details
        if not api_key or not api_secret:
            missing = []
            if not api_key: missing.append("LIVEKIT_API_KEY")
            if not api_secret: missing.append("LIVEKIT_API_SECRET")
            error_msg = f"Missing required environment variables: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Generating token for {identity} in room {room}")
        logger.info(f"Using LiveKit URL: {livekit_url}")
        
        # Validate required environment variables
        if not api_key or not api_secret:
            missing = []
            if not api_key: missing.append("LIVEKIT_API_KEY")
            if not api_secret: missing.append("LIVEKIT_API_SECRET")
            
            error_msg = f"Missing required environment variables: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Set default permissions if not provided
        if permissions is None:
            permissions = {
                "canPublish": True,
                "canSubscribe": True,
                "canPublishData": True
            }
        
        # Create LiveKit access token
        token = api.AccessToken(api_key=api_key, api_secret=api_secret)
        
        # Set token expiration (30 minutes from now)
        expires_at = datetime.utcnow() + timedelta(minutes=30)
        token = token.with_ttl(timedelta(minutes=30))
        
        # Set participant identity and name
        token = token.with_identity(identity)
        if name:
            token = token.with_name(name)
        
        # Create video grants with permissions
        grants = api.VideoGrants(
            room_join=True,
            room=room,
            can_publish=permissions.get("canPublish", True),
            can_subscribe=permissions.get("canSubscribe", True),
            can_publish_data=permissions.get("canPublishData", True)
        )
        
        # Add grants to token
        token = token.with_grants(grants)
        
        # Generate JWT
        jwt_token = token.to_jwt()
        
        logger.info(f"✓ Generated token for {identity} in room {room}")
        logger.info(f"  Token expires at: {expires_at.isoformat()}Z")
        
        return {
            "success": True,
            "token": jwt_token,
            "url": livekit_url,
            "room": room,
            "identity": identity,
            "expires_at": expires_at.isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate token: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate LiveKit token"
        }

@app.post("/token", response_model=TokenResponse)
async def create_token(request: TokenRequest, http_request: Request):
    """Generate a LiveKit access token for the specified room and identity."""
    
    # Log request details (without sensitive data)
    client_ip = http_request.client.host if http_request.client else "unknown"
    logger.info(f"Token request from {client_ip} for room '{request.room}', identity '{request.identity}'")
    
    # Generate token
    result = generate_livekit_token(
        room=request.room,
        identity=request.identity,
        name=request.name,
        permissions=request.permissions
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=500, 
            detail=result.get("message", "Token generation failed")
        )
    
    # Return token response
    return TokenResponse(
        token=result["token"],
        url=result["url"],
        room=result["room"],
        identity=result["identity"],
        expires_at=result["expires_at"]
    )

@app.post("/predict")
async def predict_endpoint(inputs: Dict[str, Any]):
    """Cerebrium prediction endpoint for backward compatibility."""
    try:
        room = inputs.get("room", "voice-assistant-room")
        identity = inputs.get("identity", f"user-{int(time.time())}")
        name = inputs.get("name")
        permissions = inputs.get("permissions", {
            "canPublish": True, 
            "canSubscribe": True,
            "canPublishData": True
        })
        
        result = generate_livekit_token(room, identity, name, permissions)
        
        if not result["success"]:
            return result
        
        return {
            "token": result["token"],
            "url": result["url"],
            "room": result["room"],
            "identity": result["identity"],
            "expires_at": result["expires_at"]
        }
        
    except Exception as e:
        logger.error(f"Prediction endpoint error: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Token generation failed"
        }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "livekit-token-server",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "livekit_url": os.getenv("LIVEKIT_URL", "Not configured")
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "LiveKit Token Server",
        "version": "1.0.0",
        "description": "Secure token generation for Gmail Voice Assistant",
        "endpoints": {
            "POST /token": "Generate LiveKit access token",
            "POST /predict": "Cerebrium prediction format",
            "GET /health": "Health check",
            "GET /": "This information"
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting LiveKit Token Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)