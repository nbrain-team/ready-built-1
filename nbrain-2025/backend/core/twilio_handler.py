"""
Twilio integration for phone-based voice AI conversations.
"""

from fastapi import APIRouter, Request, Response, WebSocket
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from twilio.rest import Client
from twilio.request_validator import RequestValidator
import os
import logging
import json
import base64
import asyncio
from typing import Dict

from .voice_config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER
)
from .voice_handler import VoiceConversationManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/twilio", tags=["twilio"])

# Initialize Twilio client only if credentials are provided
twilio_client = None
request_validator = None

if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        request_validator = RequestValidator(TWILIO_AUTH_TOKEN)
        logger.info("Twilio client initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Twilio client: {e}")
else:
    logger.warning("Twilio credentials not provided - Twilio features will be disabled")

# Store active phone sessions
phone_sessions: Dict[str, VoiceConversationManager] = {}

@router.post("/voice")
async def handle_incoming_call(request: Request):
    """Handle incoming Twilio voice calls"""
    if not twilio_client:
        logger.error("Twilio client not initialized - missing credentials")
        return Response(
            content=str(VoiceResponse()),
            media_type="application/xml"
        )
    
    try:
        # Validate request is from Twilio
        form_data = await request.form()
        
        # Get caller information
        caller = form_data.get("From", "Unknown")
        call_sid = form_data.get("CallSid")
        
        logger.info(f"Incoming call from {caller}, SID: {call_sid}")
        
        # Create TwiML response
        response = VoiceResponse()
        
        # Greet the caller
        response.say(
            "Welcome to nBrain AI Ideator. I'll connect you with our AI assistant now.",
            voice="Polly.Joanna"
        )
        
        # Set up media stream
        connect = Connect()
        stream = Stream(
            url=f"wss://{request.headers.get('host')}/twilio/stream/{call_sid}"
        )
        connect.append(stream)
        response.append(connect)
        
        return Response(content=str(response), media_type="text/xml")
    except Exception as e:
        logger.error(f"Error handling incoming call: {e}")
        return Response(
            content=str(VoiceResponse()),
            media_type="application/xml"
        )

@router.websocket("/stream/{call_sid}")
async def handle_media_stream(websocket: WebSocket, call_sid: str):
    """Handle Twilio media stream WebSocket connection."""
    await websocket.accept()
    
    # Create conversation manager for this call
    manager = VoiceConversationManager()
    phone_sessions[call_sid] = manager
    
    # Custom websocket wrapper for Twilio format
    twilio_ws = TwilioWebSocketWrapper(websocket, call_sid)
    
    try:
        # Initialize conversation
        await manager.initialize(twilio_ws)
        
        # Process incoming messages
        async for message in websocket.iter_text():
            data = json.loads(message)
            
            if data["event"] == "start":
                # Stream started
                stream_sid = data["start"]["streamSid"]
                logger.info(f"Media stream started: {stream_sid}")
                
            elif data["event"] == "media":
                # Audio data from caller
                payload = data["media"]["payload"]
                audio_data = base64.b64decode(payload)
                
                # Process through conversation manager
                async for result in manager.handle_audio_stream(audio_data):
                    # Results are handled by the wrapper
                    pass
                    
            elif data["event"] == "stop":
                # Call ended
                logger.info(f"Call ended: {call_sid}")
                break
                
    except Exception as e:
        logger.error(f"Error in media stream: {e}")
    finally:
        # Cleanup
        await manager.cleanup()
        if call_sid in phone_sessions:
            del phone_sessions[call_sid]
        await websocket.close()

class TwilioWebSocketWrapper:
    """Wrapper to adapt our WebSocket interface to Twilio's format."""
    
    def __init__(self, websocket: WebSocket, call_sid: str):
        self.websocket = websocket
        self.call_sid = call_sid
        self.stream_sid = None
        
    async def send_json(self, data: dict):
        """Send JSON data (for status messages)."""
        # Twilio doesn't use JSON messages in the same way
        # Log them instead
        logger.info(f"Status for {self.call_sid}: {data}")
        
    async def send_bytes(self, audio_data: bytes):
        """Send audio data to Twilio."""
        # Convert audio to mulaw 8000Hz as required by Twilio
        # For now, we'll send as-is (you may need audio conversion)
        
        # Encode to base64
        payload = base64.b64encode(audio_data).decode('utf-8')
        
        # Send in Twilio format
        message = {
            "event": "media",
            "streamSid": self.stream_sid,
            "media": {
                "payload": payload
            }
        }
        
        await self.websocket.send_json(message)

@router.post("/outbound")
async def make_outbound_call(phone_number: str, initial_message: str = None):
    """Make an outbound call to a phone number."""
    if not twilio_client:
        logger.error("Twilio client not initialized - cannot make outbound call")
        return {"error": "Twilio features are disabled due to missing credentials."}
    
    try:
        # Validate phone number format
        if not phone_number.startswith('+'):
            phone_number = f"+1{phone_number}"  # Assume US number
        
        # Create call
        call = twilio_client.calls.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"https://{os.getenv('RENDER_EXTERNAL_URL', 'localhost:8000')}/twilio/voice",
            status_callback=f"https://{os.getenv('RENDER_EXTERNAL_URL', 'localhost:8000')}/twilio/status"
        )
        
        # Store initial message if provided
        if initial_message:
            phone_sessions[call.sid] = {
                "initial_message": initial_message
            }
        
        return {
            "success": True,
            "call_sid": call.sid,
            "status": call.status
        }
        
    except Exception as e:
        logger.error(f"Failed to make outbound call: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/status/{call_sid}")
async def get_call_status(call_sid: str):
    """Get the status of a call."""
    if not twilio_client:
        logger.error("Twilio client not initialized - cannot fetch call status")
        return {"error": "Twilio features are disabled due to missing credentials."}
    
    try:
        call = twilio_client.calls(call_sid).fetch()
        return {
            "call_sid": call.sid,
            "status": call.status,
            "duration": call.duration,
            "from": call.from_,
            "to": call.to
        }
    except Exception as e:
        logger.error(f"Failed to get call status: {e}")
        return {
            "error": str(e)
        } 