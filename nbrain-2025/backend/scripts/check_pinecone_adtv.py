#!/usr/bin/env python3
"""
Script to check for ADTV content in Pinecone vector database.
This will help identify which documents contain ADTV references.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from core import pinecone_manager

# Load environment variables
load_dotenv()

print("Checking Pinecone for ADTV-related content...\n")

try:
    # Get all documents
    documents = pinecone_manager.list_documents()
    
    print(f"Total documents in Pinecone: {len(documents)}")
    print("\nDocuments that might contain ADTV content:")
    print("=" * 60)
    
    suspicious_docs = []
    
    for doc in documents:
        doc_name = doc['name'].lower()
        # Check for suspicious names
        if any(term in doc_name for term in ['adtv', 'american', 'dream', 'tv', 'blaze']):
            suspicious_docs.append(doc)
            print(f"\n📄 {doc['name']}")
            print(f"   Type: {doc['type']}")
            print(f"   Status: {doc['status']}")
    
    if not suspicious_docs:
        print("\n✓ No obviously ADTV-related document names found.")
        print("\nHowever, ADTV content might be inside documents with generic names.")
        print("Consider checking the content of all documents in your Knowledge Base.")
    
    print("\n" + "=" * 60)
    print("ALL DOCUMENTS IN PINECONE:")
    print("=" * 60)
    
    for i, doc in enumerate(documents, 1):
        print(f"{i}. {doc['name']} (Type: {doc['type']})")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    print("""
1. Review all documents listed above in your Knowledge Base UI
2. Delete any documents that contain ADTV content
3. If you're unsure, you can:
   - Download and check the content of each document
   - Or start fresh with a new Pinecone index
   
To delete a document via the API:
   pinecone_manager.delete_document("filename.txt")
   
To delete ALL documents (careful!):
   for doc in documents:
       pinecone_manager.delete_document(doc['name'])
""")
    
except Exception as e:
    print(f"Error checking Pinecone: {e}")
    print("\nMake sure your Pinecone environment variables are set correctly.") 