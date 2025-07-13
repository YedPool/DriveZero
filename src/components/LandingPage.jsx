import React, { useState, useEffect } from 'react'

// MODIFICATION START: Use environment variables for sensitive data
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID
const DISCOVERY_DOC = 'https://www.googleapis.com/discovery/v1/apis/gmail/v1/rest'
const SCOPES = import.meta.env.VITE_GMAIL_SCOPES || 'https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.modify'
// MODIFICATION END

function LandingPage({ onAuthSuccess }) {
  const [isLoading, setIsLoading] = useState(false)
  const [gApiReady, setGApiReady] = useState(false)

  useEffect(() => {
    initializeGoogleAPI()
  }, [])

  const initializeGoogleAPI = async () => {
    try {
      // Wait for Google APIs to load
      if (typeof window.gapi === 'undefined') {
        console.log('Google API not loaded yet, retrying...')
        setTimeout(initializeGoogleAPI, 100)
        return
      }

      await new Promise((resolve) => window.gapi.load('client', resolve))
      
      await window.gapi.client.init({
        discoveryDocs: [DISCOVERY_DOC],
      })

      setGApiReady(true)
      console.log('Google API initialized successfully')
    } catch (error) {
      console.error('Error initializing Google API:', error)
    }
  }

  const handleGoogleSignIn = async () => {
    if (!gApiReady) {
      alert('Google API not ready yet. Please wait a moment and try again.')
      return
    }

    setIsLoading(true)

    try {
      // MODIFICATION START: Improved OAuth flow with better error handling
      console.log('Starting Google OAuth flow...')
      
      // Initialize Google Identity Services token client
      const tokenClient = window.google.accounts.oauth2.initTokenClient({
        client_id: GOOGLE_CLIENT_ID,
        scope: SCOPES,
        callback: async (response) => {
          console.log('OAuth response received:', response)
          
          if (response.error) {
            console.error('OAuth error:', response.error)
            alert(`Authentication failed: ${response.error}`)
            setIsLoading(false)
            return
          }

          try {
            // Set the access token for Gmail API calls
            window.gapi.client.setToken({ access_token: response.access_token })
            
            // Store token securely
            localStorage.setItem('gmail_access_token', response.access_token)
            localStorage.setItem('token_expires_at', Date.now() + (response.expires_in * 1000))
            
            console.log('Access token set successfully')
            
            // Test Gmail API connection
            const testResponse = await window.gapi.client.gmail.users.getProfile({
              userId: 'me'
            })
            
            console.log('Gmail API test successful:', testResponse)
            
            // Get user email from profile
            const userEmail = testResponse.result.emailAddress
            console.log('User email:', userEmail)
            
            // Success! Navigate to dashboard
            onAuthSuccess(userEmail)
            
          } catch (apiError) {
            console.error('Gmail API error:', apiError)
            alert('Connected to Google but failed to access Gmail. Please check permissions.')
            setIsLoading(false)
          }
        },
        error_callback: (error) => {
          console.error('OAuth initialization error:', error)
          alert('Failed to initialize authentication. Please try again.')
          setIsLoading(false)
        }
      })

      // Request access token with user consent
      tokenClient.requestAccessToken({ 
        prompt: 'consent',
        include_granted_scopes: true
      })
      // MODIFICATION END

    } catch (error) {
      console.error('Authentication setup error:', error)
      setIsLoading(false)
      alert('Authentication setup failed. Please check your internet connection and try again.')
    }
  }

  // MODIFICATION START: Check if environment variables are configured
  const isConfigured = GOOGLE_CLIENT_ID && 
                      GOOGLE_CLIENT_ID !== 'your-actual-client-id.apps.googleusercontent.com' &&
                      GOOGLE_CLIENT_ID.includes('.apps.googleusercontent.com')
  // MODIFICATION END

  return (
    <section style={styles.heroSection}>
      <header style={styles.heroHeader}>
        <img 
          src="/drivezero-logo.png" 
          alt="DriveZero Logo" 
          style={styles.logoImage}
        />
      </header>
      
      <div style={styles.heroContent}>
        <div style={styles.contentWrapper}>
          <h1 style={styles.heroTitle}>Arrive with inbox zero.</h1>
          <p style={styles.heroSubtitle}>Empower your commute, conquer your inbox.</p>
          
          {!isConfigured && (
            <div style={styles.warningBox}>
              <p>⚠️ Google OAuth not configured</p>
              <p>Add VITE_GOOGLE_CLIENT_ID to your .env file</p>
              {!GOOGLE_CLIENT_ID && <p>Missing environment variable</p>}
            </div>
          )}
          
          <button 
            style={{
              ...styles.ctaButton,
              ...(isLoading ? styles.ctaButtonLoading : {}),
              ...((!gApiReady || !isConfigured) ? styles.ctaButtonDisabled : {})
            }}
            onClick={handleGoogleSignIn}
            disabled={isLoading || !gApiReady || !isConfigured}
          >
            {isLoading ? 'Connecting to Gmail...' : 
             !gApiReady ? 'Loading...' :
             !isConfigured ? 'OAuth Not Configured' :
             'Launch my drive!'}
          </button>
          
          {gApiReady && isConfigured && (
            <p style={styles.helpText}>
              Click to connect your Gmail account and start using voice commands
            </p>
          )}
        </div>
      </div>
    </section>
  )
}

