"""
Voice handler for AI Ideator with advanced conversation features.
Supports real-time speech recognition, natural TTS, and interruption handling.
"""

import asyncio
import json
import time
from typing import Optional, AsyncGenerator, Dict, Any
from enum import Enum
import numpy as np
from fastapi import WebSocket
from pydantic import BaseModel
import logging

from .voice_integrations import VoiceOrchestrator
from .voice_config import AUDIO_SAMPLE_RATE

logger = logging.getLogger(__name__)

class ConversationState(Enum):
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"

class VoicePersonality(BaseModel):
    name: str = "Professional Consultant"
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel from ElevenLabs
    speaking_rate: float = 1.0
    energy_level: str = "balanced"  # calm, balanced, energetic
    filler_phrases: list = [
        "Let me think about that for a moment...",
        "That's a great question...",
        "Hmm, interesting point...",
        "I see what you're getting at...",
        "Right, so if I understand correctly..."
    ]
    interruption_responses: list = [
        "Oh, please go ahead!",
        "Sorry, you were saying?",
        "Yes, please continue.",
        "I'm listening..."
    ]

class VoiceConversationManager:
    def __init__(self, personality: VoicePersonality = None):
        self.personality = personality or VoicePersonality()
        self.state = ConversationState.LISTENING
        self.conversation_history = []
        self.current_utterance = ""
        self.last_speech_time = 0
        self.websocket: Optional[WebSocket] = None
        
        # Voice orchestrator for real STT/TTS
        self.voice_orchestrator = VoiceOrchestrator()
        
        # Conversation context
        self.ideation_context = {
            "current_topic": None,
            "discussed_points": [],
            "agent_requirements": [],
            "clarifications_needed": []
        }
        
    async def initialize(self, websocket: WebSocket):
        """Initialize the conversation manager with websocket connection."""
        self.websocket = websocket
        
        # Initialize voice services
        initialized = await self.voice_orchestrator.initialize(self.personality.voice_id)
        if not initialized:
            await self.send_system_message("Failed to initialize voice services. Please check your connection.")
            return False
            
        await self.send_system_message("Voice ideator ready. Say hello to begin!")
        return True
        
    async def send_system_message(self, message: str):
        """Send a system message to the client."""
        await self.websocket.send_json({
            "type": "system",
            "message": message,
            "state": self.state.value
        })
        
    async def handle_audio_stream(self, audio_data: bytes) -> AsyncGenerator[Dict[str, Any], None]:
        """Process incoming audio stream with real STT."""
        # Process audio through Deepgram
        transcript_data = await self.voice_orchestrator.process_audio_input(audio_data)
        
        if transcript_data:
            # Check if user is speaking while AI is speaking
            if self.state == ConversationState.SPEAKING:
                self.voice_orchestrator.interrupt_speech()
                yield await self.handle_interruption()
            
            # Handle transcript
            if transcript_data["is_final"]:
                # Complete utterance
                self.current_utterance = transcript_data["text"]
                if transcript_data.get("speech_final"):
                    # User finished speaking
                    yield await self.process_user_input(self.current_utterance)
                    self.current_utterance = ""
            else:
                # Partial transcript
                yield {
                    "type": "partial_transcript",
                    "text": transcript_data["text"],
                    "confidence": transcript_data["confidence"]
                }
                
    async def handle_interruption(self) -> Dict[str, Any]:
        """Handle user interruption gracefully."""
        self.state = ConversationState.INTERRUPTED
        
        # Choose appropriate response
        response = np.random.choice(self.personality.interruption_responses)
        
        # Quick acknowledgment
        await self.speak(response, is_filler=True, quick=True)
        
        self.state = ConversationState.LISTENING
        
        return {
            "type": "interruption",
            "action": "stopped_speaking",
            "response": response
        }
        
    async def process_user_input(self, text: str) -> Dict[str, Any]:
        """Process complete user utterance with ideation logic."""
        self.state = ConversationState.THINKING
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": text,
            "timestamp": time.time()
        })
        
        # Quick thinking acknowledgment
        thinking_phrase = self._get_contextual_filler()
        await self.speak(thinking_phrase, is_filler=True, quick=True)
        
        # Process with ideator logic
        response = await self.get_ideator_response(text)
        
        # Send actual response
        await self.speak(response)
        
        # Add AI response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": time.time()
        })
        
        return {
            "type": "response",
            "user_input": text,
            "ai_response": response
        }
        
    def _get_contextual_filler(self) -> str:
        """Get a contextually appropriate filler phrase."""
        if len(self.conversation_history) < 2:
            return "Let me think about that..."
        elif "technical" in str(self.conversation_history[-1]):
            return "That's a technical question, let me consider the best approach..."
        else:
            return np.random.choice(self.personality.filler_phrases)
        
    async def get_ideator_response(self, user_input: str) -> str:
        """Get response from the ideator agent with context awareness."""
        # Import ideator handler
        from . import ideator_handler
        
        # Build context for ideator
        context = {
            "conversation_history": self.conversation_history,
            "ideation_context": self.ideation_context,
            "is_voice": True
        }
        
        # Get ideator response
        response = await ideator_handler.get_voice_response(user_input, context)
        
        # Update ideation context based on response
        self._update_ideation_context(user_input, response)
        
        return response
        
    def _update_ideation_context(self, user_input: str, ai_response: str):
        """Update the ideation context based on conversation."""
        # Simple context tracking - can be enhanced with NLP
        if "agent" in user_input.lower() or "build" in user_input.lower():
            self.ideation_context["current_topic"] = "agent_design"
        
        if "requirement" in ai_response.lower():
            self.ideation_context["clarifications_needed"].append("requirements")
            
    async def speak(self, text: str, is_filler: bool = False, quick: bool = False):
        """Convert text to speech using ElevenLabs."""
        self.state = ConversationState.SPEAKING
        
        try:
            # Send text notification to client
            await self.websocket.send_json({
                "type": "speaking_started",
                "text": text,
                "is_filler": is_filler
            })
            
            # Stream audio through ElevenLabs
            await self.voice_orchestrator.speak_response(text, self.websocket)
            
            # Notify speaking complete
            await self.websocket.send_json({
                "type": "speaking_complete"
            })
            
        except Exception as e:
            logger.error(f"Error during TTS: {e}")
        finally:
            if not quick:
                self.state = ConversationState.LISTENING
                
    async def cleanup(self):
        """Clean up resources."""
        await self.voice_orchestrator.close()
        
    def adjust_personality_dynamics(self, user_metrics: dict):
        """Adjust personality based on conversation metrics."""
        # Analyze speaking pace
        if user_metrics.get("words_per_minute", 120) > 150:
            self.personality.speaking_rate = 1.15  # Speed up slightly
            self.personality.energy_level = "energetic"
        elif user_metrics.get("words_per_minute", 120) < 90:
            self.personality.speaking_rate = 0.9  # Slow down
            self.personality.energy_level = "calm"
            
        # Adjust based on interruptions
        if user_metrics.get("interruption_count", 0) > 3:
            # User interrupts often - be more concise
            self.personality.filler_phrases = ["I see...", "Got it...", "Understood..."] 