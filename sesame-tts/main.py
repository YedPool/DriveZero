#!/usr/bin/env python3
"""
Sesame CSM TTS Server
Provides text-to-speech using Sesame's Conversational Speech Model
"""

import os
import logging
import io
import base64
from typing import Optional
from datetime import datetime

import torch
import torchaudio
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoProcessor, CsmForConditionalGeneration
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Sesame CSM TTS Server",
    description="Text-to-speech using Sesame's Conversational Speech Model",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class TTSRequest(BaseModel):
    text: str
    speaker: Optional[int] = 0
    max_audio_length_ms: Optional[int] = 10000
    return_format: Optional[str] = "wav"  # wav, mp3, base64

class TTSResponse(BaseModel):
    audio_data: str  # base64 encoded audio
    sample_rate: int
    format: str
    duration_ms: float

class TTSServer:
    def __init__(self):
        self.model = None
        self.processor = None
        self.device = self._detect_device()
        self.sample_rate = 24000  # CSM default sample rate
        
        logger.info(f"Using device: {self.device}")
        
    def _detect_device(self):
        """Detect the best available device."""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def load_model(self):
        """Load the Sesame CSM model."""
        try:
            model_id = "sesame/csm-1b"
            logger.info(f"Loading Sesame CSM model: {model_id}")
            
            # Check for HuggingFace token
            hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
            if not hf_token:
                logger.warning("No HUGGINGFACE_HUB_TOKEN environment variable found")
                logger.warning("You may need to accept the model license and set your HF token")
            else:
                logger.info("✓ HuggingFace token found")
            
            # Load processor and model
            self.processor = AutoProcessor.from_pretrained(
                model_id,
                token=hf_token
            )
            self.model = CsmForConditionalGeneration.from_pretrained(
                model_id,
                device_map=self.device,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                token=hf_token
            )
            
            logger.info("✓ Sesame CSM model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.error("Make sure you have:")
            logger.error("1. Accepted the license at https://huggingface.co/sesame/csm-1b")
            logger.error("2. Set HUGGINGFACE_HUB_TOKEN environment variable")
            return False
    
    def generate_audio(self, text: str, speaker: int = 0, max_audio_length_ms: int = 10000):
        """Generate audio from text using CSM."""
        try:
            if not self.model or not self.processor:
                raise ValueError("Model not loaded")
            
            logger.info(f"Generating audio for text: '{text[:50]}...'")
            
            # Prepare inputs
            inputs = self.processor(
                text=text,
                speaker_id=speaker,
                return_tensors="pt"
            ).to(self.device)
            
            # Generate audio
            with torch.no_grad():
                audio_codes = self.model.generate(
                    **inputs,
                    max_new_tokens=max_audio_length_ms // 25,  # Rough estimate
                    do_sample=True,
                    temperature=0.7
                )
            
            # Decode audio
            audio_array = self.processor.decode(audio_codes[0])
            
            # Ensure audio is on CPU and in correct format
            if isinstance(audio_array, torch.Tensor):
                audio_array = audio_array.cpu().float()
            
            logger.info(f"✓ Generated audio: {audio_array.shape} samples at {self.sample_rate}Hz")
            return audio_array
            
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            raise
    
    def audio_to_base64(self, audio_tensor, format="wav"):
        """Convert audio tensor to base64 encoded string."""
        try:
            # Create a bytes buffer
            buffer = io.BytesIO()
            
            # Save audio to buffer
            torchaudio.save(
                buffer, 
                audio_tensor.unsqueeze(0) if audio_tensor.dim() == 1 else audio_tensor,
                self.sample_rate,
                format=format
            )
            
            # Get bytes and encode to base64
            buffer.seek(0)
            audio_bytes = buffer.getvalue()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            return audio_base64
            
        except Exception as e:
            logger.error(f"Audio encoding failed: {e}")
            raise

# Global TTS server instance
tts_server = TTSServer()

@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    logger.info("🚀 Starting Sesame CSM TTS Server")
    
    if not tts_server.load_model():
        logger.error("❌ Failed to load TTS model")
        raise RuntimeError("Model loading failed")
    
    logger.info("✅ TTS Server ready!")

@app.post("/v1/speak", response_model=TTSResponse)
async def speak(request: TTSRequest, http_request: Request):
    """Generate speech from text (Deepgram-compatible endpoint)."""
    
    client_ip = http_request.client.host if http_request.client else "unknown"
    logger.info(f"TTS request from {client_ip}: '{request.text[:50]}...'")
    
    try:
        # Generate audio
        audio_tensor = tts_server.generate_audio(
            text=request.text,
            speaker=request.speaker,
            max_audio_length_ms=request.max_audio_length_ms
        )
        
        # Convert to base64
        audio_base64 = tts_server.audio_to_base64(audio_tensor, request.return_format)
        
        # Calculate duration
        duration_ms = len(audio_tensor) / tts_server.sample_rate * 1000
        
        return TTSResponse(
            audio_data=audio_base64,
            sample_rate=tts_server.sample_rate,
            format=request.return_format,
            duration_ms=duration_ms
        )
        
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts")
async def tts_simple(request: TTSRequest):
    """Simple TTS endpoint."""
    return await speak(request, None)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    model_loaded = tts_server.model is not None
    return {
        "status": "healthy" if model_loaded else "unhealthy",
        "service": "sesame-csm-tts",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model_loaded": model_loaded,
        "device": tts_server.device,
        "sample_rate": tts_server.sample_rate
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Sesame CSM TTS Server",
        "version": "1.0.0",
        "description": "Text-to-speech using Sesame's Conversational Speech Model",
        "endpoints": {
            "POST /v1/speak": "Generate speech (Deepgram-compatible)",
            "POST /tts": "Simple TTS generation",
            "GET /health": "Health check",
            "GET /": "This information"
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    logger.info(f"Starting Sesame CSM TTS Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)