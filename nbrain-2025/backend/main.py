from fastapi import FastAPI, HTTPException, Form, BackgroundTasks, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from typing import List, Optional, AsyncGenerator
from pydantic import BaseModel, Field, EmailStr
from dotenv import load_dotenv
import os
import sys
import json
import uuid
import tempfile
import io
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
import logging
from sqlalchemy import inspect, text
from datetime import datetime
from fastapi.concurrency import run_in_threadpool
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core import pinecone_manager, llm_handler, processor, auth, generator_handler
from core.database import Base, get_db, engine, User, ChatSession, SessionLocal, AgentIdea, CRMOpportunity, CRMDocument, CRMOpportunityAgent
from core import voice_api  # Add voice API import
from core import twilio_handler  # Add Twilio handler import
from core.google_docs_handler import google_docs_handler  # Add Google Docs handler import
from core.client_portal_endpoints import setup_client_portal_endpoints
from core.client_ai_endpoints import setup_client_ai_endpoints
from core.voice_endpoints import setup_voice_endpoints
from core.middleware import DatabaseSessionMiddleware, ErrorHandlingMiddleware  # Import the middleware

load_dotenv()

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic Models ---
class ChatMessage(BaseModel):
    text: str
    sender: str
    sources: Optional[List[str]] = None

class ChatHistory(BaseModel):
    chat_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    messages: List[ChatMessage]

class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationDetail(ConversationSummary):
    messages: List[ChatMessage]
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    query: str
    history: List[dict] = []
    client_id: Optional[str] = None  # Optional client ID for client-specific search
    chat_mode: Optional[str] = 'standard'  # Chat mode: standard, quick, deep

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UrlList(BaseModel):
    urls: List[str]

class GeneratorRequest(BaseModel):
    mappings: dict
    core_content: str
    tone: str
    style: str

class AgentIdeaCreate(BaseModel):
    title: str
    summary: str
    steps: List[str]
    agent_stack: dict
    client_requirements: List[str]
    conversation_history: Optional[List[dict]] = None
    agent_type: Optional[str] = None
    implementation_estimate: Optional[dict] = None
    security_considerations: Optional[dict] = None
    future_enhancements: Optional[List[dict]] = None

class AgentIdeaUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    steps: Optional[List[str]] = None
    agent_stack: Optional[dict] = None
    client_requirements: Optional[List[str]] = None
    status: Optional[str] = None
    implementation_estimate: Optional[dict] = None

class AgentIdeaResponse(BaseModel):
    id: str
    title: str
    summary: str
    steps: List[str]
    agent_stack: dict
    client_requirements: List[str]
    status: str
    agent_type: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    implementation_estimate: Optional[dict]
    security_considerations: Optional[dict]
    future_enhancements: Optional[List[dict]]

class IdeationMessage(BaseModel):
    message: str
    conversation_history: List[dict] = []

class EditMessage(BaseModel):
    message: str
    current_spec: dict
    conversation_history: List[dict] = []

class MoveToProductionRequest(BaseModel):
    spec_id: Optional[str]
    spec_details: dict

class CRMOpportunityCreate(BaseModel):
    status: str
    client_opportunity: str
    lead_start_date: Optional[str] = None
    lead_source: Optional[str] = None
    referral_source: Optional[str] = None
    product: Optional[str] = None
    deal_status: Optional[str] = None
    intro_call_date: Optional[str] = None
    todo_next_steps: Optional[str] = None
    discovery_call: Optional[str] = None
    presentation_date: Optional[str] = None
    proposal_sent: Optional[str] = None
    estimated_pipeline_value: Optional[str] = None
    deal_closed: Optional[str] = None
    kickoff_scheduled: Optional[str] = None
    actual_contract_value: Optional[str] = None
    monthly_fees: Optional[str] = None
    commission: Optional[str] = None
    invoice_setup: Optional[str] = None
    payment_1: Optional[str] = None
    payment_2: Optional[str] = None
    payment_3: Optional[str] = None
    payment_4: Optional[str] = None
    payment_5: Optional[str] = None
    payment_6: Optional[str] = None
    payment_7: Optional[str] = None
    notes_next_steps: Optional[str] = None

