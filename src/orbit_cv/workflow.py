import os
import ast
import json
import base64
import io
from typing import TypedDict, List, Optional, Any, Annotated
from langgraph.graph import StateGraph, END, add_messages
from orbit_cv.intake_server import extract_text_from_file
from orbit_cv.analysis_engine import run_gap_analysis, GapAnalysisResult
from orbit_cv.agents import get_llm, CVTailoringAgent, UpskillingAgent, TailoredOutput, UpskillingReport, FactCheckResult
from langgraph.types import interrupt
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage

def parse_content_item(content) -> tuple[list[dict], str]:
    """
    Parses content (which could be a string, a list of dicts, or a stringified list of dicts)
    and returns a list of files (with decoded base64 data) and a concatenated text string.
    """
    files = []
    texts = []

    if isinstance(content, str):
        content_stripped = content.strip()
        if (content_stripped.startswith("[") and content_stripped.endswith("]")) or \
           (content_stripped.startswith("{") and content_stripped.endswith("}")):
            try:
                parsed = json.loads(content_stripped)
                content = parsed
            except Exception:
                try:
                    parsed = ast.literal_eval(content_stripped)
                    content = parsed
                except Exception:
                    pass

    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                item_type = item.get("type")
                if item_type == "text":
                    texts.append(item.get("text", ""))
                elif item_type == "file":
                    mime_type = item.get("mimeType", "")
                    base64_data = item.get("data", "")
                    if base64_data:
                        try:
                            decoded = base64.b64decode(base64_data)
                            files.append({"mimeType": mime_type, "data": decoded})
                        except Exception as e:
                            print(f"Error decoding base64 file data: {e}")
                elif "image_url" in item:
                    pass
            elif isinstance(item, str):
                texts.append(item)
    elif isinstance(content, dict):
        item_type = content.get("type")
        if item_type == "text":
            texts.append(content.get("text", ""))
        elif item_type == "file":
            mime_type = content.get("mimeType", "")
            base64_data = content.get("data", "")
            if base64_data:
                try:
                    decoded = base64.b64decode(base64_data)
                    files.append({"mimeType": mime_type, "data": decoded})
                except Exception as e:
                    print(f"Error decoding base64 file data: {e}")
    elif isinstance(content, str):
        texts.append(content)

    return files, "\n".join(texts)

def extract_text_from_bytes(data: bytes, mime_type: str) -> str:
    """Extracts raw text from bytes based on mimeType."""
    if mime_type == "application/pdf":
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(data))
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        import docx
        doc = docx.Document(io.BytesIO(data))
        return "\n".join([para.text for para in doc.paragraphs if para.text])
    elif "text/" in mime_type or mime_type in ["application/json", "application/javascript"]:
        return data.decode("utf-8", errors="ignore")
    else:
        try:
            return data.decode("utf-8")
        except Exception:
            raise ValueError(f"Unsupported mimeType: {mime_type}")

def extract_jd_from_text(text: str) -> str | None:
    """Attempts to find and extract the job description from the message text."""
    lower_text = text.lower()
    markers = [
        "here is the job description:",
        "here is the job description",
        "job description:",
        "job description",
        "about the job:",
        "about the job",
        "target role:",
        "target role"
    ]
    
    for marker in markers:
        idx = lower_text.find(marker)
        if idx != -1:
            jd_part = text[idx + len(marker):].strip()
            if len(jd_part) > 20:
                return jd_part
    return None

# --- Custom Python State supporting messages and custom keys ---
class OrbitCVState(TypedDict):
    messages: Annotated[list, add_messages]
    cv_path: str
    jd_input: str
    parsed_cv: Optional[dict]
    parsed_jd: Optional[dict]
    gap_analysis: Optional[Any]
    tailored_cv: Optional[str]          # Pure document text ONLY
    cover_letter: Optional[str]        # Pure document text ONLY
    unverified_claims: Optional[List[str]]
    agent_insights: Optional[dict]     # Structural metadata for UI panels
    course_recommendations: Optional[list]

