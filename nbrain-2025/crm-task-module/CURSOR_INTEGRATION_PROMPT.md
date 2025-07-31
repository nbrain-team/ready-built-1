# Cursor AI Prompt Template for CRM/Task Module Integration

Copy and paste this prompt into Cursor when you want to integrate the CRM/Task module into your project:

---

## Integration Prompt

I want to integrate a CRM and Task Management module into my existing project. The module is located in the `crm-task-module` directory and includes:

**Backend Features:**
- Client management (CRUD operations)
- Task management linked to clients
- Communication tracking (emails, meetings, calls)
- Document management with Google Drive integration
- AI-powered features (insights, commitment extraction, natural language search)
- Activity timeline tracking

**Frontend Features:**
- Client portal with list and detail views
- Task management interface
- AI insights dashboard
- Document upload/management
- Communication history

**My current project structure:**
```
[Describe your project structure here]
- Backend: [FastAPI/Django/Flask/etc]
- Frontend: [React/Vue/Angular/etc]
- Database: [PostgreSQL/MySQL/etc]
- Current authentication: [JWT/Session/OAuth/etc]
```

**Integration requirements:**
1. Add the CRM endpoints to my existing backend at [your backend location]
2. Integrate the frontend components into my app at [your frontend location]
3. Set up the database tables alongside my existing schema
4. Connect to my existing authentication system
5. Style the components to match my current design system

**Specific customizations needed:**
- [ ] Modify the client model to include these additional fields: [list any]
- [ ] Change the API base URL to: [your API URL]
- [ ] Update the styling to use my existing CSS/component library: [library name]
- [ ] Add these custom task statuses: [list any]
- [ ] Integrate with my existing user/auth system

Please help me:
1. Set up the database migrations
2. Integrate the backend endpoints
3. Add the frontend routes and components
4. Update the authentication to use my existing system
5. Provide the environment variables I need to add

---

## Alternative Prompts for Specific Tasks

### 1. Backend-Only Integration

```
I need to integrate only the backend CRM functionality from the crm-task-module into my FastAPI application. 

My main.py is located at: [path]
My database models are at: [path]
I'm using [SQLAlchemy/Tortoise/etc] for ORM

Please help me:
1. Add the CRM models to my existing database
2. Set up the API endpoints with my URL prefix: /api/v1/crm
3. Integrate with my existing authentication decorator: @require_auth
4. Add the necessary migrations
```

### 2. Frontend-Only Integration

```
I want to add the CRM frontend components from crm-task-module to my React application.

My app structure:
- Components are in: src/components
- Pages are in: src/pages  
- API client is at: src/services/api.js
- I'm using [Material-UI/Tailwind/etc] for styling

Please help me:
1. Copy and adapt the CRM components
2. Set up the routing for /crm/* paths
3. Update the API calls to use my existing API client
4. Restyle components to match my design system
```

### 3. Database Setup Only

```
I need to set up the CRM database tables in my existing PostgreSQL database.

Current setup:
- Database name: [your_db]
- I have these existing tables: [users, products, etc]
- Using [Alembic/Django migrations/etc]

Please create:
1. Migration scripts that won't conflict with existing tables
2. Indexes for optimal performance
3. Foreign key relationships to my users table
```

### 4. Custom Field Addition

```
I need to extend the CRM module's Client model with industry-specific fields:

Additional fields needed:
- industry_sector (enum: tech, finance, healthcare, retail)
- annual_revenue (decimal)
- employee_count (integer)
- contract_value (decimal)
- renewal_date (date)
- account_manager_id (foreign key to users)

Please update:
1. The database model
2. The API endpoints to handle these fields
3. The frontend forms to include these fields
4. Add validation for the new fields
```

### 5. AI Feature Configuration

```
I want to configure the AI features in the CRM module to use [OpenAI/Google AI/Local LLM].

My setup:
- AI Provider: [OpenAI/Google/etc]
- API Key location: [env var name]
- Specific requirements: [any constraints]

Please:
1. Update the AI handler to use my provider
2. Modify the prompts for my industry: [industry]
3. Add rate limiting to prevent excessive API calls
4. Set up caching for AI responses
```

### 6. Authentication Integration

```
I need to integrate the CRM module with my existing authentication system.

My auth setup:
- Using [JWT/OAuth/Session-based] authentication
- User model location: [path]
- Auth middleware: [details]
- User ID field: [user_id/id/uuid]

Please update:
1. All endpoints to use my auth decorators
2. Database queries to filter by current user
3. Frontend API calls to include auth headers
4. User references in the database models
```

## Tips for Using These Prompts

1. **Be Specific**: Include actual file paths and names
2. **Provide Context**: Describe your existing project structure
3. **List Constraints**: Mention any limitations or requirements
4. **Incremental Approach**: Start with one component (backend OR frontend)
5. **Test First**: Ask for test cases for the integration

## Common Follow-up Prompts

After initial integration, you might need:

```
"Now help me create unit tests for the integrated CRM endpoints"

"Add error handling and logging to match my existing patterns"

"Create a migration script to import my existing customer data"

"Set up a development environment with docker-compose"

"Add API documentation using [Swagger/ReDoc]"

"Implement role-based access control for the CRM features"
```

## Environment-Specific Prompts

### For Docker Deployment
```
"Create a Dockerfile and docker-compose.yml that includes the CRM module with my existing services"
```

### For Kubernetes
```
"Generate Kubernetes manifests for deploying the CRM module alongside my existing pods"
```

### For Serverless
```
"Adapt the CRM module to work with [AWS Lambda/Vercel/Netlify Functions]"
```

---

Remember to provide as much context as possible about your existing project for the best integration results! 