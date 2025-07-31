"""
Client Portal API Endpoints
"""

from fastapi import HTTPException, Depends, BackgroundTasks, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from .database import get_db, User
from .auth import get_current_active_user
from .client_portal_handler import client_portal_handler
from .client_portal_models import (
    Client, ClientStatus, ClientTask, TaskStatus, TaskPriority,
    ClientCommunication, ClientDocument, ClientTeamMember, ClientActivity,
    ClientChatHistory, ClientAIAnalysis
)
import os
import tempfile
import json
from fastapi.responses import FileResponse
from .database import CRMOpportunity
from sqlalchemy import text

# Import Google Drive handler
from .google_drive_handler import google_drive_handler
from .client_document_processor import client_document_processor
from .oracle_handler import OracleDataSource

# Pydantic models for API
class ClientCreateRequest(BaseModel):
    name: str
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    company_website: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    project_value: Optional[float] = None
    estimated_end_date: Optional[datetime] = None
    sync_email_addresses: Optional[List[str]] = []

class ClientResponse(BaseModel):
    id: str
    name: str
    status: str
    primaryContactName: Optional[str] = None
    primaryContactEmail: Optional[str] = None
    primaryContactPhone: Optional[str] = None
    companyWebsite: Optional[str] = None
    domain: Optional[str] = None
    projectValue: Optional[float] = None
    healthScore: int
    lastCommunication: Optional[str] = None
    totalTasks: int
    completedTasks: int
    teamMembers: int
    createdAt: datetime

    class Config:
        from_attributes = True

class TaskCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    dueDate: Optional[datetime] = None
    assignedTo: Optional[str] = None
    createdAt: datetime

    class Config:
        from_attributes = True

class CommunicationCreateRequest(BaseModel):
    content: str
    type: str = "internal_chat"

class CommunicationResponse(BaseModel):
    id: str
    content: str
    type: str
    fromUser: str
    timestamp: datetime
    subject: Optional[str] = None
    toUsers: Optional[List[str]] = None
    syncedBy: Optional[str] = None  # Email address of user who synced this
    
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: str
    name: str
    type: str
    uploadedBy: Optional[str] = None
    uploadedAt: datetime
    fileSize: Optional[int] = None
    version: int = 1

    class Config:
        from_attributes = True

class TeamMemberRequest(BaseModel):
    user_id: str
    role: str = "member"
    can_view_financials: bool = False
    can_edit_tasks: bool = True
    can_upload_documents: bool = True

class ActivityResponse(BaseModel):
    id: str
    activity_type: str
    description: str
    created_at: datetime
    user_id: Optional[str] = None

    class Config:
        from_attributes = True

import logging
logger = logging.getLogger(__name__)
logger.info("Setting up client portal endpoints...")

import redis
from redis.exceptions import RedisError

# Initialize Redis client for caching
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    # Test connection
    redis_client.ping()
    redis_available = True
    logger.info("Redis cache connected successfully")
except (RedisError, Exception) as e:
    logger.warning(f"Redis not available, falling back to in-memory cache: {e}")
    redis_client = None
    redis_available = False

# Simple in-memory cache as fallback
memory_cache = {}
cache_timestamps = {}

