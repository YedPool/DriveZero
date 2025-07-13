import { useState, useEffect } from 'react'
import { useVoiceAgent } from './hooks/useVoiceAgent'
import cerebriumApi from './services/cerebriumApi'

function VoiceAssistant({ onBackToLanding, userEmail }) {
  const { 
    isConnected, 
    isRecording, 
    error, 
    messages: voiceMessages, 
    connect, 
    disconnect, 
    startRecording, 
    stopRecording,
    addMessage 
  } = useVoiceAgent()
  
  const [messages, setMessages] = useState([])
  const [isDeploying, setIsDeploying] = useState(false)

  useEffect(() => {
    // Add welcome message and initialize voice agent
    setMessages([
      {
        type: 'ai',
        content: 'Hi! I\'m your voice email assistant. Initializing voice connection...',
        timestamp: new Date()
      }
    ])
    
    // Auto-connect to voice agent on component mount
    initializeVoiceAgent()
  }, [])

  // Sync voice messages with local messages
  useEffect(() => {
    if (voiceMessages.length > 0) {
      setMessages(prev => [...prev, ...voiceMessages])
    }
  }, [voiceMessages])

  const initializeVoiceAgent = async () => {
    try {
      setIsDeploying(true)
      
      // Deploy voice agent on Cerebrium
      await cerebriumApi.deployVoiceAgent()
      
      // Connect to LiveKit room
      await connect()
      
      addMessage('ai', 'Voice assistant ready! Press the microphone button to start speaking.')
      
    } catch (error) {
      console.error('Failed to initialize voice agent:', error)
      addMessage('ai', 'Failed to initialize voice assistant. Please check your configuration.')
    } finally {
      setIsDeploying(false)
    }
  }

  const startListening = () => {
    setIsListening(true)
    // Voice recognition will go here
    console.log('Starting voice recognition...')
    
    // Simulate voice interaction
    setTimeout(() => {
      setIsListening(false)
      addMessage('user', 'What emails do I have?')
      
      // Simulate AI response
      setTimeout(() => {
        addMessage('ai', 'You have 5 unread emails. 2 are marked as important. Would you like me to read them to you?')
      }, 1000)
    }, 3000)
  }

  const addMessage = (type, content) => {
    setMessages(prev => [...prev, {
      type,
      content,
      timestamp: new Date()
    }])
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <h1 style={styles.title}>DriveZero Assistant</h1>
          <div style={styles.status}>
            <div style={{
              ...styles.statusDot,
              backgroundColor: isConnected ? '#10b981' : '#ef4444'
            }}></div>
            <span>{isConnected ? 'Connected to Gmail' : 'Disconnected'}</span>
          </div>
        </div>
        <button style={styles.backButton} onClick={onBackToLanding}>
          ← Back
        </button>
      </div>

      {/* Messages */}
      <div style={styles.messagesContainer}>
        {messages.map((message, index) => (
          <div key={index} style={{
            ...styles.message,
            ...(message.type === 'user' ? styles.userMessage : styles.aiMessage)
          }}>
            <div style={styles.messageContent}>
              {message.content}
            </div>
            <div style={styles.timestamp}>
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>

      {/* Voice Interface */}
      <div style={styles.voiceInterface}>
        <button 
          style={{
            ...styles.voiceButton,
            ...(isListening ? styles.voiceButtonActive : {})
          }}
          onClick={startListening}
          disabled={isListening}
        >
          <div style={styles.micIcon}>🎤</div>
          <div style={styles.voiceButtonText}>
            {isListening ? 'Listening...' : 'Press to speak'}
          </div>
        </button>
      </div>
    </div>
  )
}

//  Styles for voice assistant interface
const styles = {
  container: {
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#f8fafc',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif'
  },
  header: {
    padding: '1.5rem 2rem',
    backgroundColor: '#ffffff',
    borderBottom: '1px solid #e2e8f0',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  headerLeft: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem'
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: '600',
    color: '#1e293b',
    margin: 0
  },
  status: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    fontSize: '0.875rem',
    color: '#64748b'
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%'
  },
  backButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#f1f5f9',
    border: '1px solid #e2e8f0',
    borderRadius: '6px',
    cursor: 'pointer',
    color: '#475569',
    fontSize: '0.875rem'
  },
  messagesContainer: {
    flex: 1,
    padding: '1rem 2rem',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem'
  },
  message: {
    maxWidth: '80%',
    padding: '1rem',
    borderRadius: '12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.25rem'
  },
  userMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#02a6a1',
    color: '#ffffff'
  },
  aiMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#ffffff',
    color: '#1e293b',
    border: '1px solid #e2e8f0'
  },
  messageContent: {
    fontSize: '0.95rem',
    lineHeight: '1.5'
  },
  timestamp: {
    fontSize: '0.75rem',
    opacity: '0.7'
  },
  voiceInterface: {
    padding: '2rem',
    backgroundColor: '#ffffff',
    borderTop: '1px solid #e2e8f0',
    display: 'flex',
    justifyContent: 'center'
  },
  voiceButton: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '1.5rem',
    backgroundColor: '#02a6a1',
    color: '#ffffff',
    border: 'none',
    borderRadius: '50%',
    width: '120px',
    height: '120px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    boxShadow: '0 4px 20px rgba(2, 166, 161, 0.3)'
  },
  voiceButtonActive: {
    backgroundColor: '#ef4444',
    transform: 'scale(1.1)',
    boxShadow: '0 8px 30px rgba(239, 68, 68, 0.4)'
  },
  micIcon: {
    fontSize: '2rem'
  },
  voiceButtonText: {
    fontSize: '0.75rem',
    fontWeight: '500',
    textAlign: 'center'
  }
}


export default VoiceAssistant