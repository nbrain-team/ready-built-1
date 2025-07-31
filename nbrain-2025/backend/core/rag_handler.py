"""
RAG Handler - Core functionality for Retrieval-Augmented Generation
Integrates Generic RAG Platform capabilities into nBrain
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import openai
import os

from .rag_models import DataSource, DataEntry, RAGChatHistory, RAGConfiguration
from .database import User

logger = logging.getLogger(__name__)

class RAGHandler:
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.openai_client = openai
        self.openai_client.api_key = os.getenv("OPENAI_API_KEY")
        
    def get_data_sources(self) -> List[DataSource]:
        """Get all available data sources"""
        return self.db.query(DataSource).all()
    
    def get_relevant_context(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve relevant data based on query and context"""
        try:
            # Extract filters from context
            source_names = context.get('sources', [])
            date_range = context.get('date_range', {})
            filters = context.get('filters', {})
            
            # Build query
            query_builder = self.db.query(DataEntry)
            
            # Filter by sources
            if source_names:
                source_ids = self.db.query(DataSource.id).filter(
                    DataSource.name.in_(source_names)
                ).subquery()
                query_builder = query_builder.filter(DataEntry.source_id.in_(source_ids))
            
            # Apply date range
            if date_range:
                if 'start' in date_range:
                    query_builder = query_builder.filter(
                        DataEntry.timestamp >= datetime.fromisoformat(date_range['start'])
                    )
                if 'end' in date_range:
                    query_builder = query_builder.filter(
                        DataEntry.timestamp <= datetime.fromisoformat(date_range['end'])
                    )
            
            # Apply custom filters
            for key, value in filters.items():
                # Use JSON path queries for filtering data column
                query_builder = query_builder.filter(
                    func.json_extract(DataEntry.data, f'$.{key}') == value
                )
            
            # Limit results
            entries = query_builder.limit(100).all()
            
            # Format results
            results = []
            for entry in entries:
                result = {
                    'entity_id': entry.entity_id,
                    'timestamp': entry.timestamp.isoformat() if entry.timestamp else None,
                    'source': entry.source.display_name,
                    **entry.data
                }
                results.append(result)
            
            return {
                'results': results,
                'count': len(results),
                'query': query,
                'context': context
            }
            
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return {'error': str(e), 'results': []}
    
    def process_chat_query(self, query: str, session_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a chat query with RAG"""
        try:
            # Get relevant data context
            data_context = self.get_relevant_context(query, context)
            
            # Get configuration
            prompt_config = self._get_prompt_configuration()
            
            # Build system prompt
            system_prompt = prompt_config.get('system_prompt', self._get_default_system_prompt())
            
            # Add data context to prompt
            if data_context.get('results'):
                system_prompt += f"\n\nRelevant data context:\n{json.dumps(data_context['results'][:10], indent=2)}"
            
            # Call OpenAI
            response = self.openai_client.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            ai_response = response.choices[0].message.content
            
            # Save to chat history
            chat_entry = RAGChatHistory(
                user_id=self.user.id,
                session_id=session_id,
                query=query,
                response=ai_response,
                context_data=context,
                data_sources_used=[s.name for s in self.get_data_sources()]
            )
            self.db.add(chat_entry)
            self.db.commit()
            
            # Extract drill-down options from response
            drill_downs = self._extract_drill_downs(ai_response, data_context)
            
            return {
                'success': True,
                'response': ai_response,
                'session_id': session_id,
                'drill_downs': drill_downs,
                'data_context': data_context
            }
            
        except Exception as e:
            logger.error(f"Error processing chat query: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }
    
    def _get_prompt_configuration(self) -> Dict[str, Any]:
        """Get prompt configuration for the user"""
        # First try user-specific config
        config = self.db.query(RAGConfiguration).filter(
            and_(
                RAGConfiguration.user_id == self.user.id,
                RAGConfiguration.config_type == 'prompts',
                RAGConfiguration.is_active == True
            )
        ).first()
        
        if config:
            return config.config_data
        
        # Fall back to global config
        config = self.db.query(RAGConfiguration).filter(
            and_(
                RAGConfiguration.user_id == None,
                RAGConfiguration.config_type == 'prompts',
                RAGConfiguration.is_active == True
            )
        ).first()
        
        if config:
            return config.config_data
        
        # Return default
        return {
            'system_prompt': self._get_default_system_prompt()
        }
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt"""
        return """You are an AI assistant helping users analyze and understand their data. 
        You have access to various data sources and can help users explore metrics, identify trends, 
        and gain insights. Always be helpful, accurate, and provide actionable insights when possible.
        
        When presenting data:
        - Be clear and concise
        - Highlight key findings
        - Suggest relevant follow-up questions
        - Format numbers and dates appropriately
        """
    
    def _extract_drill_downs(self, response: str, data_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract potential drill-down options from the response"""
        drill_downs = []
        
        # Simple extraction based on data context
        if data_context.get('results'):
            # Add time-based drill-downs
            drill_downs.append({
                'label': 'View trend over time',
                'action': 'trend_analysis',
                'context': {'period': '30d'}
            })
            
            # Add comparison drill-downs
            drill_downs.append({
                'label': 'Compare with previous period',
                'action': 'period_comparison',
                'context': {'comparison': 'previous_period'}
            })
            
            # Add detail drill-downs based on available dimensions
            # This would be enhanced based on actual data structure
            
        return drill_downs
    
    def load_data_from_csv(self, file_path: str, source_name: str, config: Dict[str, Any]) -> bool:
        """Load data from CSV file into RAG system"""
        try:
            import pandas as pd
            
            # Read CSV
            df = pd.read_csv(file_path)
            
            # Get or create data source
            source = self.db.query(DataSource).filter_by(name=source_name).first()
            if not source:
                source = DataSource(
                    name=source_name,
                    display_name=config.get('display_name', source_name),
                    description=config.get('description', ''),
                    config=config
                )
                self.db.add(source)
                self.db.commit()
            
            # Process each row
            entity_column = config.get('entity_column', 'id')
            date_column = config.get('date_column')
            metrics_columns = config.get('metrics_columns', [])
            
            for _, row in df.iterrows():
                entry_data = {}
                
                # Extract metrics
                for col in metrics_columns:
                    if col in row:
                        entry_data[col] = row[col]
                
                # Extract dimensions
                for col in df.columns:
                    if col not in metrics_columns and col != entity_column and col != date_column:
                        entry_data[col] = row[col]
                
                # Create entry
                entry = DataEntry(
                    source_id=source.id,
                    entity_id=str(row.get(entity_column, '')),
                    timestamp=pd.to_datetime(row[date_column]) if date_column and date_column in row else None,
                    data=entry_data
                )
                self.db.add(entry)
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error loading CSV data: {str(e)}")
            self.db.rollback()
            return False 