import React from 'react'
import { createRoot } from 'react-dom/client'

function App() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>Voice Email Assistant</h1>
      <p>Basic setup is working!</p>
      
      <div style={{ marginTop: '20px' }}>
        <h2>What's Working:</h2>
        <ul>
          <li>✓ React is running</li>
          <li>✓ Vite dev server is working</li>
          <li>✓ Ready to add Gmail integration</li>
        </ul>
      </div>

      <div style={{ marginTop: '20px' }}>
        <h2>Next Steps:</h2>
        <ul>
          <li>Add Gmail API script to index.html</li>
          <li>Create vanilla JS backend files</li>
          <li>Test Gmail OAuth connection</li>
        </ul>
      </div>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)