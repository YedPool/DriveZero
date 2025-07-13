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
  const [showApiKeyPrompt, setShowApiKeyPrompt] = useState(false)
  const [restApiKey, setRestApiKey] = useState('')

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
      
      // Skip deployment - connect directly to our deployed Cerebrium voice agent
      addMessage('ai', 'Connecting to deployed voice assistant...')
      
      // Connect to LiveKit room
      await connect()
      
      addMessage('ai', 'Voice assistant ready! Press the microphone button to start speaking.')
      
    } catch (error) {
      console.error('Failed to initialize voice agent:', error)
      addMessage('ai', 'Failed to connect to voice assistant. Please check your configuration.')
    } finally {
      setIsDeploying(false)
    }
  }

  const handleApiKeySubmit = async () => {
    if (!restApiKey.trim()) {
      alert('Please enter a valid REST API key')
      return
    }
    
    try {
      setIsDeploying(true)
      setShowApiKeyPrompt(false)
      
      // Set the key in the API service
      cerebriumApi.restApiKey = restApiKey
      
      // Deploy voice agent on Cerebrium
      await cerebriumApi.deployVoiceAgent()
      
      // Connect to LiveKit room
      await connect()
      
      addMessage('ai', 'Voice assistant ready! Press the microphone button to start speaking.')
      
    } catch (error) {
      console.error('Failed to initialize voice agent:', error)
      addMessage('ai', 'Failed to initialize voice assistant. Please check your REST API key and configuration.')
      setShowApiKeyPrompt(true)
    } finally {
      setIsDeploying(false)
    }
  }

  const handleVoiceInteraction = async () => {
    if (!isConnected) {
      setMessages(prev => [...prev, {
        type: 'ai',
        content: 'Please wait for voice assistant to connect.',
        timestamp: new Date()
      }])
      return
    }

    if (isRecording) {
      // Stop recording
      await stopRecording()
      setMessages(prev => [...prev, {
        type: 'system',
        content: 'Processing your request...',
        timestamp: new Date()
      }])
    } else {
      // Start recording
      await startRecording()
      setMessages(prev => [...prev, {
        type: 'system',
        content: 'Listening... Speak now!',
        timestamp: new Date()
      }])
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <h1 style={styles.title}>DriveZero Assistant</h1>
          <div style={styles.status}>
            <div style={{
              ...styles.statusDot,
              backgroundColor: isConnected ? '#10b981' : (isDeploying ? '#f59e0b' : '#ef4444')
            }}></div>
            <span>
              {isDeploying ? 'Initializing...' : 
               isConnected ? 'Voice Assistant Ready' : 
               'Voice Assistant Offline'}
            </span>
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
            ...(isRecording ? styles.voiceButtonActive : {}),
            ...(isDeploying || !isConnected ? styles.voiceButtonDisabled : {})
          }}
          onClick={handleVoiceInteraction}
          disabled={isDeploying || !isConnected}
        >
          <div style={styles.micIcon}>🎤</div>
          <div style={styles.voiceButtonText}>
            {isDeploying ? 'Initializing...' :
             !isConnected ? 'Connecting...' :
             isRecording ? 'Listening...' : 'Press to speak'}
          </div>
          {error && (
            <div style={styles.errorText}>
              {error}
            </div>
          )}
        </button>
      </div>

      {/* API Key Prompt Modal */}
      {showApiKeyPrompt && (
        <div style={styles.modalOverlay}>
          <div style={styles.modal}>
            <h3 style={styles.modalTitle}>Cerebrium REST API Key Required</h3>
            <p style={styles.modalText}>
              To deploy the voice agent, please enter your Cerebrium REST API (Session Token):
            </p>
            <input
              type="text"
              value={restApiKey}
              onChange={(e) => setRestApiKey(e.target.value)}
              placeholder="Enter your Cerebrium session token..."
              style={styles.modalInput}
            />
            <div style={styles.modalButtons}>
              <button 
                onClick={() => setShowApiKeyPrompt(false)}
                style={styles.modalCancelButton}
              >
                Cancel
              </button>
              <button 
                onClick={handleApiKeySubmit}
                style={styles.modalSubmitButton}
                disabled={!restApiKey.trim()}
              >
                Deploy Agent
              </button>
            </div>
          </div>
        </div>
      )}
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
  },
  voiceButtonDisabled: {
    backgroundColor: '#9ca3af',
    cursor: 'not-allowed',
    opacity: '0.6'
  },
  errorText: {
    fontSize: '0.65rem',
    color: '#ef4444',
    textAlign: 'center',
    marginTop: '0.25rem'
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000
  },
  modal: {
    backgroundColor: '#ffffff',
    padding: '2rem',
    borderRadius: '12px',
    maxWidth: '500px',
    width: '90%',
    maxHeight: '80vh',
    overflow: 'auto',
    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
  },
  modalTitle: {
    fontSize: '1.25rem',
    fontWeight: '600',
    color: '#1e293b',
    margin: '0 0 1rem 0'
  },
  modalText: {
    fontSize: '0.95rem',
    color: '#64748b',
    lineHeight: '1.5',
    margin: '0 0 1.5rem 0'
  },
  modalInput: {
    width: '100%',
    padding: '0.75rem',
    border: '1px solid #e2e8f0',
    borderRadius: '6px',
    fontSize: '0.95rem',
    marginBottom: '1.5rem',
    boxSizing: 'border-box'
  },
  modalButtons: {
    display: 'flex',
    gap: '0.75rem',
    justifyContent: 'flex-end'
  },
  modalCancelButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#f1f5f9',
    border: '1px solid #e2e8f0',
    borderRadius: '6px',
    cursor: 'pointer',
    color: '#475569',
    fontSize: '0.875rem'
  },
  modalSubmitButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#02a6a1',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    color: '#ffffff',
    fontSize: '0.875rem',
    fontWeight: '500'
  }
}


export default VoiceAssistant