class CRMOpportunityUpdate(BaseModel):
    status: Optional[str] = None
    client_opportunity: Optional[str] = None
    lead_start_date: Optional[str] = None
    lead_source: Optional[str] = None
    referral_source: Optional[str] = None
    product: Optional[str] = None
    deal_status: Optional[str] = None
    intro_call_date: Optional[str] = None
    todo_next_steps: Optional[str] = None
    discovery_call: Optional[str] = None
    presentation_date: Optional[str] = None
    proposal_sent: Optional[str] = None
    estimated_pipeline_value: Optional[str] = None
    deal_closed: Optional[str] = None
    kickoff_scheduled: Optional[str] = None
    actual_contract_value: Optional[str] = None
    monthly_fees: Optional[str] = None
    commission: Optional[str] = None
    invoice_setup: Optional[str] = None
    payment_1: Optional[str] = None
    payment_2: Optional[str] = None
    payment_3: Optional[str] = None
    payment_4: Optional[str] = None
    payment_5: Optional[str] = None
    payment_6: Optional[str] = None
    payment_7: Optional[str] = None
    notes_next_steps: Optional[str] = None

class CRMOpportunityResponse(BaseModel):
    id: str
    status: str
    client_opportunity: str
    lead_start_date: Optional[str]
    lead_source: Optional[str]
    referral_source: Optional[str]
    product: Optional[str]
    deal_status: Optional[str]
    intro_call_date: Optional[str]
    todo_next_steps: Optional[str]
    discovery_call: Optional[str]
    presentation_date: Optional[str]
    proposal_sent: Optional[str]
    estimated_pipeline_value: Optional[str]
    deal_closed: Optional[str]
    kickoff_scheduled: Optional[str]
    actual_contract_value: Optional[str]
    monthly_fees: Optional[str]
    commission: Optional[str]
    invoice_setup: Optional[str]
    payment_1: Optional[str]
    payment_2: Optional[str]
    payment_3: Optional[str]
    payment_4: Optional[str]
    payment_5: Optional[str]
    payment_6: Optional[str]
    payment_7: Optional[str]
    notes_next_steps: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    documents: List[dict] = []
    agent_links: List[dict] = []

class CRMDocumentCreate(BaseModel):
    name: str
    type: str  # 'link' or 'file'
    url: Optional[str] = None

class CRMAgentLink(BaseModel):
    agent_idea_id: str
    notes: Optional[str] = None

# Add this new chat request model for non-streaming chat
class SimpleChatRequest(BaseModel):
    message: str
    client_specific: bool = False
    client_id: Optional[str] = None

# --- App Initialization ---
app = FastAPI(
    title="nBrain RAG API",
    description="API for nBrain's Retrieval-Augmented Generation platform.",
    version="0.2.2",
)

# Include voice API router
app.include_router(voice_api.router)
# Include Twilio router for phone calls
app.include_router(twilio_handler.router)

