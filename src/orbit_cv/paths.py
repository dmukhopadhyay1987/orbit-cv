import os
from pathlib import Path
from typing import Union
from dotenv import load_dotenv

# Base directory: ~/antigravity/orbit-cv
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file at PROJECT_DIR
load_dotenv(dotenv_path=PROJECT_DIR / ".env")

# Resolve DATA_DIR from environment variable or fall back to PROJECT_DIR / "data"
env_data_dir = os.getenv("DATA_DIR_PATH") or os.getenv("ORBIT_DATA_DIR")
if env_data_dir:
    DATA_DIR = Path(env_data_dir).expanduser().resolve()
else:
    DATA_DIR = PROJECT_DIR / "data"

SRC_DIR = PROJECT_DIR / "src/orbit_cv"

# Physical directories
EXPORTS_DIR = DATA_DIR / "exports"
RESUMES_DIR = DATA_DIR / "resumes"
CONTEXT_DIR = DATA_DIR / "context"
CONVERSATION_HISTORY_DIR = DATA_DIR / "conversation_history"

# Route mapping lookup table
VIRTUAL_ROUTE_MAP = {
    "src": SRC_DIR,
    "exports": EXPORTS_DIR,
    "resumes": RESUMES_DIR,
    "context": CONTEXT_DIR,
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