# --- Node 1: Document Intake (With State Inspection) ---
def intake_node(state: OrbitCVState) -> dict:
    print("\n🚀 [Graph] Step 1: Parsing incoming state...")
    print(f"   -> Full State Keys Received: {list(state.keys())}")
    
    messages = state.get("messages", [])
    print(f"   -> Messages count: {len(messages)}")
    
    # Extract latest text or attachment info from messages if present
    latest_text = ""
    for msg in reversed(messages):
        if hasattr(msg, "content"):
            latest_text = msg.content
            break
        elif isinstance(msg, dict):
            latest_text = msg.get("content", "")
            break

    # Determine CV source: check state keys or fallback to message text
    cv_input = state.get("cv_path") or latest_text or "Sample full-stack developer profile with 15 years of experience in Java, Kotlin, and MongoDB."
    
    # Parse CV text safely
    parsed_cv = {}
    extracted_text_from_prompt = ""
    
    if isinstance(cv_input, str) and os.path.exists(cv_input):
        try:
            cv_text = extract_text_from_file(cv_input)
            print(f"   -> Extracted CV Text Length: {len(cv_text)}")
            parsed_cv = {"source_file": cv_input, "raw_text": cv_text, "status": "success"}
        except Exception as e:
            parsed_cv = {"source_file": cv_input, "raw_text": str(cv_input), "status": "success"}
    else:
        # Parse it as content (possibly multipart with files/prompt text)
        files, prompt_text = parse_content_item(cv_input)
        extracted_text_from_prompt = prompt_text
        
        if files:
            cv_texts = []
            for f in files:
                try:
                    cv_text = extract_text_from_bytes(f["data"], f["mimeType"])
                    cv_texts.append(cv_text)
                except Exception as e:
                    print(f"   -> Error extracting text from uploaded file: {e}")
            if cv_texts:
                combined_cv = "\n\n".join(cv_texts)
                print(f"   -> Extracted CV Text Length from uploaded files: {len(combined_cv)}")
                parsed_cv = {"source_file": "chat_upload_files", "raw_text": combined_cv, "status": "success"}
            else:
                parsed_cv = {"source_file": "chat_upload_or_text", "raw_text": prompt_text, "status": "success"}
        else:
            parsed_cv = {"source_file": "chat_upload_or_text", "raw_text": prompt_text, "status": "success"}

    # Parse JD text safely
    parsed_jd = {}
    jd_input = state.get("jd_input")
    
    if not jd_input and extracted_text_from_prompt:
        extracted_jd = extract_jd_from_text(extracted_text_from_prompt)
        if extracted_jd:
            print(f"   -> Extracted Job Description from chat prompt, length: {len(extracted_jd)}")
            parsed_jd = {"source": "extracted_from_prompt", "raw_text": extracted_jd, "status": "success"}
            
    if not parsed_jd:
        jd_input = jd_input or "Looking for a full-stack developer."
        if isinstance(jd_input, str) and os.path.exists(jd_input):
            try:
                jd_text = extract_text_from_file(jd_input)
                parsed_jd = {"source": jd_input, "raw_text": jd_text, "status": "success"}
            except Exception as e:
                parsed_jd = {"source": jd_input, "raw_text": str(jd_input), "status": "success"}
        else:
            parsed_jd = {"source": "direct_input", "raw_text": str(jd_input), "status": "success"}

    return {"parsed_cv": parsed_cv, "parsed_jd": parsed_jd}


# --- Node 2: Relaxed Clarification (Stops the Loop) ---
def clarification_node(state: OrbitCVState) -> dict:
    print("\n🧐 [Graph] Evaluating document depth...")
    
    parsed_cv = state.get("parsed_cv", {})
    cv_raw_text = parsed_cv.get("raw_text", "")
    
    print(f"   -> Extracted CV Text Length: {len(cv_raw_text)}")
    
    # If we have any text longer than 15 characters, accept it and move on!
    # This completely eliminates the false-positive loop while you test.
    if len(cv_raw_text.strip()) > 15:
        print("   -> Sufficient text detected. Proceeding to analysis.")
        return {}
    
    print("   -> Text is too brief. Pausing for user clarification...")
    
    user_answer = interrupt({
        "question": "Please paste your CV text or job requirements here to continue."
    })
    
    return {
        "parsed_cv": {
            "source_file": "user_interrupt_response",
            "raw_text": str(user_answer),
            "status": "success"
        }
    }

