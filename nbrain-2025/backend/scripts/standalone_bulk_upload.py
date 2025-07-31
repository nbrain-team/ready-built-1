"""
Standalone Bulk Upload Script for nBrain

This script is designed to be run locally to process a directory of video files
and upload them directly to a Pinecone index. It is self-contained and does
not depend on the main FastAPI application code, to avoid local environment issues.

----------------
--- HOW TO USE ---
----------------
1. INSTALL DEPENDENCIES:
   This script requires specific packages. Install them directly using pip:
   pip install pinecone-client langchain-google-genai openai-whisper python-dotenv

2. SET UP YOUR .env FILE:
   In the same directory as this script (backend/scripts), create a file named '.env'.
   The script will NOT work without it. The file should contain your credentials:

   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_INDEX_NAME=your_pinecone_index_name
   GEMINI_API_KEY=your_gemini_api_key

3. RUN THE SCRIPT:
   From your terminal, run the script and provide the path to your video folder.
   Make sure to wrap the path in quotes if it contains spaces.

   Example:
   python backend/scripts/standalone_bulk_upload.py "/path/to/your/video folder"
"""

import os
import sys
import argparse
import tempfile
from dotenv import load_dotenv
from pathlib import Path
import subprocess

# --- Dependency Check ---
try:
    import whisper
    from pinecone import Pinecone
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
except ImportError:
    print("One or more required libraries are not installed.")
    print("Please run the following command to install them:")
    print("pip install pinecone-client langchain-google-genai openai-whisper python-dotenv")
    sys.exit(1)

# --- FFMPEG Check ---
try:
    subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
except (subprocess.CalledProcessError, FileNotFoundError):
    print("FATAL: ffmpeg is not installed or not found in your system's PATH.")
    print("Please install ffmpeg. On macOS, you can use Homebrew: 'brew install ffmpeg'")
    sys.exit(1)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Splits a long text into smaller chunks with some overlap."""
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def process_and_transcribe_video(file_path: str) -> str:
    """Processes a single video file, returning the transcribed text."""
    print(f"  - Processing video: {file_path}")
    audio_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio_file:
            audio_path = temp_audio_file.name
        
        # Use ffmpeg to extract audio without loading video into memory
        command = ["ffmpeg", "-i", file_path, "-q:a", "0", "-map", "a", audio_path, "-y"]
        print("    - Extracting audio with ffmpeg...")
        subprocess.run(command, check=True, capture_output=True, text=True)

        print("    - Transcribing audio with Whisper...")
        model = whisper.load_model("tiny")
        result = model.transcribe(audio_path, fp16=False)
        print("    - Transcription complete.")
        return result.get('text', '')
    except subprocess.CalledProcessError as e:
        print(f"    - ffmpeg failed: {e.stderr}")
        return ""
    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)

def main(directory_path: str, doc_type: str):
    """Main function to handle the bulk upload process."""
    print("--- Starting Standalone Bulk Upload ---")

    # --- Load Environment Variables ---
    script_dir = Path(__file__).parent
    dotenv_path = script_dir / ".env"

    if not dotenv_path.exists():
        print(f"FATAL: Environment file not found at {dotenv_path}")
        print("Please create a '.env' file in the 'backend/scripts' directory with your credentials.")
        return

    load_dotenv(dotenv_path=dotenv_path)

    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not all([pinecone_api_key, pinecone_index_name, gemini_api_key]):
        print("FATAL: One or more required environment variables are missing from your .env file.")
        print("Required: PINECONE_API_KEY, PINECONE_INDEX_NAME, GEMINI_API_KEY")
        return

    # --- Initialize Services ---
    print("Initializing Pinecone and Google Gemini...")
    try:
        pc = Pinecone(api_key=pinecone_api_key)
        pinecone_index = pc.Index(pinecone_index_name)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=gemini_api_key)
        print("Services initialized successfully.")
    except Exception as e:
        print(f"FATAL: Failed to initialize services. Error: {e}")
        return

    # --- Find Video Files ---
    video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    video_files = [p for p in Path(directory_path).rglob('*') if p.suffix.lower() in video_extensions]

    if not video_files:
        print(f"No video files found in '{directory_path}'. Please check the path.")
        return

    print(f"Found {len(video_files)} video file(s) to process.\n")

    # --- Process Each File ---
    for i, file_path in enumerate(video_files):
        file_name = file_path.name
        print(f"--- Processing file {i + 1}/{len(video_files)}: {file_name} ---")

        try:
            full_text = process_and_transcribe_video(str(file_path))
            if not full_text:
                print("  - Warning: No text extracted. Skipping.\n")
                continue

            print("  - Splitting text into chunks...")
            text_chunks = chunk_text(full_text)
            
            print(f"  - Generating {len(text_chunks)} embeddings...")
            embedded_chunks = embeddings.embed_documents(text_chunks)

            vectors_to_upsert = []
            for j, (chunk_text, chunk_embedding) in enumerate(zip(text_chunks, embedded_chunks)):
                vector_id = f"{file_name}-chunk-{j}"
                metadata = {
                    "source": file_name,
                    "doc_type": doc_type,
                    "text": chunk_text
                }
                vectors_to_upsert.append((vector_id, chunk_embedding, metadata))
            
            print(f"  - Uploading {len(vectors_to_upsert)} vectors to Pinecone...")
            pinecone_index.upsert(vectors=vectors_to_upsert)
            print(f"  - Successfully uploaded {file_name}.\n")

        except Exception as e:
            print(f"  - ERROR: Failed to process {file_name}. Reason: {e}\n")
            continue

    print("--- Bulk Upload Process Complete ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Standalone bulk upload script for nBrain.",
        epilog="Example: python standalone_bulk_upload.py '/path/to/video/folder' --doc-type 'video_transcription'"
    )
    parser.add_argument("directory", type=str, help="The path to the directory containing your video files.")
    parser.add_argument("--doc_type", type=str, default="Bulk Video Upload", help="The 'Document Type' to assign to these videos.")
    
    args = parser.parse_args()
    main(args.directory, args.doc_type) 