import React, { useState, useEffect } from 'react'

function Dashboard({ userEmail, onLogout }) {
  const [isConnected, setIsConnected] = useState(true)
  const [emailCount, setEmailCount] = useState(0)

  useEffect(() => {
    testGmailConnection()
  }, [])

  const testGmailConnection = async () => {
    try {
      const response = await window.gapi.client.gmail.users.messages.list({
        userId: 'me',
        maxResults: 10
      })
      
      setEmailCount(response.result.resultSizeEstimate || 0)
      console.log('Gmail connection successful:', response.result)
    } catch (error) {
      console.error('Gmail connection failed:', error)
      setIsConnected(false)
    }
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <h1 style={styles.title}>DriveZero Dashboard</h1>
          <div style={styles.userInfo}>
            <span style={styles.email}>{userEmail}</span>
            <div style={styles.status}>
              <div style={{
                ...styles.statusDot,
                backgroundColor: isConnected ? '#10b981' : '#ef4444'
              }}></div>
              <span>{isConnected ? 'Gmail Connected' : 'Connection Error'}</span>
            </div>
          </div>
        </div>
        <button style={styles.logoutButton} onClick={onLogout}>
          Logout
        </button>
      </div>

      {/* Main Content */}
      <div style={styles.mainContent}>
        <div style={styles.welcomeSection}>
          <h2 style={styles.welcomeTitle}>Welcome to your voice email assistant!</h2>
          <p style={styles.welcomeText}>
            Your Gmail account is connected. You have approximately {emailCount.toLocaleString()} emails in your account.
          </p>
        </div>

        <div style={styles.featuresGrid}>
          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>📧</div>
            <h3 style={styles.featureTitle}>Read Emails</h3>
            <p style={styles.featureDescription}>
              Say "Read my emails" to hear your latest messages
            </p>
          </div>

          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>✉️</div>
            <h3 style={styles.featureTitle}>Send Emails</h3>
            <p style={styles.featureDescription}>
              Say "Send an email to John" to compose and send messages
            </p>
          </div>

          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🔍</div>
            <h3 style={styles.featureTitle}>Search Emails</h3>
            <p style={styles.featureDescription}>
              Say "Find emails about project" to search your inbox
            </p>
          </div>

          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🎤</div>
            <h3 style={styles.featureTitle}>Voice Control</h3>
            <p style={styles.featureDescription}>
              Natural conversation with your email assistant
            </p>
          </div>
        </div>

        <div style={styles.nextSteps}>
          <h3 style={styles.nextStepsTitle}>What's Next?</h3>
          <ul style={styles.nextStepsList}>
            <li>✅ Gmail OAuth integration working</li>
            <li>🔄 Voice recognition (coming next)</li>
            <li>🔄 AI integration with OpenAI/Gemini</li>
            <li>🔄 RAG for email context</li>
            <li>🔄 Email operations (read, send, search)</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

const styles = {
  container: {
    minHeight: '100vh',
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
    fontSize: '1.75rem',
    fontWeight: '600',
    color: '#1e293b',
    margin: 0
  },
  userInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem'
  },
  email: {
    fontSize: '0.875rem',
    color: '#64748b'
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
  logoutButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#ef4444',
    color: '#ffffff',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '0.875rem',
    fontWeight: '500'
  },
  mainContent: {
    padding: '2rem',
    maxWidth: '1200px',
    margin: '0 auto'
  },
  welcomeSection: {
    textAlign: 'center',
    marginBottom: '3rem'
  },
  welcomeTitle: {
    fontSize: '2rem',
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: '1rem'
  },
  welcomeText: {
    fontSize: '1.125rem',
    color: '#64748b',
    maxWidth: '600px',
    margin: '0 auto'
  },
  featuresGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '1.5rem',
    marginBottom: '3rem'
  },
  featureCard: {
    backgroundColor: '#ffffff',
    padding: '1.5rem',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
    textAlign: 'center',
    border: '1px solid #e2e8f0'
  },
  featureIcon: {
    fontSize: '2rem',
    marginBottom: '1rem'
  },
  featureTitle: {
    fontSize: '1.125rem',
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: '0.5rem'
  },
  featureDescription: {
    fontSize: '0.875rem',
    color: '#64748b',
    lineHeight: '1.5'
  },
  nextSteps: {
    backgroundColor: '#ffffff',
    padding: '2rem',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
    border: '1px solid #e2e8f0'
  },
  nextStepsTitle: {
    fontSize: '1.25rem',
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: '1rem'
  },
  nextStepsList: {
    listStyle: 'none',
    padding: 0,
    margin: 0
  }
}

export default Dashboard