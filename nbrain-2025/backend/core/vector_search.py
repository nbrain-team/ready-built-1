"""
Vector search functionality for client documents
"""

import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from .database import SessionLocal
from .client_portal_models import ClientDocument

logger = logging.getLogger(__name__)

def search_client_documents(
    client_id: str,
    query: str,
    top_k: int = 5
) -> List[Dict]:
    """
    Search client documents for relevant content
    For now, this is a simple text search. 
    In production, this would use Pinecone or similar vector DB.
    """
    try:
        db = SessionLocal()
        
        # Get all documents for the client
        documents = db.query(ClientDocument).filter(
            ClientDocument.client_id == client_id
        ).all()
        
        results = []
        
        # Simple keyword matching for now
        keywords = query.lower().split()
        
        for doc in documents:
            # Check document name and content for keywords
            doc_text = f"{doc.name} {doc.file_path}".lower()
            
            # Count keyword matches
            match_count = sum(1 for keyword in keywords if keyword in doc_text)
            
            if match_count > 0:
                results.append({
                    'id': str(doc.id),
                    'name': doc.name,
                    'content': f"Document: {doc.name} - Type: {doc.type}",
                    'score': match_count,
                    'type': doc.type
                })
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        
        db.close()
        return results[:top_k]
        
    except Exception as e:
        logger.error(f"Error searching client documents: {e}")
        return [] 