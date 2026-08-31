#!/usr/bin/env bash
set -e

echo "🚀 Setting up OrbitCV in your existing repository..."

# Ensure we are in the repo root (checking for README.md)
if [ ! -f "README.md" ]; then
    echo "⚠️ Warning: README.md not found. Make sure you are running this from the root of your cloned repository."
fi

# Create necessary project subdirectories
mkdir -p output tests examples .antigravity

# Initialize uv project if pyproject.toml doesn't exist yet
if [ ! -f "pyproject.toml" ]; then
    uv init --app --no-readme
    echo "Initialized uv app project."
else
    echo "pyproject.toml already exists, skipping uv init."
fi

# Create/Update standard .gitignore
cat << 'EOF' > .gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
dist/
build/
*.egg-info/

# Environment variables
.env

# IDEs & Editors
.vscode/
.idea/
.antigravity/

# Runtime Outputs
output/*.md
output/*.json
EOF

# Create .editorconfig
cat << 'EOF' > .editorconfig
root = true

[*]
charset = utf-8
indent_style = space
indent_size = 4
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.{json,yml,yaml,md}]
indent_size = 2
EOF

# Create .env.example template
cat << 'EOF' > .env.example
OPENAI_API_KEY=your_openai_api_key_here
LANGCHAIN_API_KEY=your_langchain_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=orbitcv-mvp
EOF

# Copy .env.example to .env if .env doesn't exist yet (remind you to fill keys)
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env file. Please remember to populate your API keys!"
fi

# Add dependencies via uv
echo "Adding dependencies via uv..."
uv add \
    langgraph \
    langchain \
    openai \
    tavily-python \
    fastmcp \
    deepagents \
    python-dotenv \
    pydantic

# Create Antigravity 1 launch configuration
cat << 'EOF' > .antigravity/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Run OrbitCV CLI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "args": ["--cv", "examples/sample_cv.pdf", "--jd", "examples/sample_jd.txt"],
      "console": "integratedTerminal",
      "justMyCode": false,
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  ]
}
EOF

echo "✅ OrbitCV setup complete!"
echo "Next step: Populate your API keys in the generated .env file."