def setup_client_portal_endpoints(app):
    """Add Client Portal endpoints to the FastAPI app"""
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Setting up client portal endpoints...")
    
    @app.get("/clients", response_model=List[ClientResponse])
    async def get_clients(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
        response: Response = None
    ):
        """Get all clients with caching"""
        try:
            cache_key = f"clients:{current_user.id}"
            cached_data = None
            
            # Try to get from cache
            if redis_available and redis_client:
                try:
                    cached_data = redis_client.get(cache_key)
                    if cached_data:
                        logger.info("Returning clients from Redis cache")
                        return json.loads(cached_data)
                except Exception as e:
                    logger.warning(f"Redis cache read error: {e}")
            elif cache_key in memory_cache:
                # Check if memory cache is still valid (30 seconds)
                if cache_key in cache_timestamps and \
                   (datetime.utcnow() - cache_timestamps[cache_key]).seconds < 30:
                    logger.info("Returning clients from memory cache")
                    return memory_cache[cache_key]
            
            # If not in cache, fetch from database
            logger.info("Fetching clients from database")
            
            # Use a more efficient query with joins
            from sqlalchemy.orm import joinedload
            clients = db.query(Client).options(
                joinedload(Client.team_members)
            ).order_by(Client.created_at.desc()).all()
            
            # Convert to response format
            response_data = []
            for client in clients:
                # Count active team members from the loaded relationship
                team_count = len([tm for tm in client.team_members if tm.is_active])
                
                response_data.append(ClientResponse(
                    id=client.id,
                    name=client.name,
                    status=client.status.value,
                    primaryContactName=client.primary_contact_name,
                    primaryContactEmail=client.primary_contact_email,
                    primaryContactPhone=client.primary_contact_phone,
                    companyWebsite=client.company_website,
                    domain=getattr(client, 'domain', None),
                    projectValue=client.project_value,
                    healthScore=client.health_score,
                    lastCommunication=client.last_communication.isoformat() if client.last_communication else None,
                    totalTasks=client.total_tasks,
                    completedTasks=client.completed_tasks,
                    teamMembers=team_count,
                    createdAt=client.created_at
                ))
            
            # Cache the response
            if redis_available and redis_client:
                try:
                    redis_client.setex(
                        cache_key,
                        30,  # 30 seconds TTL
                        json.dumps([r.dict() for r in response_data])
                    )
                except Exception as e:
                    logger.warning(f"Redis cache write error: {e}")
            else:
                # Use memory cache
                memory_cache[cache_key] = response_data
                cache_timestamps[cache_key] = datetime.utcnow()
            
            # Set cache headers
            if response:
                response.headers["Cache-Control"] = "public, max-age=30"
                response.headers["X-Cache"] = "MISS"
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error fetching clients: {e}")
            if "column clients.domain does not exist" in str(e):
                raise HTTPException(
                    status_code=500, 
                    detail="Database schema is out of date. Please run the domain migration."
                )
            else:
                raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/clients/aggregated-summary")
    async def get_aggregated_client_summary(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get aggregated summary across all clients"""
        try:
            # Get all active clients
            clients = db.query(Client).filter(
                Client.status.in_([ClientStatus.ACTIVE, ClientStatus.ONGOING])
            ).all()
            
            logger.info(f"Found {len(clients)} active/ongoing clients")
            
            # Get next week's meetings across all clients
            current_time = datetime.utcnow()
            one_week_later = current_time + timedelta(days=7)
            
            # Look for calendar events in ClientCommunication table
            # Note: For calendar events, created_at stores the event start time
            upcoming_meetings = db.query(ClientCommunication).join(Client).filter(
                ClientCommunication.type == "calendar_event",
                ClientCommunication.created_at >= current_time,
                ClientCommunication.created_at <= one_week_later,
                Client.status.in_([ClientStatus.ACTIVE, ClientStatus.ONGOING])
            ).order_by(ClientCommunication.created_at.asc()).limit(10).all()
            
            # Also check for any calendar events that might have been synced recently
            # but have dates in the past (in case created_at was set to sync time instead of event time)
            logger.info(f"Searching for calendar events between {current_time} and {one_week_later}")
            logger.info(f"Found {len(upcoming_meetings)} upcoming meetings")
            
            # Also log total calendar events for debugging
            total_calendar_events = db.query(ClientCommunication).filter(
                ClientCommunication.type == "calendar_event"
            ).count()
            logger.info(f"Total calendar events in database: {total_calendar_events}")
            
            # Format meetings with client info
            meetings_list = []
            for meeting in upcoming_meetings:
                client = db.query(Client).filter(Client.id == meeting.client_id).first()
                if client:
                    meetings_list.append({
                        "id": meeting.id,
                        "clientId": client.id,
                        "clientName": client.name,
                        "clientDomain": client.domain,
                        "clientWebsite": client.company_website,
                        "title": meeting.subject or "Untitled Meeting",
                        "startTime": meeting.created_at.isoformat(),
                        "attendees": meeting.to_users or []
                    })
            
            # Get sentiment issues from AI analysis
            sentiment_issues = []
            ai_analysis_count = 0
            
            for client in clients:
                # Get latest sentiment analysis
                sentiment_analysis = db.query(ClientAIAnalysis).filter(
                    ClientAIAnalysis.client_id == client.id,
                    ClientAIAnalysis.analysis_type == 'sentiment'
                ).order_by(ClientAIAnalysis.created_at.desc()).first()
                
                if sentiment_analysis:
                    ai_analysis_count += 1
                    if sentiment_analysis.result_data:
                        concerns = sentiment_analysis.result_data.get('concerns', [])
                        if concerns:
                            sentiment_issues.append({
                                "clientId": client.id,
                                "clientName": client.name,
                                "clientDomain": client.domain,
                                "clientWebsite": client.company_website,
                                "concerns": concerns[:2],  # Limit to 2 concerns per client
                                "sentiment": sentiment_analysis.result_data.get('current_sentiment', {}).get('sentiment', 'neutral'),
                                "trend": sentiment_analysis.result_data.get('trend', 'stable')
                            })
            
            logger.info(f"Found {ai_analysis_count} clients with sentiment analysis")
            
            # Get suggested tasks from AI analysis
            suggested_tasks = []
            tasks_analysis_count = 0
            
            for client in clients:
                # Get latest suggested tasks
                tasks_analysis = db.query(ClientAIAnalysis).filter(
                    ClientAIAnalysis.client_id == client.id,
                    ClientAIAnalysis.analysis_type == 'suggested_tasks'
                ).order_by(ClientAIAnalysis.created_at.desc()).first()
                
                if tasks_analysis:
                    tasks_analysis_count += 1
                    if tasks_analysis.result_data:
                        # Handle both list and dict formats
                        tasks_data = tasks_analysis.result_data
                        if isinstance(tasks_data, dict):
                            tasks = tasks_data.get('tasks', [])
                        elif isinstance(tasks_data, list):
                            tasks = tasks_data
                        else:
                            tasks = []
                            
                        for task in tasks[:2]:  # Limit to 2 tasks per client
                            # Handle task format
                            if isinstance(task, dict):
                                task_title = task.get('title', '')
                                task_priority = task.get('priority', 'medium')
                                task_reason = task.get('reason', '')
                            else:
                                # If task is a string or other format
                                task_title = str(task)
                                task_priority = 'medium'
                                task_reason = ''
                                
                            if task_title:
                                suggested_tasks.append({
                                    "clientId": client.id,
                                    "clientName": client.name,
                                    "clientDomain": client.domain,
                                    "clientWebsite": client.company_website,
                                    "task": task_title,
                                    "priority": task_priority,
                                    "reason": task_reason
                                })
            
            logger.info(f"Found {tasks_analysis_count} clients with suggested tasks analysis")
            
            return {
                "upcomingMeetings": meetings_list,
                "sentimentIssues": sentiment_issues,
                "suggestedTasks": suggested_tasks
            }
            
        except Exception as e:
            logger.error(f"Error getting aggregated summary: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "upcomingMeetings": [],
                "sentimentIssues": [],
                "suggestedTasks": []
            }
    
    @app.post("/clients", response_model=ClientResponse)
    async def create_client(
        request: ClientCreateRequest,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Create a new client"""
        client = Client(
            name=request.name,
            primary_contact_name=request.primary_contact_name,
            primary_contact_email=request.primary_contact_email,
            primary_contact_phone=request.primary_contact_phone,
            company_website=request.company_website,
            domain=request.domain,
            industry=request.industry,
            project_value=request.project_value,
            estimated_end_date=request.estimated_end_date,
            start_date=datetime.utcnow(),
            created_by=current_user.id,
            status=ClientStatus.ACTIVE,
            sync_email_addresses=request.sync_email_addresses or []
        )
        
        db.add(client)
        
        # Commit the client first to get the ID
        db.commit()
        db.refresh(client)
        
        # Create initial activity
        activity = ClientActivity(
            client_id=client.id,
            user_id=current_user.id,
            activity_type="client_created",
            description=f"Client {client.name} was created"
        )
        db.add(activity)
        
        # Create Google Drive folder
        try:
            folder_id = google_drive_handler.create_client_folder(client.name)
            if folder_id:
                logger.info(f"Created Google Drive folder for client {client.name}")
                activity = ClientActivity(
                    client_id=client.id,
                    user_id=current_user.id,
                    activity_type="drive_folder_created",
                    description=f"Google Drive folder created for client",
                    meta_data={"folder_id": folder_id}
                )
                db.add(activity)
        except Exception as e:
            logger.error(f"Error creating Google Drive folder for {client.name}: {e}")
        
        db.commit()
        db.refresh(client)
        
        return ClientResponse(
            id=client.id,
            name=client.name,
            status=client.status.value,
            primaryContactName=client.primary_contact_name,
            primaryContactEmail=client.primary_contact_email,
            primaryContactPhone=client.primary_contact_phone,
            companyWebsite=client.company_website,
            domain=client.domain,
            projectValue=client.project_value,
            healthScore=100,
            lastCommunication=None,
            totalTasks=0,
            completedTasks=0,
            teamMembers=0,
            createdAt=client.created_at
        )
    
    @app.get("/clients/{client_id}")
    async def get_client(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get client details"""
        summary = client_portal_handler.get_client_summary(client_id, db)
        if not summary:
            raise HTTPException(status_code=404, detail="Client not found")
        
        client = summary["client"]
        
        # Count emails
        total_emails = db.query(ClientCommunication).filter(
            ClientCommunication.client_id == client_id,
            ClientCommunication.type == 'email'
        ).count()
        
        # Count meetings/calendar events
        total_meetings = db.query(ClientCommunication).filter(
            ClientCommunication.client_id == client_id,
            ClientCommunication.type == 'calendar_event'
        ).count()
        
        # Count documents
        total_documents = db.query(ClientDocument).filter(
            ClientDocument.client_id == client_id
        ).count()
        
        return {
            "id": client.id,
            "name": client.name,
            "status": client.status.value,
            "primaryContactName": client.primary_contact_name,
            "primaryContactEmail": client.primary_contact_email,
            "primaryContactPhone": client.primary_contact_phone,
            "companyWebsite": client.company_website,
            "domain": client.domain,
            "syncEmailAddresses": client.sync_email_addresses or [],
            "industry": client.industry,
            "projectValue": client.project_value,
            "healthScore": summary["health_score"],
            "teamCount": summary["team_count"],
            "taskSummary": summary["task_summary"],
            "recentActivities": summary["recent_activities"],
            "totalTasks": client.total_tasks,
            "completedTasks": client.completed_tasks,
            "totalEmails": total_emails,
            "totalMeetings": total_meetings,
            "totalDocuments": total_documents,
            "lastCommunication": client.last_communication.isoformat() if client.last_communication else None
        }
    
    @app.put("/clients/{client_id}")
    async def update_client(
        client_id: str,
        request: ClientCreateRequest,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Update client information"""
        logger.info(f"PUT /clients/{client_id} called")
        logger.info(f"Request data: {request}")
        
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Update fields
        client.name = request.name
        client.primary_contact_name = request.primary_contact_name
        client.primary_contact_email = request.primary_contact_email
        client.primary_contact_phone = request.primary_contact_phone
        client.company_website = request.company_website
        client.domain = request.domain  # Use request.domain directly
        client.sync_email_addresses = request.sync_email_addresses or []
        client.industry = request.industry
        client.project_value = request.project_value
        
        # Create activity
        activity = ClientActivity(
            client_id=client_id,
            user_id=current_user.id,
            activity_type="client_updated",
            description=f"Client information updated"
        )
        db.add(activity)
        
        db.commit()
        db.refresh(client)
        
        # Return updated client with calculated fields
        team_count = db.query(ClientTeamMember).filter(
            ClientTeamMember.client_id == client.id,
            ClientTeamMember.is_active == True
        ).count()
        
        return ClientResponse(
            id=client.id,
            name=client.name,
            status=client.status.value,
            primaryContactName=client.primary_contact_name,
            primaryContactEmail=client.primary_contact_email,
            primaryContactPhone=client.primary_contact_phone,
            companyWebsite=client.company_website,
            domain=client.domain,
            projectValue=client.project_value,
            healthScore=client_portal_handler.calculate_health_score(client.id, db),
            lastCommunication=client.last_communication.isoformat() if client.last_communication else None,
            totalTasks=client.total_tasks,
            completedTasks=client.completed_tasks,
            teamMembers=team_count,
            createdAt=client.created_at
        )
    
    @app.post("/clients/{client_id}/tasks", response_model=TaskResponse)
    async def create_task(
        client_id: str,
        request: TaskCreateRequest,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Create a task for a client"""
        # Verify client exists
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        task = ClientTask(
            client_id=client_id,
            title=request.title,
            description=request.description,
            priority=TaskPriority(request.priority),
            due_date=request.due_date,
            assigned_to=request.assigned_to,
            assigned_by=current_user.id,
            status=TaskStatus.TODO
        )
        
        db.add(task)
        
        # Update client task counts
        client.total_tasks += 1
        
        # Create activity
        activity = ClientActivity(
            client_id=client_id,
            user_id=current_user.id,
            activity_type="task_created",
            description=f"Task '{task.title}' was created",
            meta_data={"task_id": task.id}
        )
        db.add(activity)
        
        db.commit()
        db.refresh(task)
        
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            dueDate=task.due_date,
            assignedTo=task.assigned_to,
            createdAt=task.created_at
        )
    
    @app.get("/clients/{client_id}/tasks", response_model=List[TaskResponse])
    async def get_tasks(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get all tasks for a client"""
        tasks = db.query(ClientTask).filter(
            ClientTask.client_id == client_id
        ).order_by(ClientTask.created_at.desc()).all()
        
        return [
            TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status.value,
                priority=task.priority.value,
                dueDate=task.due_date,
                assignedTo=task.assigned_to,
                createdAt=task.created_at
            )
            for task in tasks
        ]
    
    @app.post("/clients/{client_id}/communications", response_model=CommunicationResponse)
    async def create_communication(
        client_id: str,
        request: CommunicationCreateRequest,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Create a communication entry"""
        # Verify client exists
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        communication = ClientCommunication(
            client_id=client_id,
            type=request.type,
            content=request.content,
            from_user=current_user.email,
            to_users=[],  # Internal chat doesn't have specific recipients
            created_at=datetime.utcnow()
        )
        
        db.add(communication)
        
        # Update client's last communication timestamp
        client.last_communication = datetime.utcnow()
        
        # Create activity
        activity = ClientActivity(
            client_id=client_id,
            user_id=current_user.id,
            activity_type="communication_added",
            description=f"New {request.type} communication",
            meta_data={"communication_id": communication.id}
        )
        db.add(activity)
        
        db.commit()
        db.refresh(communication)
        
        return CommunicationResponse(
            id=communication.id,
            content=communication.content,
            type=communication.type,
            fromUser=communication.from_user,
            timestamp=communication.created_at
        )
    
    @app.get("/clients/{client_id}/communications", response_model=List[CommunicationResponse])
    async def get_communications(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get communications for a client"""
        # Use timestamp column if it exists, otherwise fall back to created_at
        communications = db.query(ClientCommunication).filter(
            ClientCommunication.client_id == client_id
        ).order_by(ClientCommunication.created_at.desc()).limit(50).all()
        
        return [
            CommunicationResponse(
                id=comm.id,
                content=comm.content or comm.summary or comm.subject or '',
                type=comm.type,
                fromUser=comm.from_user,
                timestamp=comm.created_at,  # Use created_at as timestamp
                subject=comm.subject,
                toUsers=comm.to_users,
                syncedBy=getattr(comm, 'synced_by', None)  # Include synced_by if it exists
            )
            for comm in reversed(communications)  # Reverse to show oldest first
        ]
    
    @app.post("/crm/opportunities/{opportunity_id}/convert-to-client")
    async def convert_opportunity_to_client(
        opportunity_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Manually convert a CRM opportunity to a client"""
        try:
            # Get the opportunity
            opportunity = db.query(CRMOpportunity).filter(
                CRMOpportunity.id == opportunity_id
            ).first()
            
            if not opportunity:
                raise HTTPException(status_code=404, detail="Opportunity not found")
            
            # Use the handler to create the client
            client = client_portal_handler.create_client_from_crm(opportunity_id, db)
            
            return {
                "success": True,
                "client_id": client.id,
                "message": f"Successfully created client {client.name}"
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/clients/{client_id}/documents")
    async def upload_document(
        client_id: str,
        file: UploadFile = File(...),
        document_type: str = Form("other"),
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Upload a document for a client"""
        # Verify client exists
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Create uploads directory if it doesn't exist
        upload_dir = f"uploads/clients/{client_id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = f"{upload_dir}/{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Create document record
        document = ClientDocument(
            client_id=client_id,
            name=file.filename,
            type=document_type,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type,
            uploaded_by=current_user.id
        )
        
        db.add(document)
        
        # Create activity
        activity = ClientActivity(
            client_id=client_id,
            user_id=current_user.id,
            activity_type="document_uploaded",
            description=f"Uploaded document: {file.filename}",
            meta_data={"document_id": document.id, "document_type": document_type}
        )
        db.add(activity)
        
        db.commit()
        db.refresh(document)
        
        return {
            "id": document.id,
            "name": document.name,
            "type": document.type,
            "uploadedAt": document.uploaded_at,
            "fileSize": document.file_size
        }
    
    @app.get("/clients/{client_id}/documents", response_model=List[DocumentResponse])
    async def get_documents(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get all documents for a client (including Google Drive files)"""
        # Get client
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get uploaded documents from database
        documents = db.query(ClientDocument).filter(
            ClientDocument.client_id == client_id
        ).order_by(ClientDocument.uploaded_at.desc()).all()
        
        response_docs = [
            DocumentResponse(
                id=doc.id,
                name=doc.name,
                type=doc.type,
                uploadedBy=doc.uploaded_by,
                uploadedAt=doc.uploaded_at,
                fileSize=doc.file_size,
                version=doc.version
            )
            for doc in documents
        ]
        
        # Get Google Drive documents
        try:
            drive_docs = google_drive_handler.list_client_documents(client.name)
            
            # Convert Google Drive docs to DocumentResponse format
            for drive_doc in drive_docs:
                response_docs.append(DocumentResponse(
                    id=f"gdrive_{drive_doc['id']}",  # Prefix to distinguish from local docs
                    name=drive_doc['name'],
                    type=drive_doc['type'],
                    uploadedBy="Google Drive",
                    uploadedAt=datetime.fromisoformat(drive_doc['modifiedTime'].replace('Z', '+00:00')),
                    fileSize=int(drive_doc.get('size', 0)),
                    version=1
                ))
        except Exception as e:
            logger.error(f"Error fetching Google Drive documents: {e}")
        
        return response_docs
    
    @app.get("/clients/{client_id}/drive-documents")
    async def get_drive_documents(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get Google Drive documents for a client"""
        # Get client
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        try:
            documents = google_drive_handler.list_client_documents(client.name)
            folder_link = google_drive_handler.get_folder_link(client.name)
            
            return {
                "documents": documents,
                "folderLink": folder_link
            }
        except Exception as e:
            logger.error(f"Error fetching Google Drive documents: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/clients/{client_id}/create-drive-folder")
    async def create_drive_folder(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Create Google Drive folder for a client (if it doesn't exist)"""
        # Get client
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        try:
            folder_id = google_drive_handler.create_client_folder(client.name)
            if folder_id:
                # Create activity
                activity = ClientActivity(
                    client_id=client.id,
                    user_id=current_user.id,
                    activity_type="drive_folder_created",
                    description=f"Google Drive folder created for client",
                    meta_data={"folder_id": folder_id}
                )
                db.add(activity)
                db.commit()
                
                return {"message": "Google Drive folder created successfully", "folderId": folder_id}
            else:
                return {"message": "Folder already exists or could not be created"}
        except Exception as e:
            logger.error(f"Error creating Google Drive folder: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/clients/{client_id}/documents/{document_id}/download")
    async def download_document(
        client_id: str,
        document_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Download a document"""
        document = db.query(ClientDocument).filter(
            ClientDocument.id == document_id,
            ClientDocument.client_id == client_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="File not found on server")
        
        # Update access count
        document.last_accessed = datetime.utcnow()
        document.access_count += 1
        db.commit()
        
        return FileResponse(
            path=document.file_path,
            filename=document.name,
            media_type=document.mime_type
        )
    
    @app.post("/clients/{client_id}/team-members")
    async def add_team_member(
        client_id: str,
        request: TeamMemberRequest,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Add a team member to a client"""
        # Verify client exists
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Check if user is already a team member
        existing = db.query(ClientTeamMember).filter(
            ClientTeamMember.client_id == client_id,
            ClientTeamMember.user_id == request.user_id,
            ClientTeamMember.is_active == True
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="User is already a team member")
        
        # Add team member
        team_member = ClientTeamMember(
            client_id=client_id,
            user_id=request.user_id,
            role=request.role,
            can_view_financials=request.can_view_financials,
            can_edit_tasks=request.can_edit_tasks,
            can_upload_documents=request.can_upload_documents,
            added_by=current_user.id
        )
        
        db.add(team_member)
        
        # Create activity
        activity = ClientActivity(
            client_id=client_id,
            user_id=current_user.id,
            activity_type="team_member_added",
            description=f"Added team member with role: {request.role}",
            meta_data={"member_id": request.user_id, "role": request.role}
        )
        db.add(activity)
        
        db.commit()
        
        return {"message": "Team member added successfully"}
    
    @app.get("/clients/{client_id}/team-members")
    async def get_team_members(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get all team members for a client"""
        team_members = db.query(ClientTeamMember, User).join(
            User, ClientTeamMember.user_id == User.id
        ).filter(
            ClientTeamMember.client_id == client_id,
            ClientTeamMember.is_active == True
        ).all()
        
        return [
            {
                "id": member.id,
                "user_id": member.user_id,
                "email": user.email,
                "role": member.role,
                "can_view_financials": member.can_view_financials,
                "can_edit_tasks": member.can_edit_tasks,
                "can_upload_documents": member.can_upload_documents,
                "added_date": member.added_date
            }
            for member, user in team_members
        ]
    
    @app.delete("/clients/{client_id}/team-members/{member_id}")
    async def remove_team_member(
        client_id: str,
        member_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Remove a team member from a client"""
        member = db.query(ClientTeamMember).filter(
            ClientTeamMember.id == member_id,
            ClientTeamMember.client_id == client_id,
            ClientTeamMember.is_active == True
        ).first()
        
        if not member:
            raise HTTPException(status_code=404, detail="Team member not found")
        
        # Soft delete
        member.is_active = False
        
        # Create activity
        activity = ClientActivity(
            client_id=client_id,
            user_id=current_user.id,
            activity_type="team_member_removed",
            description=f"Removed team member",
            meta_data={"member_id": member.user_id}
        )
        db.add(activity)
        
        db.commit()
        
        return {"message": "Team member removed successfully"}
    
    @app.get("/clients/{client_id}/activities", response_model=List[ActivityResponse])
    async def get_activities(
        client_id: str,
        limit: int = 50,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get activity timeline for a client"""
        try:
            # Verify client exists
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                logger.warning(f"Client not found: {client_id}")
                raise HTTPException(status_code=404, detail="Client not found")
            
            activities = db.query(ClientActivity).filter(
                ClientActivity.client_id == client_id
            ).order_by(ClientActivity.created_at.desc()).limit(limit).all()
            
            return [
                ActivityResponse(
                    id=activity.id,
                    activity_type=activity.activity_type,
                    description=activity.description,
                    created_at=activity.created_at,
                    user_id=activity.user_id
                )
                for activity in activities
            ]
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching activities for client {client_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/clients/{client_id}/upcoming-meetings")
    async def get_upcoming_meetings(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get upcoming meetings for a client"""
        # Get calendar events that are in the future (next 30 days)
        # Note: For calendar events, created_at stores the event start time
        current_time = datetime.utcnow()
        thirty_days_later = current_time + timedelta(days=30)
        
        # Log for debugging
        logger.info(f"Fetching upcoming meetings for client {client_id}")
        logger.info(f"Time range: {current_time} to {thirty_days_later}")
        
        # First, check total calendar events for this client
        total_calendar_events = db.query(ClientCommunication).filter(
            ClientCommunication.client_id == client_id,
            ClientCommunication.type == "calendar_event"
        ).count()
        logger.info(f"Total calendar events for client: {total_calendar_events}")
        
        # Get upcoming meetings in the next 30 days
        upcoming_meetings = db.query(ClientCommunication).filter(
            ClientCommunication.client_id == client_id,
            ClientCommunication.type == "calendar_event",
            ClientCommunication.created_at > current_time,
            ClientCommunication.created_at <= thirty_days_later
        ).order_by(ClientCommunication.created_at.asc()).all()
        
        logger.info(f"Found {len(upcoming_meetings)} upcoming meetings")
        
        # If no upcoming meetings, let's check if there are any recent past meetings for debugging
        if len(upcoming_meetings) == 0 and total_calendar_events > 0:
            sample_events = db.query(ClientCommunication).filter(
                ClientCommunication.client_id == client_id,
                ClientCommunication.type == "calendar_event"
            ).order_by(ClientCommunication.created_at.desc()).limit(5).all()
            
            for event in sample_events:
                logger.info(f"Sample event: {event.subject} at {event.created_at}")
        
        # Format the response
        meetings = []
        for meeting in upcoming_meetings:
            # Parse location from content if available
            location = "N/A"
            if meeting.content:
                lines = meeting.content.split('\n')
                for line in lines:
                    if line.startswith('Location:'):
                        location = line.replace('Location:', '').strip()
                        break
            
            meetings.append({
                "id": meeting.id,
                "title": meeting.subject or "Untitled Meeting",
                "startTime": meeting.created_at.isoformat(),
                "location": location,
                "attendees": meeting.to_users or [],
                "organizer": meeting.from_user
            })
        
        return meetings
    
    @app.put("/clients/{client_id}/tasks/{task_id}/status")
    async def update_task_status(
        client_id: str,
        task_id: str,
        status: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Update task status"""
        task = db.query(ClientTask).filter(
            ClientTask.id == task_id,
            ClientTask.client_id == client_id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        old_status = task.status.value
        task.status = TaskStatus(status)
        
        # Update completed date and task counts
        if status == "completed" and old_status != "completed":
            task.completed_date = datetime.utcnow()
            client = db.query(Client).filter(Client.id == client_id).first()
            if client:
                client.completed_tasks += 1
        elif status != "completed" and old_status == "completed":
            task.completed_date = None
            client = db.query(Client).filter(Client.id == client_id).first()
            if client:
                client.completed_tasks = max(0, client.completed_tasks - 1)
        
        # Create activity
        activity = ClientActivity(
            client_id=client_id,
            user_id=current_user.id,
            activity_type="task_status_changed",
            description=f"Task '{task.title}' status changed from {old_status} to {status}",
            meta_data={"task_id": task_id, "old_status": old_status, "new_status": status}
        )
        db.add(activity)
        
        db.commit()
        
        return {"message": "Task status updated successfully"} 

    @app.post("/clients/{client_id}/sync-emails")
    async def sync_client_emails(
        client_id: str,
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Sync emails from Oracle for a specific client"""
        # Verify client exists
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Run email sync synchronously to ensure data persists
        try:
            client_portal_handler.sync_oracle_emails_to_client(client_id, db)
            db.commit()
            return {"message": "Email sync completed successfully"}
        except Exception as e:
            logger.error(f"Error during email sync: {e}")
            db.rollback()
            return {"message": f"Email sync completed with errors: {str(e)}"}
    
    @app.post("/clients/{client_id}/sync-all")
    async def sync_all_client_data(
        client_id: str,
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Sync all data (emails and calendar) from Oracle for a specific client"""
        # Verify client exists
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Run sync synchronously instead of in background to ensure data persists
        try:
            # Sync emails
            client_portal_handler.sync_oracle_emails_to_client(client_id, db)
            # Sync calendar
            client_portal_handler.sync_oracle_calendar_to_client(client_id, db)
            
            # Flush to ensure all pending operations are sent to the database
            db.flush()
            
            # Log how many communications we have before commit
            comm_count = db.query(ClientCommunication).filter(
                ClientCommunication.client_id == client_id
            ).count()
            logger.info(f"Communications in session before commit: {comm_count}")
            
            # Ensure all changes are committed
            db.commit()
            
            # Verify after commit
            comm_count_after = db.query(ClientCommunication).filter(
                ClientCommunication.client_id == client_id
            ).count()
            logger.info(f"Communications after commit: {comm_count_after}")
            
            return {"message": "Email and calendar sync completed successfully", "emails_synced": comm_count_after}
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            db.rollback()
            return {"message": f"Sync completed with errors: {str(e)}"}
    
    @app.post("/clients/{client_id}/auto-create-tasks")
    async def auto_create_tasks(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Auto-create tasks from email communications"""
        # Verify client exists
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Run task creation
        client_portal_handler.auto_create_tasks_from_emails(client_id, db)
        
        return {"message": "Tasks created from emails successfully"} 

    @app.post("/clients/{client_id}/process-documents")
    async def process_client_documents(
        client_id: str,
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Process and vectorize all documents in a client's Google Drive folder"""
        # Get client
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Run processing in background
        background_tasks.add_task(
            client_document_processor.process_client_drive_documents,
            client_id,
            client.name,
            db
        )
        
        return {"message": "Document processing started in background"}
    
    @app.get("/clients/{client_id}/vectorized-documents")
    async def get_vectorized_documents(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get list of vectorized documents for a client"""
        documents = db.query(ClientDocument).filter(
            ClientDocument.client_id == client_id,
            ClientDocument.vectorized == True
        ).all()
        
        return [
            {
                "id": doc.id,
                "name": doc.name,
                "type": doc.type,
                "vectorized_at": doc.vectorized_at,
                "google_drive_id": doc.google_drive_id
            }
            for doc in documents
        ] 

    @app.get("/clients/{client_id}/vectorization-status")
    async def get_vectorization_status(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get vectorization status for all documents of a client"""
        # Get client
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get all documents from Google Drive
        try:
            drive_docs = google_drive_handler.list_client_documents(client.name)
        except Exception as e:
            logger.error(f"Error fetching Google Drive documents: {e}")
            drive_docs = []
        
        # Get vectorized documents from database
        vectorized_docs = db.query(ClientDocument).filter(
            ClientDocument.client_id == client_id,
            ClientDocument.vectorized == True
        ).all()
        
        # Create a map of vectorized document IDs
        vectorized_ids = {doc.google_drive_id: doc for doc in vectorized_docs}
        
        # Build status for each document
        document_status = []
        for drive_doc in drive_docs:
            is_vectorized = drive_doc['id'] in vectorized_ids
            doc_info = {
                "id": drive_doc['id'],
                "name": drive_doc['name'],
                "type": drive_doc['type'],
                "size": drive_doc.get('size', 0),
                "modifiedTime": drive_doc['modifiedTime'],
                "vectorized": is_vectorized,
                "vectorized_at": vectorized_ids[drive_doc['id']].vectorized_at.isoformat() if is_vectorized else None
            }
            document_status.append(doc_info)
        
        # Calculate summary statistics
        total_documents = len(drive_docs)
        vectorized_count = len(vectorized_ids)
        
        return {
            "summary": {
                "total_documents": total_documents,
                "vectorized_count": vectorized_count,
                "percentage_complete": (vectorized_count / total_documents * 100) if total_documents > 0 else 0
            },
            "documents": document_status
        } 

    @app.post("/clients/{client_id}/chat-history")
    async def save_chat_to_client(
        client_id: str,
        message: str = Form(...),
        query: Optional[str] = Form(None),
        sources: Optional[str] = Form(None),  # JSON string
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Save a chat message to client history"""
        # Verify client exists
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Parse sources if provided
        sources_list = []
        if sources:
            try:
                sources_list = json.loads(sources)
            except:
                sources_list = []
        
        # Create chat history entry
        chat_entry = ClientChatHistory(
            client_id=client_id,
            message=message,
            query=query,
            sources=sources_list,
            created_by=current_user.id
        )
        
        db.add(chat_entry)
        db.commit()
        db.refresh(chat_entry)
        
        return {"success": True, "id": chat_entry.id}
    
    @app.get("/clients/{client_id}/chat-history")
    async def get_client_chat_history(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get chat history for a client"""
        chat_history = db.query(ClientChatHistory).filter(
            ClientChatHistory.client_id == client_id
        ).order_by(ClientChatHistory.created_at.desc()).all()
        
        return [{
            "id": chat.id,
            "message": chat.message,
            "query": chat.query,
            "sources": chat.sources,
            "created_at": chat.created_at,
            "created_by": chat.created_by
        } for chat in chat_history]
    
    @app.delete("/clients/{client_id}/chat-history/{chat_id}")
    async def delete_chat_history_item(
        client_id: str,
        chat_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Delete a chat history item"""
        chat_entry = db.query(ClientChatHistory).filter(
            ClientChatHistory.id == chat_id,
            ClientChatHistory.client_id == client_id
        ).first()
        
        if not chat_entry:
            raise HTTPException(status_code=404, detail="Chat history item not found")
        
        db.delete(chat_entry)
        db.commit()
        
        return {"success": True}

    @app.delete("/clients/{client_id}")
    async def delete_client(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Delete a client and all associated data (except Google Drive folder)"""
        # Get client
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Delete associated data in order (due to foreign key constraints)
        # Delete activities
        db.query(ClientActivity).filter(ClientActivity.client_id == client_id).delete()
        
        # Delete team members
        db.query(ClientTeamMember).filter(ClientTeamMember.client_id == client_id).delete()
        
        # Delete documents
        db.query(ClientDocument).filter(ClientDocument.client_id == client_id).delete()
        
        # Delete communications
        db.query(ClientCommunication).filter(ClientCommunication.client_id == client_id).delete()
        
        # Delete tasks
        db.query(ClientTask).filter(ClientTask.client_id == client_id).delete()
        
        # Finally delete the client
        db.delete(client)
        
        db.commit()
        
        logger.info(f"Client {client.name} (ID: {client_id}) deleted by user {current_user.email}")
        
        return {"message": f"Client {client.name} has been successfully deleted"} 

    @app.post("/clients/sync-all-clients")
    async def sync_all_clients(
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Sync all data for all clients - emails, calendar, AI analysis, etc."""
        # Get all active clients
        clients = db.query(Client).filter(
            Client.status.in_([ClientStatus.ACTIVE, ClientStatus.ONGOING])
        ).all()
        
        if not clients:
            return {"message": "No active clients to sync", "clients_count": 0}
        
        logger.info(f"Starting sync for {len(clients)} clients by user {current_user.email}")
        
        # Run the sync in background
        background_tasks.add_task(
            sync_all_clients_background,
            [client.id for client in clients],
            [client.name for client in clients],
            current_user.id
        )
        
        return {
            "message": f"Started syncing {len(clients)} clients in background",
            "clients_count": len(clients),
            "status": "processing"
        }

    @app.get("/clients/debug-summary-data")
    async def debug_summary_data(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Debug endpoint to check what data exists for the aggregated summary"""
        try:
            # Count calendar events
            total_calendar_events = db.query(ClientCommunication).filter(
                ClientCommunication.type == "calendar_event"
            ).count()
            
            # Get sample calendar events
            sample_events = db.query(ClientCommunication).filter(
                ClientCommunication.type == "calendar_event"
            ).limit(5).all()
            
            # Count AI analysis records
            ai_analysis_count = db.query(ClientAIAnalysis).count()
            sentiment_count = db.query(ClientAIAnalysis).filter(
                ClientAIAnalysis.analysis_type == "sentiment"
            ).count()
            tasks_count = db.query(ClientAIAnalysis).filter(
                ClientAIAnalysis.analysis_type == "suggested_tasks"
            ).count()
            
            # Get sample AI analysis
            sample_sentiment = db.query(ClientAIAnalysis).filter(
                ClientAIAnalysis.analysis_type == "sentiment"
            ).first()
            
            return {
                "calendar_events": {
                    "total": total_calendar_events,
                    "samples": [
                        {
                            "id": event.id,
                            "client_id": event.client_id,
                            "subject": event.subject,
                            "created_at": event.created_at.isoformat() if event.created_at else None,
                            "type": event.type
                        }
                        for event in sample_events
                    ]
                },
                "ai_analysis": {
                    "total": ai_analysis_count,
                    "sentiment_analyses": sentiment_count,
                    "suggested_tasks_analyses": tasks_count,
                    "sample_sentiment": {
                        "client_id": sample_sentiment.client_id,
                        "result_data": sample_sentiment.result_data
                    } if sample_sentiment else None
                },
                "current_time_utc": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in debug endpoint: {e}")
            return {"error": str(e)}

    @app.get("/clients/{client_id}/calendar-sync-status")
    async def get_calendar_sync_status(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Check calendar sync status and configuration for a client"""
        # Get client
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get sync email addresses
        sync_emails = []
        if hasattr(client, 'sync_email_addresses') and client.sync_email_addresses:
            sync_emails.extend(client.sync_email_addresses)
        if client.primary_contact_email and client.primary_contact_email not in sync_emails:
            sync_emails.append(client.primary_contact_email)
        
        # Check connected calendar sources
        calendar_sources = db.query(OracleDataSource).filter(
            OracleDataSource.source_type == "calendar",
            OracleDataSource.status == "connected"
        ).all()
        
        # Get calendar event count
        calendar_events = db.query(ClientCommunication).filter(
            ClientCommunication.client_id == client_id,
            ClientCommunication.type == "calendar_event"
        ).order_by(ClientCommunication.created_at.desc()).limit(10).all()
        
        # Check for future events
        current_time = datetime.utcnow()
        future_events_count = db.query(ClientCommunication).filter(
            ClientCommunication.client_id == client_id,
            ClientCommunication.type == "calendar_event",
            ClientCommunication.created_at > current_time
        ).count()
        
        return {
            "sync_email_addresses": sync_emails,
            "connected_calendar_sources": len(calendar_sources),
            "total_calendar_events": len(calendar_events),
            "future_events_count": future_events_count,
            "recent_events": [
                {
                    "id": event.id,
                    "subject": event.subject,
                    "event_time": event.created_at.isoformat() if event.created_at else None,
                    "organizer": event.from_user,
                    "attendees": event.to_users
                }
                for event in calendar_events[:5]
            ],
            "sync_status": {
                "has_sync_emails": len(sync_emails) > 0,
                "has_calendar_sources": len(calendar_sources) > 0,
                "has_synced_events": len(calendar_events) > 0
            }
        }

    @app.get("/debug/oracle-sources")
    async def debug_oracle_sources(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Debug endpoint to check all Oracle data sources"""
        try:
            # Get all Oracle data sources
            all_sources = db.query(OracleDataSource).all()
            
            sources_info = []
            for source in all_sources:
                # Get user info
                user = db.query(User).filter(User.id == source.user_id).first()
                sources_info.append({
                    "id": source.id,
                    "user_email": user.email if user else "Unknown",
                    "user_id": source.user_id,
                    "source_type": source.source_type,
                    "status": source.status,
                    "has_credentials": bool(source.credentials),
                    "has_refresh_token": bool(source.credentials.get('refresh_token')) if source.credentials else False,
                    "last_sync": source.last_sync.isoformat() if source.last_sync else None,
                    "created_at": source.created_at.isoformat() if source.created_at else None
                })
            
            # Count by type and status
            summary = {
                "total_sources": len(all_sources),
                "by_type": {},
                "by_status": {},
                "connected_calendars": len([s for s in all_sources if s.source_type == "calendar" and s.status == "connected"]),
                "connected_emails": len([s for s in all_sources if s.source_type == "email" and s.status == "connected"])
            }
            
            for source in all_sources:
                # Count by type
                if source.source_type not in summary["by_type"]:
                    summary["by_type"][source.source_type] = 0
                summary["by_type"][source.source_type] += 1
                
                # Count by status
                if source.status not in summary["by_status"]:
                    summary["by_status"][source.status] = 0
                summary["by_status"][source.status] += 1
            
            return {
                "summary": summary,
                "sources": sources_info
            }
            
        except Exception as e:
            logger.error(f"Error in debug oracle sources: {e}")
            return {"error": str(e)}

    @app.get("/clients/{client_id}/debug-calendar-events")
    async def debug_calendar_events(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Debug endpoint to check all calendar events for a client"""
        try:
            # Get all calendar events for this client
            all_events = db.query(ClientCommunication).filter(
                ClientCommunication.client_id == client_id,
                ClientCommunication.type == "calendar_event"
            ).order_by(ClientCommunication.created_at.desc()).all()
            
            current_time = datetime.utcnow()
            
            events_data = []
            for event in all_events:
                event_time = event.created_at
                is_future = event_time > current_time if event_time else False
                
                events_data.append({
                    "id": event.id,
                    "subject": event.subject,
                    "event_time": event.created_at.isoformat() if event.created_at else None,
                    "is_future": is_future,
                    "time_until": str(event_time - current_time) if event_time and is_future else None,
                    "from_user": event.from_user,
                    "to_users": event.to_users,
                    "content": event.content[:100] if event.content else None
                })
            
            # Count events by time period
            past_events = [e for e in events_data if not e["is_future"]]
            future_events = [e for e in events_data if e["is_future"]]
            
            return {
                "current_utc_time": current_time.isoformat(),
                "total_events": len(all_events),
                "past_events_count": len(past_events),
                "future_events_count": len(future_events),
                "events": events_data,
                "summary": {
                    "has_future_events": len(future_events) > 0,
                    "next_event": future_events[0] if future_events else None,
                    "most_recent_past": past_events[0] if past_events else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error in debug calendar events: {e}")
            return {"error": str(e)}

    @app.post("/clients/{client_id}/force-calendar-sync")
    async def force_calendar_sync(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Force a fresh calendar sync for a client"""
        # Verify client exists
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        try:
            # First, remove old calendar events to force a fresh sync
            old_events = db.query(ClientCommunication).filter(
                ClientCommunication.client_id == client_id,
                ClientCommunication.type == "calendar_event"
            ).all()
            
            logger.info(f"Removing {len(old_events)} old calendar events for fresh sync")
            
            for event in old_events:
                db.delete(event)
            
            db.commit()
            
            # Now sync fresh calendar data
            client_portal_handler.sync_oracle_calendar_to_client(client_id, db)
            
            # Commit the new data
            db.commit()
            
            # Get the new count
            new_count = db.query(ClientCommunication).filter(
                ClientCommunication.client_id == client_id,
                ClientCommunication.type == "calendar_event"
            ).count()
            
            # Check how many are future events
            current_time = datetime.utcnow()
            future_count = db.query(ClientCommunication).filter(
                ClientCommunication.client_id == client_id,
                ClientCommunication.type == "calendar_event",
                ClientCommunication.created_at > current_time
            ).count()
            
            return {
                "message": "Calendar sync completed successfully",
                "old_events_removed": len(old_events),
                "new_events_synced": new_count,
                "future_events": future_count
            }
            
        except Exception as e:
            logger.error(f"Error during forced calendar sync: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

# Background task function for syncing all clients
def sync_all_clients_background(client_ids: List[str], client_names: List[str], user_id: str):
    """Background task to sync all clients"""
    from .database import SessionLocal
    from .client_ai_handler import client_ai_handler
    
    db = SessionLocal()
    successful_syncs = 0
    failed_syncs = 0
    
    try:
        for i, client_id in enumerate(client_ids):
            client_name = client_names[i]
            logger.info(f"Syncing client {i+1}/{len(client_ids)}: {client_name}")
            
            try:
                # 1. Sync emails and calendar
                client_portal_handler.sync_oracle_emails_to_client(client_id, db)
                client_portal_handler.sync_oracle_calendar_to_client(client_id, db)
                db.commit()
                
                # 2. Generate AI analysis (with AI enabled check)
                if os.getenv('ENABLE_CLIENT_AI', 'true').lower() == 'true':
                    try:
                        # Commitments
                        commitments = client_ai_handler.extract_commitments(client_id, db)
                        if not commitments.get('error'):
                            # Store in database
                            from .client_portal_models import ClientAIAnalysis
                            analysis = ClientAIAnalysis(
                                client_id=client_id,
                                analysis_type='commitments',
                                result_data=commitments,
                                created_by=user_id
                            )
                            db.add(analysis)
                        
                        # Weekly Summary
                        summary = client_ai_handler.generate_weekly_summary(client_id, db)
                        if not summary.get('error'):
                            analysis = ClientAIAnalysis(
                                client_id=client_id,
                                analysis_type='weekly_summary',
                                result_data=summary,
                                created_by=user_id
                            )
                            db.add(analysis)
                        
                        # Sentiment Analysis
                        sentiment = client_ai_handler.analyze_sentiment(client_id, db)
                        if not sentiment.get('error'):
                            analysis = ClientAIAnalysis(
                                client_id=client_id,
                                analysis_type='sentiment',
                                result_data=sentiment,
                                created_by=user_id
                            )
                            db.add(analysis)
                        
                        # Suggested Tasks
                        tasks = client_ai_handler.suggest_tasks(client_id, db)
                        if not tasks.get('error'):
                            analysis = ClientAIAnalysis(
                                client_id=client_id,
                                analysis_type='suggested_tasks',
                                result_data=tasks,
                                created_by=user_id
                            )
                            db.add(analysis)
                        
                        db.commit()
                    except Exception as ai_error:
                        logger.error(f"Error generating AI analysis for {client_name}: {ai_error}")
                        db.rollback()
                
                # 3. Create activity log
                activity = ClientActivity(
                    client_id=client_id,
                    user_id=user_id,
                    activity_type="full_sync_completed",
                    description=f"Full data sync completed",
                    meta_data={"sync_type": "bulk_sync"}
                )
                db.add(activity)
                db.commit()
                
                successful_syncs += 1
                logger.info(f"Successfully synced client: {client_name}")
                
            except Exception as e:
                logger.error(f"Error syncing client {client_name}: {e}")
                db.rollback()
                failed_syncs += 1
                continue
        
        logger.info(f"Sync all clients completed. Success: {successful_syncs}, Failed: {failed_syncs}")
        
    except Exception as e:
        logger.error(f"Critical error in sync all clients: {e}")
    finally:
        db.close() 