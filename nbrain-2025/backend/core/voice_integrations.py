"""
Real-time voice integrations for Deepgram STT and ElevenLabs TTS.
"""

import asyncio
import base64
import json
from typing import AsyncGenerator, Optional
import websockets
import httpx
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import logging

from .voice_config import (
    DEEPGRAM_API_KEY, 
    ELEVENLABS_API_KEY,
    DEEPGRAM_MODEL,
    ELEVENLABS_MODEL,
    ELEVENLABS_VOICE_SETTINGS,
    AUDIO_SAMPLE_RATE
)

logger = logging.getLogger(__name__)

class DeepgramSTT:
    """Deepgram real-time speech-to-text integration."""
    
    def __init__(self):
        self.dg_client = DeepgramClient(DEEPGRAM_API_KEY)
        self.dg_connection = None
        self.transcript_queue = asyncio.Queue()
        
    async def connect(self):
        """Establish WebSocket connection to Deepgram."""
        try:
            # Configure Deepgram options for best real-time performance
            options = LiveOptions(
                model=DEEPGRAM_MODEL,
                language="en-US",
                punctuate=True,
                smart_format=True,
                interim_results=True,
                utterance_end_ms=1000,
                vad_events=True,
                endpointing=300
            )
            
            # Create WebSocket connection
            self.dg_connection = self.dg_client.listen.live.v("1")
            
            # Set up event handlers
            self.dg_connection.on(LiveTranscriptionEvents.Transcript, self._handle_transcript)
            self.dg_connection.on(LiveTranscriptionEvents.Close, lambda _: logger.info("Deepgram connection closed"))
            
            # Start the connection
            await self.dg_connection.start(options)
            
            logger.info("Deepgram STT connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Deepgram: {e}")
            return False
            
    async def _handle_transcript(self, *args, **kwargs):
        """Handle incoming transcripts from Deepgram."""
        result = args[0] if args else kwargs.get('result')
        
        if result and hasattr(result, 'channel'):
            channel = result.channel
            if hasattr(channel, 'alternatives') and channel.alternatives:
                alternative = channel.alternatives[0]
                transcript = alternative.transcript
                confidence = getattr(alternative, 'confidence', 0)
                is_final = result.is_final if hasattr(result, 'is_final') else False
                speech_final = result.speech_final if hasattr(result, 'speech_final') else False
                
                if transcript:
                    await self.transcript_queue.put({
                        "text": transcript,
                        "confidence": confidence,
                        "is_final": is_final,
                        "speech_final": speech_final
                    })
                    
    async def send_audio(self, audio_data: bytes):
        """Send audio data to Deepgram for transcription."""
        if self.dg_connection:
            await self.dg_connection.send(audio_data)
            
    async def get_transcript(self) -> Optional[dict]:
        """Get next transcript from queue."""
        try:
            return await asyncio.wait_for(self.transcript_queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            return None
            
    async def close(self):
        """Close Deepgram connection."""
        if self.dg_connection:
            await self.dg_connection.finish()
            

class ElevenLabsTTS:
    """ElevenLabs text-to-speech integration with streaming."""
    
    def __init__(self, voice_id: str = "21m00Tcm4TlvDq8ikWAM"):
        self.voice_id = voice_id
        self.api_key = ELEVENLABS_API_KEY
        self.ws_url = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id={ELEVENLABS_MODEL}"
        self.socket = None
        self.audio_queue = asyncio.Queue()
        
    async def connect(self):
        """Connect to ElevenLabs WebSocket for streaming TTS."""
        try:
            headers = {
                "xi-api-key": self.api_key,
            }
            
            self.socket = await websockets.connect(self.ws_url, extra_headers=headers)
            
            # Send initial configuration
            await self.socket.send(json.dumps({
                "text": " ",
                "voice_settings": ELEVENLABS_VOICE_SETTINGS,
                "generation_config": {
                    "chunk_length_schedule": [120, 160, 250, 290]
                }
            }))
            
            # Start audio receiver
            asyncio.create_task(self._receive_audio())
            
            logger.info("ElevenLabs TTS connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to ElevenLabs: {e}")
            return False
            
    async def _receive_audio(self):
        """Receive audio chunks from ElevenLabs."""
        try:
            async for message in self.socket:
                data = json.loads(message)
                
                if data.get("audio"):
                    # Decode base64 audio
                    audio_chunk = base64.b64decode(data["audio"])
                    await self.audio_queue.put(audio_chunk)
                    
                if data.get("isFinal"):
                    # Signal end of audio
                    await self.audio_queue.put(None)
                    
        except Exception as e:
            logger.error(f"Error receiving ElevenLabs audio: {e}")
            
    async def speak(self, text: str, flush: bool = False) -> AsyncGenerator[bytes, None]:
        """Stream text to speech."""
        if not self.socket:
            await self.connect()
            
        # Send text for synthesis
        await self.socket.send(json.dumps({
            "text": text + " " if not flush else text,
            "flush": flush
        }))
        
        # Yield audio chunks as they arrive
        while True:
            try:
                chunk = await asyncio.wait_for(self.audio_queue.get(), timeout=5.0)
                if chunk is None:  # End of stream
                    break
                yield chunk
            except asyncio.TimeoutError:
                if flush:
                    break
                continue
                
    async def close(self):
        """Close ElevenLabs connection."""
        if self.socket:
            await self.socket.close()
            

class VoiceOrchestrator:
    """Orchestrates STT and TTS for natural conversations."""
    
    def __init__(self):
        self.stt = DeepgramSTT()
        self.tts = None  # Will be initialized with voice selection
        self.is_speaking = False
        self.should_stop_speaking = False
        
    async def initialize(self, voice_id: str = "21m00Tcm4TlvDq8ikWAM"):
        """Initialize both STT and TTS connections."""
        self.tts = ElevenLabsTTS(voice_id)
        
        # Connect both services
        stt_connected = await self.stt.connect()
        tts_connected = await self.tts.connect()
        
        return stt_connected and tts_connected
        
    async def process_audio_input(self, audio_data: bytes) -> Optional[dict]:
        """Process incoming audio and return transcript if available."""
        await self.stt.send_audio(audio_data)
        return await self.stt.get_transcript()
        
    async def speak_response(self, text: str, websocket) -> None:
        """Speak a response with support for interruption."""
        self.is_speaking = True
        self.should_stop_speaking = False
        
        try:
            async for audio_chunk in self.tts.speak(text, flush=True):
                if self.should_stop_speaking:
                    logger.info("Speech interrupted by user")
                    break
                    
                # Send audio chunk to client
                await websocket.send_bytes(audio_chunk)
                
        finally:
            self.is_speaking = False
            
    def interrupt_speech(self):
        """Signal to stop current speech."""
        if self.is_speaking:
            self.should_stop_speaking = True
            
    async def close(self):
        """Clean up connections."""
        await self.stt.close()
        if self.tts:
            await self.tts.close() 