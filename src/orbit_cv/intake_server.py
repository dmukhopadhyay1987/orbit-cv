from fastmcp import FastMCP
from pathlib import Path
import os

# Initialize the FastMCP server instance
mcp = FastMCP(name="OrbitCV Intake Server")

def extract_text_from_file(file_path: str) -> str:
    """Helper utility to extract raw text from various file formats."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    suffix = path.suffix.lower()
    if suffix in [".txt", ".md"]:
        return path.read_text(encoding="utf-8")
    elif suffix == ".pdf":
        import pypdf
        reader = pypdf.PdfReader(path)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif suffix == ".docx":
        import docx
        doc = docx.Document(path)
        return "\n".join([para.text for para in doc.paragraphs if para.text])
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Supported formats: .txt, .md, .pdf, .docx")

@mcp.tool()
def parse_cv(file_path: str) -> dict:
    """Parse a CV file (.txt, .md, .pdf, .docx) into a structured dictionary containing raw text and metadata."""
    try:
        raw_text = extract_text_from_file(file_path)
        return {
            "source_file": file_path,
            "format": Path(file_path).suffix.lower(),
            "raw_text": raw_text,
            "status": "success"
        }
    except Exception as e:
        return {
            "source_file": file_path,
            "error": str(e),
            "status": "failed"
        }

@mcp.tool()
def parse_job_description(content_or_path: str) -> dict:
    """Parse a job description provided either as direct raw text or as a file path (.txt, .md, .pdf, .docx)."""
    try:
        if os.path.exists(content_or_path):
            raw_text = extract_text_from_file(content_or_path)
            source = content_or_path
        else:
            raw_text = content_or_path
            source = "direct_text_input"

        return {
            "source": source,
            "raw_text": raw_text,
            "status": "success"
        }
    except Exception as e:
        return {
            "source": content_or_path,
            "error": str(e),
            "status": "failed"
        }

if __name__ == "__main__":
    # Run the server via stdio transport for local agent integration
    mcp.run()
