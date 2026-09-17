# src/orbit_cv/agent.py
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagents import create_deep_agent
from langchain_quickjs import CodeInterpreterMiddleware

from orbit_cv.model import model
from orbit_cv.subagents_config import SUBAGENTS
from orbit_cv.middleware.rlm_context import RLMContextMiddleware
from orbit_cv.middleware.todo_tracker import TodoTrackerMiddleware

# Explicitly load environment variables
load_dotenv(find_dotenv())

# Define absolute base directory relative to this file
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Resolves to project root
DATA_DIR = BASE_DIR / "data"

# Ensure runtime directories exist
for folder in ["exports", "resumes", "context", "history", "conversation_history"]:
    (DATA_DIR / folder).mkdir(parents=True, exist_ok=True)

# Read system instructions deterministically
AGENTS_MD_PATH = BASE_DIR / "src" / "orbit_cv" / "AGENTS.md"
system_instructions = AGENTS_MD_PATH.read_text(encoding="utf-8")

model.profile = {**model.profile, "max_input_tokens": 700}

# Absolute-path Composite Backend
backend = CompositeBackend(
    default=StateBackend(),
    routes={
        "/exports": FilesystemBackend(root_dir=str(DATA_DIR / "exports")),
        "/resumes": FilesystemBackend(root_dir=str(DATA_DIR / "resumes")),
        "/context": FilesystemBackend(root_dir=str(DATA_DIR / "context")),
        "/history": FilesystemBackend(root_dir=str(DATA_DIR / "history")),
        "/conversation_history": FilesystemBackend(root_dir=str(DATA_DIR / "conversation_history")),
    }
)

# Initialize Deep Agent
agent = create_deep_agent(
    model=model,
    system_prompt=system_instructions,
    subagents=SUBAGENTS,
    middleware=[
        RLMContextMiddleware(),
        TodoTrackerMiddleware(),
        CodeInterpreterMiddleware(subagents=True)
    ],
    backend=backend
)