import React, { useState } from 'react'
import LandingPage from './components/LandingPage'
import MobileDashboard from './components/MobileDashboard'
import VoiceAssistant from './VoiceAssistant'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [userEmail, setUserEmail] = useState('')
  const [showVoiceAssistant, setShowVoiceAssistant] = useState(false)

  const handleAuthSuccess = (email) => {
    console.log('Authentication successful for:', email)
    setUserEmail(email)
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
    setUserEmail('')
    setShowVoiceAssistant(false)
    // Clear any stored tokens
    localStorage.removeItem('gmail_access_token')
  }

  return (
    <div className="App">
      {!isAuthenticated ? (
        <LandingPage onAuthSuccess={handleAuthSuccess} />
      ) : showVoiceAssistant ? (
        <VoiceAssistant 
          userEmail={userEmail} 
          onBackToLanding={() => setShowVoiceAssistant(false)} 
        />
      ) : (
        <MobileDashboard 
          userEmail={userEmail} 
          onLogout={handleLogout}
          onOpenVoiceAssistant={() => setShowVoiceAssistant(true)}
        />
      )}
    </div>
  )
}

export default App