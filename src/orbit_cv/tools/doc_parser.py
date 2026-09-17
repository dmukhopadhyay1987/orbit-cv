# src/orbit_cv/tools/doc_parser.py
import urllib.request
from bs4 import BeautifulSoup
import docx
from langchain_core.tools import tool
import pypdf

from orbit_cv.paths import RESUMES_DIR, resolve_path

# Canonical CV Path resolved through path utility
CANONICAL_CV_PATH = resolve_path("candidate_cv.txt", default_route="resumes")


@tool
def read_candidate_cv(file_path: str = "candidate_cv.txt") -> dict:
    """Reads the pre-processed candidate CV plain text from /resumes/candidate_cv.txt.

    If an external or virtual file path is provided, it resolves the route safely and
    extracts text directly from PDF, DOCX, or plain text formats.
    """
    target_path = resolve_path(file_path, default_route="resumes")

    # Fast path: Read canonical file directly if requested or defaulted
    if CANONICAL_CV_PATH.exists() and (
        file_path == "candidate_cv.txt" or target_path == CANONICAL_CV_PATH
    ):
        try:
            raw_text = CANONICAL_CV_PATH.read_text(encoding="utf-8")
            return {
                "status": "success",
                "source": str(CANONICAL_CV_PATH),
                "cv_text": raw_text,
            }
        except Exception as e:
            return {
                "error": f"Failed to read candidate CV from {CANONICAL_CV_PATH}: {str(e)}"
            }

    # Fallback path: Inspect targeted file
    if not target_path.exists():
        return {"error": f"CV file not found at: {target_path}"}

    ext = target_path.suffix.lower().lstrip(".")
    raw_text = ""

    try:
        if ext == "pdf":
            reader = pypdf.PdfReader(str(target_path))
            raw_text = "\n".join(
                [page.extract_text() for page in reader.pages if page.extract_text()]
            )
        elif ext in ["docx", "doc"]:
            doc = docx.Document(str(target_path))
            raw_text = "\n".join(
                [p.text for p in doc.paragraphs if p.text.strip()]
            )
        else:
            raw_text = target_path.read_text(encoding="utf-8", errors="ignore")

        return {
            "status": "success",
            "source": str(target_path),
            "cv_text": raw_text,
        }
    except Exception as e:
        return {"error": f"Failed to parse document at {target_path}: {str(e)}"}


@tool
def extract_job_description_from_url(url: str) -> dict:
    """Fetches a webpage from a URL and extracts standard text content for a job description."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
            },
        )
        with urllib.request.urlopen(req) as response:
            html = response.read().decode("utf-8", errors="ignore")

        soup = BeautifulSoup(html, "html.parser")
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text(separator=" ")
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = "\n".join(chunk for chunk in chunks if chunk)

        return {
            "url": url,
            "status": "success",
            "content": clean_text[:4000],
        }
    except Exception as e:
        return {"error": f"Failed to fetch job description from URL: {str(e)}"}