class CerebriumAPI {
  constructor() {
    this.apiKey = import.meta.env.VITE_CEREBRIUM_API_KEY
    this.baseUrl = import.meta.env.VITE_VOICE_AGENT_URL || 'https://api.cerebrium.ai'
  }

  async deployVoiceAgent() {
    try {
      const response = await fetch(`${this.baseUrl}/deploy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`
        },
        body: JSON.stringify({
          model: 'voice-agent',
          config: {
            stt_model: 'whisper-1',
            llm_model: 'gpt-4',
            tts_model: 'eleven-labs',
            system_prompt: `You are a helpful email assistant. You can help users read, compose, and manage their Gmail emails through voice commands. Keep responses concise and natural for voice interaction.`,
            livekit: {
              url: import.meta.env.VITE_LIVEKIT_URL,
              api_key: import.meta.env.VITE_LIVEKIT_API_KEY,
              api_secret: import.meta.env.VITE_LIVEKIT_API_SECRET
            }
          }
        })
      })

      if (!response.ok) {
        throw new Error(`Failed to deploy voice agent: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Error deploying voice agent:', error)
      throw error
    }
  }

  async getLiveKitToken(roomName, identity) {
    try {
      const response = await fetch(`${this.baseUrl}/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`
        },
        body: JSON.stringify({
          room: roomName,
          identity: identity,
          permissions: {
            canPublish: true,
            canSubscribe: true,
            canRecord: false
          }
        })
      })

      if (!response.ok) {
        throw new Error(`Failed to get LiveKit token: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Error getting LiveKit token:', error)
      throw error
    }
  }

  async processEmailCommand(command, userEmail) {
    try {
      const response = await fetch(`${this.baseUrl}/email-command`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`
        },
        body: JSON.stringify({
          command,
          userEmail,
          context: 'gmail-voice-assistant'
        })
      })

      if (!response.ok) {
        throw new Error(`Failed to process email command: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Error processing email command:', error)
      throw error
    }
  }
}

export default new CerebriumAPI()