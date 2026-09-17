# src/orbit_cv/utils/paths.py
from pathlib import Path
from typing import Union

# Base directory: ~/antigravity/orbit-cv
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
SRC_DIR = BASE_DIR / "src/orbit_cv"

# Physical directories
EXPORTS_DIR = DATA_DIR / "exports"
RESUMES_DIR = DATA_DIR / "resumes"
CONTEXT_DIR = DATA_DIR / "context"
HISTORY_DIR = DATA_DIR / "history"
CONVERSATION_HISTORY_DIR = DATA_DIR / "conversation_history"

# Route mapping lookup table
VIRTUAL_ROUTE_MAP = {
    "src": SRC_DIR,
    "exports": EXPORTS_DIR,
    "resumes": RESUMES_DIR,
    "context": CONTEXT_DIR,
    "history": HISTORY_DIR,
    "conversation_history": CONVERSATION_HISTORY_DIR,
}


def ensure_data_directories() -> None:
    """Ensures all physical runtime data directories exist."""
    for path in VIRTUAL_ROUTE_MAP.values():
        path.mkdir(parents=True, exist_ok=True)


def resolve_path(file_path: Union[str, Path], default_route: str = "exports") -> Path:
    """
    Safely resolves virtual route strings (e.g., '/exports/doc.md', 'candidate_cv.txt')
    to absolute physical disk paths under DATA_DIR.
    """
    ensure_data_directories()
    
    path_str = str(file_path).strip()
    clean_path = path_str.lstrip("/").lstrip("./")
    parts = Path(clean_path).parts
    
    if not parts:
        raise ValueError("Invalid empty path provided.")
    
    first_part = parts[0]
    
    if first_part in VIRTUAL_ROUTE_MAP:
        sub_path = Path(*parts[1:]) if len(parts) > 1 else Path(parts[0])
        resolved = VIRTUAL_ROUTE_MAP[first_part] / sub_path
    else:
        fallback_dir = VIRTUAL_ROUTE_MAP.get(default_route, EXPORTS_DIR)
        resolved = fallback_dir / Path(clean_path).name

    return resolved