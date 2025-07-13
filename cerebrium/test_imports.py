#!/usr/bin/env python3
"""
Test script to check what's available in LiveKit agents.
"""

try:
    import livekit.agents
    print("✅ livekit.agents imported successfully")
    print("Available in livekit.agents:", dir(livekit.agents))
except ImportError as e:
    print("❌ Failed to import livekit.agents:", e)

try:
    from livekit.agents.voice_assistant import VoiceAssistant
    print("✅ VoiceAssistant from livekit.agents.voice_assistant imported successfully")
except ImportError as e:
    print("❌ Failed to import VoiceAssistant from livekit.agents.voice_assistant:", e)

try:
    from livekit.agents import VoiceAssistant
    print("✅ VoiceAssistant from livekit.agents imported successfully")
except ImportError as e:
    print("❌ Failed to import VoiceAssistant from livekit.agents:", e)

try:
    from livekit import agents
    print("✅ livekit.agents as agents imported successfully")
    if hasattr(agents, 'VoiceAssistant'):
        print("✅ VoiceAssistant found in agents")
    else:
        print("❌ VoiceAssistant not found in agents")
except ImportError as e:
    print("❌ Failed to import livekit.agents:", e)

print("\n--- Checking for alternative patterns ---")
try:
    import livekit
    print("Available in livekit:", dir(livekit))
except ImportError as e:
    print("❌ Failed to import livekit:", e)