# --- Node 2: RLM Analysis Engine ---
def analysis_node(state: OrbitCVState) -> dict:
    print("\n🧠 [Graph] Step 2: Executing RLM Chain-of-Thought Gap Analysis with gpt-5-nano...")
    parsed_cv = state["parsed_cv"]
    parsed_jd = state["parsed_jd"]
    
    gap_result = run_gap_analysis(parsed_cv, parsed_jd)
    print(f"   -> Alignment Score: {gap_result.alignment_score}%")
    print(f"   -> Identified Skill Gaps: {gap_result.skill_gaps}")
    return {"gap_analysis": gap_result}

def fact_check_node(state: OrbitCVState) -> dict:
    print("\n🛡️ [Graph] Fact-Checking: Auditing generated output against Master CV...")
    
    master_cv_text = state.get("parsed_cv", {}).get("raw_text", "")
    generated_cv = state.get("tailored_cv", "")
    generated_letter = state.get("cover_letter", "")
    
    if not generated_cv or not master_cv_text:
        return {}

    llm = get_llm(temperature=0).with_structured_output(FactCheckResult)
    
    prompt = f"""
    You are an automated compliance editor for executive resume tailoring.
    
    MASTER CV (Source of Truth):
    {master_cv_text}
    
    GENERATED TAILORED CV:
    {generated_cv}
    
    GENERATED COVER LETTER:
    {generated_letter}
    
    Your Task:
    1. Compare the generated CV and cover letter against the Master CV.
    2. Remove any claims not supported by the Master CV.
    3. Strip out ALL non-document content (e.g., '> Let op:', notes, footnotes, disclaimers) from the final document strings.
    4. Provide a 2-3 sentence strategic rationale in 'strategy_notes' explaining how the resume was aligned to the job description.
    """
    
    audit_result: FactCheckResult = llm.invoke(prompt)
    
    # Clean separation: Documents remain pure; insights move to metadata
    return {
        "tailored_cv": audit_result.cleaned_tailored_cv,
        "cover_letter": audit_result.cleaned_cover_letter,
        "unverified_claims": audit_result.hallucinated_claims,
        "agent_insights": {
            "strategy_notes": audit_result.strategy_notes,
            "removed_claims_count": len(audit_result.hallucinated_claims),
            "flagged_claims": audit_result.hallucinated_claims
        }
    }

# --- Node 3: CV Tailoring & Branding ---
def tailoring_node(state: OrbitCVState) -> dict:
    print("\n✍️ [Graph] Step 3: Rewriting CV and drafting targeted cover letter...")
    raw_cv = state["parsed_cv"].get("raw_text", "")
    jd_text = state["parsed_jd"].get("raw_text", "")
    gap_analysis = state["gap_analysis"]
    
    agent = CVTailoringAgent()
    output: TailoredOutput = agent.run(raw_cv, jd_text, gap_analysis)
    
    response_text = f"### Tailored CV\n\n{output.tailored_cv_markdown}\n\n### Cover Letter\n\n{output.cover_letter_markdown}"
    
    return {
        "tailored_cv": output.tailored_cv_markdown,
        "cover_letter": output.cover_letter_markdown
    }

