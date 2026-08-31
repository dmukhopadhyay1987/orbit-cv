import os
from typing import List, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from dotenv import load_dotenv

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
    """Agent responsible for searching real-time learning resources via Tavily for identified skill gaps."""
    def __init__(self):
        self.llm = get_llm(0.1)
        # Initialize Tavily search tool via langchain-tavily
        self.search_tool = TavilySearch(max_results=3, topic="general", search_depth="basic")

    def run(self, skill_gaps: List[str]) -> UpskillingReport:
        if not skill_gaps:
            return UpskillingReport(recommendations=[])
        unique_gaps = list(dict.fromkeys([g.strip() for g in skill_gaps if g.strip()]))
        # Execute targeted web searches for each skill gap using Tavily
        search_context = []
        for skill in skill_gaps:
            query = f"best current online courses certifications for learning {skill}"
            try:
                results = self.search_tool.invoke({"query": query})
                search_context.append(f"Skill: {skill}\nSearch Results: {results}")
            except Exception as e:
                search_context.append(f"Skill: {skill}\nSearch failed: {str(e)}")

        context_str = "\n\n".join(search_context)

        prompt = f"""
        You are an expert technical career mentor. Based on the web search results for the user's identified skill gaps,
        synthesize a structured list of top recommendations for online courses or certifications.
        
        --- IDENTIFIED SKILL GAPS ---
        {skill_gaps}
        
        --- WEB SEARCH RESULTS ---
        {context_str}
        """
        
        structured_llm = self.llm.with_structured_output(UpskillingReport)
        return structured_llm.invoke(prompt)

if __name__ == "__main__":
    print("Phase 4 agents module loaded successfully.")
