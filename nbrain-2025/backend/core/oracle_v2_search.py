"""
Oracle V2 Search Module - Vector search using Pinecone
"""

import os
import logging
from typing import List, Dict, Any, Optional
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class OracleSearch:
    """Vector search functionality for Oracle V2"""
    
    def __init__(self):
        self.pinecone_manager = None
        self.embeddings_model = None
        
        try:
            from .pinecone_manager import PineconeManager
            self.pinecone_manager = PineconeManager()
            logger.info("Pinecone initialized for Oracle search")
        except Exception as e:
            logger.warning(f"Pinecone not available: {e}")
        
        try:
            from sentence_transformers import SentenceTransformer
            self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embeddings model loaded")
        except Exception as e:
            logger.warning(f"Embeddings model not available: {e}")
    
    def index_email(self, user_id: str, email_data: Dict[str, Any]):
        """Index an email for vector search"""
        if not self.pinecone_manager or not self.embeddings_model:
            logger.debug("Vector indexing not available")
            return
        
        try:
            # Create content for embedding
            content = f"""
            Subject: {email_data.get('subject', '')}
            From: {email_data.get('from', '')}
            Date: {email_data.get('date', '')}
            Body: {email_data.get('body', '')[:2000]}
            """
            
            # Generate embedding
            embedding = self.embeddings_model.encode(content).tolist()
            
            # Create unique ID
            email_id = email_data.get('id', '')
            vector_id = f"oracle_{user_id}_{email_id}"
            
            # Metadata for filtering and display
            metadata = {
                'user_id': user_id,
                'email_id': email_id,
                'subject': email_data.get('subject', '')[:200],
                'from': email_data.get('from', '')[:100],
                'date': email_data.get('date', ''),
                'snippet': email_data.get('body', '')[:500],
                'source': 'oracle_email',
                'indexed_at': datetime.utcnow().isoformat()
            }
            
            # Upsert to Pinecone
            self.pinecone_manager.upsert_vectors([{
                'id': vector_id,
                'values': embedding,
                'metadata': metadata
            }])
            
            logger.debug(f"Indexed email {email_id} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to index email: {e}")
    
    def index_action_item(self, user_id: str, action_item: Dict[str, Any]):
        """Index an action item for search"""
        if not self.pinecone_manager or not self.embeddings_model:
            return
        
        try:
            # Create content for embedding
            content = f"""
            Action: {action_item.get('title', '')}
            Priority: {action_item.get('priority', '')}
            Category: {action_item.get('category', '')}
            Context: {action_item.get('context', '')}
            From: {action_item.get('from_email', '')}
            Subject: {action_item.get('subject', '')}
            """
            
            # Generate embedding
            embedding = self.embeddings_model.encode(content).tolist()
            
            # Create unique ID
            action_id = action_item.get('id', '')
            vector_id = f"oracle_action_{user_id}_{action_id}"
            
            # Metadata
            metadata = {
                'user_id': user_id,
                'action_id': action_id,
                'title': action_item.get('title', ''),
                'priority': action_item.get('priority', 'medium'),
                'category': action_item.get('category', 'other'),
                'status': action_item.get('status', 'pending'),
                'source': 'oracle_action',
                'indexed_at': datetime.utcnow().isoformat()
            }
            
            # Upsert to Pinecone
            self.pinecone_manager.upsert_vectors([{
                'id': vector_id,
                'values': embedding,
                'metadata': metadata
            }])
            
        except Exception as e:
            logger.error(f"Failed to index action item: {e}")
    
    def search(self, user_id: str, query: str, 
               source_filter: Optional[str] = None,
               limit: int = 20) -> List[Dict[str, Any]]:
        """Search across emails and action items"""
        
        if not self.pinecone_manager or not self.embeddings_model:
            logger.warning("Vector search not available")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings_model.encode(query).tolist()
            
            # Build filter
            filter_dict = {'user_id': user_id}
            if source_filter:
                filter_dict['source'] = source_filter
            
            # Search in Pinecone
            results = self.pinecone_manager.query_vectors(
                query_embedding,
                top_k=limit,
                filter=filter_dict,
                include_metadata=True
            )
            
            # Format results
            formatted_results = []
            for match in results.get('matches', []):
                metadata = match.get('metadata', {})
                score = match.get('score', 0)
                
                if metadata.get('source') == 'oracle_email':
                    formatted_results.append({
                        'type': 'email',
                        'id': metadata.get('email_id', ''),
                        'subject': metadata.get('subject', ''),
                        'from': metadata.get('from', ''),
                        'date': metadata.get('date', ''),
                        'snippet': metadata.get('snippet', ''),
                        'score': score
                    })
                elif metadata.get('source') == 'oracle_action':
                    formatted_results.append({
                        'type': 'action_item',
                        'id': metadata.get('action_id', ''),
                        'title': metadata.get('title', ''),
                        'priority': metadata.get('priority', ''),
                        'category': metadata.get('category', ''),
                        'status': metadata.get('status', ''),
                        'score': score
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def find_similar_emails(self, user_id: str, email_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find emails similar to a given email"""
        
        if not self.pinecone_manager:
            return []
        
        try:
            # Get the email's vector
            vector_id = f"oracle_{user_id}_{email_id}"
            
            # Fetch the vector
            fetch_result = self.pinecone_manager.index.fetch([vector_id])
            
            if vector_id not in fetch_result.get('vectors', {}):
                return []
            
            email_vector = fetch_result['vectors'][vector_id]['values']
            
            # Search for similar
            results = self.pinecone_manager.query_vectors(
                email_vector,
                top_k=limit + 1,  # +1 to exclude self
                filter={'user_id': user_id, 'source': 'oracle_email'},
                include_metadata=True
            )
            
            # Format and exclude self
            similar_emails = []
            for match in results.get('matches', []):
                metadata = match.get('metadata', {})
                if metadata.get('email_id') != email_id:
                    similar_emails.append({
                        'id': metadata.get('email_id', ''),
                        'subject': metadata.get('subject', ''),
                        'from': metadata.get('from', ''),
                        'date': metadata.get('date', ''),
                        'snippet': metadata.get('snippet', ''),
                        'similarity': match.get('score', 0)
                    })
            
            return similar_emails[:limit]
            
        except Exception as e:
            logger.error(f"Similar email search failed: {e}")
            return []
    
    def delete_user_vectors(self, user_id: str):
        """Delete all vectors for a user"""
        if not self.pinecone_manager:
            return
        
        try:
            # Delete by metadata filter
            self.pinecone_manager.index.delete(
                filter={'user_id': user_id}
            )
            logger.info(f"Deleted vectors for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to delete user vectors: {e}")

# Global search instance
oracle_search = OracleSearch() 