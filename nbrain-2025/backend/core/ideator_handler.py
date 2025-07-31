import os
import json
from typing import List, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
import logging

logger = logging.getLogger(__name__)

# Agent templates for quick starts
AGENT_TEMPLATES = {
    "customer_service": {
        "name": "Customer Service Agent",
        "description": "Handles customer inquiries, complaints, and support tickets",
        "initial_questions": [
            "What type of products/services will this agent support?",
            "What communication channels should it handle (email, chat, phone)?",
            "What level of decision-making authority should it have?"
        ]
    },
    "data_analysis": {
        "name": "Data Analysis Agent", 
        "description": "Analyzes data, generates insights, and creates reports",
        "initial_questions": [
            "What data sources will this agent need to access?",
            "What types of analysis should it perform?",
            "Who is the target audience for the insights?"
        ]
    },
    "content_creation": {
        "name": "Content Creation Agent",
        "description": "Creates various types of content like articles, social media posts, and marketing materials",
        "initial_questions": [
            "What types of content will this agent create?",
            "What tone and style should it use?",
            "What approval process is needed?"
        ]
    },
    "process_automation": {
        "name": "Process Automation Agent",
        "description": "Automates repetitive tasks and workflows",
        "initial_questions": [
            "What specific processes need automation?",
            "What systems will it need to integrate with?",
            "What are the success metrics?"
        ]
    }
}

IDEATOR_SYSTEM_PROMPT = """You are an expert AI Agent Architect helping users design custom AI agents. Your role is to:

1. Guide users through a THOROUGH conversational process to understand their needs
2. Ask multiple rounds of clarifying questions to gather COMPREHENSIVE requirements
3. Suggest modern AI technologies and best practices
4. Generate detailed agent specifications with cost estimates

You should be friendly, professional, and VERY thorough. Think like a senior consultant conducting a discovery session. Always explore:

INITIAL DISCOVERY (Round 1):
- Core problem and pain points
- Target users and stakeholders
- Desired outcomes and success metrics
- Current workflow (if any)
- Platform requirements: Do they have an existing platform/app to integrate with, or do we need to build a complete frontend?

DEEP DIVE (Round 2):
- Specific features and capabilities needed
- Data sources and formats
- Integration requirements (APIs, databases, tools)
- Performance expectations
- Security and compliance needs

TECHNICAL REQUIREMENTS (Round 3):
- Expected volume/scale of operations
- Response time requirements
- Error handling preferences
- Monitoring and reporting needs
- User interface requirements (if frontend needed)

BUSINESS CONTEXT (Round 4):
- Team technical capabilities
- Change management considerations
- Future scalability needs

IMPORTANT GUIDELINES:
- When users say things like "You decide", "I'm not sure", "What do you recommend?", or "You choose what's best", take charge and make expert recommendations based on best practices
- Always explain your recommendations briefly so they understand the reasoning
- Make it clear that specifications can be edited later as requirements become clearer
- Balance thoroughness with user comfort - if they seem overwhelmed, reassure them that you can make expert choices

When you have COMPREHENSIVE information (after at least 3-4 rounds of questions), you'll create a detailed specification including:
- Summary
- Step-by-step workflow
- Technical stack recommendations
- Implementation timeline and cost estimates
- Client requirements

Remember to:
- Ask 2-3 focused questions at a time
- When users defer to your expertise, confidently recommend the best solution
- Provide examples to clarify when helpful
- Validate understanding before moving forward
- Be encouraging and reassuring, especially for non-technical users
- Let users know they can always edit the specification later"""

