import os
import requests
import argparse
import time
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from a .env file in the parent directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Get the backend URL from environment variables, with a default for local dev
API_BASE_URL = os.environ.get("VITE_API_BASE_URL", "http://localhost:10000")

def upload_file(file_path: str, doc_type: str = "transcription"):
    """
    Manages the three-step upload process for a single file.
    """
    file_name = os.path.basename(file_path)
    content_type = "text/plain"
    
    try:
        # --- Step 1: Get a pre-signed URL from our backend ---
        print(f"   [1/3] Requesting upload URL for {file_name}...")
        presigned_url_response = requests.post(
            f"{API_BASE_URL}/generate-upload-url",
            json={"file_name": file_name, "content_type": content_type}
        )
        presigned_url_response.raise_for_status()
        upload_data = presigned_url_response.json()
        upload_url = upload_data['upload_url']
        
        # --- Step 2: Upload the actual file to Google Cloud Storage ---
        print(f"   [2/3] Uploading file to Google Cloud Storage...")
        with open(file_path, 'rb') as f:
            upload_response = requests.put(
                upload_url,
                data=f,
                headers={'Content-Type': content_type}
            )
            upload_response.raise_for_status()
            
        # --- Step 3: Notify our backend that the upload is complete ---
        print(f"   [3/3] Notifying server to process the file...")
        notify_response = requests.post(
            f"{API_BASE_URL}/notify-upload",
            json={
                "file_name": file_name,
                "content_type": content_type,
                "doc_type": doc_type
            }
        )
        notify_response.raise_for_status()
        
        print(f"✅ Successfully initiated processing for {file_name}\n")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Error uploading {file_name}: {e}")
        if e.response:
            print(f"    Response: {e.response.text}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Bulk upload text files to the nBrain Knowledge Base.")
    parser.add_argument("folder_path", type=str, help="The full path to the folder containing the transcription files.")
    args = parser.parse_args()

    folder_path = os.path.expanduser(args.folder_path)

    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found at '{folder_path}'")
        return

    print(f"Starting bulk upload from folder: {folder_path}")
    print(f"Targeting API server: {API_BASE_URL}\n")
    
    files_to_upload = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
    total_files = len(files_to_upload)
    
    if total_files == 0:
        print("No .txt files found in the specified folder.")
        return

    successful_uploads = 0
    failed_uploads = 0

    for i, file_name in enumerate(files_to_upload):
        print(f"--- Processing file {i+1} of {total_files}: {file_name} ---")
        file_path = os.path.join(folder_path, file_name)
        
        if upload_file(file_path):
            successful_uploads += 1
        else:
            failed_uploads += 1
        
        # Add a small delay to avoid overwhelming the server
        time.sleep(1) 

    print("\n--- Bulk Upload Complete ---")
    print(f"Successfully processed: {successful_uploads}")
    print(f"Failed: {failed_uploads}")
    print("----------------------------")

if __name__ == "__main__":
    main() 