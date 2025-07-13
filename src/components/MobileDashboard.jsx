import React, { useState, useEffect } from 'react'

function MobileDashboard({ userEmail, onLogout }) {
  const [emailData, setEmailData] = useState({
    primary: 42,
    updates: 15,
    social: 8,
    promotions: 23
  })
  const [isListening, setIsListening] = useState(false)
  const [isConnected, setIsConnected] = useState(true)

  useEffect(() => {
    // Fetch real Gmail data when component mounts
    fetchGmailData()

  }, [])

  const fetchGmailData = async () => {
    try {
      // Get real Gmail category counts
      console.log('Fetching Gmail data...')
      
      // Get messages from each category
      const primaryResponse = await window.gapi.client.gmail.users.messages.list({
        userId: 'me',
        labelIds: ['INBOX', 'CATEGORY_PERSONAL'],
        maxResults: 500
      })
      
      const updatesResponse = await window.gapi.client.gmail.users.messages.list({
        userId: 'me',
        labelIds: ['CATEGORY_UPDATES'],
        maxResults: 500
      })
      
      const socialResponse = await window.gapi.client.gmail.users.messages.list({
        userId: 'me',
        labelIds: ['CATEGORY_SOCIAL'],
        maxResults: 500
      })
      
      const promotionsResponse = await window.gapi.client.gmail.users.messages.list({
        userId: 'me',
        labelIds: ['CATEGORY_PROMOTIONS'],
        maxResults: 500
      })

      setEmailData({
        primary: primaryResponse.result.resultSizeEstimate || 0,
        updates: updatesResponse.result.resultSizeEstimate || 0,
        social: socialResponse.result.resultSizeEstimate || 0,
        promotions: promotionsResponse.result.resultSizeEstimate || 0
      })
      
      console.log('Gmail data updated:', emailData)
      
    } catch (error) {
      console.error('Failed to fetch Gmail data:', error)
      setIsConnected(false)
    }
  }

  const handleVoicePress = () => {
    setIsListening(!isListening)
    // Voice recognition will be implemented here
    console.log('Voice button pressed, listening:', !isListening)
    
    if (!isListening) {
      // Start listening
      console.log('Starting voice recognition...')
      // Web Speech API integration will go here
    } else {
      // Stop listening
      console.log('Stopping voice recognition...')
    }
  }

  return (
    <div style={styles.container}>
      {/* Background with overlay */}
      <div style={styles.background}></div>
      
      {/* Header with logout */}
      <div style={styles.header}>
        <button style={styles.logoutButton} onClick={onLogout}>
          ← Back
        </button>
      </div>

      {/* Main email display circles */}
      <div style={styles.emailDisplay}>
        {/* Large Primary circle */}
        <div style={styles.primaryCircleContainer}>
          <div style={{...styles.circle, ...styles.primaryCircle}}>
            <span style={styles.primaryNumber}>{emailData.primary}</span>
            <span style={styles.primaryLabel}>Primary</span>
          </div>
        </div>

        {/* Smaller category circles */}
        <div style={styles.categoryCircles}>
          <div style={{...styles.circle, ...styles.categoryCircle}}>
            <span style={styles.categoryNumber}>{emailData.updates}</span>
            <span style={styles.categoryLabel}>Updates</span>
          </div>
          
          <div style={{...styles.circle, ...styles.categoryCircle}}>
            <span style={styles.categoryNumber}>{emailData.social}</span>
            <span style={styles.categoryLabel}>Social</span>
          </div>
          
          <div style={{...styles.circle, ...styles.categoryCircle}}>
            <span style={styles.categoryNumber}>{emailData.promotions}</span>
            <span style={styles.categoryLabel}>Promotions</span>
          </div>
        </div>
      </div>

      {/* Voice interface at bottom */}
      <div style={styles.voiceContainer}>
        <button 
          style={{
            ...styles.voiceButton,
            ...(isListening ? styles.voiceButtonActive : {})
          }}
          onClick={handleVoicePress}
        >
          <img src="/microphone-icon.png" alt="Microphone" style={styles.micImage} />
        </button>
      </div>

      {/* Connection status indicator */}
      {!isConnected && (
        <div style={styles.statusWarning}>
          Gmail connection lost
        </div>
      )}
    </div>
  )
}

// Mobile-optimized styles with dynamic circles
const styles = {
  container: {
    position: 'relative',
    height: '100vh',
    width: '100vw',
    maxWidth: '428px', // iPhone 14 Pro Max width
    margin: '0 auto',
    display: 'flex',
    flexDirection: 'column',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif',
    overflow: 'hidden'
  },
  background: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'linear-gradient(rgba(0, 50, 50, 0.3), rgba(0, 50, 50, 0.5)), url("/mobile-dashboard-bg.png")',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
    zIndex: -1
  },
  header: {
    padding: '1rem',
    display: 'flex',
    justifyContent: 'flex-start',
    alignItems: 'center',
    zIndex: 10
  },
  logoutButton: {
    background: 'rgba(255, 255, 255, 0.2)',
    color: '#ffffff',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    borderRadius: '20px',
    padding: '0.5rem 1rem',
    fontSize: '0.875rem',
    cursor: 'pointer',
    backdropFilter: 'blur(10px)'
  },
  emailDisplay: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '2rem 1rem',
    gap: '3rem'
  },
  primaryCircleContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center'
  },
  categoryCircles: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '1.5rem',
    flexWrap: 'wrap'
  },
  circle: {
    borderRadius: '50%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
    backdropFilter: 'blur(10px)',
    border: '1px solid rgba(255, 255, 255, 0.2)'
  },
  primaryCircle: {
    width: '180px',
    height: '180px',
    background: 'rgba(2, 166, 161, 0.9)',
    color: '#ffffff'
  },
  categoryCircle: {
    width: '100px',
    height: '100px',
    background: 'rgba(255, 255, 255, 0.9)',
    color: '#02a6a1'
  },
  primaryNumber: {
    fontSize: '3.5rem',
    fontWeight: '700',
    lineHeight: '1',
    marginBottom: '0.25rem'
  },
  primaryLabel: {
    fontSize: '1.125rem',
    fontWeight: '500',
    opacity: '0.9'
  },
  categoryNumber: {
    fontSize: '1.75rem',
    fontWeight: '700',
    lineHeight: '1',
    marginBottom: '0.25rem'
  },
  categoryLabel: {
    fontSize: '0.75rem',
    fontWeight: '500',
    opacity: '0.8'
  },
  voiceContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '2rem',
    paddingBottom: '3rem'
  },
  voiceButton: {
    width: '80px',
    height: '80px',
    borderRadius: '50%',
    background: 'rgba(2, 166, 161, 0.9)',
    border: 'none',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    boxShadow: '0 8px 32px rgba(2, 166, 161, 0.4)',
    backdropFilter: 'blur(10px)'
  },
  voiceButtonActive: {
    background: 'rgba(239, 68, 68, 0.9)',
    transform: 'scale(1.1)',
    boxShadow: '0 12px 40px rgba(239, 68, 68, 0.5)'
  },
  statusWarning: {
    position: 'absolute',
    top: '4rem',
    left: '50%',
    transform: 'translateX(-50%)',
    background: 'rgba(239, 68, 68, 0.9)',
    color: '#ffffff',
    padding: '0.5rem 1rem',
    borderRadius: '20px',
    fontSize: '0.75rem',
    backdropFilter: 'blur(10px)'
  }
}

export default MobileDashboard