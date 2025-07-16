#!/usr/bin/env python3
"""
Whisper STT Server
Provides speech-to-text using OpenAI's Whisper model
"""

import os
import logging
import io
import base64
import json
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

import whisper
import torch
import numpy as np
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Whisper STT Server",
    description="Speech-to-text using OpenAI's Whisper model",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)

class STTRequest(BaseModel):
    audio_data: str  # base64 encoded audio
    language: Optional[str] = None
    model: Optional[str] = "base"

class STTResponse(BaseModel):
    text: str
    language: str
    confidence: Optional[float] = None
    duration: Optional[float] = None

class STTServer:
    def __init__(self):
        self.model = None
        self.device = self._detect_device()
        self.model_name = "base"  # Default model
        
        logger.info(f"Using device: {self.device}")
        
    def _detect_device(self):
        """Detect the best available device."""
        if torch.cuda.is_available():
            return "cuda"
        else:
            return "cpu"
    
    def load_model(self, model_name: str = "base"):
        """Load the Whisper model."""
        try:
            logger.info(f"Loading Whisper model: {model_name}")
            self.model = whisper.load_model(model_name, device=self.device)
            self.model_name = model_name
            logger.info(f"✓ Whisper model '{model_name}' loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def transcribe_audio(self, audio_data: np.ndarray, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribe audio using Whisper."""
        try:
            if not self.model:
                raise ValueError("Model not loaded")
            
            logger.info(f"Transcribing audio: {audio_data.shape} samples")
            
            # Whisper expects audio to be float32 normalized to [-1, 1]
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize if needed
            if audio_data.max() > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Transcribe
            result = self.model.transcribe(
                audio_data,
                language=language,
                fp16=self.device == "cuda"
            )
            
            logger.info(f"✓ Transcription completed: '{result['text'][:50]}...'")
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    def base64_to_audio(self, audio_base64: str) -> np.ndarray:
        """Convert base64 encoded audio to numpy array."""
        try:
            # Decode base64
            audio_bytes = base64.b64decode(audio_base64)
            
            # Load audio from bytes
            import torchaudio
            audio_buffer = io.BytesIO(audio_bytes)
            waveform, sample_rate = torchaudio.load(audio_buffer)
            
            # Convert to numpy and resample to 16kHz (Whisper's expected rate)
            audio_np = waveform.numpy().squeeze()
            
            if sample_rate != 16000:
                import torchaudio.transforms as T
                resampler = T.Resample(sample_rate, 16000)
                waveform_resampled = resampler(waveform)
                audio_np = waveform_resampled.numpy().squeeze()
            
            return audio_np
            
        except Exception as e:
            logger.error(f"Audio decoding failed: {e}")
            raise

# Global STT server instance
stt_server = STTServer()

@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    logger.info("🚀 Starting Whisper STT Server")
    
    model_name = os.getenv("WHISPER_MODEL", "base")
    if not stt_server.load_model(model_name):
        logger.error("❌ Failed to load STT model")
        raise RuntimeError("Model loading failed")
    
    logger.info("✅ STT Server ready!")

@app.post("/v1/listen", response_model=STTResponse)
async def listen(request: STTRequest, http_request: Request):
    """Transcribe speech from audio (Deepgram-compatible endpoint)."""
    
    client_ip = http_request.client.host if http_request.client else "unknown"
    logger.info(f"STT request from {client_ip}")
    
    try:
        # Decode audio
        audio_np = stt_server.base64_to_audio(request.audio_data)
        
        # Transcribe
        result = stt_server.transcribe_audio(audio_np, request.language)
        
        return STTResponse(
            text=result["text"],
            language=result.get("language", "unknown"),
            confidence=None,  # Whisper doesn't provide confidence scores
            duration=len(audio_np) / 16000  # Duration in seconds
        )
        
    except Exception as e:
        logger.error(f"STT transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe")
async def transcribe_file(file: UploadFile = File(...), language: Optional[str] = None):
    """Transcribe uploaded audio file."""
    try:
        # Read file contents
        audio_bytes = await file.read()
        
        # Load audio
        import torchaudio
        audio_buffer = io.BytesIO(audio_bytes)
        waveform, sample_rate = torchaudio.load(audio_buffer)
        
        # Convert to numpy and resample if needed
        audio_np = waveform.numpy().squeeze()
        if sample_rate != 16000:
            import torchaudio.transforms as T
            resampler = T.Resample(sample_rate, 16000)
            waveform_resampled = resampler(waveform)
            audio_np = waveform_resampled.numpy().squeeze()
        
        # Transcribe
        result = stt_server.transcribe_audio(audio_np, language)
        
        return {
            "text": result["text"],
            "language": result.get("language", "unknown"),
            "segments": result.get("segments", []),
            "duration": len(audio_np) / 16000
        }
        
    except Exception as e:
        logger.error(f"File transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/v1/listen")
async def websocket_listen(websocket: WebSocket):
    """WebSocket endpoint for real-time transcription (Deepgram-compatible)."""
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Receive audio data
            data = await websocket.receive_bytes()
            
            try:
                # Process audio (simplified - in production you'd buffer chunks)
                audio_buffer = io.BytesIO(data)
                waveform, sample_rate = torchaudio.load(audio_buffer)
                audio_np = waveform.numpy().squeeze()
                
                if sample_rate != 16000:
                    import torchaudio.transforms as T
                    resampler = T.Resample(sample_rate, 16000)
                    waveform_resampled = resampler(waveform)
                    audio_np = waveform_resampled.numpy().squeeze()
                
                # Transcribe
                result = stt_server.transcribe_audio(audio_np)
                
                # Send result
                response = {
                    "type": "Results",
                    "channel": {
                        "alternatives": [{
                            "transcript": result["text"],
                            "confidence": 0.95  # Mock confidence
                        }]
                    },
                    "is_final": True
                }
                
                await websocket.send_text(json.dumps(response))
                
            except Exception as e:
                logger.error(f"WebSocket transcription error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "Error",
                    "message": str(e)
                }))
                
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    model_loaded = stt_server.model is not None
    return {
        "status": "healthy" if model_loaded else "unhealthy",
        "service": "whisper-stt",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model_loaded": model_loaded,
        "model_name": stt_server.model_name,
        "device": stt_server.device
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Whisper STT Server",
        "version": "1.0.0",
        "description": "Speech-to-text using OpenAI's Whisper model",
        "endpoints": {
            "POST /v1/listen": "Transcribe audio (Deepgram-compatible)",
            "POST /transcribe": "Transcribe uploaded file",
            "WS /v1/listen": "Real-time transcription WebSocket",
            "GET /health": "Health check",
            "GET /": "This information"
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    logger.info(f"Starting Whisper STT Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)