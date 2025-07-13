import os
import asyncio
import logging

import openai
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailVoiceAgent:
    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Gmail integration would go here
        self.gmail_service = None
        
    async def get_email_context(self, user_email: str) -> str:
        """
        Fetch user's email context for the AI assistant.
        This would integrate with Gmail API in production.
        """
        # Mock email data for now
        return f"""
        You are a voice assistant for {user_email}. 
        You can help with:
        - Reading unread emails
        - Composing and sending emails
        - Searching through email history
        - Managing email labels and organization
        
        Current status: Connected to Gmail account {user_email}
        """

    async def process_voice_command(self, transcript: str, user_email: str) -> str:
        """
        Process voice commands and generate appropriate responses.
        """
        try:
            email_context = await self.get_email_context(user_email)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": f"""
                        {email_context}
                        
                        You are a helpful voice assistant specialized in email management.
                        Keep responses concise and natural for voice interaction.
                        Always confirm actions before executing them.
                        """
                    },
                    {
                        "role": "user", 
                        "content": transcript
                    }
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
            return "I'm sorry, I encountered an error processing your request. Please try again."

def get_stt_service():
    """Deepgram Nova-2 for ultra-fast STT (following Cerebrium guide)."""
    from livekit.plugins import deepgram
    logger.info("Using Deepgram Nova-2 for STT")
    return deepgram.STT.load(
        model="nova-2",
        language="en-US",
        smart_format=True,
        profanity_filter=False,
        punctuate=True,
        diarize=False,  # Single speaker for voice assistant
    )

def get_tts_service():
    """Deepgram Rime for ultra-low latency TTS (following Cerebrium guide)."""
    from livekit.plugins import deepgram
    logger.info("Using Deepgram Rime for TTS")
    return deepgram.TTS.load(
        voice="aura-asteria-en",  # High-quality female voice
        model="aura",
        encoding="linear16",
        sample_rate=24000,
    )

# Simple LiveKit Agent Configuration (without VoiceAssistant)
async def entrypoint(ctx: JobContext):
    """Main entry point for the voice assistant."""
    
    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Initialize individual components (import plugins inside function)
    from livekit.plugins import openai as openai_plugin
    
    stt = get_stt_service()
    llm_service = openai_plugin.LLM.load(
        model="gpt-4o-mini",
        temperature=0.7,
    )
    tts = get_tts_service()
    
    logger.info("Voice assistant components initialized")
    
    # Simple message handler for testing
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant):
        logger.info(f"Participant connected: {participant.identity}")
    
    @ctx.room.on("track_published") 
    def on_track_published(publication, participant):
        logger.info(f"Track published: {publication.kind} from {participant.identity}")
    
    # Keep the agent running
    logger.info("Voice assistant ready and waiting for connections...")
    
    # Wait indefinitely
    while True:
        await asyncio.sleep(10)
        logger.info("Voice assistant heartbeat...")

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=None,
        ),
    )