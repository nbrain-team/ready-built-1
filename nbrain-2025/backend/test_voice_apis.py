"""
Test script to verify voice API integrations are working.
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_deepgram():
    """Test Deepgram API connection."""
    from core.voice_integrations import DeepgramSTT
    
    print("Testing Deepgram connection...")
    stt = DeepgramSTT()
    connected = await stt.connect()
    
    if connected:
        print("✅ Deepgram connected successfully!")
        await stt.close()
    else:
        print("❌ Deepgram connection failed")
        
async def test_elevenlabs():
    """Test ElevenLabs API connection."""
    from core.voice_integrations import ElevenLabsTTS
    
    print("\nTesting ElevenLabs connection...")
    tts = ElevenLabsTTS()
    connected = await tts.connect()
    
    if connected:
        print("✅ ElevenLabs connected successfully!")
        
        # Test generating a short phrase
        print("Testing TTS generation...")
        audio_chunks = []
        async for chunk in tts.speak("Hello, this is a test.", flush=True):
            audio_chunks.append(chunk)
            
        if audio_chunks:
            print(f"✅ Generated {len(audio_chunks)} audio chunks")
        
        await tts.close()
    else:
        print("❌ ElevenLabs connection failed")
        
async def test_twilio():
    """Test Twilio credentials."""
    from core.twilio_handler import twilio_client
    
    print("\nTesting Twilio credentials...")
    try:
        # Get account info
        account = twilio_client.api.accounts(os.getenv("TWILIO_ACCOUNT_SID")).fetch()
        print(f"✅ Twilio account active: {account.friendly_name}")
        print(f"   Phone number: {os.getenv('TWILIO_PHONE_NUMBER')}")
    except Exception as e:
        print(f"❌ Twilio error: {e}")

async def main():
    """Run all tests."""
    print("🎤 Voice API Integration Tests\n")
    
    await test_deepgram()
    await test_elevenlabs()
    await test_twilio()
    
    print("\n✨ Tests complete!")

if __name__ == "__main__":
    asyncio.run(main()) 