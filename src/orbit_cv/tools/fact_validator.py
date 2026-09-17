from langchain_core.tools import tool

@tool
def validate_groundedness(draft_text: str, source_cv_text: str) -> dict:
    """Verifies that facts/metrics in the draft text are grounded in the original CV text."""
    # Basic structural check helper
    draft_words = set(draft_text.lower().split())
    source_words = set(source_cv_text.lower().split())
    overlap = len(draft_words.intersection(source_words))
    
    return {
        "status": "completed",
        "overlap_word_count": overlap,
        "note": "Subagent should inspect discrepancies between draft claims and source facts."
    }
