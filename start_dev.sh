#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Project paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 0. Load environment variables from .env file if it exists
ENV_FILE="${PROJECT_ROOT}/.env"
if [ -f "$ENV_FILE" ]; then
    # Export non-commented key=value pairs
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

# Resolve DATA_DIR in priority order: DATA_DIR_PATH -> ORBIT_DATA_DIR -> default fallback
if [ -n "${DATA_DIR_PATH}" ]; then
    DATA_DIR="${DATA_DIR_PATH}"
elif [ -n "${ORBIT_DATA_DIR}" ]; then
    DATA_DIR="${ORBIT_DATA_DIR}"
else
    DATA_DIR="${PROJECT_ROOT}/data"
fi

# Expand tilde (~) if present in the resolved path
DATA_DIR="${DATA_DIR/#\~/$HOME}"

echo "=========================================="
echo "🚀 Orbit CV - Clean Development Startup"
echo "=========================================="
echo "📂 Target Data Directory: ${DATA_DIR}"

# 1. Clean exports, context, and conversation history
echo "🧹 Cleaning previous state and history output directories..."

CLEAN_DIRS=(
    "${DATA_DIR}/resumes"
    "${DATA_DIR}/exports"
    "${DATA_DIR}/context"
    "${DATA_DIR}/conversation_history"
)

for dir in "${CLEAN_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        # Removes contents without deleting the directory itself
        rm -rf "${dir:?}"/*
        echo "  - Cleared: ${dir}"
    else
        mkdir -p "$dir"
        echo "  - Created: ${dir}"
    fi
done

# Ensure resumes directory exists
if [ ! -d "${DATA_DIR}/resumes" ]; then
    mkdir -p "${DATA_DIR}/resumes"
    echo "  - Created: ${DATA_DIR}/resumes"
fi

# 2. Clear LangGraph local state / SQLite checkpoint cache
LANGGRAPH_CACHE="${PROJECT_ROOT}/.langgraph_api"
if [ -d "$LANGGRAPH_CACHE" ]; then
    echo "🗑️ Clearing LangGraph checkpoint cache (.langgraph_api)..."
    rm -rf "$LANGGRAPH_CACHE"
fi

# 3. Launch LangGraph Server with clean checkpoint flag
echo "------------------------------------------"
echo "⚡ Starting LangGraph Dev Server..."
echo "------------------------------------------"

# Runs langgraph dev with fresh checkpoint state
uv run langgraph dev