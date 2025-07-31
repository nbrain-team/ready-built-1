"""
Client Document Processor
Handles document processing and vectorization for client-specific documents
"""

import os
import logging
import tempfile
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .google_drive_handler import google_drive_handler
from . import pinecone_manager
from . import processor
from .client_portal_models import Client, ClientDocument
from googleapiclient.http import MediaIoBaseDownload
import io

logger = logging.getLogger(__name__)

class ClientDocumentProcessor:
    def __init__(self):
        self.drive_service = None
        if google_drive_handler.service:
            self.drive_service = google_drive_handler.service
    
    def process_client_drive_documents(self, client_id: str, client_name: str, db: Session):
        """Process all documents in a client's Google Drive folder"""
        if not self.drive_service:
            logger.error("Google Drive service not initialized")
            return
        
        try:
            # Get client's folder
            folder = google_drive_handler._find_client_folder(client_name)
            if not folder:
                logger.warning(f"No folder found for client {client_name}")
                return
            
            # List all files in the folder
            documents = google_drive_handler.list_client_documents(client_name)
            
            for doc in documents:
                try:
                    # Check if document already processed
                    existing = db.query(ClientDocument).filter(
                        ClientDocument.client_id == client_id,
                        ClientDocument.google_drive_id == doc['id']
                    ).first()
                    
                    if existing and existing.vectorized:
                        logger.info(f"Document {doc['name']} already vectorized")
                        continue
                    
                    # Process the document
                    self._process_single_document(client_id, client_name, doc, db)
                    
                except Exception as e:
                    logger.error(f"Error processing document {doc['name']}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error processing drive documents for client {client_name}: {e}")
    
    def _process_single_document(self, client_id: str, client_name: str, doc: Dict, db: Session):
        """Process a single document from Google Drive"""
        logger.info(f"Processing document: {doc['name']} for client {client_name}")
        
        # Skip Google-specific formats that can't be downloaded directly
        if doc['mimeType'].startswith('application/vnd.google-apps'):
            if doc['mimeType'] == 'application/vnd.google-apps.document':
                # Export Google Docs as PDF
                self._process_google_doc(client_id, client_name, doc, db)
            else:
                logger.info(f"Skipping Google app file: {doc['name']}")
            return
        
        # Download the file
        try:
            request = self.drive_service.files().get_media(fileId=doc['id'])
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{doc['name']}") as tmp_file:
                tmp_file.write(file_content.getvalue())
                temp_path = tmp_file.name
            
            # Process with the existing processor
            chunks = processor.process_file(temp_path, doc['name'])
            
            if chunks:
                # Add metadata for client-specific search
                metadata = {
                    "source": doc['name'],
                    "doc_type": "client_document",
                    "client_id": client_id,
                    "client_name": client_name,
                    "google_drive_id": doc['id'],
                    "mime_type": doc['mimeType']
                }
                
                # Use client-specific namespace in Pinecone
                namespace = f"client_{client_id}"
                pinecone_manager.upsert_chunks(chunks, metadata, namespace=namespace)
                
                # Record in database
                if not db.query(ClientDocument).filter(
                    ClientDocument.google_drive_id == doc['id']
                ).first():
                    client_doc = ClientDocument(
                        client_id=client_id,
                        name=doc['name'],
                        type="google_drive",
                        google_drive_id=doc['id'],
                        google_drive_link=doc.get('webViewLink'),
                        mime_type=doc['mimeType'],
                        file_size=doc.get('size', 0),
                        vectorized=True,
                        vectorized_at=datetime.utcnow()
                    )
                    db.add(client_doc)
                    db.commit()
                else:
                    # Update existing record
                    existing = db.query(ClientDocument).filter(
                        ClientDocument.google_drive_id == doc['id']
                    ).first()
                    existing.vectorized = True
                    existing.vectorized_at = datetime.utcnow()
                    db.commit()
                
                logger.info(f"Successfully vectorized {doc['name']} with {len(chunks)} chunks")
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        except Exception as e:
            logger.error(f"Error downloading/processing file {doc['name']}: {e}")
    
    def _process_google_doc(self, client_id: str, client_name: str, doc: Dict, db: Session):
        """Process Google Docs by exporting as PDF"""
        try:
            # Export as PDF
            request = self.drive_service.files().export_media(
                fileId=doc['id'],
                mimeType='application/pdf'
            )
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            # Save to temporary file
            pdf_name = f"{doc['name']}.pdf"
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{pdf_name}") as tmp_file:
                tmp_file.write(file_content.getvalue())
                temp_path = tmp_file.name
            
            # Process the PDF
            chunks = processor.process_file(temp_path, pdf_name)
            
            if chunks:
                # Add metadata
                metadata = {
                    "source": doc['name'],
                    "doc_type": "client_document",
                    "client_id": client_id,
                    "client_name": client_name,
                    "google_drive_id": doc['id'],
                    "mime_type": "application/pdf",
                    "original_type": doc['mimeType']
                }
                
                # Use client-specific namespace
                namespace = f"client_{client_id}"
                pinecone_manager.upsert_chunks(chunks, metadata, namespace=namespace)
                
                # Record in database
                if not db.query(ClientDocument).filter(
                    ClientDocument.google_drive_id == doc['id']
                ).first():
                    client_doc = ClientDocument(
                        client_id=client_id,
                        name=doc['name'],
                        type="google_drive",
                        google_drive_id=doc['id'],
                        google_drive_link=doc.get('webViewLink'),
                        mime_type=doc['mimeType'],
                        vectorized=True,
                        vectorized_at=datetime.utcnow()
                    )
                    db.add(client_doc)
                    db.commit()
                else:
                    # Update existing
                    existing = db.query(ClientDocument).filter(
                        ClientDocument.google_drive_id == doc['id']
                    ).first()
                    existing.vectorized = True
                    existing.vectorized_at = datetime.utcnow()
                    db.commit()
                
                logger.info(f"Successfully vectorized Google Doc {doc['name']} with {len(chunks)} chunks")
            
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        except Exception as e:
            logger.error(f"Error processing Google Doc {doc['name']}: {e}")
    
    def search_client_documents(self, client_id: str, query: str, top_k: int = 5):
        """Search within a specific client's documents"""
        namespace = f"client_{client_id}"
        return pinecone_manager.query_index(query, top_k=top_k, namespace=namespace)

# Singleton instance
client_document_processor = ClientDocumentProcessor() 