import json
from pathlib import Path
from typing import Any, Union
from langchain_core.tools import tool
from orbit_cv.paths import CONTEXT_DIR


def _get_safe_context_path(filename: str) -> Path:
    """Ensures the requested filename stays strictly inside CONTEXT_DIR."""
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    target_path = (CONTEXT_DIR / filename).resolve()
    
    # Path traversal protection
    if not str(target_path).startswith(str(CONTEXT_DIR.resolve())):
        raise ValueError(f"Security error: Path '{filename}' attempts to escape the context directory.")
    
    return target_path


@tool
def save_context_file(filename: str, content: Union[str, dict, list]) -> str:
    """Saves arbitrary structured data, text, or JSON content to a specified file inside the /context directory.

    Args:
        filename: The target filename (e.g., 'market_analysis.json', 'candidate_profile.json', 'notes.md').
        content: The data payload to write. Can be a dict/list (saved as JSON), or a string.

    Returns:
        A confirmation message instructing the LLM to complete its execution step.
    """
    try:
        file_path = _get_safe_context_path(filename)

        if file_path.suffix.lower() == ".json" or isinstance(content, (dict, list)):
            # If string representation of JSON was passed, parse first
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    pass  # Treat as plain string if parsing fails
            
            if isinstance(content, (dict, list)):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(content, f, indent=2)
            else:
                file_path.write_text(str(content), encoding="utf-8")
        else:
            file_path.write_text(str(content), encoding="utf-8")

        return (
            f"SUCCESS: Saved content to {file_path.name}. "
            "Task complete. DO NOT invoke this tool again for the same step."
        )

    except Exception as e:
        return f"FAILED: Error saving context file '{filename}': {str(e)}"


@tool
def read_context_file(filename: str) -> Any:
    """Reads content from a specified file inside the /context directory.

    Args:
        filename: The target filename to read (e.g., 'market_analysis.json', 'candidate_profile.json').

    Returns:
        Parsed JSON object (dict/list) for JSON files, raw text for text files, or an error dictionary.
    """
    try:
        file_path = _get_safe_context_path(filename)

        if not file_path.exists():
            return {"error": f"File '{filename}' not found in context directory ({CONTEXT_DIR})."}

        if file_path.suffix.lower() == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return {"content": file_path.read_text(encoding="utf-8")}

    except Exception as e:
        return {"error": f"Failed to read context file '{filename}': {str(e)}"}
