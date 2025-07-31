"""
Voice API endpoints for real-time audio conversations.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from sqlalchemy.orm import Session
import asyncio
import json
import base64
from typing import Optional
import os
from datetime import datetime

from .database import get_db, User, AgentIdea
from .auth import get_current_active_user
from .voice_handler import VoiceConversationManager, VoicePersonality

router = APIRouter(prefix="/voice", tags=["voice"])

# Store active conversations
active_conversations = {}

class VoiceSession:
    def __init__(self, user_id: int, session_id: str):
        self.user_id = user_id
        self.session_id = session_id
        self.manager = VoiceConversationManager()
        self.start_time = datetime.utcnow()
        self.agent_idea_id: Optional[int] = None
        
@router.websocket("/ws/{session_id}")
async def voice_websocket(
    websocket: WebSocket,
    session_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for voice conversations."""
    await websocket.accept()
    
    try:
        # Authenticate user from query params or first message
        user = None
        auth_message = await websocket.receive_json()
        if auth_message.get("type") == "auth":
            token = auth_message.get("token")
            # Manual token verification for WebSocket
            from .auth import verify_token
            try:
                payload = verify_token(token)
                email = payload.get("sub")
                user = db.query(User).filter(User.email == email).first()
            except:
                user = None
            
        if not user:
            await websocket.send_json({"type": "error", "message": "Authentication required"})
            await websocket.close()
            return
            
        # Create voice session
        session = VoiceSession(user.id, session_id)
        active_conversations[session_id] = session
        
        # Initialize conversation manager
        await session.manager.initialize(websocket)
        
        # Start async tasks
        tasks = []
        
        # Main message handler
        async def handle_messages():
            while True:
                try:
                    message = await websocket.receive()
                    
                    if "text" in message:
                        data = json.loads(message["text"])
                        await handle_control_message(session, data)
                        
                    elif "bytes" in message:
                        # Handle audio data
                        audio_data = message["bytes"]
                        async for result in session.manager.handle_audio_stream(audio_data):
                            await websocket.send_json(result)
                            
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
                    
        tasks.append(asyncio.create_task(handle_messages()))
        
        # Wait for tasks
        await asyncio.gather(*tasks)
        
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"Connection error: {str(e)}"
        })
    finally:
        # Cleanup
        if session_id in active_conversations:
            del active_conversations[session_id]
        await websocket.close()
        
async def handle_control_message(session: VoiceSession, data: dict):
    """Handle control messages from client."""
    msg_type = data.get("type")
    
    if msg_type == "start_ideation":
        # Start new ideation session
        topic = data.get("topic", "new agent")
        await session.manager.websocket.send_json({
            "type": "ideation_started",
            "topic": topic,
            "message": f"Great! Let's explore ideas for {topic}. What problem are you trying to solve?"
        })
        
    elif msg_type == "save_idea":
        # Save the current conversation as an agent idea
        if session.manager.conversation_history:
            # Extract idea from conversation
            idea_data = await extract_idea_from_conversation(
                session.manager.conversation_history
            )
            # Save to database
            # ... database logic here
            
    elif msg_type == "change_voice":
        # Allow changing voice personality
        voice_id = data.get("voice_id")
        if voice_id:
            session.manager.personality.voice_id = voice_id
            
    elif msg_type == "end_session":
        # Gracefully end the session
        await session.manager.websocket.send_json({
            "type": "session_ended",
            "duration": (datetime.utcnow() - session.start_time).seconds
        })
        
async def extract_idea_from_conversation(history: list) -> dict:
    """Extract structured agent idea from conversation history."""
    # This will use GPT to extract structured data
    # For now, return placeholder
    return {
        "name": "Extracted Agent Idea",
        "description": "Agent idea from voice conversation",
        "implementation_details": ""
    }
    
@router.get("/voices")
async def get_available_voices():
    """Get list of available voice personalities."""
    voices = [
        {
            "id": "21m00Tcm4TlvDq8ikWAM",
            "name": "Rachel",
            "description": "Professional, clear, and friendly",
            "gender": "female",
            "style": "consultant"
        },
        {
            "id": "pNInz6obpgDQGcFmaJgB",
            "name": "Adam",
            "description": "Confident and articulate",
            "gender": "male",
            "style": "executive"
        },
        {
            "id": "ThT5KcBeYPX3keUQqHPh",
            "name": "Dorothy",
            "description": "Warm and engaging",
            "gender": "female",
            "style": "mentor"
        }
    ]
    return {"voices": voices}
    
@router.get("/session/{session_id}/transcript")
async def get_session_transcript(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get transcript of a voice session."""
    session = active_conversations.get(session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return {
        "session_id": session_id,
        "transcript": session.manager.conversation_history,
        "duration": (datetime.utcnow() - session.start_time).seconds
    } 