const styles = {
  heroSection: {
    minHeight: '100vh',
    width: '100%',
    background: 'linear-gradient(rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0.2)), url("/car-dashboard-bg.png")',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
    backgroundAttachment: 'fixed',
    margin: 0,
    padding: 0,
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif',
    color: '#ffffff'
  },
  heroHeader: {
    padding: '0rem 6rem',
    zIndex: 10
  },
  logoImage: {
    height: '200px',
    width: 'auto',
    filter: 'brightness(1.2)'
  },
  heroContent: {
    flex: 1,
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'flex-start',
    padding: '0rem 6rem 2rem 6rem',
    maxWidth: '1200px',
    width: '100%',
    marginTop: '-2rem'
  },
  contentWrapper: {
    maxWidth: '600px'
  },
  heroTitle: {
    fontSize: 'clamp(3rem, 8vw, 6rem)',
    fontWeight: '700',
    lineHeight: '1.1',
    marginBottom: '1.5rem',
    letterSpacing: '-0.02em'
  },
  heroSubtitle: {
    fontSize: 'clamp(1.25rem, 3vw, 1.5rem)',
    color: '#e0e0e0',
    marginBottom: '3rem',
    fontWeight: '400',
    maxWidth: '500px'
  },
  warningBox: {
    backgroundColor: 'rgba(251, 191, 36, 0.1)',
    border: '1px solid rgba(251, 191, 36, 0.3)',
    borderRadius: '8px',
    padding: '1rem',
    marginBottom: '2rem',
    fontSize: '0.875rem',
    color: '#fbbf24'
  },
  ctaButton: {
    background: '#02a6a1',
    color: '#ffffff',
    border: 'none',
    padding: '1rem 2.5rem',
    fontSize: '1.125rem',
    fontWeight: '600',
    borderRadius: '12px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    textDecoration: 'none',
    display: 'inline-block',
    boxShadow: '0 4px 20px rgba(2, 166, 161, 0.3)',
    marginBottom: '1rem'
  },
  ctaButtonLoading: {
    background: '#028a85',
    cursor: 'not-allowed',
    opacity: '0.8'
  },
  ctaButtonDisabled: {
    background: '#6b7280',
    cursor: 'not-allowed',
    opacity: '0.6',
    boxShadow: 'none'
  },
  helpText: {
    fontSize: '0.875rem',
    color: '#d1d5db',
    marginTop: '0.5rem'
  }
}

export default LandingPage