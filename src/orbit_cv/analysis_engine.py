import os
from pydantic import BaseModel, Field
from typing import List
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GapAnalysisResult(BaseModel):
    missing_keywords: List[str] = Field(
        description="Crucial technical or soft skills present in the job description but missing or underrepresented in the CV."
    )
    tonal_mismatches: List[str] = Field(
        description="Observations regarding tone, terminology, or formatting differences between the CV and the target role expectations."
    )
    skill_gaps: List[str] = Field(
        description="Explicit hard skill gaps that require bridging via courses, certifications, or targeted project highlights."
    )
    alignment_score: int = Field(
        description="Estimated match percentage score from 0 to 100 based on core requirements."
    )
    summary_critique: str = Field(
        description="Detailed chain-of-thought critique explaining the structural alignment status and recommendations."
    )

def run_gap_analysis(parsed_cv: dict, parsed_jd: dict) -> GapAnalysisResult:
    """
    Executes deep reasoning and gap analysis utilizing gpt-5-nano and structured outputs 
    modeled around RLM context processing.
    """
    # Initialize the cost-effective gpt-5-nano model optimized for low-latency reasoning
    llm = ChatOpenAI(
        model="gpt-5-nano",
        temperature=0.1
    )
    
    # Construct the analysis prompt incorporating raw texts from the FastMCP intake phase
    prompt = f"""
    You are an expert technical recruiter, career architect, and senior hiring manager.
    Perform a meticulous gap analysis comparing the candidate's CV against the target Job Description.
    
    --- CANDIDATE CV ---
    {parsed_cv.get('raw_text', '')}
    
    --- JOB DESCRIPTION ---
    {parsed_jd.get('raw_text', '')}
    
    Evaluate thoroughly for missing keywords, core skill deficits, and semantic mismatches.
    """
    
    # Bind output to the Pydantic schema for strict contract enforcement
    structured_llm = llm.with_structured_output(GapAnalysisResult)
    result = structured_llm.invoke(prompt)
    
    return result

if __name__ == "__main__":
    # Quick standalone test block
    print("Analysis engine module loaded successfully.")
