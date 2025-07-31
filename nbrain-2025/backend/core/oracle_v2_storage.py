"""
Oracle V2 Storage Layer - Redis with JSON file fallback
"""

import json
import os
import pickle
from typing import Dict, List, Optional, Any
from datetime import datetime
import redis
import logging

logger = logging.getLogger(__name__)

class OracleStorage:
    """Storage layer for Oracle V2 with Redis primary and JSON fallback"""
    
    def __init__(self):
        self._redis_client = None
        self._redis_initialized = False
        self.storage_path = "oracle_data"
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
    
    @property
    def redis_client(self):
        """Lazy initialization of Redis client"""
        if not self._redis_initialized:
            self._redis_initialized = True
            try:
                redis_url = os.getenv("REDIS_URL")
                if redis_url:
                    self._redis_client = redis.from_url(redis_url, decode_responses=False)
                    self._redis_client.ping()
                    logger.info(f"Connected to Redis for Oracle storage at {redis_url}")
                else:
                    logger.warning("REDIS_URL not set, using file storage")
            except Exception as e:
                logger.warning(f"Redis not available, using file storage: {e}")
                self._redis_client = None
        return self._redis_client
    
    def _get_file_path(self, key: str) -> str:
        """Get file path for a given key"""
        return os.path.join(self.storage_path, f"{key}.json")
    
    def set_user_credentials(self, user_id: str, credentials: Dict[str, Any]):
        """Store user OAuth credentials"""
        key = f"oracle:creds:{user_id}"
        
        if self.redis_client:
            try:
                self.redis_client.set(key, pickle.dumps(credentials))
                self.redis_client.expire(key, 30 * 24 * 60 * 60)  # 30 days
                return
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        # Fallback to file
        file_path = self._get_file_path(f"creds_{user_id}")
        with open(file_path, 'w') as f:
            json.dump(credentials, f)
    
    def get_user_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user OAuth credentials"""
        key = f"oracle:creds:{user_id}"
        
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return pickle.loads(data)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        # Fallback to file
        file_path = self._get_file_path(f"creds_{user_id}")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        
        return None
    
    def set_action_items(self, user_id: str, action_items: List[Any]):
        """Store user's action items"""
        key = f"oracle:items:{user_id}"
        
        # Convert action items to serializable format
        items_data = []
        for item in action_items:
            item_dict = item.to_dict() if hasattr(item, 'to_dict') else item
            items_data.append(item_dict)
        
        if self.redis_client:
            try:
                self.redis_client.set(key, json.dumps(items_data))
                self.redis_client.expire(key, 7 * 24 * 60 * 60)  # 7 days
                return
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        # Fallback to file
        file_path = self._get_file_path(f"items_{user_id}")
        with open(file_path, 'w') as f:
            json.dump(items_data, f, default=str)
    
    def get_action_items(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's action items"""
        key = f"oracle:items:{user_id}"
        
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        # Fallback to file
        file_path = self._get_file_path(f"items_{user_id}")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        
        return []
    
    def store_action_item(self, user_id: str, action_item: Any) -> Dict[str, Any]:
        """Store a single action item"""
        import uuid
        
        # Get existing items
        existing_items = self.get_action_items(user_id)
        
        # Convert action item to dict
        item_dict = action_item.to_dict() if hasattr(action_item, 'to_dict') else action_item
        
        # Ensure the item has an ID
        if 'id' not in item_dict:
            item_dict['id'] = str(uuid.uuid4())
        
        # Add the new item
        existing_items.append(item_dict)
        
        # Store all items back
        self.set_action_items(user_id, existing_items)
        
        return item_dict
    
    def add_to_vector_index(self, user_id: str, email_id: str, content: str, metadata: Dict[str, Any]):
        """Add email content to vector index for search"""
        # This will be implemented with Pinecone integration
        key = f"oracle:vectors:{user_id}:{email_id}"
        
        vector_data = {
            "content": content,
            "metadata": metadata,
            "indexed_at": datetime.utcnow().isoformat()
        }
        
        if self.redis_client:
            try:
                self.redis_client.hset(f"oracle:vectors:{user_id}", email_id, json.dumps(vector_data))
                return
            except Exception as e:
                logger.error(f"Redis vector store error: {e}")
        
        # For now, store in file as placeholder
        file_path = self._get_file_path(f"vectors_{user_id}")
        vectors = {}
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                vectors = json.load(f)
        
        vectors[email_id] = vector_data
        with open(file_path, 'w') as f:
            json.dump(vectors, f, default=str)
    
    def search_vectors(self, user_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search vectors (placeholder for Pinecone search)"""
        # This will be replaced with actual vector search
        results = []
        
        if self.redis_client:
            try:
                vectors = self.redis_client.hgetall(f"oracle:vectors:{user_id}")
                for email_id, data in vectors.items():
                    vector_data = json.loads(data)
                    # Simple text search for now
                    if query.lower() in vector_data.get('content', '').lower():
                        results.append({
                            "email_id": email_id.decode() if isinstance(email_id, bytes) else email_id,
                            "content": vector_data.get('content', ''),
                            "metadata": vector_data.get('metadata', {})
                        })
            except Exception as e:
                logger.error(f"Redis search error: {e}")
        
        return results[:limit]
    
    def clear_user_data(self, user_id: str):
        """Clear all user data"""
        if self.redis_client:
            try:
                # Clear all user keys
                for key in self.redis_client.scan_iter(f"oracle:*:{user_id}*"):
                    self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
        
        # Clear files
        for filename in os.listdir(self.storage_path):
            if user_id in filename:
                os.remove(os.path.join(self.storage_path, filename))

# Global storage instance
oracle_storage = OracleStorage() 