# tools/doc_parser.py
import os
import pypdf
import docx
import urllib.request
from bs4 import BeautifulSoup
from langchain_core.tools import tool

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "resumes")
CANONICAL_CV_PATH = os.path.join(DATA_DIR, "candidate_cv.txt")

@tool
def read_candidate_cv(file_path: str = CANONICAL_CV_PATH) -> dict:
    """Reads the pre-processed candidate CV plain text from /resumes/candidate_cv.txt.
    
    If an external file path is provided and candidate_cv.txt does not exist, 
    it falls back to reading and extracting text from that file directly.
    """
    target_path = file_path if file_path else CANONICAL_CV_PATH
    
    if not os.path.isabs(target_path):
        target_path = os.path.join(PROJECT_ROOT, target_path)

    # Fast path: Read directly if candidate_cv.txt exists
    if os.path.exists(CANONICAL_CV_PATH) and target_path == CANONICAL_CV_PATH:
        try:
            with open(CANONICAL_CV_PATH, "r", encoding="utf-8") as f:
                raw_text = f.read()
            return {
                "status": "success",
                "source": CANONICAL_CV_PATH,
                "cv_text": raw_text
            }
        except Exception as e:
            return {"error": f"Failed to read candidate CV from {CANONICAL_CV_PATH}: {str(e)}"}

    # Fallback path: If reading a different or unparsed input file
    if not os.path.exists(target_path):
        return {"error": f"CV file not found at: {target_path}"}

    ext = target_path.lower().split(".")[-1]
    raw_text = ""

    try:
        if ext == "pdf":
            reader = pypdf.PdfReader(target_path)
            raw_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif ext in ["docx", "doc"]:
            doc = docx.Document(target_path)
            raw_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        else:
            with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()

        return {
            "status": "success",
            "source": target_path,
            "cv_text": raw_text
        }
    except Exception as e:
        return {"error": f"Failed to parse document at {target_path}: {str(e)}"}

@tool
def extract_job_description_from_url(url: str) -> dict:
    """Fetches a webpage from a URL and extracts standard text content for a job description."""
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        soup = BeautifulSoup(html, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return {
            "url": url,
            "status": "success",
            "content": clean_text[:4000]
        }
    except Exception as e:
        return {"error": f"Failed to fetch job description from URL: {str(e)}"}
