"""
Example integration of CRM/Task module into an existing FastAPI application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Add the module to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the setup functions
from backend.core.client_portal_endpoints import setup_client_portal_endpoints
from backend.core.client_ai_endpoints import setup_client_ai_endpoints
from backend.core.crm_endpoints import setup_crm_endpoints

# Import database setup
from backend.core.database import engine, Base

# Create your FastAPI app
app = FastAPI(title="My App with CRM")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Add CRM endpoints to your app
setup_client_portal_endpoints(app)
setup_client_ai_endpoints(app)
setup_crm_endpoints(app)

# Your existing routes
@app.get("/")
def read_root():
    return {"message": "Welcome to My App with CRM"}

# Add any other existing routes here...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 