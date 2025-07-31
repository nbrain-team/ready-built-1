"""
Custom middleware for the application
"""

import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from .database import SessionLocal

logger = logging.getLogger(__name__)

class DatabaseSessionMiddleware(BaseHTTPMiddleware):
    """Middleware to handle database sessions"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Create a database session for each request"""
        response = None
        db: Session = SessionLocal()
        
        try:
            # Store the session in request state
            request.state.db = db
            response = await call_next(request)
            
            # Only commit if we had a successful response
            if response and response.status_code < 400:
                try:
                    db.commit()
                except Exception as e:
                    logger.error(f"Error committing transaction: {e}")
                    db.rollback()
                    raise
            else:
                # Rollback on error responses
                db.rollback()
                
        except Exception as e:
            logger.error(f"Error in request: {e}")
            # Always rollback on exceptions
            try:
                db.rollback()
            except:
                pass
            raise
        finally:
            # Always close the session
            try:
                db.close()
            except:
                pass
                
        return response

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle errors and ensure clean database state"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors and ensure database cleanup"""
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log the error
            logger.error(f"Unhandled error in request: {e}", exc_info=True)
            
            # Try to clean up any database session
            if hasattr(request.state, 'db'):
                try:
                    request.state.db.rollback()
                    request.state.db.close()
                except:
                    pass
                    
            # Re-raise the exception
            raise 