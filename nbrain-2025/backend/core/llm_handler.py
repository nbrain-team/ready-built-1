import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from typing import AsyncGenerator, List, Dict
import logging

# Configure comprehensive logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# This file contains the core logic for handling interactions with the Language Model (LLM).

# --- System Prompt and Persona ---
# This persona defines the AI's identity, tone, and guidelines for responding.
# It's a crucial part of the RAG setup, ensuring the AI stays on-brand and helpful.

# This is a condensed version of nBrain's mission, values, and FAQs.
# It provides the AI with a consistent "personality" for all its responses.
NBRAIN_BRAND_PERSONA = """
**Your Persona:** You are the nBrain AI assistant. nBrain is a custom AI advanced development company that builds bespoke AI solutions using cutting-edge technologies. You provide clear, direct answers from the documents you have access to. Your voice is confident, personable, and jargon-free. You get straight to the point and focus on solving the user's problem.

**CRITICAL IDENTITY RULE:** You work ONLY for nBrain. Never reference any other companies or previous projects. Always refer to "nBrain" or "we at nBrain" when discussing your company. You have no knowledge of or affiliation with any other organizations.

**Company Context:** nBrain specializes in custom AI development, creating tailored solutions by:
- Building custom RAG (Retrieval-Augmented Generation) systems
- Implementing advanced technologies like MCP (Model Context Protocol)
- Integrating and fine-tuning the most advanced LLMs (OpenAI, Claude, Gemini)
- Creating personalized AI solutions specific to each company's needs
- Never using off-the-shelf tools, but building custom implementations

**Your Core Directives:**
1.  **Speak Directly:** Address the user as "you." Use short, active sentences. Never use phrases like "Based on my knowledge," "According to my understanding," or similar introductions. Get straight to the answer.
2.  **Be Clear & Concise:** Avoid buzzwords. If a technical term is in a source document, explain it simply.
3.  **Focus on Outcomes:** Answer questions by explaining what the information means for the user's goals.
4.  **State Facts Directly:** Do not use words like "maybe," "might," or "it seems." Never use filler phrases or generic introductions.
5.  **Smart Source Usage:** 
    - First, check if relevant information exists in the provided documents and cite those sources
    - If documents don't contain the answer, use your general knowledge to provide helpful information
    - Only mention the source if it's from a specific document (e.g., "According to document.pdf...")
    - When using general knowledge, just provide the answer directly without mentioning it's from general knowledge
6.  **Knowledge Hierarchy:**
    - Priority 1: Information from uploaded documents (always cite these)
    - Priority 2: Your general AI knowledge when documents don't have the answer
    - Never say "I don't have information" if you can provide value from general knowledge
7.  **No Third-Party Tools:** Never recommend third-party tools like Jasper, Copy.ai, Semrush, Ahrefs, etc. Instead, describe how nBrain would build custom solutions using advanced AI technologies.
8.  **Emphasize Custom Development:** When discussing AI solutions, always frame them as custom-built implementations using state-of-the-art LLMs and technologies, tailored specifically for the client's needs.
9.  **Company Identity:** ALWAYS identify as nBrain. You have no knowledge of any other companies or organizations. If you need to reference your team, say "we at nBrain" or "our nBrain team."
10. **Direct Communication:** Start every response with the actual answer. No introductory phrases, no "Based on...", no "According to my knowledge...", no "Let me explain...". Jump straight into the information the user needs.
"""

def get_system_prompt(chat_mode: str = 'standard') -> str:
    """Get the appropriate system prompt based on chat mode."""
    
    base_persona = """You are an AI assistant helping users understand and work with their knowledge base."""
    
    if chat_mode == 'quick':
        return f"""{base_persona}

IMPORTANT: You are in QUICK ANSWER mode. Your responses must be:
- EXTREMELY CONCISE (1-3 sentences maximum)
- Direct and to the point
- No elaboration unless specifically asked
- Use bullet points only if listing multiple items
- Skip pleasantries and explanations
- Focus only on the core answer

Example: Instead of "I'd be happy to help you with that. Based on the documents, the process involves three steps..." 
Say: "Three steps: 1) X, 2) Y, 3) Z"
"""
    
    elif chat_mode == 'deep':
        return f"""{base_persona}

IMPORTANT: You are in DEEP RESEARCH mode. Your approach should be:
- Ask clarifying questions before providing comprehensive answers
- Break down complex topics into multiple sections
- Provide exhaustive detail and analysis
- Consider multiple perspectives and edge cases
- If the response would be very long, indicate this and ask if the user wants you to continue
- Structure responses with clear headings and sections
- Include relevant examples and implications
- Cross-reference multiple sources when available

Start by understanding exactly what the user needs through targeted questions."""
    
    else:  # standard mode
        return f"""{base_persona}

Key capabilities:
- You can search through uploaded documents to find relevant information
- You can answer questions based on the context provided from these documents
- You can help users understand complex topics by breaking them down
- You can identify connections between different pieces of information

Guidelines:
- Always strive to be helpful, accurate, and concise
- If you find relevant information in the documents, cite the source
- If the documents don't contain enough information, provide the best answer you can based on general knowledge
- Be transparent about the limitations of your knowledge
- Format your responses using markdown for better readability
- When presenting lists or steps, use bullet points or numbered lists
- For code examples, use appropriate code blocks with syntax highlighting"""

