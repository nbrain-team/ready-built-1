# AI Agent Ideator Module

This is a standalone export of the AI Agent Ideator functionality from the nBrain platform.

## What's Included

- **Complete Frontend Components**: React/TypeScript components for the ideation interface
- **Backend API**: FastAPI endpoints and AI conversation handler
- **Database Schema**: SQL migration for the agent_ideas table
- **Integration Guide**: Detailed instructions for integrating into your platform
- **Opening Prompt**: Ready-to-use prompt for Cursor AI integration

## Quick Start

1. **For Cursor Integration**: Open `CURSOR_OPENING_PROMPT.md` and copy the entire content into a new Cursor window in your target project.

2. **For Manual Integration**: Follow the step-by-step guide in `INTEGRATION_INSTRUCTIONS.md`.

## Key Features

- 🤖 AI-powered conversational agent design
- 📝 Detailed specification generation
- ✏️ Inline editing of specifications
- 📊 Cost estimation (traditional vs AI approach)
- 📄 PDF export functionality
- 🚀 Production handoff workflow

## Requirements

- Python 3.8+ with FastAPI
- React with TypeScript
- PostgreSQL or compatible database
- Google Gemini API key

## File Structure

```
agent-ideator-export/
├── frontend/           # React components and utilities
├── backend/           # FastAPI endpoints and handlers
├── database/          # SQL migrations
├── INTEGRATION_INSTRUCTIONS.md
├── CURSOR_OPENING_PROMPT.md
├── requirements.txt
└── README.md
```

## Support

This module was extracted from the nBrain platform. For questions about the original implementation, refer to the code comments and documentation included in each file.