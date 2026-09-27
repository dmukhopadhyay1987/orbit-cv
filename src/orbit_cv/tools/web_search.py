from typing import List, Optional
from dotenv import find_dotenv, load_dotenv
from ddgs import DDGS
from langchain_core.tools import tool

# Automatically discover and load .env at module import
load_dotenv(find_dotenv(), override=True)


def _perform_ddg_search(query: str, max_results: int = 5) -> List[dict]:
    """Executes a search using the duckduckgo_search package directly."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            
        # Normalize result format for downstream subagents
        formatted_results = []
        for r in results:
            formatted_results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "content": r.get("body", "")
            })
        return formatted_results
    except Exception as e:
        raise RuntimeError(f"DuckDuckGo search error: {str(e)}")


@tool
def search_web_jobs(skills: List[str], location: Optional[str] = "") -> dict:
    """Searches web job boards (LinkedIn, Glassdoor, etc.) based on candidate skills."""
    skills_str = " ".join(skills[:5]) if skills else ""
    loc_str = location.strip() if location else ""
    query = f"job postings {skills_str} {loc_str}".strip()

    try:
        results = _perform_ddg_search(query, max_results=5)
        return {
            "query": query,
            "results": results
        }
    except Exception as e:
        return {"error": f"Job search failed: {str(e)}", "query": query}
