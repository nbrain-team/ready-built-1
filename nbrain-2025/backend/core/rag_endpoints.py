"""
RAG API Endpoints for nBrain
Provides chat, data management, and configuration endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid
import json
import os
from datetime import datetime
from sqlalchemy import func

from .database import get_db, User
from .auth import get_current_active_user
from .rag_handler import RAGHandler
from .rag_models import DataSource, DataEntry, RAGChatHistory, RAGConfiguration

# Pydantic models for requests/responses
class RAGChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}

class RAGChatResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    session_id: str
    drill_downs: Optional[List[Dict[str, Any]]] = []
    data_context: Optional[Dict[str, Any]] = {}

class DataSourceCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = ""
    config: Dict[str, Any]

class DataSourceResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    config: Dict[str, Any]
    created_at: datetime
    entry_count: Optional[int] = 0

class RAGConfigurationCreate(BaseModel):
    config_type: str
    config_data: Dict[str, Any]

def setup_rag_endpoints(app):
    """Setup RAG endpoints on the main FastAPI app"""
    
    router = APIRouter(prefix="/api/rag", tags=["rag"])
    
    @router.get("/health")
    async def rag_health_check():
        """Check RAG system health"""
        return {"status": "healthy", "module": "rag"}
    
    @router.post("/chat", response_model=RAGChatResponse)
    async def rag_chat(
        request: RAGChatRequest,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Process a RAG chat query"""
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Initialize handler
        handler = RAGHandler(db, current_user)
        
        # Process query
        result = handler.process_chat_query(
            query=request.query,
            session_id=session_id,
            context=request.context
        )
        
        return RAGChatResponse(**result)
    
    @router.get("/chat/history/{session_id}")
    async def get_chat_history(
        session_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get chat history for a session"""
        history = db.query(RAGChatHistory).filter(
            RAGChatHistory.session_id == session_id,
            RAGChatHistory.user_id == current_user.id
        ).order_by(RAGChatHistory.created_at).all()
        
        return {
            "session_id": session_id,
            "messages": [
                {
                    "query": h.query,
                    "response": h.response,
                    "timestamp": h.created_at.isoformat(),
                    "context": h.context_data
                }
                for h in history
            ]
        }
    
    @router.get("/chat/sessions")
    async def get_chat_sessions(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get all chat sessions for the user"""
        sessions = db.query(
            RAGChatHistory.session_id,
            func.min(RAGChatHistory.created_at).label('started_at'),
            func.max(RAGChatHistory.created_at).label('last_message_at'),
            func.count(RAGChatHistory.id).label('message_count')
        ).filter(
            RAGChatHistory.user_id == current_user.id
        ).group_by(RAGChatHistory.session_id).all()
        
        return {
            "sessions": [
                {
                    "session_id": s.session_id,
                    "started_at": s.started_at.isoformat(),
                    "last_message_at": s.last_message_at.isoformat(),
                    "message_count": s.message_count
                }
                for s in sessions
            ]
        }
    
    @router.get("/data-sources", response_model=List[DataSourceResponse])
    async def get_data_sources(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get all available data sources"""
        sources = db.query(DataSource).all()
        
        # Add entry counts
        response = []
        for source in sources:
            entry_count = db.query(DataEntry).filter(
                DataEntry.source_id == source.id
            ).count()
            
            response.append(DataSourceResponse(
                id=source.id,
                name=source.name,
                display_name=source.display_name,
                description=source.description,
                config=source.config,
                created_at=source.created_at,
                entry_count=entry_count
            ))
        
        return response
    
    @router.post("/data-sources", response_model=DataSourceResponse)
    async def create_data_source(
        data: DataSourceCreate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Create a new data source"""
        # Check if source already exists
        existing = db.query(DataSource).filter(
            DataSource.name == data.name
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Data source already exists")
        
        # Create new source
        source = DataSource(
            name=data.name,
            display_name=data.display_name,
            description=data.description,
            config=data.config
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        
        return DataSourceResponse(
            id=source.id,
            name=source.name,
            display_name=source.display_name,
            description=source.description,
            config=source.config,
            created_at=source.created_at,
            entry_count=0
        )
    
    @router.post("/data-sources/{source_id}/upload")
    async def upload_data(
        source_id: int,
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Upload data file for a data source"""
        # Verify source exists
        source = db.query(DataSource).filter(DataSource.id == source_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Data source not found")
        
        # Save uploaded file
        file_path = f"/tmp/rag_upload_{uuid.uuid4()}_{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process in background
        background_tasks.add_task(
            process_data_upload,
            file_path,
            source.name,
            source.config,
            current_user.id,
            db
        )
        
        return {
            "message": "File uploaded successfully. Processing in background.",
            "source_id": source_id
        }
    
    @router.get("/configurations")
    async def get_configurations(
        config_type: Optional[str] = None,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get RAG configurations"""
        query = db.query(RAGConfiguration).filter(
            RAGConfiguration.user_id == current_user.id,
            RAGConfiguration.is_active == True
        )
        
        if config_type:
            query = query.filter(RAGConfiguration.config_type == config_type)
        
        configs = query.all()
        
        return {
            "configurations": [
                {
                    "id": c.id,
                    "config_type": c.config_type,
                    "config_data": c.config_data,
                    "created_at": c.created_at.isoformat(),
                    "updated_at": c.updated_at.isoformat()
                }
                for c in configs
            ]
        }
    
    @router.post("/configurations")
    async def create_configuration(
        data: RAGConfigurationCreate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Create or update RAG configuration"""
        # Deactivate existing configs of same type
        db.query(RAGConfiguration).filter(
            RAGConfiguration.user_id == current_user.id,
            RAGConfiguration.config_type == data.config_type
        ).update({"is_active": False})
        
        # Create new config
        config = RAGConfiguration(
            user_id=current_user.id,
            config_type=data.config_type,
            config_data=data.config_data
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        
        return {
            "id": config.id,
            "config_type": config.config_type,
            "config_data": config.config_data,
            "created_at": config.created_at.isoformat()
        }
    
    # Include the router in the app
    app.include_router(router)

def process_data_upload(file_path: str, source_name: str, config: Dict[str, Any], user_id: int, db: Session):
    """Background task to process uploaded data"""
    try:
        from .database import SessionLocal
        from .rag_handler import RAGHandler
        
        # Create new session for background task
        db = SessionLocal()
        user = db.query(User).filter(User.id == user_id).first()
        
        handler = RAGHandler(db, user)
        success = handler.load_data_from_csv(file_path, source_name, config)
        
        # Clean up
        os.remove(file_path)
        db.close()
        
        return success
    except Exception as e:
        print(f"Error processing data upload: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
        return False 