"""Voice API Configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

# Voice API Keys
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Voice Settings
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
DEFAULT_VOICE_SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.75
}

# Keep the old name for backward compatibility
ELEVENLABS_VOICE_SETTINGS = DEFAULT_VOICE_SETTINGS

# Deepgram Settings
DEEPGRAM_MODEL = "nova-2"
DEEPGRAM_LANGUAGE = "en-US"

# ElevenLabs Settings
ELEVENLABS_MODEL = "eleven_monolingual_v1"

# Audio Settings
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1

# WebSocket Settings
WS_CHUNK_SIZE = 4096 