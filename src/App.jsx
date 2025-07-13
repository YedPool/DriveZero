import React, { useState } from 'react'
import LandingPage from './components/LandingPage'
import MobileDashboard from './components/MobileDashboard'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [userEmail, setUserEmail] = useState('')

  const handleAuthSuccess = (email) => {
    console.log('Authentication successful for:', email)
    setUserEmail(email)
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
    setUserEmail('')
    // Clear any stored tokens
    localStorage.removeItem('gmail_access_token')
  }

  return (
    <div className="App">
      {!isAuthenticated ? (
        <LandingPage onAuthSuccess={handleAuthSuccess} />
      ) : (
        <MobileDashboard userEmail={userEmail} onLogout={handleLogout} />
      )}
    </div>
  )
}

export default App