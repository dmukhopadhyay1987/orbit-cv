#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Project paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${PROJECT_ROOT}/data"

echo "=========================================="
echo "🚀 Orbit CV - Clean Development Startup"
echo "=========================================="

# 1. Clean exports, context, and conversation history
echo "🧹 Cleaning previous state and history output directories..."

CLEAN_DIRS=(
    "${DATA_DIR}/resumes"
    "${DATA_DIR}/exports"
    "${DATA_DIR}/context"
    "${DATA_DIR}/history"
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

# Ensure resumes directory exists (preserving candidate_cv.txt)
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