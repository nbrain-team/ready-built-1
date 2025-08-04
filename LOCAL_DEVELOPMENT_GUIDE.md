# Local Development Guide

This guide helps you run the nBrain platform locally while using the same Render database as production.

## Quick Start

### 1. Start the Backend (Terminal 1)
```bash
./run_local.sh
```
This will:
- Use the Render database (same data as production)
- Start backend on http://localhost:8000
- Auto-reload when you make changes

### 2. Start the Frontend (Terminal 2)
```bash
./run_frontend_local.sh
```
This will:
- Start frontend on http://localhost:5173
- Connect to your local backend
- Hot-reload when you make changes

### 3. Access the Application
Open http://localhost:5173/salon in your browser

## Benefits of Local Development

1. **Instant Changes**: No waiting for Render deployments
2. **Same Data**: Uses the exact same database as production
3. **Hot Reload**: Both frontend and backend auto-reload on changes
4. **Better Debugging**: See errors immediately in terminal
5. **Faster Testing**: Test fixes in seconds, not minutes

## Testing Workflow

1. Make your code changes
2. Save the file (backend/frontend will auto-reload)
3. Test in browser immediately
4. Once working, commit and push to deploy to Render

## Troubleshooting

### Backend Issues
- Check `.env.local` exists in `nbrain-2025/backend/`
- Ensure Python 3.8+ is installed
- Check terminal for error messages

### Frontend Issues
- Check `.env.local` exists in `nbrain-2025/frontend/`
- Ensure Node.js 16+ is installed
- Clear browser cache if needed

### Database Connection
- The database URL in `.env.local` connects to your Render database
- This means you're working with real production data
- Be careful with destructive operations!

## Making Changes

### Backend Changes
1. Edit files in `nbrain-2025/backend/`
2. Backend auto-reloads
3. Test API at http://localhost:8000/docs

### Frontend Changes
1. Edit files in `nbrain-2025/frontend/`
2. Frontend hot-reloads
3. See changes instantly at http://localhost:5173

## Deploying to Production

Once your local changes work:
```bash
git add .
git commit -m "Your change description"
git push origin main
```

Render will automatically deploy your changes (takes 3-5 minutes).

## Current Issue Status

The last issue was JSON serialization errors due to infinity/NaN values. This has been fixed by:
- Checking for NULL values before division
- Validating float values are JSON-compliant
- Converting invalid values to 0

You can now test this fix locally before it deploys to Render! 