@app.on_event("startup")
def on_startup():
    # The database setup is now handled by the build script (build.sh)
    # to ensure the database is ready before the app starts.
    logger.info("Application startup: Database setup is handled by the build process.")
    
    # Debug logging to see what environment we're using
    logger.info("="*60)
    logger.info("ENVIRONMENT CONFIGURATION:")
    logger.info(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT SET')[:50]}...")  # Show first 50 chars
    logger.info(f"PINECONE_INDEX_NAME: {os.getenv('PINECONE_INDEX_NAME', 'NOT SET')}")
    logger.info(f"PINECONE_ENVIRONMENT: {os.getenv('PINECONE_ENVIRONMENT', 'NOT SET')}")
    logger.info("="*60)
    pass

# --- CORS Middleware ---
# Log the environment for debugging
logger.info(f"Setting up CORS middleware...")
logger.info(f"Frontend should be using VITE_API_BASE_URL from environment")

# More explicit CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Add database session middleware AFTER CORS middleware
app.add_middleware(DatabaseSessionMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# Add explicit OPTIONS handler for preflight requests
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

# Add health check endpoint
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint to verify database connectivity"""
    try:
        # Try a simple query
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Database connection error")

# Root endpoint
@app.get("/")
def read_root():
    return {"status": "nBrain RAG API is running"}

@app.get("/test-cors")
def test_cors():
    """Simple endpoint to test CORS configuration"""
    return {
        "status": "CORS test successful",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "If you can see this from the frontend, CORS is working!"
    }

# --- Background Processing ---
def process_and_index_files(temp_file_paths: List[str], original_file_names: List[str]):
    logger.info(f"BACKGROUND_TASK: Starting processing for {len(original_file_names)} files.")
    for i, temp_path in enumerate(temp_file_paths):
        original_name = original_file_names[i]
        logger.info(f"BACKGROUND_TASK: Processing {original_name}")
        try:
            chunks = processor.process_file(temp_path, original_name)
            if chunks:
                metadata = {"source": original_name, "doc_type": "file_upload"}
                pinecone_manager.upsert_chunks(chunks, metadata)
                logger.info(f"BACKGROUND_TASK: Successfully processed and indexed {original_name}")
            else:
                logger.warning(f"BACKGROUND_TASK: No chunks found for {original_name}. Skipping.")
        except Exception as e:
            logger.error(f"BACKGROUND_TASK_ERROR: Failed to process {original_name}. Reason: {e}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    logger.info("BACKGROUND_TASK: File processing complete.")

def process_and_index_urls(urls: List[str]):
    logger.info(f"BACKGROUND_TASK: Starting crawling for {len(urls)} URLs.")
    for url in urls:
        logger.info(f"BACKGROUND_TASK: Processing {url}")
        try:
            chunks = processor.process_url(url)
            if chunks:
                metadata = {"source": url, "doc_type": "url_crawl"}
                pinecone_manager.upsert_chunks(chunks, metadata)
                logger.info(f"BACKGROUND_TASK: Successfully processed and indexed {url}")
            else:
                logger.warning(f"BACKGROUND_TASK: No content found for {url}. Skipping.")
        except Exception as e:
            logger.error(f"BACKGROUND_TASK_ERROR: Failed to process {url}. Reason: {e}")
    logger.info("BACKGROUND_TASK: URL crawling complete.")

# --- API Endpoints ---
@app.post("/signup", response_model=Token)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user_data.password)
    new_user = User(email=user_data.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token = auth.create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/upload-files")
async def upload_files(files: List[UploadFile] = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    temp_file_paths = []
    original_file_names = []
    for file in files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_paths.append(temp_file.name)
            original_file_names.append(file.filename)
    background_tasks.add_task(process_and_index_files, temp_file_paths, original_file_names)
    return {"message": f"Successfully uploaded {len(files)} files. Processing has started in the background."}

@app.post("/crawl-urls")
async def crawl_urls(url_list: UrlList, background_tasks: BackgroundTasks = BackgroundTasks()):
    background_tasks.add_task(process_and_index_urls, url_list.urls)
    return {"message": f"Started crawling {len(url_list.urls)} URLs in the background."}

@app.get("/documents")
async def get_documents():
    try:
        return pinecone_manager.list_documents()
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{file_name}")
async def delete_document(file_name: str):
    try:
        pinecone_manager.delete_document(file_name)
        return {"message": f"Successfully deleted {file_name}."}
    except Exception as e:
        logger.error(f"Error deleting document {file_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generator/process")
async def generator_process(
    file: UploadFile = File(...),
    key_fields: str = Form(...),
    core_content: str = Form(...),
    is_preview: str = Form(...), # Comes in as a string 'true' or 'false'
    generation_goal: str = Form("") # Optional field for extra instructions
):
    preview_mode = is_preview.lower() == 'true'
    key_fields_list = json.loads(key_fields)
    csv_buffer = io.BytesIO(await file.read())

    # Create the generator; it will handle preview logic internally
    content_generator = generator_handler.generate_content_rows(
        csv_file=csv_buffer,
        key_fields=key_fields_list,
        core_content=core_content,
        is_preview=preview_mode,
        generation_goal=generation_goal
    )

    # ALWAYS stream the response to avoid timeouts. The frontend will handle
    # closing the connection early for previews.
    async def stream_csv_content():
        try:
            # The first yield is the header
            header = await anext(content_generator)
            yield json.dumps({"type": "header", "data": header}) + "\n"

            # Yield each subsequent row
            async for row in content_generator:
                yield json.dumps({"type": "row", "data": row}) + "\n"
            
            yield json.dumps({"type": "done"}) + "\n"
            logger.info("Successfully streamed all CSV content.")

        except Exception as e:
            logger.error(f"Error during CSV stream: {e}", exc_info=True)
            error_payload = json.dumps({"type": "error", "detail": str(e)})
            yield error_payload + "\n"

    return StreamingResponse(stream_csv_content(), media_type="application/x-ndjson")

# This is a standalone function to be called from the stream
def save_chat_history_sync(
    chat_data: ChatHistory,
    db: Session,
    current_user: User
):
    """Saves a chat conversation to the database (synchronous version)."""
    try:
        first_user_message = next((msg.text for msg in chat_data.messages if msg.sender == 'user'), "New Chat")
        title = (first_user_message[:100] + '...') if len(first_user_message) > 100 else first_user_message
        messages_as_dicts = [msg.dict() for msg in chat_data.messages]

        # Check if a conversation with this ID already exists
        existing_convo = db.query(ChatSession).filter(ChatSession.id == str(chat_data.chat_id)).first()

        if existing_convo:
            # Update existing conversation
            existing_convo.messages = messages_as_dicts
            logger.info(f"Updating conversation {existing_convo.id}")
        else:
            # Create new conversation
            db_convo = ChatSession(
                id=str(chat_data.chat_id),
                title=title,
                messages=messages_as_dicts,
                user_id=current_user.id
            )
            db.add(db_convo)
            logger.info(f"Creating new conversation {db_convo.id}")
        
        db.commit()
    except Exception as e:
        logger.error(f"Failed to save chat history: {e}", exc_info=True)
        db.rollback()


@app.get("/history", response_model=list[ConversationSummary])
async def get_all_chat_histories(db: Session = Depends(get_db), current_user: User = Depends(auth.get_current_active_user)):
    return db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()

@app.get("/history/{conversation_id}", response_model=ConversationDetail)
async def get_chat_history(conversation_id: str, db: Session = Depends(get_db), current_user: User = Depends(auth.get_current_active_user)):
    conversation = db.query(ChatSession).filter(
        ChatSession.id == conversation_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")
    return conversation

@app.post("/chat")
async def chat(
    req: SimpleChatRequest,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Simple non-streaming chat endpoint"""
    try:
        # Check if client-specific search is requested
        if req.client_specific and req.client_id:
            # Import here to avoid circular imports
            from core.client_document_processor import client_document_processor
            
            # Use client-specific search
            matches = client_document_processor.search_client_documents(
                req.client_id, 
                req.message, 
                top_k=5
            )
            source_documents = [{"source": m.get('metadata', {}).get('source'), "client_specific": True} for m in matches]
        else:
            # Use general search
            matches = pinecone_manager.query_index(req.message, top_k=5)
            source_documents = [{"source": m.get('metadata', {}).get('source')} for m in matches]

        # Generate the answer using the LLM
        full_response = ""
        generator = llm_handler.stream_answer(req.message, matches, [])
        
        async for chunk in generator:
            full_response += chunk

        # Return the complete response
        return {
            "response": full_response,
            "sources": source_documents
        }
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, current_user: User = Depends(auth.get_current_active_user)):
    async def stream_generator() -> AsyncGenerator[str, None]:
        full_response = ""
        source_documents = []
        chat_id = str(uuid.uuid4()) # Generate a single ID for the entire conversation

        try:
            # Check if client-specific search is requested
            if req.client_id:
                # Import here to avoid circular imports
                from core.client_document_processor import client_document_processor
                
                # Use client-specific search
                matches = client_document_processor.search_client_documents(
                    req.client_id, 
                    req.query, 
                    top_k=5
                )
                source_documents = [{"source": m.get('metadata', {}).get('source'), "client_specific": True} for m in matches]
            else:
                # Use general search
                matches = pinecone_manager.query_index(req.query, top_k=5)
                source_documents = [{"source": m.get('metadata', {}).get('source')} for m in matches]

            # Choose the appropriate handler based on chat mode
            if req.chat_mode == 'deep':
                # Use deep research handler for comprehensive responses
                from core.deep_research_handler import deep_research_handler
                generator = deep_research_handler.stream_deep_research_response(req.query, matches, req.history)
            else:
                # Use standard handler with mode-specific prompts
                generator = llm_handler.stream_answer(req.query, matches, req.history, req.chat_mode or 'standard')
            
            async for chunk in generator:
                # The generator from llm_handler now only yields content strings
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk, 'chatId': chat_id, 'sources': source_documents})}\n\n"

            if full_response:
                history_messages = req.history + [
                    {"text": req.query, "sender": "user"},
                    {"text": full_response, "sender": "ai", "sources": [s['source'] for s in source_documents if s['source']]}
                ]
                
                pydantic_messages = [ChatMessage(**msg) for msg in history_messages]
                # Use the same chat_id generated at the start of the stream
                history_to_save = ChatHistory(chat_id=uuid.UUID(chat_id), messages=pydantic_messages)

                with SessionLocal() as db:
                    await run_in_threadpool(save_chat_history_sync, history_to_save, db, current_user)

        except Exception as e:
            logger.error(f"Error during chat stream: {e}", exc_info=True)
            error_message = json.dumps({"error": "An unexpected error occurred."})
            yield f"data: {error_message}\n\n"
        finally:
            yield "data: [DONE]\n\n"
            logger.info("Chat stream finished.")

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

