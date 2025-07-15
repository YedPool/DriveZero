import { useState, useCallback, useRef, useEffect } from 'react'
import { Room, RoomEvent, Track } from 'livekit-client'
import cerebriumApi from '../services/cerebriumApi'

export const useVoiceAgent = () => {
  const [isConnected, setIsConnected] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState(null)
  const roomRef = useRef(null)
  const [messages, setMessages] = useState([])

  const connect = useCallback(async () => {
    try {
      setError(null)
      
      // Get LiveKit connection info from the token server
      console.log('Getting LiveKit token from token server...')
      
      const roomName = 'voice-assistant-room'
      const identity = `user-${Date.now()}`
      
      const response = await cerebriumApi.getLiveKitToken(roomName, identity)
      console.log('Received token response:', response)
      
      const { token, url } = response
      console.log('Received LiveKit token, connecting to:', url)
      
      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      })
      
      roomRef.current = room
      
      // Set up event listeners
      room.on(RoomEvent.Connected, () => {
        console.log('Connected to voice agent room')
        setIsConnected(true)
        addMessage('system', 'Connected to voice assistant!')
      })
      
      room.on(RoomEvent.Disconnected, (reason) => {
        console.log('Disconnected from voice agent:', reason)
        setIsConnected(false)
        addMessage('system', 'Disconnected from voice assistant')
      })
      
      room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
        console.log('Track subscribed:', track.kind, participant.identity)
        
        if (track.kind === Track.Kind.Audio && participant.identity.includes('agent')) {
          // Attach AI voice response audio
          const audioElement = track.attach()
          audioElement.autoplay = true
          document.body.appendChild(audioElement)
        }
      })
      
      room.on(RoomEvent.LocalTrackPublished, (publication, participant) => {
        console.log('Local track published:', publication.kind)
      })
      
      // Connect using token and URL from our deployed voice agent
      await room.connect(url, token)
      
    } catch (err) {
      console.error('Failed to connect to voice agent:', err)
      setError(err.message)
      addMessage('system', `Connection failed: ${err.message}`)
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
    if (!isConnected) {
      setError('Not connected to voice agent')
      return
    }

    try {
      setIsRecording(true)
      setError(null)

      // Simulate microphone recording for now
      if (roomRef.current && roomRef.current.localParticipant) {
        // Real LiveKit connection
        await roomRef.current.localParticipant.enableMicrophone(true)
      } else {
        // Simulation mode - just show we're listening
        console.log('Simulating microphone recording...')
      }
      
      addMessage('user', 'Listening...')
      
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