import os
from typing import List, Optional
from dotenv import find_dotenv, load_dotenv
from langchain_core.tools import tool
from tavily import TavilyClient

# Automatically discover and load .env at module import
load_dotenv(find_dotenv(), override=True)

def _get_tavily_client() -> TavilyClient:
    """Retrieves and instantiates the Tavily client.
    
    Raises:
        ImportError: If tavily-python is not installed.
        ValueError: If TAVILY_API_KEY is missing from environment variables.
    """
    if TavilyClient is None:
        raise ImportError("The 'tavily-python' package is not installed. Run 'pip install tavily-python'.")

    api_key = os.getenv("TAVILY_API_KEY")
    
    # Secondary check in case load_dotenv was missed
    if not api_key:
        load_dotenv(find_dotenv(), override=True)
        api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise ValueError("TAVILY_API_KEY is not set in environment variables or .env file.")

    return TavilyClient(api_key=api_key)


@tool
def search_web_jobs(skills: List[str], location: Optional[str] = "") -> dict:
    """Searches web job boards (LinkedIn, Glassdoor, etc.) based on candidate skills."""
    skills_str = " ".join(skills[:5]) if skills else ""
    loc_str = location.strip() if location else ""
    query = f"job postings {skills_str} {loc_str}".strip()

    try:
        client = _get_tavily_client()
        res = client.search(query=query, search_depth="basic", max_results=5)
        return {
            "query": query,
            "results": res.get("results", [])
        }
    except Exception as e:
        return {"error": f"Job search failed: {str(e)}", "query": query}


@tool
def search_courses(skills_gap: List[str]) -> dict:
    """Searches Coursera, edX, or Udemy for courses matching a skills gap list."""
    gap_str = " ".join(skills_gap[:4]) if skills_gap else ""
    query = f"online courses certifications {gap_str}".strip()

    try:
        client = _get_tavily_client()
        res = client.search(query=query, search_depth="basic", max_results=5)
        return {
            "query": query,
            "results": res.get("results", [])
        }
    except Exception as e:
        return {"error": f"Course search failed: {str(e)}", "query": query}