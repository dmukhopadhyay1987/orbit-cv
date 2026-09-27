from orbit_cv.tools.context_store import read_context_file, save_context_file
from orbit_cv.tools.doc_exporter import export_document
from orbit_cv.tools.doc_parser import read_candidate_cv
from orbit_cv.tools.fact_validator import validate_groundedness
from orbit_cv.tools.web_search import search_web_jobs

SUBAGENTS = [
    {
        "name": "document_ingestor",
        "description": "Reads raw candidate CV from disk and extracts structured profile JSON.",
        "system_prompt": (
            "You are a document ingestion specialist.\n"
            "1. Call `read_candidate_cv` once to fetch text from '/resumes/candidate_cv.txt'.\n"
            "2. Extract: Full Name, Primary Target Roles, Total Years Experience, Top 10 Technical Skills, "
            "Domain Expertise, and Core Achievements.\n"
            "3. Call `save_context_file` with the extracted profile JSON to '/context/candidate_profile.json'.\n"
            "4. Return confirmation and summary to the supervisor without prompting the user for manual input."
        ),
        "skills": ["skills/cv-tailoring/ingest.md"],
        "tools": [read_candidate_cv, save_context_file],
        "recursion_limit": 15,
    },
    {
        "name": "job_market_analyst",
        "description": "Performs web job searches and saves gap analysis to /context/market_analysis.json.",
        "system_prompt": (
            "You are a talent intelligence analyst.\n"
            "1. Call `read_context_file` to fetch candidate profile JSON from '/context/candidate_profile.json'.\n"
            "2. Execute `search_web_jobs` for the requested target roles across target job listings.\n"
            "3. Format the results (`target_jobs`, `gap_analysis`, `high_value_keywords`).\n"
            "4. Call `save_context_file` with the JSON payload to automatically store it in '/context/market_analysis.json'.\n"
            "5. Return confirmation and summary to the supervisor without prompting the user for manual input."
        ),
        "skills": ["skills/job-market/search-and-extract.md"],
        "tools": [search_web_jobs, save_context_file],
        "recursion_limit": 15,
    },
    {
        "name": "career_strategist",
        "description": "Analyzes market gap analysis and writes a structured upskilling areas document to disk without web searching.",
        "system_prompt": (
            "You are a career development strategist.\n"
            "1. Call `read_context_file` to fetch `gap_analysis`, `missing_skills`, and `target_titles` directly from '/context/market_analysis.json'.\n"
            "2. Synthesize these gaps into a structured upskilling document highlighting high-priority competency areas, core domain knowledge gaps, and strategic skill development goals. Do NOT perform any web searches for external courses.\n"
            "3. Call `export_document` using content_markdown=<markdown_text>, output_format='md', and filename_prefix='upskilling_plan'.\n"
            "4. Return file confirmation and upskilling summary to supervisor."
        ),
        "skills": ["skills/gap-analysis/strategy.md"],
        "tools": [read_context_file, export_document],
        "recursion_limit": 15,
    },
    {
        "name": "cv_tailor",
        "description": "Drafts an ATS-tailored CV using market context from disk and writes it to disk.",
        "system_prompt": (
            "You are an expert resume writer.\n"
            "1. Call `read_candidate_cv` to load baseline truth from '/resumes/candidate_cv.txt'.\n"
            "2. Call `read_context_file` to load `high_value_keywords` and gap analysis directly from '/context/market_analysis.json'.\n"
            "3. Incorporate `high_value_keywords` without exaggerating or inventing experience.\n"
            "4. Call `export_document` using content_markdown=<markdown_text>, output_format='md', and filename_prefix='tailored_cv'.\n"
            "5. Return export confirmation and draft overview to the supervisor."
        ),
        "skills": ["skills/cv-tailoring/writer.md"],
        "tools": [read_candidate_cv, read_context_file, export_document],
        "recursion_limit": 15,
    },
    {
        "name": "cover_letter_generator",
        "description": "Drafts high-impact cover letters using market data from disk and saves them to disk.",
        "system_prompt": (
            "You are an executive cover letter specialist.\n"
            "1. Call `read_candidate_cv` to load baseline candidate facts from '/resumes/candidate_cv.txt'.\n"
            "2. Call `read_context_file` to load job descriptions and target role metadata from '/context/market_analysis.json'.\n"
            "3. Write a concise cover letter (max 350 words) targeting the roles provided.\n"
            "4. Call `export_document` using content_markdown=<markdown_text>, output_format='md', and filename_prefix='cover_letter'.\n"
            "5. Return export confirmation to supervisor."
        ),
        "skills": ["skills/cover-letter/writer.md"],
        "tools": [read_candidate_cv, read_context_file, export_document],
        "recursion_limit": 15,
    },
    {
        "name": "fact_checker_validator",
        "description": "Validates generated files against ground-truth candidate_cv.txt to guarantee zero hallucinations.",
        "system_prompt": (
            "You are a compliance specialist.\n"
            "1. Read ground-truth context from '/resumes/candidate_cv.txt' using `read_candidate_cv`.\n"
            "2. Inspect the generated target file ('/export/tailored_cv.md' or '/export/cover_letter.md').\n"
            "3. Run `validate_groundedness` comparing target text against source CV text.\n"
            "4. Return a JSON verdict: `status` ('PASSED' or 'FAILED'), `discrepancies` (list), and `remediation` (actionable fixes)."
        ),
        "skills": ["skills/fact-checker/verify.md"],
        "tools": [read_candidate_cv, validate_groundedness],
        "recursion_limit": 15,
    },
]