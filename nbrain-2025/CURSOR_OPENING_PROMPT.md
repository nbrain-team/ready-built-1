# AI Agent Ideator Integration - Cursor Opening Prompt

Copy and paste this entire prompt into your new Cursor window to begin the integration:

---

I need to integrate an AI Agent Ideator module into this project. The module is a complete system for creating AI agent specifications through a conversational interface.

## Module Overview
The AI Agent Ideator is a sophisticated tool that:
- Guides users through creating detailed AI agent specifications via conversation
- Manages agent ideas with full CRUD operations
- Provides inline editing of specifications
- Generates PDF exports of specifications
- Estimates costs (traditional vs AI-powered approaches)
- Handles production handoff workflow

## Files to Integrate

I have the following files in the `agent-ideator-export` folder:

**Frontend Components:**
- `frontend/components/AgentIdeator.tsx` - Main ideation chat interface
- `frontend/components/AgentIdeatorEdit.tsx` - Edit existing specifications
- `frontend/components/AgentSpecification.tsx` - View/edit specification details
- `frontend/components/EditableSection.tsx` - Inline editing for simple fields
- `frontend/components/EditableComplexSection.tsx` - Inline editing for arrays
- `frontend/components/TechnicalStackEditor.tsx` - Technical stack editor
- `frontend/components/FutureEnhancementsEditor.tsx` - Future enhancements editor
- `frontend/pages/Agents.tsx` - Main page component
- `frontend/utils/pdfGenerator.ts` - PDF export functionality

**Backend Files:**
- `backend/core/agent_ideator_endpoints.py` - FastAPI endpoints
- `backend/core/agent_ideator_models.py` - SQLAlchemy models
- `backend/core/ideator_handler.py` - AI conversation logic

**Database:**
- `database/migrations/create_agent_ideas_table.sql` - Database schema

**Documentation:**
- `INTEGRATION_INSTRUCTIONS.md` - Detailed integration guide
- `requirements.txt` - Python dependencies

## Integration Requirements

Please help me integrate this module by:

1. **Analyzing my current project structure** to understand:
   - FastAPI backend setup and authentication system
   - React frontend structure and routing
   - Database configuration (SQLAlchemy)
   - Current API patterns and conventions

2. **Adapting the module** to fit my project:
   - Update import paths to match my project structure
   - Integrate with my existing authentication system
   - Match my API endpoint patterns
   - Align with my database models structure

3. **Setting up the backend**:
   - Add the AgentIdea model to my database
   - Run the SQL migration
   - Integrate the API endpoints into my FastAPI app
   - Ensure the ideator_handler works with my setup

4. **Setting up the frontend**:
   - Install required npm packages
   - Copy components to appropriate directories
   - Update the API client configuration
   - Add routing for the agent ideator page
   - Integrate with my existing navigation

5. **Handling dependencies**:
   - Ensure all Python packages are installed
   - Verify Google Gemini API key is configured
   - Set up any missing environment variables

## Key Technical Details

- The module uses **Google Gemini** for AI conversations (requires `GEMINI_API_KEY`)
- Frontend uses **Radix UI** for components
- Supports **streaming responses** for real-time chat
- Uses **react-markdown** for formatting
- Exports to **PDF** using jspdf and html2canvas

## Expected Outcome

After integration, users should be able to:
1. Access the AI Agent Ideator from the navigation
2. Start a new agent ideation conversation
3. View, edit, and delete existing agent specifications
4. Export specifications as PDFs
5. Send specifications to production team

Please analyze my project structure first, then provide step-by-step instructions for integrating this module while maintaining consistency with my existing codebase.

---

**Note**: After pasting this prompt, make sure to have the `agent-ideator-export` folder accessible in your project directory. 