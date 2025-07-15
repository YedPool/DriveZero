# Service Discovery Architecture for Cerebrium

## URL Pattern
Cerebrium services follow this pattern:
```
https://api.aws.us-east-1.cerebrium.ai/v4/p-{PROJECT_ID}/{DEPLOYMENT_NAME}:{PORT}
```

## Service Registry
- **LiveKit Server**: `gmail-livekit-server:7880`
- **Token Server**: `gmail-token-server:8000` 
- **Agent Worker**: `gmail-voice-assistant-allinone:8600`

## Environment Variables for Service Discovery
```bash
CEREBRIUM_PROJECT_ID=your-project-id
LIVEKIT_DEPLOYMENT_NAME=gmail-livekit-server
TOKEN_SERVER_DEPLOYMENT_NAME=gmail-token-server
AGENT_DEPLOYMENT_NAME=gmail-voice-assistant-allinone
```

## Communication Flow
1. **Frontend** → **Token Server** (gets JWT token)
2. **Token Server** → **LiveKit Server** (validates credentials) 
3. **Frontend** → **LiveKit Server** (WebRTC connection using token)
4. **LiveKit Server** → **Agent Worker** (triggers voice processing)

## Auto-Discovery Functions
Each service includes helper functions to discover other services automatically.