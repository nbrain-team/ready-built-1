"""
Oracle Endpoints Patch - Simplified versions to avoid database issues
"""

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
import logging

from .database import get_db, User
from .auth import get_current_active_user

logger = logging.getLogger(__name__)

def patch_oracle_endpoints(router):
    """Patch Oracle endpoints with simplified versions"""
    
    @router.get("/action-items", response_model=List[Dict[str, Any]])
    async def get_action_items_simple(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Simplified action items endpoint"""
        try:
            # Use raw SQL to avoid ORM issues
            result = db.execute(text("""
                SELECT id, title, source, source_type, due_date, 
                       priority, status, meta_data, created_at
                FROM oracle_action_items
                WHERE user_id = :user_id
                AND (status != 'deleted' OR status IS NULL)
                ORDER BY created_at DESC
                LIMIT 100
            """), {"user_id": current_user.id})
            
            items = []
            for row in result:
                items.append({
                    "id": row.id,
                    "title": row.title,
                    "source": row.source,
                    "sourceType": row.source_type,
                    "dueDate": row.due_date.isoformat() if row.due_date else None,
                    "priority": row.priority,
                    "status": row.status,
                    "createdAt": row.created_at.isoformat() if row.created_at else None,
                    "metaData": row.meta_data or {}
                })
            
            return items
        except Exception as e:
            logger.error(f"Error fetching action items: {e}")
            # Return empty list instead of error
            return []
    
    @router.get("/suggested-tasks", response_model=List[Dict[str, Any]])
    async def get_suggested_tasks_simple(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Simplified suggested tasks endpoint"""
        try:
            # Use raw SQL to avoid ORM issues
            result = db.execute(text("""
                SELECT id, title, source, priority, created_at
                FROM oracle_action_items
                WHERE user_id = :user_id
                AND status = 'pending'
                ORDER BY created_at DESC
                LIMIT 10
            """), {"user_id": current_user.id})
            
            tasks = []
            for row in result:
                tasks.append({
                    "id": row.id,
                    "title": row.title,
                    "source": row.source,
                    "priority": row.priority,
                    "createdAt": row.created_at.isoformat() if row.created_at else None
                })
            
            return tasks
        except Exception as e:
            logger.error(f"Error fetching suggested tasks: {e}")
            return []
    
    # Return the patched router
    return router 