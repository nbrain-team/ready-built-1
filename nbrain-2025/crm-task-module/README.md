# CRM & Task Management Module

This is a standalone module extracted from the nBrain platform that provides comprehensive CRM and Task Management functionality.

## Features

### CRM Features
- **Client Management**: Create, update, and manage client profiles
- **Client Portal**: Dedicated client-facing portal for each client
- **Communication Tracking**: Track all emails, meetings, and interactions
- **Document Management**: Store and organize client documents
- **AI-Powered Insights**: Get intelligent insights about client relationships
- **Activity Timeline**: See all client interactions in chronological order
- **Custom Fields**: Add custom data fields for clients

### Task Management
- **Task Creation**: Create tasks linked to clients
- **Priority Management**: Set task priorities (High, Medium, Low)
- **Due Date Tracking**: Track task deadlines
- **Status Management**: Track task status (Todo, In Progress, Completed)
- **Task Assignment**: Assign tasks to team members
- **Task Comments**: Add comments and updates to tasks
- **Recurring Tasks**: Set up recurring tasks

### AI Features
- **Smart Search**: Natural language search across all client data
- **Commitment Extraction**: Automatically extract commitments from communications
- **Sentiment Analysis**: Analyze client sentiment from communications
- **Meeting Summaries**: Generate AI summaries of meetings
- **Next Steps Suggestions**: AI-suggested next actions for each client

## Directory Structure

```
crm-task-module/
├── backend/
│   ├── core/
│   │   ├── client_portal_models.py      # Database models
│   │   ├── client_portal_endpoints.py   # Main API endpoints
│   │   ├── client_portal_handler.py     # Business logic
│   │   ├── client_ai_endpoints.py       # AI feature endpoints
│   │   ├── client_ai_handler.py         # AI processing logic
│   │   ├── client_document_processor.py # Document handling
│   │   ├── crm_endpoints.py            # CRM-specific endpoints
│   │   ├── database.py                  # Database configuration
│   │   └── auth.py                      # Authentication
│   └── scripts/
│       ├── create_client_portal_tables.py    # Database setup
│       ├── add_missing_client_columns.py     # Migration scripts
│       └── add_missing_client_document_columns.py
└── frontend/
    └── src/
        ├── pages/
        │   ├── ClientPortal.tsx         # Main client portal page
        │   ├── ClientDetail.tsx         # Client details page
        │   └── NewClient.tsx            # Create new client page
        ├── components/
        │   ├── ClientAIInsights.tsx     # AI insights component
        │   ├── ClientAvatar.tsx         # Client avatar display
        │   ├── ClientSelector.tsx       # Client selection dropdown
        │   └── EditClientDialog.tsx     # Edit client dialog
        └── api.ts                       # API configuration
```

## Database Schema

### Main Tables

1. **clients** - Core client information
   - id, name, email, phone, company, status, etc.
   - Custom fields support via JSON

2. **client_tasks** - Task management
   - id, client_id, title, description, priority, status, due_date
   - Assignment and completion tracking

3. **client_communications** - Communication history
   - id, client_id, type (email/meeting/call), subject, content
   - Timestamps and participant tracking

4. **client_documents** - Document storage
   - id, client_id, filename, file_type, storage_path
   - Version control support

5. **client_activities** - Activity timeline
   - id, client_id, activity_type, description
   - Automatic tracking of all interactions

## Installation

### Backend Setup

1. **Install Python Dependencies**
```bash
pip install -r requirements.txt
```

2. **Environment Variables**
Create a `.env` file with:
```
DATABASE_URL=postgresql://user:pass@host:port/dbname
SECRET_KEY=your-secret-key
GOOGLE_API_KEY=your-google-api-key  # For AI features
GOOGLE_DRIVE_FOLDER_ID=your-folder-id  # For document storage
```

3. **Database Setup**
```bash
# Run the database creation script
python backend/scripts/create_client_portal_tables.py

# Run any migration scripts
python backend/scripts/add_missing_client_columns.py
python backend/scripts/add_missing_client_document_columns.py
```

### Frontend Setup

1. **Install Dependencies**
```bash
npm install @radix-ui/themes @radix-ui/react-icons axios
```

2. **Configure API Endpoint**
Update `frontend/src/api.ts` with your backend URL:
```typescript
const apiBaseUrl = 'http://your-backend-url';
```

## Integration Guide

### Backend Integration

1. **Add to your FastAPI app**:
```python
from crm_task_module.backend.core import client_portal_endpoints, client_ai_endpoints, crm_endpoints

# In your main.py
client_portal_endpoints.setup_client_portal_endpoints(app)
client_ai_endpoints.setup_client_ai_endpoints(app)
crm_endpoints.setup_crm_endpoints(app)
```

2. **Database Models**:
```python
from crm_task_module.backend.core.client_portal_models import Client, ClientTask, ClientCommunication
# Models will be automatically created when you run the setup script
```

### Frontend Integration

1. **Add Routes**:
```typescript
// In your router configuration
<Route path="/clients" element={<ClientPortal />} />
<Route path="/clients/:clientId" element={<ClientDetail />} />
<Route path="/clients/new" element={<NewClient />} />
```

2. **Import Components**:
```typescript
import ClientPortal from './crm-task-module/frontend/src/pages/ClientPortal';
import ClientDetail from './crm-task-module/frontend/src/pages/ClientDetail';
```

## API Endpoints

### Client Management
- `GET /clients` - List all clients
- `POST /clients` - Create new client
- `GET /clients/{id}` - Get client details
- `PUT /clients/{id}` - Update client
- `DELETE /clients/{id}` - Delete client

### Task Management
- `GET /clients/{id}/tasks` - Get client tasks
- `POST /clients/{id}/tasks` - Create task
- `PUT /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task

### Communications
- `GET /clients/{id}/communications` - Get communications
- `POST /clients/{id}/communications` - Log communication
- `GET /clients/{id}/emails` - Get email history

### AI Features
- `POST /client-ai/search` - Natural language search
- `GET /client-ai/{id}/insights` - Get AI insights
- `POST /client-ai/{id}/extract-commitments` - Extract commitments

## Customization

### Adding Custom Fields
Add to the client model's `custom_fields` JSON column:
```python
client.custom_fields = {
    "industry": "Technology",
    "annual_revenue": 1000000,
    "custom_field": "value"
}
```

### Extending Task Types
Modify the `TaskStatus` and `TaskPriority` enums in `client_portal_models.py`.

### Custom AI Prompts
Edit prompts in `client_ai_handler.py` to customize AI behavior.

## Dependencies

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- Google Generative AI (for AI features)
- python-multipart (for file uploads)

### Frontend
- React
- TypeScript
- Radix UI
- Axios

## License

This module is extracted from nBrain and follows the same license terms. 