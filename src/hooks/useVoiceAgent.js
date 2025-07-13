import { useState, useCallback, useRef } from 'react'
import { Room } from 'livekit-client'

export const useVoiceAgent = () => {
  const [isConnected, setIsConnected] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState(null)
  const roomRef = useRef(null)
  const [messages, setMessages] = useState([])

  const connect = useCallback(async () => {
    try {
      setError(null)
      
      // Get LiveKit token from your backend/Cerebrium endpoint
      const response = await fetch(`${import.meta.env.VITE_VOICE_AGENT_URL}/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${import.meta.env.VITE_CEREBRIUM_API_KEY}`
        },
        body: JSON.stringify({
          room: 'voice-assistant-room',
          identity: `user-${Date.now()}`
        })
      })

      if (!response.ok) {
        throw new Error('Failed to get LiveKit token')
      }

      const { token } = await response.json()
      
      // Create and connect to LiveKit room
      const room = new Room()
      roomRef.current = room
      
      room.on('connected', () => {
        console.log('Connected to voice agent')
        setIsConnected(true)
      })
      
      room.on('disconnected', () => {
        console.log('Disconnected from voice agent')
        setIsConnected(false)
      })
      
      room.on('trackSubscribed', (track, publication, participant) => {
        if (track.kind === 'audio' && participant.identity.includes('voice-agent')) {
          // Attach the audio track to play AI responses
          const audioElement = track.attach()
          audioElement.play()
        }
      })

      await room.connect(import.meta.env.VITE_LIVEKIT_URL, token)
      
    } catch (err) {
      console.error('Failed to connect to voice agent:', err)
      setError(err.message)
    }
  }, [])

  const disconnect = useCallback(() => {
    if (roomRef.current) {
      roomRef.current.disconnect()
      roomRef.current = null
    }
    setIsConnected(false)
  }, [])

  const startRecording = useCallback(async () => {
    if (!roomRef.current || !isConnected) {
      setError('Not connected to voice agent')
      return
    }

    try {
      setIsRecording(true)
      setError(null)

      // Enable microphone and publish audio track
      await roomRef.current.localParticipant.enableMicrophone(true)
      
      addMessage('system', 'Listening...')
      
    } catch (err) {
      console.error('Failed to start recording:', err)
      setError(err.message)
      setIsRecording(false)
    }
  }, [isConnected])

  const stopRecording = useCallback(async () => {
    if (!roomRef.current) return

    try {
      // Disable microphone
      await roomRef.current.localParticipant.enableMicrophone(false)
      setIsRecording(false)
      
      addMessage('system', 'Processing...')
      
    } catch (err) {
      console.error('Failed to stop recording:', err)
      setError(err.message)
    }
  }, [])

  const addMessage = useCallback((type, content) => {
    setMessages(prev => [...prev, {
      type,
      content,
      timestamp: new Date()
    }])
  }, [])

  return {
    isConnected,
    isRecording,
    error,
    messages,
    connect,
    disconnect,
    startRecording,
    stopRecording,
    addMessage
  }
}