async def process_ideation_message(message: str, conversation_history: List[Dict]) -> Dict:
    """Process a message in the agent ideation conversation."""
    
    # Handle initial empty message
    if not message and len(conversation_history) == 0:
        return await start_ideation_session()
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=os.environ["GEMINI_API_KEY"],
        temperature=0.7,
        streaming=True  # Enable streaming
    )
    
    # Build message history
    messages = [SystemMessage(content=IDEATOR_SYSTEM_PROMPT)]
    
    # Add conversation history
    for msg in conversation_history:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg.get("content", "")))
        elif msg.get("role") == "assistant":
            messages.append(AIMessage(content=msg.get("content", "")))
    
    # Add current message
    messages.append(HumanMessage(content=message))
    
    # Check if we have enough information to generate a complete specification
    should_generate_spec = await check_if_ready_for_spec(messages)
    
    if should_generate_spec:
        # Generate the complete agent specification
        spec_response = await generate_agent_specification(messages)
        return {
            "response": spec_response["summary_message"],
            "complete": True,
            "specification": spec_response,
            "stream": False
        }
    else:
        # Return streaming response
        return {
            "stream": True,
            "complete": False,
            "generator": stream_response(llm, messages)
        }

async def stream_response(llm, messages):
    """Stream the response from the LLM."""
    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content

