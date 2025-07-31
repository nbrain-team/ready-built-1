from langchain_text_splitters import RecursiveCharacterTextSplitter
import docx
from pypdf import PdfReader
import requests
from bs4 import BeautifulSoup
import os

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

def _get_text_splitter():
    """Returns a configured text splitter."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len
    )

def _get_text_from_docx(file_path: str) -> str:
    """Extracts text from a .docx file."""
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def _get_text_from_pdf(file_path: str) -> str:
    """Extracts text from a .pdf file."""
    reader = PdfReader(file_path)
    return "\n".join([page.extract_text() for page in reader.pages])

def _get_text_from_txt(file_path: str) -> str:
    """Reads text from a .txt file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def process_file(file_path: str, original_filename: str) -> list[str]:
    """
    Determines the file type from the original filename and processes it.
    """
    text_splitter = _get_text_splitter()
    text = ""
    file_ext = os.path.splitext(original_filename)[1].lower()

    if file_ext == ".docx":
        text = _get_text_from_docx(file_path)
    elif file_ext == ".pdf":
        text = _get_text_from_pdf(file_path)
    elif file_ext == ".txt":
        text = _get_text_from_txt(file_path)
    else:
        print(f"Warning: Unsupported file type '{file_ext}' for file {original_filename}")
        return []

    return text_splitter.split_text(text)

def process_url(url: str) -> list[str]:
    """
    Fetches content from a URL, extracts text, and splits it into chunks.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
            
        text = soup.get_text(separator="\n", strip=True)
        
        text_splitter = _get_text_splitter()
        return text_splitter.split_text(text)
        
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return [] 