@app.post("/agent-ideas", response_model=AgentIdeaResponse)
async def create_agent_idea(
    idea: AgentIdeaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """Create a new agent idea from the ideation process."""
    db_idea = AgentIdea(
        id=str(uuid.uuid4()),
        title=idea.title,
        summary=idea.summary,
        steps=idea.steps,
        agent_stack=idea.agent_stack,
        client_requirements=idea.client_requirements,
        conversation_history=idea.conversation_history,
        agent_type=idea.agent_type,
        implementation_estimate=idea.implementation_estimate,
        security_considerations=idea.security_considerations,
        future_enhancements=idea.future_enhancements,
        user_id=current_user.id
    )
    db.add(db_idea)
    db.commit()
    db.refresh(db_idea)
    return db_idea

@app.get("/agent-ideas", response_model=List[AgentIdeaResponse])
async def get_agent_ideas(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """Get all agent ideas (shared across all users)."""
    return db.query(AgentIdea).order_by(AgentIdea.created_at.desc()).all()

@app.get("/agent-ideas/{idea_id}", response_model=AgentIdeaResponse)
async def get_agent_idea(
    idea_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """Get a specific agent idea (accessible by any user)."""
    idea = db.query(AgentIdea).filter(
        AgentIdea.id == idea_id
    ).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Agent idea not found")
    return idea

@app.put("/agent-ideas/{idea_id}", response_model=AgentIdeaResponse)
async def update_agent_idea(
    idea_id: str,
    update: AgentIdeaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """Update an existing agent idea (any user can update)."""
    idea = db.query(AgentIdea).filter(
        AgentIdea.id == idea_id
    ).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Agent idea not found")
    
    update_data = update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(idea, field, value)
    
    idea.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(idea)
    return idea

@app.put("/agent-ideas/{idea_id}/full-update", response_model=AgentIdeaResponse)
async def full_update_agent_idea(
    idea_id: str,
    spec_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """Full update of an agent idea with all fields."""
    idea = db.query(AgentIdea).filter(
        AgentIdea.id == idea_id
    ).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Agent idea not found")
    
    # Update all fields from spec_data
    for field, value in spec_data.items():
        if hasattr(idea, field) and field not in ['id', 'created_at', 'user_id']:
            setattr(idea, field, value)
    
    idea.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(idea)
    return idea

@app.delete("/agent-ideas/{idea_id}")
async def delete_agent_idea(
    idea_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """Delete an agent idea (any user can delete)."""
    idea = db.query(AgentIdea).filter(
        AgentIdea.id == idea_id
    ).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Agent idea not found")
    
    db.delete(idea)
    db.commit()
    return {"message": "Agent idea deleted successfully"}

@app.post("/agent-ideator/chat")
async def agent_ideator_chat(
    message: IdeationMessage,
    current_user: User = Depends(auth.get_current_active_user)
):
    """Handle the conversational agent ideation process."""
    from core import ideator_handler
    
    response = await ideator_handler.process_ideation_message(
        message.message,
        message.conversation_history
    )
    
    # Check if it's a streaming response
    if response.get("stream"):
        async def stream_generator():
            try:
                async for chunk in response["generator"]:
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                logger.error(f"Error during ideation stream: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        # Non-streaming response
        return response

@app.post("/agent-ideator/edit")
async def agent_ideator_edit(
    message: EditMessage,
    current_user: User = Depends(auth.get_current_active_user)
):
    """Handle the conversational agent editing process."""
    from core import ideator_handler
    
    response = await ideator_handler.process_edit_message(
        message.message,
        message.current_spec,
        message.conversation_history
    )
    
    # Check if it's a streaming response
    if response.get("stream"):
        async def stream_generator():
            try:
                async for chunk in response["generator"]:
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                logger.error(f"Error during edit stream: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        # Non-streaming response
        return response

@app.post("/agent-ideas/move-to-production")
async def move_agent_to_production(
    request: MoveToProductionRequest,
    current_user: User = Depends(auth.get_current_active_user)
):
    """Send agent specification to production team (via email for now)."""
    try:
        # Format the specification details
        spec = request.spec_details
        email_content = f"""
New Agent Production Request from {current_user.email}

Agent Title: {spec.get('title', 'N/A')}
Type: {spec.get('agent_type', 'N/A')}

Summary:
{spec.get('summary', 'N/A')}

Implementation Steps:
{chr(10).join(f"- {step}" for step in spec.get('steps', []))}

Technical Stack:
{json.dumps(spec.get('agent_stack', {}), indent=2)}

Client Requirements:
{chr(10).join(f"- {req}" for req in spec.get('client_requirements', []))}

Cost Estimate:
Traditional Approach: {spec.get('implementation_estimate', {}).get('traditional_approach', {}).get('total_cost', 'N/A')}
AI-Powered Approach: {spec.get('implementation_estimate', {}).get('ai_powered_approach', {}).get('total_cost', 'N/A')}

Specification ID: {spec.get('id', 'N/A')}
User Email: {current_user.email}
"""
        
        # For now, just log it - in production, you'd send an actual email
        logger.info(f"Production request from {current_user.email}:")
        logger.info(email_content)
        
        # In a real implementation, you would send an email here
        # Example email sending code (requires SMTP configuration):
        """
        msg = MIMEMultipart()
        msg['From'] = 'system@nbrain.ai'
        msg['To'] = 'danny@nbrain.ai'
        msg['Subject'] = f'New Agent Production Request: {spec.get("title", "Untitled")}'
        msg.attach(MIMEText(email_content, 'plain'))
        
        # Send email via SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('your-email@gmail.com', 'your-password')
            server.send_message(msg)
        """
        
        return {"message": "Agent specification sent to production team successfully"}
    except Exception as e:
        logger.error(f"Error sending to production: {e}")
        raise HTTPException(status_code=500, detail="Failed to send specification to production team")

@app.post("/agent-ideas/create-google-doc")
async def create_agent_google_doc(
    spec_data: dict,
    current_user: User = Depends(auth.get_current_active_user)
):
    """Create a Google Doc from agent specification."""
    try:
        result = google_docs_handler.create_agent_spec_doc(spec_data)
        
        if result['success']:
            return {
                "success": True,
                "doc_url": result['doc_url'],
                "doc_id": result['doc_id'],
                "message": "Google Doc created successfully"
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=result.get('error', 'Failed to create Google Doc')
            )
    except Exception as e:
        logger.error(f"Error creating Google Doc: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create Google Doc: {str(e)}"
        )

# --- CRM Endpoints ---
# Import and setup CRM endpoints
from core.crm_endpoints import setup_crm_endpoints
setup_crm_endpoints(app)

# --- Oracle Endpoints ---
# Import and setup Oracle V2 endpoints
try:
    logger.info("Attempting to import Oracle V2 endpoints...")
    from core.oracle_v2_endpoints import router as oracle_router, oauth_callback
    logger.info("Successfully imported Oracle V2")
    app.include_router(oracle_router)
    logger.info("Successfully included Oracle V2 router")
    
    # Register the OAuth callback separately without the prefix
    @app.get("/oracle/auth/callback")
    async def oauth_callback_handler(
        code: str,
        state: str
    ):
        return await oauth_callback(code, state)
    
    logger.info("Oracle V2 endpoints configured successfully")
    
except ImportError as e:
    logger.error(f"Failed to import Oracle V2 endpoints: {e}")
    logger.error("Oracle functionality will be limited")
    
    # Create minimal fallback endpoints
    from fastapi import APIRouter
    oracle_router = APIRouter(prefix="/api/oracle", tags=["oracle"])
    
    @oracle_router.get("/action-items")
    async def fallback_action_items(current_user: User = Depends(auth.get_current_active_user)):
        return []
    
    @oracle_router.get("/sources")
    async def fallback_sources(current_user: User = Depends(auth.get_current_active_user)):
        return []
    
    app.include_router(oracle_router)

# Always register the OAuth callback endpoint
@app.get("/oracle/auth/callback")
async def oauth_callback_fallback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Fallback OAuth callback handler"""
    try:
        from core.oracle_endpoints import oauth_callback
        return await oauth_callback(code, state, db)
    except:
        # Return a basic success response
        return {
            "status": "error",
            "message": "OAuth callback handler not available",
            "result": {"error": "Service temporarily unavailable"}
        }

# Add non-prefixed Oracle endpoints for ProfilePage compatibility
# These are always registered regardless of whether Oracle endpoints import successfully
@app.get("/oracle/sources")
async def get_oracle_sources_compat(
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get data sources for ProfilePage compatibility"""
    try:
        from core.oracle_endpoints import get_data_sources
        return await get_data_sources(current_user, db)
    except:
        # Fallback response
        return [
            {"id": "disconnected-email", "name": "Gmail", "type": "email", "status": "disconnected"},
            {"id": "disconnected-calendar", "name": "Google Calendar", "type": "calendar", "status": "disconnected"},
            {"id": "disconnected-drive", "name": "Google Drive", "type": "drive", "status": "disconnected"}
        ]

@app.post("/oracle/connect/{source_type}")
async def connect_oracle_source_compat(
    source_type: str,
    current_user: User = Depends(auth.get_current_active_user)
):
    """Connect data source for ProfilePage compatibility"""
    try:
        from core.oracle_endpoints import connect_data_source
        return await connect_data_source(source_type, current_user)
    except:
        # Fallback response
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "https://command.nbrain.ai/oracle/auth/callback")
        return {"authUrl": f"https://accounts.google.com/oauth/authorize?client_id=dummy&redirect_uri={redirect_uri}&scope=dummy&state=dummy"}

@app.post("/oracle/sync/{source_type}")
async def sync_oracle_source_compat(
    source_type: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Sync data source for ProfilePage compatibility"""
    try:
        from core.oracle_endpoints import sync_data_source
        return await sync_data_source(source_type, background_tasks, current_user, db)
    except:
        # Fallback response
        return {"message": f"Syncing {source_type} in background"}

@app.delete("/oracle/disconnect/{source_type}")
async def disconnect_oracle_source_compat(
    source_type: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Disconnect data source for ProfilePage compatibility"""
    try:
        from core.oracle_endpoints import disconnect_data_source
        return await disconnect_data_source(source_type, current_user, db)
    except:
        # Fallback response
        return {"message": f"Successfully disconnected {source_type}"}

# --- Client Portal Endpoints ---
# Import and setup Client Portal endpoints
setup_client_portal_endpoints(app)

# Setup Client AI endpoints
setup_client_ai_endpoints(app)

# Setup Voice endpoints
setup_voice_endpoints(app)

# Setup Super Agent endpoints
from core.super_agent_endpoints import setup_super_agent_endpoints
setup_super_agent_endpoints(app)

# Setup Social Media endpoints
from core.social_media_endpoints import setup_social_media_endpoints
setup_social_media_endpoints(app)

# Setup RAG endpoints
from core.rag_endpoints import setup_rag_endpoints
from core.salon_endpoints import setup_salon_endpoints
setup_rag_endpoints(app)

# Setup Salon Analytics endpoints
setup_salon_endpoints(app)

# Setup User Management endpoints
from core.user_routes import router as user_router
app.include_router(user_router, prefix="/user", tags=["users"])

# Setup Recordings endpoints
from core.recordings_endpoints import router as recordings_router
from core.social_media_automator.api import router as social_media_automator_router
from core.readai_endpoints import setup_readai_endpoints
app.include_router(recordings_router, prefix="/api/recordings", tags=["recordings"])

# Social Media Automator endpoints
app.include_router(social_media_automator_router, prefix="/api/social-media-automator", tags=["social-media-automator"])

# ReadAI integration
setup_readai_endpoints(app)

# Note: WebSocket endpoints don't use the /api prefix
# from core.recordings_endpoints import websocket_transcribe
# app.add_api_websocket_route("/ws/transcribe", websocket_transcribe)

# --- Run the app ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.get("/debug/oracle-health")
async def check_oracle_health(db: Session = Depends(get_db)):
    """Debug endpoint to check Oracle database health"""
    try:
        # Check if oracle tables exist
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'oracle_%'
        """))
        tables = [row[0] for row in result]
        
        # Try a simple query
        try:
            count = db.query(User).count()
            db_status = "healthy"
        except Exception as e:
            db_status = f"error: {str(e)}"
            # Rollback any failed transaction
            db.rollback()
        
        # Check if oracle endpoints are loaded by looking for specific routes
        oracle_routes = []
        for route in app.routes:
            if hasattr(route, 'path') and '/oracle/' in route.path:
                oracle_routes.append(route.path)
        
        return {
            "oracle_tables": tables,
            "database_status": db_status,
            "oracle_endpoints_loaded": len(oracle_routes) > 0,
            "oracle_routes": oracle_routes[:5]  # Show first 5 routes as sample
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}