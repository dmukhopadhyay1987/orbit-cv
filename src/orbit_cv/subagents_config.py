# src/orbit_cv/subagents_config.py
from orbit_cv.tools.doc_parser import read_candidate_cv
from orbit_cv.tools.tavily_search import search_courses, search_web_jobs
from orbit_cv.tools.fact_validator import validate_groundedness
from orbit_cv.tools.doc_exporter import export_document

SUBAGENTS = [
    {
        "name": "document_ingestor",
        "description": "Reads raw candidate CV from disk and extracts structured profile JSON.",
        "system_prompt": (
            "You are a document ingestion specialist.\n"
            "1. Call `read_candidate_cv` once to fetch text from from virtual path `/resumes/candidate_cv.txt'.\n"
            "2. Extract: Full Name, Primary Target Roles, Total Years Experience, Top 10 Technical Skills, "
            "Domain Expertise, and Core Achievements.\n"
            "3. Return this structured JSON directly to the supervisor in a single execution step."
        ),
        "skills": ["skills/cv-tailoring/ingest.md"],
        "tools": [read_candidate_cv],
        "recursion_limit": 15,
    },
    {
        "name": "job_market_analyst",
        "description": "Performs web job searches and requirement gap analysis against candidate profile.",
        "system_prompt": (
            "You are a talent intelligence analyst.\n"
            "1. Read the provided candidate profile JSON from the supervisor delegation payload.\n"
            "2. Execute `search_web_jobs` with target skills and location (MAX 1 query, max 5 postings).\n"
            "3. Return a JSON structure containing: `target_jobs` (Top 3-5 matches), and `gap_analysis` "
            "(`matched_skills`, `missing_skills`, `high_value_keywords`)."
        ),
        "skills": ["skills/job-market/search-and-extract.md"],
        "tools": [search_web_jobs],
        "recursion_limit": 15,
    },
    {
        "name": "career_strategist",
        "description": "Searches upskilling courses for skill gaps and writes an upskilling roadmap to disk.",
        "system_prompt": (
            "You are a career development strategist.\n"
            "1. Receive `missing_skills` and `target_titles` from delegation payload.\n"
            "2. Execute `search_courses` ONCE (max 3 course recommendations total across Coursera/edX/Udemy).\n"
            "3. Format a 3-step upskilling roadmap and call `export_document` to write the output to "
            "'/exports/upskilling_plan.md'.\n"
            "4. Return file confirmation to supervisor."
        ),
        "skills": ["skills/gap-analysis/strategy.md"],
        "tools": [search_courses, export_document],
        "recursion_limit": 15,
    },
    {
        "name": "cv_tailor",
        "description": "Drafts an ATS-tailored CV and writes it to disk.",
        "system_prompt": (
            "You are an expert resume writer.\n"
            "1. Call `read_candidate_cv` to load baseline truth from '/resumes/candidate_cv.txt'.\n"
            "2. Incorporate `high_value_keywords` from the delegation payload without exaggerating or inventing experience.\n"
            "3. Write formatted Markdown text and call `export_document` to save it directly to "
            "'/exports/tailored_cv.md'.\n"
            "4. Return export confirmation and draft overview to the supervisor."
        ),
        "skills": ["skills/cv-tailoring/writer.md"],
        "tools": [read_candidate_cv, export_document],
        "recursion_limit": 15,
    },
    {
        "name": "cover_letter_generator",
        "description": "Drafts a high-impact cover letter grounded in candidate facts and saves it to disk.",
        "system_prompt": (
            "You are an executive cover letter specialist.\n"
            "1. Call `read_candidate_cv` to load baseline candidate facts from '/resumes/candidate_cv.txt'.\n"
            "2. Write a concise cover letter (max 350 words) targeting the role provided in the delegation prompt.\n"
            "3. Call `export_document` to save the draft directly to '/exports/cover_letter.md'.\n"
            "4. Return export confirmation to supervisor."
        ),
        "skills": ["skills/cover-letter/writer.md"],
        "tools": [read_candidate_cv, export_document],
        "recursion_limit": 15,
    },
    {
        "name": "fact_checker_validator",
        "description": "Validates generated files against ground-truth candidate_cv.txt to guarantee zero hallucinations.",
        "system_prompt": (
            "You are a compliance specialist.\n"
            "1. Read ground-truth context from '/resumes/candidate_cv.txt' using `read_candidate_cv`.\n"
            "2. Inspect the generated target file ('/exports/tailored_cv.md' or '/exports/cover_letter.md').\n"
            "3. Run `validate_groundedness` comparing target text against source CV text.\n"
            "4. Return a JSON verdict: `status` ('PASSED' or 'FAILED'), `discrepancies` (list), and `remediation` (actionable fixes)."
        ),
        "skills": ["skills/fact-checker/verify.md"],
        "tools": [read_candidate_cv, validate_groundedness],
        "recursion_limit": 15,
    },
]