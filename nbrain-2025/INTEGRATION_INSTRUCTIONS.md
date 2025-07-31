# AI Agent Ideator Module - Integration Instructions

## Overview
This module provides a complete AI-powered agent ideation system that guides users through creating detailed specifications for custom AI agents. It includes:
- Conversational ideation interface
- Agent specification management (CRUD)
- Editable specifications with real-time updates
- PDF export functionality
- Cost estimation (traditional vs AI-powered approaches)
- Production handoff workflow

## Module Structure
```
agent-ideator-export/
├── frontend/
│   ├── components/
│   │   ├── AgentIdeator.tsx          # Main ideation chat interface
│   │   ├── AgentIdeatorEdit.tsx      # Edit existing specifications
│   │   ├── AgentSpecification.tsx    # View/edit specification details
│   │   ├── EditableSection.tsx       # Inline editing for simple fields
│   │   ├── EditableComplexSection.tsx # Inline editing for arrays
│   │   ├── TechnicalStackEditor.tsx  # Technical stack editor
│   │   └── FutureEnhancementsEditor.tsx # Future enhancements editor
│   ├── pages/
│   │   └── Agents.tsx               # Main page component
│   └── utils/
│       └── pdfGenerator.ts          # PDF export functionality
├── backend/
│   └── core/
│       ├── agent_ideator_endpoints.py # API endpoints
│       ├── agent_ideator_models.py    # Database models
│       └── ideator_handler.py         # AI conversation logic
├── database/
│   └── migrations/
│       └── create_agent_ideas_table.sql # Database schema
├── requirements.txt                     # Python dependencies
└── INTEGRATION_INSTRUCTIONS.md          # This file
```

## Prerequisites
1. **Backend**: FastAPI application with SQLAlchemy ORM
2. **Frontend**: React application with TypeScript
3. **Database**: PostgreSQL (or any SQLAlchemy-compatible database)
4. **AI**: Google Gemini API key (stored as `GEMINI_API_KEY` environment variable)
5. **Authentication**: User authentication system with `get_current_active_user` dependency

## Backend Integration

### Step 1: Database Setup
1. Run the SQL migration to create the `agent_ideas` table:
```sql
-- Run the contents of database/migrations/create_agent_ideas_table.sql
```

2. Add the AgentIdea model to your SQLAlchemy models:
```python
# In your database.py or models.py
from backend.core.agent_ideator_models import AgentIdea

# Add to your User model if you have one:
agent_ideas = relationship("AgentIdea", back_populates="user")
```

### Step 2: API Endpoints Setup
1. Copy the backend files to your project:
```bash
cp backend/core/agent_ideator_endpoints.py YOUR_PROJECT/backend/core/
cp backend/core/ideator_handler.py YOUR_PROJECT/backend/core/
```

2. In your main FastAPI app file:
```python
from backend.core.agent_ideator_endpoints import setup_agent_ideator_endpoints
from backend.core.ideator_handler import process_ideation_message, process_edit_message
from your_app.database import get_db, AgentIdea
from your_app.auth import get_current_active_user

# After creating your FastAPI app
app = FastAPI()

# Setup the agent ideator endpoints
setup_agent_ideator_endpoints(
    app=app,
    get_db=get_db,
    get_current_active_user=get_current_active_user,
    AgentIdea=AgentIdea,
    process_ideation_message=process_ideation_message,
    process_edit_message=process_edit_message
)
```

### Step 3: Environment Variables
Add to your `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Step 4: Install Python Dependencies
```bash
pip install -r requirements.txt
```

## Frontend Integration

### Step 1: Install NPM Dependencies
```bash
npm install @radix-ui/themes @radix-ui/react-icons react-markdown remark-gfm jspdf html2canvas
```

### Step 2: Copy Frontend Files
1. Copy all component files from `frontend/components/` to your React project's components directory
2. Copy `frontend/pages/Agents.tsx` to your pages directory
3. Copy `frontend/utils/pdfGenerator.ts` to your utils directory

### Step 3: API Configuration
Create or update your API configuration file:
```typescript
// api.ts or similar
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### Step 4: Add Routes
Add the agent ideator route to your React Router:
```tsx
import Agents from './pages/Agents';

// In your router configuration
<Route path="/agent-ideas" element={<Agents />} />
```

### Step 5: Add Navigation
Add a navigation link to access the Agent Ideator:
```tsx
// In your navigation component
<Link to="/agent-ideas">AI Agent Ideator</Link>
```

## Customization Options

### 1. Styling
The components use Radix UI themes. To customize:
- Update color variables in your CSS
- Modify size props in components
- Adjust spacing using Radix UI's gap and padding props

### 2. Agent Types
To add new agent types, update `AGENT_TEMPLATES` in `ideator_handler.py`:
```python
AGENT_TEMPLATES = {
    "your_new_type": {
        "name": "Your Agent Type",
        "description": "Description",
        "initial_questions": ["Question 1", "Question 2"]
    }
}
```

### 3. Cost Estimation
Modify the cost calculation logic in `ideator_handler.py` in the `generate_agent_specification` function.

### 4. PDF Export
Customize the PDF layout in `pdfGenerator.ts` by modifying the `generateAgentSpecPDF` function.

## API Endpoints

The module provides these endpoints:

- `POST /agent-ideas` - Create new agent specification
- `GET /agent-ideas` - List all agent specifications
- `GET /agent-ideas/{id}` - Get specific specification
- `PUT /agent-ideas/{id}` - Update specification
- `PUT /agent-ideas/{id}/full-update` - Full update of specification
- `DELETE /agent-ideas/{id}` - Delete specification
- `POST /agent-ideator/chat` - Handle ideation conversation
- `POST /agent-ideator/edit` - Handle edit conversation
- `POST /agent-ideas/move-to-production` - Send to production team

## Troubleshooting

### Common Issues

1. **"GEMINI_API_KEY not found"**
   - Ensure the environment variable is set
   - Restart your backend server after setting it

2. **Database errors**
   - Ensure the migration has been run
   - Check that foreign key to users table exists

3. **CORS issues**
   - Add your frontend URL to CORS allowed origins in FastAPI

4. **Streaming not working**
   - Ensure your reverse proxy (if any) supports SSE
   - Check that `text/event-stream` responses aren't being buffered

### Debug Mode
Enable debug logging in `ideator_handler.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Production Considerations

1. **Rate Limiting**: Add rate limiting to the AI endpoints to prevent abuse
2. **Caching**: Consider caching agent specifications for better performance
3. **Background Jobs**: Move email sending to a background job queue
4. **File Storage**: For PDF exports, consider using cloud storage instead of local
5. **Monitoring**: Add logging and monitoring for AI API usage and costs

## Support

For issues or questions about integration:
1. Check the component PropTypes for required props
2. Review the API endpoint documentation in the code
3. Ensure all dependencies are installed
4. Check browser console and server logs for errors

## License

This module is provided as-is for integration into your existing platform. Ensure you comply with all third-party licenses, especially for Radix UI and Google Gemini. 