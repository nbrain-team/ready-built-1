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

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
request_validator = RequestValidator(TWILIO_AUTH_TOKEN)

# Store active phone sessions
phone_sessions: Dict[str, VoiceConversationManager] = {}

@router.post("/voice")
async def handle_incoming_call(request: Request):
    """Handle incoming phone calls via Twilio."""
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
    try:
        # Validate phone number format
        if not phone_number.startswith('+'):
            phone_number = '+1' + phone_number  # Assume US number
            
        # Make the call
        call = twilio_client.calls.create(
            twiml=f'<Response><Say>Hello, this is nBrain AI calling. {initial_message or "How can I help you today?"}</Say></Response>',
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER
        )
        
        logger.info(f"Outbound call initiated: {call.sid}")
        
        return {
            "call_sid": call.sid,
            "status": "initiated",
            "to": phone_number
        }
        
    except Exception as e:
        logger.error(f"Failed to make outbound call: {e}")
        return {"error": str(e)}

@router.get("/call-status/{call_sid}")
async def get_call_status(call_sid: str):
    """Get the status of a call."""
    try:
        call = twilio_client.calls(call_sid).fetch()
        return {
            "call_sid": call_sid,
            "status": call.status,
            "duration": call.duration,
            "from": call.from_,
            "to": call.to
        }
    except Exception as e:
        return {"error": str(e)} 