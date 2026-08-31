import os
from typing import List, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5-nano")

def get_llm(temperature: float = 0):
    return ChatOpenAI(model=MODEL_NAME, temperature=temperature)

# --- Schemas for Tailoring and Upskilling ---

class TailoredOutput(BaseModel):
    tailored_cv_markdown: str = Field(
        description="The fully rewritten CV in clean Markdown format with targeted personal branding and highlighted skills."
    )
    cover_letter_markdown: str = Field(
        description="A highly targeted, persuasive motivation/cover letter customized for the job description."
    )

class CourseRecommendation(BaseModel):
    skill: str = Field(description="The specific skill gap being addressed.")
    course_title: str = Field(description="Title of the course, certification, or learning path.")
    provider: str = Field(description="Platform or institution offering the course (e.g., Coursera, Udemy, AWS, etc.).")
    url: str = Field(description="Direct URL link found via search results.")
    rationale: str = Field(description="Explanation of how this recommendation bridges the gap.")

class UpskillingReport(BaseModel):
    recommendations: List[CourseRecommendation] = Field(
        description="List of targeted courses and certifications for the identified skill gaps."
    )

class FactCheckResult(BaseModel):
    hallucinated_claims: List[str] = Field(
        description="List of skills, tools, certifications, or language claims found in the generated output that are NOT supported by the master CV."
    )
    cleaned_tailored_cv: str = Field(
        description="The tailored CV text with all unverified claims, commentary, notes, and disclaimers completely removed."
    )
    cleaned_cover_letter: str = Field(
        description="The cover letter text with all unverified claims and meta-commentary removed."
    )
    strategy_notes: str = Field(
        description="Summary of adjustments made during tailoring (e.g. key keywords targeted, experience restructured) to display in the UI sidebar."
    )

# --- Agent Implementations ---

class CVTailoringAgent:
    """Agent responsible for rewriting the CV and crafting a targeted cover letter."""
    def __init__(self):
        self.llm = get_llm(0.2)

    def run(self, raw_cv: str, jd_text: str, gap_analysis: Any) -> TailoredOutput:
        prompt = f"""
        You are an elite executive resume writer and career branding specialist.
        Using the original CV, target Job Description, and Gap Analysis provided below,
        rewrite the CV bullet points to strategically highlight matching skills, align with key terminology,
        and maximize personal branding. Also, draft a compelling, professional cover letter.
        
        --- GAP ANALYSIS ---
        Missing Keywords: {gap_analysis.missing_keywords}
        Tonal Mismatches: {gap_analysis.tonal_mismatches}
        Skill Gaps: {gap_analysis.skill_gaps}
        
        --- ORIGINAL CV ---
        {raw_cv}
        
        --- JOB DESCRIPTION ---
        {jd_text}
        """
        structured_llm = self.llm.with_structured_output(TailoredOutput)
        return structured_llm.invoke(prompt)

class UpskillingAgent:
    def __init__(self, tavily_client=None):
        # Initialize your Tavily client here if not already done
        self.client = tavily_client

    def _sanitize_title(self, raw_title: str, skill: str) -> str:
        """Fixes generic Tavily titles like 'Course Link' or empty titles."""
        if not raw_title or raw_title.lower().strip() in ["course link", "home", "search", "index"]:
            return f"{skill} Training / Certification"
        return raw_title.strip()

    def _search_single_gap(self, skill: str) -> list[dict]:
        """Queries Tavily for a single skill gap and cleans the output."""
        query = f"best online course certification for {skill}"
        recs = []
        
        try:
            # Replace with your actual Tavily search API call logic
            response = self.client.search(query=query, max_results=2)
            results = response.get("results", [])
            
            for res in results:
                raw_url = res.get("url", "#")
                raw_title = res.get("title", "")
                
                recs.append({
                    "skill": skill,
                    "title": self._sanitize_title(raw_title, skill),
                    "url": raw_url,
                    "description": res.get("snippet", "")[:150]
                })
        except Exception as e:
            print(f"⚠️ Error searching for gap '{skill}': {e}")
            
        return recs

    def run(self, skill_gaps: list[str]) -> UpskillingReport:
        # Deduplicate skill inputs
        unique_gaps = list(dict.fromkeys([g.strip() for g in skill_gaps if g.strip()]))
        if not unique_gaps:
            return UpskillingReport(recommendations=[])

        all_recs = []
        # Execute Tavily API calls in parallel across multiple worker threads
        max_workers = min(len(unique_gaps), 5)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(self._search_single_gap, unique_gaps)
            for res in results:
                all_recs.extend(res)

        return UpskillingReport(recommendations=all_recs)

if __name__ == "__main__":
    print("Phase 4 agents module loaded successfully.")
