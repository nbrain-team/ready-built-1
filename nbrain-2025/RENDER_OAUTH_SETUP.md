# Google OAuth Setup for Render Deployment

## Environment Variables to Add in Render Dashboard

### For Backend Service (nbrain-backend)

1. Go to your Render Dashboard
2. Click on your backend service (nbrain-backend)
3. Go to "Environment" tab
4. Add these environment variables:

```
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
GOOGLE_REDIRECT_URI=https://<your-frontend-url>.onrender.com/oracle/auth/callback
SECRET_KEY=<generate-a-random-secret-key>
```

### Important Notes:

1. **GOOGLE_REDIRECT_URI**: Must match EXACTLY what you put in Google Cloud Console
   - Format: `https://nbrain-frontend-xxxx.onrender.com/oracle/auth/callback`
   - Replace `xxxx` with your actual Render service ID

2. **Finding Your Render URLs**:
   - Frontend URL: Look at your frontend service in Render dashboard
   - Backend URL: Look at your backend service in Render dashboard
   - They'll be in format: `https://service-name-xxxx.onrender.com`

3. **Security**:
   - Never commit these values to git
   - Use Render's environment variable management
   - Keep your Client Secret secure

## Steps to Configure:

1. **In Render Dashboard**:
   - Navigate to your backend service
   - Click "Environment" in the left sidebar
   - Click "Add Environment Variable"
   - Add each variable one by one

2. **Update Google Cloud Console**:
   - Go to APIs & Services → Credentials
   - Edit your OAuth 2.0 Client ID
   - Add your production redirect URI:
     `https://your-frontend-url.onrender.com/oracle/auth/callback`
   - Save changes

3. **Deploy Changes**:
   - After adding environment variables, Render will automatically redeploy
   - Wait for the deployment to complete (usually 5-10 minutes)

## Testing Production OAuth:

1. Visit your production site: `https://your-frontend-url.onrender.com`
2. Navigate to Oracle page
3. Click "Connect" on Gmail
4. Should redirect to Google OAuth
5. After approval, should redirect back to your production Oracle page

## Troubleshooting:

### "Redirect URI mismatch" error:
- Ensure the URI in Google Console matches EXACTLY
- Check for trailing slashes
- Verify https vs http
- Confirm the Render service name is correct

### "Invalid client" error:
- Verify GOOGLE_CLIENT_ID is set correctly in Render
- Check that GOOGLE_CLIENT_SECRET is set (won't be visible after saving)
- Ensure no extra spaces in the environment variables

### Connection fails silently:
- Check Render logs for your backend service
- Look for OAuth-related error messages
- Verify all required environment variables are set 