async def check_if_ready_for_spec(messages: List) -> bool:
    """Check if we have enough information to generate a specification."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=os.environ["GEMINI_API_KEY"],
        temperature=0.3
    )
    
    check_prompt = """Based on the conversation so far, do we have COMPREHENSIVE information to create a detailed agent specification? 
    
    We need ALL of the following:
    1. Clear understanding of the problem and desired outcomes
    2. Detailed functionality requirements and user workflows
    3. Technical requirements (integrations, data sources, performance)
    4. Business context (timeline, budget considerations, team capabilities)
    5. At least 3-4 rounds of Q&A have occurred
    6. User has provided specific, detailed answers (not just high-level)
    
    Only respond 'YES' if we have thorough, detailed information in ALL areas.
    Respond with only 'YES' or 'NO'."""
    
    messages_copy = messages + [HumanMessage(content=check_prompt)]
    response = await llm.ainvoke(messages_copy)
    
    return response.content.strip().upper() == "YES"

async def generate_agent_specification(messages: List) -> Dict:
    """Generate a complete agent specification based on the conversation."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=os.environ["GEMINI_API_KEY"],
        temperature=0.5
    )
    
    spec_prompt = """Based on our conversation, generate a comprehensive agent specification in JSON format with these sections:

    {
        "title": "Descriptive agent name",
        "agent_type": "one of: customer_service, data_analysis, content_creation, process_automation, or other",
        "summary": "2-3 sentence overview of the agent's purpose and value",
        "steps": [
            "Clear, action-oriented description with sub-tasks and technical details for the first phase",
            "Next step in the workflow with specific implementation details",
            ...
        ],
        "agent_stack": {
            "llm_model": {
                "primary_model": {
                    "recommendation": "Best primary model based on use case (e.g., Claude 3 Opus for complex reasoning, GPT-4 for general tasks, Gemini 1.5 Pro for long context, Mistral for efficiency)",
                    "provider": "Provider name (Anthropic, OpenAI, Google, etc.)",
                    "strengths": ["List of specific strengths for this use case"],
                    "reasoning": "Detailed explanation of why this model excels for these requirements"
                },
                "specialized_models": {
                    "vision": {
                        "model": "Best vision model if images are involved (e.g., GPT-4V, Claude 3 Vision, Gemini Pro Vision)",
                        "use_cases": "When to use this model"
                    },
                    "code_generation": {
                        "model": "Best for code tasks (e.g., Claude 3 for complex code, GPT-4 for general coding, Codex/Copilot for IDE integration)",
                        "use_cases": "When to use this model"
                    },
                    "data_analysis": {
                        "model": "Best for data/math (e.g., Code Interpreter GPT-4, Claude 3 with tools, Gemini with Code Execution)",
                        "use_cases": "When to use this model"
                    },
                    "fast_inference": {
                        "model": "Fast, cost-effective model (e.g., Claude 3 Haiku, GPT-3.5-turbo, Mistral 7B)",
                        "use_cases": "For high-volume, simple tasks"
                    }
                },
                "router_configuration": {
                    "enabled": "true/false - whether to use LLM routing",
                    "routing_strategy": "How to decide which model to use (e.g., task-based, complexity-based, cost-optimized)",
                    "router_logic": "Specific routing rules or ML-based router recommendation",
                    "fallback_model": "Model to use if router fails"
                },
                "cost_optimization": {
                    "strategy": "How to balance performance vs cost",
                    "estimated_monthly_cost": "Rough estimate based on expected usage"
                }
            },
            "vector_database": {
                "recommendation": "ALWAYS include (e.g., Pinecone for production, Weaviate for hybrid search, Qdrant for on-premise, ChromaDB for development)",
                "purpose": "Store embeddings for long-term memory, training data, and retrieval",
                "reasoning": "Why this specific vector DB is recommended",
                "configuration": {
                    "index_type": "Type of index (e.g., HNSW, IVF)",
                    "dimensions": "Based on embedding model",
                    "metric": "Distance metric (cosine, euclidean, etc.)"
                }
            },
            "retrieval_system": {
                "recommendation": "Advanced retrieval method (e.g., RAG with reranking, Hybrid RAG+BM25, GraphRAG for connected data)",
                "components": {
                    "retriever": "Primary retrieval method",
                    "reranker": "Model for reranking (e.g., Cohere Rerank, BGE-reranker)",
                    "hybrid_search": "Combining vector + keyword search",
                    "query_expansion": "Methods to improve recall"
                },
                "reasoning": "How this enhances the agent's capabilities"
            },
            "embedding_model": {
                "recommendation": "Best embedding model for this use case (e.g., OpenAI ada-002 for general, BGE-large for multilingual, Instructor for task-specific)",
                "dimensions": "Embedding dimensions and why",
                "special_requirements": "Any specific needs (multilingual, domain-specific, etc.)"
            },
            "orchestration": {
                "framework": "Tool for managing workflows (e.g., LangChain for flexibility, AutoGen for multi-agent, CrewAI for team simulation, Custom for specific needs)",
                "reasoning": "Why this framework fits the requirements",
                "agent_architecture": "Single agent, multi-agent, or hierarchical"
            },
            "integrations": [
                {
                    "service": "API or service name",
                    "purpose": "What it's used for",
                    "security": "How credentials are handled"
                }
            ],
            "frontend": {
                "framework": "UI framework if needed",
                "features": "Key UI features and interactions"
            },
            "monitoring": {
                "tools": "Observability and analytics tools (e.g., LangSmith, Helicone, Custom dashboards)",
                "metrics": "Key metrics to track",
                "llm_monitoring": "Specific LLM usage and performance tracking"
            },
            "infrastructure": {
                "hosting": "Recommended hosting solution",
                "scalability": "How the system scales",
                "gpu_requirements": "If needed for local model deployment"
            }
        },
        "security_considerations": {
            "data_handling": {
                "encryption_at_rest": "How data is encrypted when stored",
                "encryption_in_transit": "How data is encrypted during transmission",
                "data_retention": "Policies for data retention and deletion"
            },
            "access_control": {
                "authentication": "Method for user authentication",
                "authorization": "Role-based access control details",
                "api_security": "API key management and rotation"
            },
            "compliance": {
                "standards": ["Relevant compliance standards (GDPR, HIPAA, SOC2, etc.)"],
                "audit_logging": "What actions are logged for audit"
            },
            "advanced_security_options": {
                "private_deployment": "Options for on-premise or VPC deployment",
                "zero_trust": "Zero-trust architecture considerations",
                "secrets_management": "Using services like HashiCorp Vault or AWS Secrets Manager",
                "data_isolation": "Multi-tenant data isolation strategies"
            }
        },
        "client_requirements": [
            "Specific access or resources needed from the client with detailed explanation",
            "API keys or credentials required and how they'll be secured",
            "Data access requirements and compliance needs",
            "Infrastructure requirements if any",
            ...
        ],
        "future_enhancements": [
            {
                "enhancement": "Advanced feature or capability",
                "description": "Detailed description of what this would add",
                "impact": "Business impact and user benefits",
                "implementation_effort": "Estimated effort to implement"
            },
            ... (at least 4-5 innovative enhancement ideas)
        ],
        "implementation_estimate": {
            "traditional_approach": {
                "hours": "Estimated hours for traditional development",
                "breakdown": {
                    "planning": "X hours - detailed planning activities",
                    "development": "X hours - core development work",
                    "testing": "X hours - comprehensive testing",
                    "deployment": "X hours - deployment and configuration",
                    "documentation": "X hours - user and technical documentation"
                },
                "total_cost": "Estimated cost at $150/hour"
            },
            "ai_powered_approach": {
                "hours": "10% of traditional hours",
                "methodology": "Using AI-driven development with nBrain's advanced tooling",
                "ai_tools_used": ["List of AI tools that accelerate development"],
                "cost_savings": "90% reduction from traditional approach",
                "total_cost": "10% of traditional cost",
                "additional_benefits": ["Faster iteration", "Built-in best practices", "Continuous improvement"]
            }
        },
        "summary_message": "A friendly message summarizing what we've created and the value proposition"
    }

    IMPORTANT GUIDELINES FOR LLM SELECTION:
    - NEVER default to just GPT-4 for everything
    - Consider the specific use case: Claude 3 excels at complex reasoning and code, Gemini 1.5 Pro handles long context best, GPT-4 is versatile
    - For vision tasks: Always recommend specialized vision models
    - For high-volume tasks: Always include a fast inference option
    - Always suggest LLM routing when multiple capabilities are needed
    - Consider cost implications and provide optimization strategies
    - Include open-source alternatives when appropriate (Llama 3, Mistral, etc.)
    
    OTHER IMPORTANT NOTES: 
    - ALWAYS include vector databases for long-term memory and training, even for simple use cases
    - ALWAYS include advanced retrieval (RAG/CAG/MCP) to ensure scalability
    - Provide detailed explanations for each technical choice
    - Include comprehensive security considerations
    - Generate innovative future enhancement ideas that extend the core functionality
    - Be specific and detailed in all sections"""
    
    messages_copy = messages + [HumanMessage(content=spec_prompt)]
    response = await llm.ainvoke(messages_copy)
    
    try:
        # Extract JSON from the response
        json_str = response.content
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
        
        spec = json.loads(json_str)
        return spec
    except Exception as e:
        logger.error(f"Error parsing specification JSON: {e}")
        # Fallback response
        return {
            "title": "Custom AI Agent",
            "agent_type": "other",
            "summary": "An AI agent designed based on your requirements.",
            "steps": ["Error generating detailed steps. Please try again."],
            "agent_stack": {"error": "Could not generate stack details"},
            "client_requirements": ["Error generating requirements"],
            "security_considerations": {"error": "Could not generate security details"},
            "future_enhancements": [],
            "summary_message": "I encountered an error generating the specification. Please try again."
        }