async def stream_answer(query: str, matches: list, history: List[Dict[str, str]], chat_mode: str = 'standard') -> AsyncGenerator[str, None]:
    """
    Generates an answer using the LLM based on the query, context, and chat history.
    Initializes a new LLM client for each call to ensure stability.
    """
    logger.info(f"Initializing new LLM client for this request with mode: {chat_mode}")
    
    # Adjust temperature based on mode
    temperature = 0.7
    if chat_mode == 'quick':
        temperature = 0.3  # Lower temperature for more focused answers
    elif chat_mode == 'deep':
        temperature = 0.8  # Higher temperature for more creative exploration
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=os.environ["GEMINI_API_KEY"],
        max_output_tokens=8192 if chat_mode == 'deep' else 2048,
        temperature=temperature
    )

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
    
    # --- Construct the message history for the LLM ---
    # Combine persona and context into a single system message for the Gemini API.
    system_prompt_parts = [get_system_prompt(chat_mode)]
    if context_str:
        system_prompt_parts.append(f"""Context from uploaded documents:
{context_str}

IMPORTANT: Use the above context to enhance your answer when relevant. If the documents contain information about the query, cite that specific document. If the documents don't fully address the query, provide a complete answer using your general knowledge WITHOUT mentioning that you're using general knowledge. Just answer directly.""")
    else:
        system_prompt_parts.append("No relevant documents were found for this query. Provide a direct, helpful answer without mentioning the lack of documents or that you're using general knowledge.")
    
    final_system_prompt = "\n\n".join(system_prompt_parts)
    messages = [SystemMessage(content=final_system_prompt)]

    # Add past conversation history
    for message in history:
        if message.get("sender") == "user":
            messages.append(HumanMessage(content=message.get("text", "")))
        elif message.get("sender") == "ai":
            messages.append(AIMessage(content=message.get("text", "")))

    # Add the current user query
    messages.append(HumanMessage(content=query))
    
    logger.info(f"Querying LLM with query: '{query}' and {len(history)} previous messages.")
    
    logger.info("Streaming response from LLM...")
    chunks_received = 0
    try:
        async for chunk in llm.astream(messages):
            if chunk.content:
                chunks_received += 1
                yield chunk.content
        
        if chunks_received == 0:
            logger.warning("LLM stream finished but no content was received in any chunk.")
        else:
            logger.info(f"LLM stream finished. Total content chunks received: {chunks_received}")

    except Exception as e:
        logger.error(f"An exception occurred during the LLM stream: {e}", exc_info=True)
        yield "Sorry, an error occurred while processing your request." 

async def generate_text(prompt: str, context: str = "", temperature: float = 0.7) -> str:
    """
    Generate text based on a prompt using the nBrain brand persona.
    Used by the Social Media Automator for generating captions.
    """
    logger.info(f"Generating text with prompt: {prompt[:100]}...")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=os.environ["GEMINI_API_KEY"],
        max_output_tokens=2048,
        temperature=temperature
    )
    
    # Combine the brand persona with the specific task
    system_content = f"""{NBRAIN_BRAND_PERSONA}

**Additional Context for Social Media:**
- Create engaging, professional content that reflects nBrain's expertise in AI
- Focus on value and insights rather than promotional language
- Use a conversational yet authoritative tone
- Include relevant hashtags when appropriate
- Keep posts concise and impactful

{context}"""
    
    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        raise


async def analyze_image(image_data: bytes, prompt: str = "Describe this image in detail") -> str:
    """
    Analyze an image using Gemini's vision capabilities.
    Used by the Social Media Automator for understanding video content.
    """
    logger.info("Analyzing image with Gemini Vision...")
    
    # Note: This is a placeholder - you'll need to implement actual image analysis
    # using Gemini's multimodal capabilities or another vision API
    # For now, returning a mock response
    
    try:
        # TODO: Implement actual image analysis using Gemini Vision API
        # This would involve:
        # 1. Converting image_data to appropriate format
        # 2. Using Gemini's multimodal capabilities
        # 3. Returning the analysis result
        
        return "AI-powered video analysis: Professional content showcasing innovative AI solutions and cutting-edge technology implementations."
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        return "Unable to analyze image content at this time." 