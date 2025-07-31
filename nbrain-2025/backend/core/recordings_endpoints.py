from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import json
import uuid
import datetime
import asyncio
import logging
from pathlib import Path
import tempfile
import os
from sqlalchemy.orm import Session
from sqlalchemy import text
import openai
import base64

from .database import get_db
from .auth import get_current_active_user
from .client_portal_handler import ClientPortalHandler
from .database import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize OpenAI client once
openai_client = None
if os.getenv("OPENAI_API_KEY"):
    openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize handlers
client_handler = ClientPortalHandler()

# Store for active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

class TranscriptionWebSocket:
    """Handle real-time transcription via WebSocket"""
    
    def __init__(self, websocket: WebSocket, connection_id: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.audio_chunks = []  # Store individual chunks
        self.webm_header = None  # Store WebM header
        self.transcript_buffer = []
        self.action_items = []
        self.recommendations = []
        self.summary = ""
        self.client_id = None
        self.context = None
        self.last_process_time = datetime.datetime.now()
        self.chunk_count = 0
        self.silent_attempts = 0
        self.total_audio_size = 0
    
    async def process_audio_chunk(self, audio_data: bytes) -> None:
        """Process audio chunk and send updates"""
        try:
            self.chunk_count += 1
            self.total_audio_size += len(audio_data)
            
            # First chunk should contain WebM header
            if self.chunk_count == 1 and len(audio_data) > 4:
                if audio_data[:4] == b'\x1a\x45\xdf\xa3':  # EBML header
                    logger.info("Detected WebM header in first chunk")
                    # Extract a generous amount for the header (WebM headers can be large)
                    header_size = min(len(audio_data), 5000)
                    self.webm_header = audio_data[:header_size]
            
            # Store the chunk
            self.audio_chunks.append(audio_data)
            
            current_time = datetime.datetime.now()
            time_since_last_process = (current_time - self.last_process_time).total_seconds()
            
            # Log progress
            logger.debug(f"Chunk {self.chunk_count}: {len(audio_data)} bytes, Total chunks: {len(self.audio_chunks)}, Total size: {self.total_audio_size}")
            
            # Process when we have enough chunks (every 10 seconds or so)
            should_process = (
                len(self.audio_chunks) >= 10 or  # 10+ chunks
                (len(self.audio_chunks) >= 5 and time_since_last_process > 10) or  # 5+ chunks and 10 seconds
                (self.total_audio_size > 200000)  # Over 200KB total
            )
            
            if should_process:
                await self.attempt_transcription()
                self.last_process_time = current_time
                    
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
    
    async def attempt_transcription(self) -> None:
        """Attempt to transcribe accumulated audio chunks"""
        if not self.audio_chunks or not self.webm_header:
            logger.warning("No audio chunks or header available for transcription")
            return
        
        try:
            # Combine all chunks into complete audio
            complete_audio = b''.join(self.audio_chunks)
            
            # Try transcription
            transcript_text = await self.transcribe_audio(complete_audio)
            
            if transcript_text:
                self.transcript_buffer.append(transcript_text)
                self.silent_attempts = 0
                
                # Send transcript update
                await self.websocket.send_json({
                    "type": "transcript",
                    "text": transcript_text,
                    "timestamp": datetime.datetime.now().timestamp(),
                    "isFinal": True
                })
                
                # Clear processed chunks but keep some overlap for context
                if len(self.audio_chunks) > 2:
                    # Keep last 2 chunks for continuity
                    keep_chunks = self.audio_chunks[-2:]
                    keep_size = sum(len(chunk) for chunk in keep_chunks)
                    self.audio_chunks = keep_chunks
                    self.total_audio_size = keep_size
                
                # Analyze for insights periodically
                if len(self.transcript_buffer) % 3 == 0:
                    await self.analyze_transcript()
            else:
                self.silent_attempts += 1
                
                # If too many failed attempts, clear old chunks
                if self.silent_attempts > 3 and len(self.audio_chunks) > 5:
                    logger.info("Too many silent attempts, trimming old chunks")
                    self.audio_chunks = self.audio_chunks[-3:]  # Keep only last 3 chunks
                    self.total_audio_size = sum(len(chunk) for chunk in self.audio_chunks)
                    self.silent_attempts = 0
                    
        except Exception as e:
            logger.error(f"Error in transcription attempt: {e}")
    
    async def flush_buffer(self) -> None:
        """Force process any remaining audio in the buffer"""
        if self.audio_chunks:
            logger.info(f"Flushing {len(self.audio_chunks)} chunks with total size {self.total_audio_size} bytes")
            await self.attempt_transcription()
    
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio using OpenAI Whisper API"""
        try:
            if not openai_client:
                logger.warning("OpenAI API key not configured")
                return ""
            
            # Create a complete WebM file with header
            if self.webm_header and not audio_data.startswith(b'\x1a\x45\xdf\xa3'):
                # Prepend the header to make a valid WebM file
                complete_webm = self.webm_header + audio_data
            else:
                complete_webm = audio_data
            
            # Check minimum size
            if len(complete_webm) < 20000:  # 20KB minimum
                logger.debug(f"Audio too small for transcription: {len(complete_webm)} bytes")
                return ""
            
            logger.info(f"Attempting transcription with {len(complete_webm)} bytes")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_file:
                temp_file.write(complete_webm)
                temp_file_path = temp_file.name
                temp_file.flush()
                os.fsync(temp_file.fileno())  # Ensure data is written to disk
            
            try:
                # Verify file was written correctly
                actual_size = os.path.getsize(temp_file_path)
                logger.info(f"Temp file {temp_file_path} written with {actual_size} bytes")
                
                # Log first few bytes to verify format
                with open(temp_file_path, "rb") as f:
                    header_bytes = f.read(20)
                    logger.debug(f"File header: {header_bytes.hex()}")
                
                # Call OpenAI Whisper API
                with open(temp_file_path, "rb") as audio_file:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language="en",
                            response_format="text",
                            prompt="This is a business meeting or conference call. Transcribe all speech clearly."
                        )
                    )
                
                transcript = response.strip()
                
                # Clean up common artifacts and repeated words
                transcript = self.clean_transcript(transcript)
                
                # Filter out non-meaningful transcripts
                meaningless = ["", "you", "thank you.", ".", " ", "[music]", "[silence]", 
                              "you.", "hmm.", "uh.", "um.", "ah.", "[inaudible]", "[applause]",
                              "scratch", "scratch.", "test", "testing"]
                
                if transcript and len(transcript) > 5 and transcript.lower() not in meaningless:
                    logger.info(f"Successfully transcribed: {transcript[:100]}...")
                    return transcript
                else:
                    logger.debug(f"Filtered out transcript: '{transcript}'")
                    return ""
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            if "Invalid file format" in str(e):
                logger.error("File format issue - the audio data may be corrupted")
            return ""
    
    def clean_transcript(self, transcript: str) -> str:
        """Clean up common artifacts and issues in transcripts"""
        if not transcript:
            return ""
        
        # Remove common artifacts
        artifacts_to_remove = [
            "Transcribed by https://otter.ai",
            "Transcribed by otter.ai",
            "Powered by otter.ai",
            "Created by otter.ai",
            "Generated by otter.ai",
            "www.otter.ai",
            "otter.ai"
        ]
        
        cleaned = transcript
        for artifact in artifacts_to_remove:
            cleaned = cleaned.replace(artifact, "")
        
        # Remove repeated words (like "Scratch. Scratch. Scratch.")
        words = cleaned.split()
        if len(words) > 1:
            # Remove consecutive duplicate words
            cleaned_words = [words[0]]
            for i in range(1, len(words)):
                if words[i].lower() != words[i-1].lower():
                    cleaned_words.append(words[i])
                elif words[i].lower() == "scratch":
                    # Skip repeated "scratch"
                    continue
            cleaned = " ".join(cleaned_words)
        
        # Remove multiple spaces and clean up
        cleaned = " ".join(cleaned.split())
        
        # Remove trailing/leading punctuation artifacts
        cleaned = cleaned.strip(" .,;:")
        
        return cleaned

    async def analyze_transcript(self) -> None:
        """Analyze transcript for action items and insights"""
        full_transcript = " ".join(self.transcript_buffer)
        
        try:
            # Check if we have OpenAI configured for analysis
            if openai_client:
                # Use GPT to analyze the transcript
                prompt = f"""
                Analyze this meeting transcript and extract:
                1. Action items (specific tasks that need to be done)
                2. Key recommendations or decisions
                3. Brief summary of the discussion
                
                Transcript:
                {full_transcript}
                
                Return as JSON with keys: action_items (list of strings), recommendations (list of strings), summary (string)
                """
                
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that analyzes meeting transcripts."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=500
                    )
                )
                
                try:
                    insights = json.loads(response.choices[0].message.content)
                    
                    # Send new action items
                    for item in insights.get("action_items", []):
                        if item not in self.action_items:
                            self.action_items.append(item)
                            await self.websocket.send_json({
                                "type": "action_item",
                                "item": item
                            })
                    
                    # Send new recommendations
                    for rec in insights.get("recommendations", []):
                        if rec not in self.recommendations:
                            self.recommendations.append(rec)
                            await self.websocket.send_json({
                                "type": "recommendation",
                                "recommendation": rec
                            })
                    
                    # Update summary
                    if insights.get("summary"):
                        self.summary = insights["summary"]
                        await self.websocket.send_json({
                            "type": "summary_update",
                            "summary": self.summary
                        })
                        
                except json.JSONDecodeError:
                    logger.error("Failed to parse LLM response as JSON")
                    
            else:
                # Fallback to keyword-based analysis
                if "follow up" in full_transcript.lower() or "todo" in full_transcript.lower():
                    self.action_items.append("Follow up on discussed items")
                    await self.websocket.send_json({
                        "type": "action_item",
                        "item": "Follow up on discussed items"
                    })
                
                if "improve" in full_transcript.lower() or "consider" in full_transcript.lower():
                    self.recommendations.append("Consider the improvements discussed")
                    await self.websocket.send_json({
                        "type": "recommendation",
                        "recommendation": "Consider the improvements discussed"
                    })
                
                self.summary = f"Meeting transcript with {len(self.transcript_buffer)} segments recorded."
                await self.websocket.send_json({
                    "type": "summary_update",
                    "summary": self.summary
                })
                
        except Exception as e:
            logger.error(f"Error analyzing transcript: {e}")

@router.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """WebSocket endpoint for real-time transcription"""
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    
    transcription_handler = TranscriptionWebSocket(websocket, connection_id)
    active_connections[connection_id] = websocket
    
    try:
        while True:
            # Receive data from client
            data = await websocket.receive()
            
            if data["type"] == "websocket.receive":
                if "text" in data:
                    # Handle text messages (config, etc.)
                    message = json.loads(data["text"])
                    if message.get("type") == "config":
                        # Store configuration
                        transcription_handler.client_id = message.get("clientId")
                        transcription_handler.context = message.get("context")
                        
                elif "bytes" in data:
                    # Handle audio data
                    await transcription_handler.process_audio_chunk(data["bytes"])
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
        # Process any remaining audio before closing
        await transcription_handler.flush_buffer()
        # Do final analysis if we have content
        if transcription_handler.transcript_buffer:
            await transcription_handler.analyze_transcript()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        # Try to flush buffer even on error
        try:
            await transcription_handler.flush_buffer()
        except:
            pass
    finally:
        if connection_id in active_connections:
            del active_connections[connection_id]

@router.post("/save")
async def save_recording(
    audio: UploadFile = File(...),
    duration: int = Form(...),
    context: str = Form(...),
    transcript: str = Form(""),
    actionItems: str = Form("[]"),
    recommendations: str = Form("[]"),
    summary: str = Form(""),
    clientId: Optional[str] = Form(None),
    clientName: Optional[str] = Form(None),
    user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Save a completed recording with metadata"""
    try:
        # Generate unique ID
        recording_id = str(uuid.uuid4())
        
        # Save audio file
        audio_dir = Path("recordings") / user.id
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        audio_filename = f"{recording_id}.webm"
        audio_path = audio_dir / audio_filename
        
        # Save audio file
        with open(audio_path, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # Parse JSON fields
        action_items_list = json.loads(actionItems)
        recommendations_list = json.loads(recommendations)
        
        # Save to database using raw SQL
        db.execute(text("""
            INSERT INTO recordings (
                id, user_id, client_id, client_name, context,
                audio_path, duration, transcript, action_items,
                recommendations, summary, created_at
            ) VALUES (:id, :user_id, :client_id, :client_name, :context,
                     :audio_path, :duration, :transcript, :action_items,
                     :recommendations, :summary, :created_at)
        """), {
            "id": recording_id,
            "user_id": user.id,
            "client_id": clientId,
            "client_name": clientName,
            "context": context,
            "audio_path": str(audio_path),
            "duration": duration,
            "transcript": transcript,
            "action_items": json.dumps(action_items_list),
            "recommendations": json.dumps(recommendations_list),
            "summary": summary,
            "created_at": datetime.datetime.now()
        })
        
        # If client context, also save action items to client
        if clientId and action_items_list:
            for item in action_items_list:
                task_id = str(uuid.uuid4())
                db.execute(text("""
                    INSERT INTO client_tasks (
                        id, client_id, title, description, status,
                        source, created_at, created_by
                    ) VALUES (:id, :client_id, :title, :description, :status,
                            :source, :created_at, :created_by)
                """), {
                    "id": task_id,
                    "client_id": clientId,
                    "title": item,
                    "description": f"From recording on {datetime.datetime.now().strftime('%Y-%m-%d')}",
                    "status": "pending",
                    "source": "recording",
                    "created_at": datetime.datetime.now(),
                    "created_by": user.id
                })
        
        db.commit()
        
        return JSONResponse({
            "id": recording_id,
            "audioUrl": f"/api/recordings/{recording_id}/audio",
            "message": "Recording saved successfully"
        })
        
    except Exception as e:
        logger.error(f"Error saving recording: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{recording_id}/audio")
async def get_recording_audio(
    recording_id: str,
    user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve audio file for a recording"""
    try:
        # Get recording info
        result = db.execute(text("""
            SELECT audio_path, user_id FROM recordings
            WHERE id = :id
        """), {"id": recording_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Recording not found")
        
        audio_path, owner_id = result
        
        # Check permissions
        if owner_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Return audio file
        from fastapi.responses import FileResponse
        return FileResponse(audio_path, media_type="audio/webm")
        
    except Exception as e:
        logger.error(f"Error retrieving audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/client/{client_id}")
async def get_client_recordings(
    client_id: str,
    user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all recordings for a specific client"""
    try:
        results = db.execute(text("""
            SELECT id, client_name, duration, transcript, action_items,
                   recommendations, summary, created_at
            FROM recordings
            WHERE client_id = :client_id AND user_id = :user_id
            ORDER BY created_at DESC
        """), {"client_id": client_id, "user_id": user.id}).fetchall()
        
        recordings = []
        for row in results:
            recordings.append({
                "id": row[0],
                "clientName": row[1],
                "duration": row[2],
                "transcript": row[3],
                "actionItems": json.loads(row[4]) if row[4] else [],
                "recommendations": json.loads(row[5]) if row[5] else [],
                "summary": row[6],
                "createdAt": row[7].isoformat() if row[7] else None
            })
        
        return recordings
        
    except Exception as e:
        logger.error(f"Error fetching client recordings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/oracle/recent")
async def get_oracle_recordings(
    limit: int = 10,
    user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get recent Oracle (non-client) recordings"""
    try:
        results = db.execute(text("""
            SELECT id, duration, transcript, action_items,
                   recommendations, summary, created_at
            FROM recordings
            WHERE context = 'oracle' AND user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit
        """), {"user_id": user.id, "limit": limit}).fetchall()
        
        recordings = []
        for row in results:
            recordings.append({
                "id": row[0],
                "duration": row[1],
                "transcript": row[2],
                "actionItems": json.loads(row[3]) if row[3] else [],
                "recommendations": json.loads(row[4]) if row[4] else [],
                "summary": row[5],
                "createdAt": row[6].isoformat() if row[6] else None
            })
        
        return recordings
        
    except Exception as e:
        logger.error(f"Error fetching oracle recordings: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 