async def start_ideation_session() -> Dict:
    """Start a new ideation session with a welcome message."""
    welcome_message = """Hey there! 👋 I'm here to help you ideate and create a scope for a new AI agent. 

I'll guide you through the process, and by the end, we'll have a comprehensive specification including the technical stack, workflow, and requirements.

To get started, please tell me about the agent you have in mind. You can share:
- What problem it should solve
- Who will use it
- Any specific functionality you need
- Whether you have an existing platform/app to integrate with

Don't worry about being too technical - just explain it in your own words, and I'll ask clarifying questions as needed. 

If you're unsure about any technical details, just let me know and I'll recommend the best approach based on industry best practices. You can always edit the specification later as your requirements become clearer."""
    
    # Create a generator that yields the welcome message in chunks
    async def welcome_generator():
        # Simulate streaming by breaking the message into words
        words = welcome_message.split(' ')
        for i, word in enumerate(words):
            if i > 0:
                yield ' '
            yield word
    
    return {
        "stream": True,
        "complete": False,
        "generator": welcome_generator()
    }

async def process_edit_message(message: str, current_spec: Dict, conversation_history: List[Dict]) -> Dict:
    """Process an edit message for an existing agent specification."""
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=os.environ["GEMINI_API_KEY"],
        temperature=0.7,
        streaming=True  # Enable streaming
    )
    
    edit_system_prompt = """You are an expert AI Agent Architect helping users edit their existing agent specifications. 

Current specification:
""" + json.dumps(current_spec, indent=2) + """

Your role is to:
1. Understand what changes the user wants to make
2. Apply those changes to the specification
3. Maintain consistency across all sections
4. Ask clarifying questions if needed
5. Generate an updated specification when changes are clear

Be friendly, precise, and thorough. Always think about how changes to one section might affect others."""
    
    # Build message history
    messages = [SystemMessage(content=edit_system_prompt)]
    
    # Add conversation history
    for msg in conversation_history:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg.get("content", "")))
        elif msg.get("role") == "assistant":
            messages.append(AIMessage(content=msg.get("content", "")))
    
    # Add current message
    messages.append(HumanMessage(content=message))
    
    # Check if we should generate the updated spec
    should_update = await check_if_ready_to_update(messages, message)
    
    if should_update:
        # Generate the updated specification
        updated_spec = await generate_updated_specification(messages, current_spec)
        return {
            "response": "I've updated the specification based on your requested changes. The agent specification has been saved with your modifications.",
            "complete": True,
            "updated_spec": updated_spec,
            "stream": False
        }
    else:
        # Return streaming response
        return {
            "stream": True,
            "complete": False,
            "generator": stream_response(llm, messages)
        }

