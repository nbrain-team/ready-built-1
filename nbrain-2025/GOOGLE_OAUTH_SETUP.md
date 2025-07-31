# Google OAuth Setup Guide for nBrain Oracle

## Overview
This guide will help you set up Google OAuth2 to enable Gmail and Calendar integration in the Oracle feature.

## Prerequisites
- Google Cloud Console account
- Access to your nBrain backend environment variables

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name your project (e.g., "nBrain Oracle")
4. Click "Create"

## Step 2: Enable Required APIs

1. In your project, go to "APIs & Services" → "Library"
2. Search for and enable these APIs:
   - Gmail API
   - Google Calendar API
   - Google Drive API (optional, for future features)

## Step 3: Create OAuth2 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen first:
   - Choose "External" user type
   - Fill in required fields:
     - App name: "nBrain Oracle"
     - User support email: your email
     - Developer contact: your email
   - Add scopes:
     - `../auth/gmail.readonly`
     - `../auth/calendar.readonly`
     - `../auth/drive.readonly`
   - Add test users (your email and any test accounts)

4. Create OAuth client:
   - Application type: "Web application"
   - Name: "nBrain Oracle Web Client"
   - Authorized redirect URIs:
     - For local development: `http://localhost:3000/oracle/auth/callback`
     - For production: `https://yourdomain.com/oracle/auth/callback`
   - Click "Create"

5. Save your credentials:
   - Client ID: `GOOGLE_CLIENT_ID`
   - Client Secret: `GOOGLE_CLIENT_SECRET`

## Step 4: Configure Environment Variables

Add these to your backend `.env` file:

```bash
# Google OAuth2
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:3000/oracle/auth/callback
```

For production, update `GOOGLE_REDIRECT_URI` to your production URL.

## Step 5: Handle OAuth Callback in Frontend

The Oracle page needs to handle the OAuth callback. Add this route to your React app:

```typescript
// In App.tsx or your router configuration
<Route path="/oracle/auth/callback" element={<OracleAuthCallback />} />
```

Create the callback component:

```typescript
// frontend/src/pages/OracleAuthCallback.tsx
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

const OracleAuthCallback = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const handleCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');

      if (code && state) {
        try {
          await api.get(`/oracle/oauth/callback?code=${code}&state=${state}`);
          navigate('/oracle', { state: { message: 'Successfully connected!' } });
        } catch (error) {
          console.error('OAuth callback error:', error);
          navigate('/oracle', { state: { error: 'Failed to connect' } });
        }
      }
    };

    handleCallback();
  }, [navigate]);

  return <div>Connecting your account...</div>;
};

export default OracleAuthCallback;
```

## Step 6: Email Sync Configuration

To configure email filtering (only threads you've responded to), the backend needs to be updated:

```python
# In oracle_handler.py, update the sync_emails method:
# Change the query to filter for threads with your replies
query = f'from:me after:{(datetime.now() - timedelta(days=90)).strftime("%Y/%m/%d")}'
```

## Troubleshooting

### "Nothing happens when clicking Connect"
1. Check browser console for errors (F12)
2. Verify environment variables are set
3. Check backend logs for missing credentials
4. Ensure frontend is making the correct API call

### "Invalid redirect URI"
1. Ensure the redirect URI in Google Console matches exactly
2. Include protocol (http/https) and port if applicable
3. Add both localhost and production URLs

### "Access blocked: This app's request is invalid"
1. Make sure OAuth consent screen is configured
2. Add test users if in development
3. Verify all required scopes are added

## Security Notes

1. Never commit credentials to version control
2. Use environment variables for all sensitive data
3. In production, consider encrypting stored OAuth tokens
4. Implement token refresh logic for long-term access

## Testing

1. Click "Connect" on Gmail in Oracle page
2. You should be redirected to Google's consent screen
3. Grant permissions
4. You'll be redirected back to the Oracle page
5. The Gmail source should show as "connected"
6. Click sync to import emails

## Next Steps

After setup:
1. The system will sync emails from the last 90 days
2. Only threads where you've sent replies will be processed
3. Action items will be automatically extracted
4. Email content will be vectorized for semantic search 