# --- Node 4: Tavily Upskilling Research ---
def upskilling_node(state: OrbitCVState) -> dict:
    print("\n🔍 [Graph] Step 4: Researching upskilling courses via Tavily API...")
    gap_analysis = state["gap_analysis"]
    skill_gaps = gap_analysis.skill_gaps if gap_analysis else []

    agent = UpskillingAgent()
    report: UpskillingReport = agent.run(skill_gaps)

    recs_data = [rec.model_dump() if hasattr(rec, "model_dump") else rec for rec in report.recommendations]

    # Build Markdown list to feed the Vercel frontend chat stream
    if report.recommendations:
        upskilling_md = "### 💡 Recommended Courses & Upskilling\n\n"
        for rec in report.recommendations:
            # Safely retrieve fields from Pydantic object or dict
            title = getattr(rec, "title", None) or (rec.get("title") if isinstance(rec, dict) else "Course Link")
            url = getattr(rec, "url", None) or (rec.get("url") if isinstance(rec, dict) else "#")
            skill = getattr(rec, "skill", None) or (rec.get("skill") if isinstance(rec, dict) else "Target Skill")
            description = getattr(rec, "description", None) or (rec.get("description") if isinstance(rec, dict) else "")

            item_str = f"* **{skill}**: [{title}]({url})"
            if description:
                item_str += f" — *{description}*"
            upskilling_md += f"{item_str}\n"
    else:
        upskilling_md = "### 💡 Recommended Courses & Upskilling\n\nNo additional courses required based on current alignment."

    # Update metadata insights so frontend sidebars receive the parsed data
    insights = state.get("agent_insights") or {}
    insights["course_recommendations"] = recs_data

    return {
        "course_recommendations": recs_data,
        "agent_insights": insights,
        "messages": [AIMessage(content=upskilling_md)]
    }

# --- Conditional Router ---
def should_upskill(state: OrbitCVState) -> str:
    """Determines whether to execute the upskilling search node or skip to the end."""
    gap_analysis = state.get("gap_analysis")
    if gap_analysis and gap_analysis.skill_gaps and len(gap_analysis.skill_gaps) > 0:
        return "upskill"
    print("   -> No significant skill gaps found. Skipping Tavily upskilling search.")
    return "skip_upskill"

def format_final_output_node(state: OrbitCVState) -> dict:
    cv_text = state.get("tailored_cv", "")
    letter_text = state.get("cover_letter", "")
    recs = state.get("course_recommendations", [])

    combined_output = f"### Tailored CV\n\n{cv_text}\n\n---\n\n### Cover Letter\n\n{letter_text}"

    if recs:
        combined_output += "\n\n---\n\n### 💡 Skill Gap & Upskilling Recommendations\n\n"
        for rec in recs:
            title = rec.get("title", "Course Link")
            url = rec.get("url", "#")
            skill = rec.get("skill", "Skill")
            combined_output += f"* **{skill}**: [{title}]({url})\n"

    return {"messages": [AIMessage(content=combined_output)]}

# --- Graph Compilation ---
def create_orbitcv_graph():
    workflow = StateGraph(OrbitCVState)
    
    # 1. Add Nodes
    workflow.add_node("intake", intake_node)
    workflow.add_node("clarify", clarification_node)
    workflow.add_node("analyze", analysis_node)
    workflow.add_node("tailor", tailoring_node)
    workflow.add_node("fact_check", fact_check_node)  # <-- Add node registration here
    workflow.add_node("upskill", upskilling_node)
    workflow.add_node("format_final_output", format_final_output_node)

    # 2. Wire Edges
    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "clarify")
    workflow.add_edge("clarify", "analyze")
    workflow.add_edge("analyze", "tailor")
    workflow.add_edge("tailor", "fact_check")         # <-- Route tailor -> fact_check
    
    # 3. Route from fact_check into conditional upskilling
    workflow.add_conditional_edges(
        "fact_check",
        should_upskill,
        {
            "upskill": "upskill",
            "skip_upskill": "format_final_output"
        }
    )
    workflow.add_edge("upskill", "format_final_output")
    workflow.add_edge("format_final_output", END)
    
    return workflow.compile()
    
# Compile the graph and expose it as a global variable for the LangGraph dev server
graph = create_orbitcv_graph()

if __name__ == "__main__":
    print("LangGraph workflow compiled successfully.")