async def check_if_ready_to_update(messages: List, user_message: str) -> bool:
    """Check if we have clear instructions to update the specification."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=os.environ["GEMINI_API_KEY"],
        temperature=0.3
    )
    
    check_prompt = f"""Based on the user's latest message: "{user_message}"
    
    Do we have clear, specific instructions about what to change in the specification?
    Consider if the user has:
    1. Clearly stated what they want to change
    2. Provided enough detail to make the change
    3. Answered any clarifying questions
    
    Respond with only 'YES' or 'NO'."""
    
    messages_copy = messages + [HumanMessage(content=check_prompt)]
    response = await llm.ainvoke(messages_copy)
    
    return response.content.strip().upper() == "YES"

async def generate_updated_specification(messages: List, current_spec: Dict) -> Dict:
    """Generate an updated agent specification based on the edit conversation."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=os.environ["GEMINI_API_KEY"],
        temperature=0.5
    )
    
    update_prompt = """Based on our conversation, generate the UPDATED agent specification in JSON format.
    
    Start with the current specification and apply ONLY the changes discussed. 
    Maintain all other aspects of the specification that weren't mentioned.
    
    Return the complete updated specification in the same JSON format as the original."""
    
    messages_copy = messages + [HumanMessage(content=update_prompt)]
    response = await llm.ainvoke(messages_copy)
    
    try:
        # Extract JSON from the response
        json_str = response.content
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
        
        updated_spec = json.loads(json_str)
        
        # Preserve fields that shouldn't change
        updated_spec["id"] = current_spec.get("id")
        updated_spec["created_at"] = current_spec.get("created_at")
        updated_spec["status"] = current_spec.get("status", "draft")
        
        return updated_spec
    except Exception as e:
        logger.error(f"Error parsing updated specification JSON: {e}")
        # Return the original spec if parsing fails
        return current_spec