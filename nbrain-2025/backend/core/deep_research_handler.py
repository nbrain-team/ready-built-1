"""
Deep Research Handler for comprehensive, multi-turn conversations
"""

import os
import logging
from typing import List, Dict, AsyncGenerator, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
import json

logger = logging.getLogger(__name__)

class DeepResearchHandler:
    def __init__(self):
        self.conversation_state = {}
        
    def get_deep_research_prompt(self) -> str:
        """Get the system prompt for deep research mode."""
        return """You are an AI research assistant operating in DEEP RESEARCH mode.

Your approach should be:
1. **Clarifying Questions Phase**: Before diving into a comprehensive answer, ask 2-3 targeted questions to understand:
   - The specific context and use case
   - The desired depth and scope
   - Any constraints or preferences
   - The intended outcome or application

2. **Comprehensive Analysis Phase**: Once you have clarity, provide:
   - Detailed, structured analysis with clear sections
   - Multiple perspectives and considerations
   - Examples and case studies when relevant
   - Potential challenges and solutions
   - Best practices and recommendations

3. **Multi-Part Responses**: For very long responses:
   - Break content into logical sections
   - Indicate when a response will be extensive
   - Ask if the user wants to continue to the next section
   - Provide summaries at key points

4. **Interactive Exploration**: Throughout the conversation:
   - Offer to dive deeper into specific areas
   - Suggest related topics to explore
   - Maintain context across the entire conversation
   - Reference previous points when relevant

Remember: The goal is to provide PhD-level depth while maintaining clarity and usefulness."""

    async def should_ask_clarifying_questions(self, query: str, history: List[Dict]) -> bool:
        """Determine if we should ask clarifying questions."""
        # If this is the first message or a new topic, ask clarifying questions
        if len(history) == 0:
            return True
        
        # Check if the query is very broad or ambiguous
        broad_indicators = ['how', 'what', 'explain', 'tell me about', 'overview', 'general']
        query_lower = query.lower()
        
        if any(indicator in query_lower for indicator in broad_indicators):
            # Check if we've already asked questions about this topic
            recent_ai_messages = [msg for msg in history[-4:] if msg.get('sender') == 'ai']
            if recent_ai_messages:
                # If we've recently asked questions, don't ask again
                for msg in recent_ai_messages:
                    if '?' in msg.get('text', ''):
                        return False
            return True
        
        return False

    async def generate_clarifying_questions(self, query: str, context: str) -> str:
        """Generate appropriate clarifying questions based on the query."""
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=os.environ["GEMINI_API_KEY"],
            temperature=0.7,
            max_output_tokens=1024
        )
        
        prompt = f"""Based on this user query: "{query}"

And this context (if any): {context if context else "No specific context available"}

Generate 2-3 clarifying questions that would help provide a more comprehensive and useful response. 
The questions should:
- Be specific and targeted
- Help understand the user's exact needs
- Uncover important context or constraints
- Be formatted as a numbered list

End with: "Or if you'd prefer, I can provide a general comprehensive overview based on what you've shared so far."
"""
        
        messages = [
            SystemMessage(content="You are a research assistant that asks smart clarifying questions."),
            HumanMessage(content=prompt)
        ]
        
        response = await llm.ainvoke(messages)
        return response.content

    def format_section_header(self, section_num: int, total_sections: int, title: str) -> str:
        """Format a section header for multi-part responses."""
        return f"\n\n## Part {section_num} of {total_sections}: {title}\n\n"

    def should_break_response(self, content: str) -> bool:
        """Determine if a response should be broken into multiple parts."""
        # Break if content is longer than ~2000 words (rough estimate)
        word_count = len(content.split())
        return word_count > 2000

    async def stream_deep_research_response(
        self, 
        query: str, 
        matches: list, 
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Stream a deep research response with potential clarifying questions."""
        
        # Check if we should ask clarifying questions
        if await self.should_ask_clarifying_questions(query, history):
            # Generate context from matches
            context = ""
            if matches:
                context_parts = []
                for match in matches[:3]:  # Top 3 matches for context
                    text = match.get('metadata', {}).get('text', '')
                    if text:
                        context_parts.append(text[:200] + "...")
                context = "\n".join(context_parts)
            
            # Generate and yield clarifying questions
            questions = await self.generate_clarifying_questions(query, context)
            yield questions
        else:
            # Provide comprehensive response
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                google_api_key=os.environ["GEMINI_API_KEY"],
                temperature=0.8,
                max_output_tokens=8192,
                streaming=True
            )
            
            # Build comprehensive prompt
            system_prompt = self.get_deep_research_prompt()
            
            # Add context from matches
            context_str = ""
            if matches:
                chunks_by_source = {}
                for match in matches:
                    source = match.get('metadata', {}).get('source', 'Unknown Source')
                    text = match.get('metadata', {}).get('text', '')
                    if source not in chunks_by_source:
                        chunks_by_source[source] = []
                    chunks_by_source[source].append(text)

                formatted_chunks = []
                for source, texts in chunks_by_source.items():
                    source_header = f"--- Context from document: {source} ---"
                    source_content = "\n".join(f"- {text}" for text in texts)
                    formatted_chunks.append(f"{source_header}\n{source_content}")
                
                context_str = "\n\n".join(formatted_chunks)
                system_prompt += f"\n\nRelevant context:\n{context_str}"
            
            messages = [SystemMessage(content=system_prompt)]
            
            # Add conversation history
            for msg in history:
                if msg.get("sender") == "user":
                    messages.append(HumanMessage(content=msg.get("text", "")))
                elif msg.get("sender") == "ai":
                    messages.append(AIMessage(content=msg.get("text", "")))
            
            # Add current query
            messages.append(HumanMessage(content=query))
            
            # Stream the comprehensive response
            async for chunk in llm.astream(messages):
                if chunk.content:
                    yield chunk.content

# Singleton instance
deep_research_handler = DeepResearchHandler() 