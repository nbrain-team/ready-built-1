# nBrain 2025 + Generic RAG Platform Deployment Guide

## Overview
This guide will help you deploy the integrated nBrain 2025 platform with the Generic RAG module on Render.

## Prerequisites
- GitHub account
- Render account
- Required API keys (see Environment Variables section)

## Step-by-Step Deployment

### 1. GitHub Setup

1. Commit all changes:
```bash
git add .
git commit -m "Integrate Generic RAG platform into nBrain 2025"
```

2. Create a new GitHub repository and push:
```bash
git remote add origin https://github.com/YOUR_USERNAME/nbrain-rag-platform.git
git branch -M main
git push -u origin main
```

### 2. Render Setup

1. Log in to [Render Dashboard](https://dashboard.render.com)

2. Create a new PostgreSQL Database:
   - Click "New +" → "PostgreSQL"
   - Name: `nbrain-rag-db`
   - Database: `nbrain_rag_production`
   - User: `nbrain_rag_user`
   - Region: Oregon (US West)
   - Plan: Pro (for production)
   - Click "Create Database"
   - Save the Internal Database URL

3. Create Backend Service:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Name: `nbrain-rag-backend`
   - Region: Oregon (US West)
   - Branch: main
   - Root Directory: `nbrain-2025/backend`
   - Runtime: Docker
   - Plan: Pro
   - Click "Create Web Service"

4. Create Frontend Service:
   - Click "New +" → "Static Site"
   - Connect your GitHub repository
   - Name: `nbrain-rag-frontend`
   - Branch: main
   - Root Directory: `nbrain-2025/frontend`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `dist`
   - Click "Create Static Site"

### 3. Environment Variables

In the Backend Service settings, add these environment variables:

#### Required Variables:
```
DATABASE_URL=<Internal Database URL from step 2>
OPENAI_API_KEY=<Your OpenAI API key>
GEMINI_API_KEY=<Your Google Gemini API key>
PINECONE_API_KEY=<Your Pinecone API key>
PINECONE_INDEX_NAME=<Your Pinecone index name>
PINECONE_ENVIRONMENT=<Your Pinecone environment>
```

#### Google OAuth (for Oracle features):
```
GOOGLE_CLIENT_ID=<Your Google OAuth client ID>
GOOGLE_CLIENT_SECRET=<Your Google OAuth client secret>
GOOGLE_REDIRECT_URI=https://nbrain-rag-backend.onrender.com/oracle/auth/callback
GOOGLE_SERVICE_ACCOUNT_JSON=<Your service account JSON>
```

#### Voice Services (optional):
```
DEEPGRAM_API_KEY=<Your Deepgram API key>
ELEVENLABS_API_KEY=<Your ElevenLabs API key>
TWILIO_ACCOUNT_SID=<Your Twilio account SID>
TWILIO_AUTH_TOKEN=<Your Twilio auth token>
TWILIO_PHONE_NUMBER=<Your Twilio phone number>
```

#### Other Services (optional):
```
CLOUDINARY_API_KEY=<Your Cloudinary API key>
CLOUDINARY_API_SECRET=<Your Cloudinary API secret>
CLOUDINARY_CLOUD_NAME=<Your Cloudinary cloud name>
BRIGHTDATA_API_TOKEN=<Your Bright Data API token>
BRIGHTDATA_BROWSER_URL=<Your Bright Data browser URL>
SERP_API_KEY=<Your SERP API key>
```

### 4. Frontend Environment Variables

In the Frontend Service settings, add:
```
VITE_API_BASE_URL=https://nbrain-rag-backend.onrender.com
```

### 5. Database Migration

After the backend is deployed, run the migration:

1. Go to the Backend Service dashboard
2. Click "Shell" tab
3. Run:
```bash
python run_migration.py
psql $DATABASE_URL -f database/migrations/add_rag_tables.sql
```

### 6. Verify Deployment

1. Check backend health: `https://nbrain-rag-backend.onrender.com/health`
2. Check RAG health: `https://nbrain-rag-backend.onrender.com/api/rag/health`
3. Access frontend: `https://nbrain-rag-frontend.onrender.com`

## Local Development

### Using Docker Compose:

1. Create `.env` file with your API keys:
```env
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
PINECONE_INDEX_NAME=your_index_here
PINECONE_ENVIRONMENT=your_env_here
```

2. Start services:
```bash
docker-compose up
```

3. Access:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000
   - Database: localhost:5432

### Manual Setup:

1. Backend:
```bash
cd nbrain-2025/backend
pip install -r requirements.txt
python main.py
```

2. Frontend:
```bash
cd nbrain-2025/frontend
npm install
npm run dev
```

## Using the RAG Module

### 1. Create Data Source
- Navigate to the RAG Chat interface
- Click "Upload Data" in the sidebar
- Define your data schema

### 2. Upload Data
- Prepare CSV file with your data
- Upload through the interface
- Wait for processing to complete

### 3. Query Your Data
- Select data sources in the sidebar
- Ask questions in natural language
- Use drill-down buttons for deeper insights

## Troubleshooting

### Common Issues:

1. **Database Connection Error**
   - Verify DATABASE_URL is correct
   - Check if database is running
   - Ensure migrations have been run

2. **API Key Errors**
   - Verify all required API keys are set
   - Check for typos or extra spaces
   - Ensure keys have proper permissions

3. **Build Failures**
   - Check build logs in Render dashboard
   - Verify all dependencies are listed
   - Ensure Dockerfile paths are correct

### Support Resources:
- Render Documentation: https://render.com/docs
- nBrain Issues: Create issue in your GitHub repo
- RAG Module: Check logs for detailed error messages

## Security Considerations

1. **API Keys**: Never commit API keys to Git
2. **Database**: Use strong passwords and SSL connections
3. **CORS**: Configure allowed origins in production
4. **Authentication**: Ensure JWT secrets are strong and unique

## Performance Optimization

1. **Database Indexes**: RAG tables include optimized indexes
2. **Caching**: Redis is configured for session management
3. **Connection Pooling**: Optimized for concurrent requests
4. **Data Limits**: RAG queries limited to 100 results by default

## Next Steps

1. Configure data sources for your use case
2. Customize AI prompts in RAG configurations
3. Set up monitoring and alerts in Render
4. Configure custom domains if needed 