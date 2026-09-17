# src/orbit_cv/agent.py
from dotenv import load_dotenv, find_dotenv
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagents import create_deep_agent
from langchain_quickjs import CodeInterpreterMiddleware

from orbit_cv.model import model
from orbit_cv.subagents_config import SUBAGENTS
from orbit_cv.middleware.rlm_context import RLMContextMiddleware
from orbit_cv.middleware.todo_tracker import TodoTrackerMiddleware
from orbit_cv.paths import (
    SRC_DIR,
    EXPORTS_DIR,
    RESUMES_DIR,
    CONTEXT_DIR,
    HISTORY_DIR,
    CONVERSATION_HISTORY_DIR,
    ensure_data_directories
)

# Load environment variables
load_dotenv(find_dotenv())

# Guarantee directory structure exists
ensure_data_directories()

# Read system prompt
AGENTS_MD_PATH = SRC_DIR / "AGENTS.md"
system_instructions = AGENTS_MD_PATH.read_text(encoding="utf-8")

model.profile = {**model.profile, "max_input_tokens": 700}

# Composite Backend mapped via path utility constants
backend = CompositeBackend(
    default=StateBackend(),
    routes={
        "/exports": FilesystemBackend(root_dir=str(EXPORTS_DIR)),
        "/resumes": FilesystemBackend(root_dir=str(RESUMES_DIR)),
        "/context": FilesystemBackend(root_dir=str(CONTEXT_DIR)),
        "/history": FilesystemBackend(root_dir=str(HISTORY_DIR)),
        "/conversation_history": FilesystemBackend(root_dir=str(CONVERSATION_HISTORY_DIR)),
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