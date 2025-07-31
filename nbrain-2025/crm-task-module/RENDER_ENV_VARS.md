# Render Environment Variables for CRM/Task Module

This document lists all environment variables needed to deploy the CRM/Task module on Render.

## Required Environment Variables

### 1. Database Configuration
```bash
DATABASE_URL=postgresql://username:password@hostname:5432/database_name
```
- **Example**: `postgresql://crm_user:secure_password@dpg-xyz123.render.com:5432/crm_db`
- **Note**: Render provides this automatically when you create a PostgreSQL database

### 2. Security
```bash
SECRET_KEY=your-very-long-random-secret-key-here
```
- **Generate with**: `openssl rand -hex 32`
- **Example**: `a9f3b2c8d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1`

### 3. AI Configuration (Choose One)

#### Option A: Google AI (Gemini)
```bash
GOOGLE_API_KEY=your-google-ai-api-key
# OR
GEMINI_API_KEY=your-gemini-api-key
```
- **Get from**: https://makersuite.google.com/app/apikey

#### Option B: OpenAI
```bash
OPENAI_API_KEY=sk-your-openai-api-key
```
- **Get from**: https://platform.openai.com/api-keys

### 4. Google Drive Integration (For Document Storage)
```bash
GOOGLE_DRIVE_FOLDER_ID=1ABC123DEF456GHI789JKL
GOOGLE_SERVICE_ACCOUNT_KEY={"type":"service_account","project_id":"your-project"...}
```
- **Note**: The service account key should be the entire JSON content as a single line

### 5. Email Integration (Optional - For Gmail Sync)
```bash
GOOGLE_CLIENT_ID=123456789012-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-1234567890abcdefghij
GOOGLE_REDIRECT_URI=https://your-app.onrender.com/oauth/callback
```
- **Get from**: Google Cloud Console OAuth 2.0 credentials

### 6. Application Settings
```bash
ENVIRONMENT=production
DEBUG=False
CORS_ORIGINS=["https://your-frontend.onrender.com","https://your-domain.com"]
```

### 7. File Upload Settings
```bash
MAX_UPLOAD_SIZE_MB=10
ALLOWED_FILE_TYPES=["pdf","doc","docx","txt","png","jpg","jpeg","xlsx","xls"]
```

### 8. Redis Configuration (Optional - For Caching)
```bash
REDIS_URL=redis://default:password@red-xyz123.render.com:6379
```
- **Note**: Only if you're using Redis for caching

## Render-Specific Settings

### 9. Python Version
```bash
PYTHON_VERSION=3.11
```

### 10. Build Command
In Render dashboard, set:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Setting Environment Variables in Render

1. **Navigate to your service** in the Render dashboard
2. Click on **"Environment"** in the left sidebar
3. Click **"Add Environment Variable"**
4. Add each variable one by one

### Pro Tips:

1. **Use Environment Groups**: Create a group for shared variables across services
2. **Secret Files**: For the Google Service Account key, use Render's secret files feature:
   - Create a secret file named `google-credentials.json`
   - Reference it as: `GOOGLE_SERVICE_ACCOUNT_KEY_PATH=/etc/secrets/google-credentials.json`

3. **Database URL**: If using Render's PostgreSQL:
   - It's automatically set as `DATABASE_URL`
   - Internal connection string is faster than external

## Minimal Setup (Quick Start)

For a minimal working deployment, you only need:

```bash
# Required
DATABASE_URL=postgresql://...  # Auto-provided by Render PostgreSQL
SECRET_KEY=your-32-char-secret-key

# Pick one AI provider
GOOGLE_API_KEY=your-google-ai-key
# OR
OPENAI_API_KEY=sk-your-openai-key

# Basic CORS
CORS_ORIGINS=["https://your-frontend-domain.com"]
```

## Environment Variable Template

Copy this template and fill in your values:

```bash
# Database (auto-provided by Render)
DATABASE_URL=

# Security (generate with: openssl rand -hex 32)
SECRET_KEY=

# AI Provider (choose one)
GOOGLE_API_KEY=
# OPENAI_API_KEY=

# Google Drive (optional)
GOOGLE_DRIVE_FOLDER_ID=
GOOGLE_SERVICE_ACCOUNT_KEY=

# Email Integration (optional)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=https://your-app.onrender.com/oauth/callback

# Application
ENVIRONMENT=production
DEBUG=False
CORS_ORIGINS=["https://your-frontend.com"]

# File Settings
MAX_UPLOAD_SIZE_MB=10
ALLOWED_FILE_TYPES=["pdf","doc","docx","txt","png","jpg","jpeg"]
```

## Troubleshooting

1. **Database Connection Issues**:
   - Ensure `DATABASE_URL` includes `?sslmode=require` for external connections
   - Use internal database URL for better performance

2. **CORS Errors**:
   - Make sure your frontend URL is in `CORS_ORIGINS`
   - Include both with and without trailing slashes

3. **File Upload Issues**:
   - Render has a 100MB request size limit
   - Consider using external storage (S3, Google Cloud Storage) for large files

4. **Memory Issues**:
   - Upgrade to at least 512MB RAM for AI features
   - Consider using background workers for heavy AI tasks 