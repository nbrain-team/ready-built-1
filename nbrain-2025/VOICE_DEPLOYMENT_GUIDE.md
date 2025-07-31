# Voice AI Ideator - Deployment Guide for Render

## 🚀 Overview

This guide will help you deploy the Voice AI Ideator to Render and configure Twilio webhooks for phone integration.

## 📋 Prerequisites

- Render account with your app deployed
- Twilio account with phone number: `+18884886019`
- API Keys already configured in the code

## 🔧 Step 1: Deploy to Render

### Update your `render.yaml` (if using):

```yaml
services:
  - type: web
    name: nbrain-backend
    env: python
    buildCommand: "cd backend && pip install -r requirements.txt && python scripts/db_setup.py"
    startCommand: "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: nbrain-db
          property: connectionString
      - key: ELEVENLABS_API_KEY
        value: sk_a3a33b78b9a5c6b6a6194afb5ec699a2ee54701ac35d66dd
      - key: DEEPGRAM_API_KEY
        value: e43ec55c7676465f2fecd506ed8258976b85c76a
      - key: TWILIO_ACCOUNT_SID
        value: YOUR_TWILIO_ACCOUNT_SID_HERE
      - key: TWILIO_AUTH_TOKEN
        value: Ti8SKXTiZXt9UCZZelknygxUBf5FDGNb
      - key: TWILIO_PHONE_NUMBER
        value: +18884886019
```

### Or add environment variables manually in Render Dashboard:

1. Go to your service in Render
2. Navigate to "Environment"
3. Add these variables:
   - `ELEVENLABS_API_KEY`
   - `DEEPGRAM_API_KEY`
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_PHONE_NUMBER`

## 🔗 Step 2: Configure Twilio Webhook

### Get your Render URL:
Your backend URL will be something like: `https://nbrain-backend-xxxx.onrender.com`

### Configure Twilio:

1. **Log into Twilio Console**: https://console.twilio.com

2. **Navigate to Phone Numbers**:
   - Go to "Phone Numbers" → "Manage" → "Active Numbers"
   - Click on your number: `+18884886019`

3. **Configure Voice Webhook**:
   - In the "Voice Configuration" section
   - Set "A call comes in" to: **Webhook**
   - URL: `https://your-render-backend-url.onrender.com/twilio/voice`
   - HTTP Method: **POST**

4. **Save the configuration**

## 🧪 Step 3: Test Your Setup

### Test Web Interface:
1. Visit: `https://your-frontend-url.onrender.com/voice-ideator`
2. Click the phone icon to connect
3. Press the microphone to start talking

### Test Phone Integration:
1. Call `1-888-488-6019`
2. You should hear: "Welcome to nBrain AI Ideator. I'll connect you with our AI assistant now."
3. Start speaking naturally about your agent idea

## 🛠️ Step 4: Monitoring & Debugging

### Check Render Logs:
```bash
# In Render dashboard, go to "Logs" tab
# Look for:
- "Deepgram STT connected successfully"
- "ElevenLabs TTS connected successfully"
- "Incoming call from +1XXXXXXXXXX"
```

### Test Webhook Manually:
```bash
curl -X POST https://your-backend-url.onrender.com/twilio/voice \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567890&CallSid=test123"
```

### Common Issues:

1. **WebSocket Connection Failed**:
   - Ensure Render supports WebSocket (it does on paid plans)
   - Check CORS settings

2. **Twilio Webhook Not Reaching Render**:
   - Verify the URL is correct
   - Check Render logs for incoming requests
   - Ensure your service is deployed and running

3. **Audio Issues**:
   - Verify API keys are correct
   - Check browser permissions for microphone
   - Monitor WebSocket messages in browser console

## 📊 Step 5: Production Considerations

### Security:
1. Enable Twilio request validation (already in code)
2. Use environment variables for all keys
3. Set up HTTPS (Render does this automatically)

### Scaling:
1. Monitor concurrent calls
2. Consider upgrading Render plan for more resources
3. Implement call queuing if needed

### Cost Management:
- ElevenLabs: Monitor character usage
- Deepgram: Track minutes transcribed
- Twilio: Monitor call minutes

## 🎯 Quick Test Commands

### Test Voice APIs:
```bash
cd backend
python test_voice_apis.py
```

### Make Outbound Call (via API):
```bash
curl -X POST https://your-backend-url.onrender.com/twilio/outbound \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"phone_number": "+1234567890", "initial_message": "Hello from nBrain"}'
```

## 📱 Twilio Configuration Details

- **Account SID**: YOUR_TWILIO_ACCOUNT_SID_HERE
- **Phone Number**: +18884886019 (1-888-488-6019)
- **Webhook URL**: `https://your-backend.onrender.com/twilio/voice`
- **WebSocket URL**: Auto-configured in the code

## ✅ Verification Checklist

- [ ] Backend deployed to Render
- [ ] Environment variables set
- [ ] Twilio webhook configured
- [ ] Test call successful
- [ ] Web interface working
- [ ] Logs showing connections

## 🆘 Support

If you encounter issues:
1. Check Render logs first
2. Verify all API keys are correct
3. Test each component individually
4. Monitor the WebSocket connections

Your Voice AI Ideator is now ready to handle both web and phone conversations! 🎉 