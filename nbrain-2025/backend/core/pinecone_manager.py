import os
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import Pinecone as LangchainPinecone
from typing import List

# --- Environment Setup ---
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBEDDING_MODEL_NAME = "models/embedding-001"
EMBEDDING_DIMENSION = 768

def _get_pinecone_index():
    """Initializes and returns a Pinecone index client."""
    if not PINECONE_API_KEY or not PINECONE_INDEX_NAME or not PINECONE_ENV:
        raise ValueError("Pinecone API key, index name, or environment not set in environment.")
    
    pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
    
    # Note: We are now assuming the index exists and is configured correctly.
    # The volatile startup process should not be creating/validating indexes.
    return pc.Index(PINECONE_INDEX_NAME)

def _get_embedding_model():
    """Initializes and returns a Gemini embedding model client."""
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key not set in environment.")
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL_NAME,
        google_api_key=GEMINI_API_KEY
    )

def upsert_chunks(chunks: List[str], metadata: dict, namespace: str = None):
    """
    Embeds text chunks using Google Gemini and upserts them into Pinecone.
    Initializes clients on-the-fly for stability.
    
    Args:
        chunks: List of text chunks to embed and store
        metadata: Metadata to attach to all chunks
        namespace: Optional namespace for client-specific storage
    """
    embeddings = _get_embedding_model()
    
    docs_with_metadata = []
    for i, chunk in enumerate(chunks):
        doc_metadata = metadata.copy()
        doc_metadata["text"] = chunk
        docs_with_metadata.append(doc_metadata)

    # If namespace is provided, we need to use the index directly
    if namespace:
        index = _get_pinecone_index()
        # Generate embeddings
        chunk_embeddings = embeddings.embed_documents(chunks)
        
        # Prepare vectors for upsert
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, chunk_embeddings)):
            vector_metadata = metadata.copy()
            vector_metadata["text"] = chunk
            vectors.append({
                "id": f"{metadata.get('source', 'doc')}_{i}_{namespace}",
                "values": embedding,
                "metadata": vector_metadata
            })
        
        # Upsert to specific namespace
        index.upsert(vectors=vectors, namespace=namespace)
    else:
        # Use the default LangChain method for general documents
        LangchainPinecone.from_texts(
            texts=chunks,
            embedding=embeddings,
            metadatas=docs_with_metadata,
            index_name=os.getenv("PINECONE_INDEX_NAME")
        )

def list_documents():
    """
    Lists all unique documents in the Pinecone index.
    Initializes clients on-the-fly for stability.
    """
    try:
        index = _get_pinecone_index()
        results = index.query(
            vector=[0] * EMBEDDING_DIMENSION,
            top_k=1000,
            include_metadata=True
        )
        
        seen_files = set()
        unique_documents = []
        for match in results.get('matches', []):
            file_name = match.get('metadata', {}).get('source')
            if file_name and file_name not in seen_files:
                unique_documents.append({
                    "name": file_name,
                    "type": match.get('metadata', {}).get('doc_type', 'N/A'),
                    "status": "Ready"
                })
                seen_files.add(file_name)
        return unique_documents
    except Exception as e:
        print(f"Error listing documents from Pinecone: {e}")
        return []

def delete_document(file_name: str):
    """
    Deletes all vectors associated with a specific file_name from the index.
    Initializes clients on-the-fly for stability.
    """
    index = _get_pinecone_index()
    index.delete(filter={"source": file_name})

def query_index(query: str, top_k: int = 10, file_names: List[str] = None, namespace: str = None):
    """
    Queries the index with a question and returns the most relevant text chunks
    and their source documents.
    Initializes clients on-the-fly for stability.
    
    Args:
        query: The search query
        top_k: Number of results to return
        file_names: Optional list of file names to filter by
        namespace: Optional namespace for client-specific search
    """
    index = _get_pinecone_index()
    embeddings = _get_embedding_model()
    
    query_embedding = embeddings.embed_query(query)
    
    filter_metadata = None
    if file_names:
        filter_metadata = {"source": {"$in": file_names}}

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter=filter_metadata,
        namespace=namespace  # Add namespace parameter
    )
    
    return results.get('matches', []) 