"""
HeyGen Video Avatar Handler
"""

import os
import logging
import requests
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

class HeyGenHandler:
    """Handles HeyGen API integration for video avatar creation"""
    
    def __init__(self):
        self.api_key = os.getenv('HEYGEN_API_KEY')
        self.base_url = "https://api.heygen.com/v2"
        self.default_avatar_id = os.getenv('HEYGEN_DEFAULT_AVATAR_ID', 'josh_lite3_20230714')
        self.default_voice_id = os.getenv('HEYGEN_DEFAULT_VOICE_ID')
        
        if not self.api_key:
            logger.warning("HEYGEN_API_KEY not found. Video avatar features will be disabled.")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API headers"""
        return {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def list_avatars(self) -> Dict[str, Any]:
        """List available avatars"""
        if not self.api_key:
            return {"error": "HeyGen API key not configured"}
        
        try:
            response = requests.get(
                f"{self.base_url}/avatars",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error listing avatars: {e}")
            return {"error": str(e)}
    
    def generate_video(
        self, 
        text: str, 
        avatar_id: Optional[str] = None,
        voice_id: Optional[str] = None,
        title: Optional[str] = None,
        test_mode: bool = False
    ) -> Dict[str, Any]:
        """Generate a video with the avatar speaking the text"""
        if not self.api_key:
            return {"error": "HeyGen API key not configured"}
        
        try:
            # Prepare the request payload
            payload = {
                "video_inputs": [{
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id or self.default_avatar_id,
                        "avatar_style": "normal"
                    },
                    "voice": {
                        "type": "text",
                        "input_text": text,
                        "voice_id": voice_id or self.default_voice_id
                    } if voice_id or self.default_voice_id else {
                        "type": "text",
                        "input_text": text
                    }
                }],
                "test": test_mode,
                "caption": False
            }
            
            if title:
                payload["title"] = title
            
            # Make the API request
            response = requests.post(
                f"{self.base_url}/video/generate",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("error"):
                return {"error": result.get("message", "Unknown error")}
            
            return {
                "success": True,
                "video_id": result.get("data", {}).get("video_id"),
                "status": "processing"
            }
            
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            return {"error": str(e)}
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """Check the status of a video generation"""
        if not self.api_key:
            return {"error": "HeyGen API key not configured"}
        
        try:
            response = requests.get(
                f"{self.base_url}/video/{video_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            result = response.json()
            data = result.get("data", {})
            
            return {
                "status": data.get("status"),
                "video_url": data.get("video_url"),
                "thumbnail_url": data.get("thumbnail_url"),
                "duration": data.get("duration"),
                "error": data.get("error")
            }
            
        except Exception as e:
            logger.error(f"Error checking video status: {e}")
            return {"error": str(e)}
    
    def wait_for_video(self, video_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for video to complete processing"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_video_status(video_id)
            
            if status.get("error"):
                return status
            
            if status.get("status") == "completed":
                return status
            elif status.get("status") == "failed":
                return {"error": "Video generation failed"}
            
            # Wait before checking again
            time.sleep(5)
        
        return {"error": "Video generation timed out"}

# Singleton instance
heygen_handler = HeyGenHandler() 