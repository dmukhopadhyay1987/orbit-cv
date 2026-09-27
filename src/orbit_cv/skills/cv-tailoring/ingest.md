# Skill: Candidate Profile Data Extraction

- **Role**: Specialized Ingestion Agent for parsing and structuring candidate CV metrics.
- **Execution Target**: Extract primary metadata from local CV plain text and return a structured JSON profile summary.

## Execution Protocol

1. **Read Source Plain Text**:
   - Call `read_candidate_cv` with `file_path="candidate_cv.txt"`. If `file_path` is empty or omitted, default to `"candidate_cv.txt"`.
2. **Extract Key Profile Elements**:
   - Parse and extract the following schema:
     ```json
     {
       "full_name": "string",
       "target_titles": ["string"],
       "total_years_exp": number,
       "top_10_skills": ["string"],
       "domain_expertise": ["string"],
       "core_achievements": ["string"]
     }
     ```
3. **Return State**:
   - Return the structured JSON payload directly to the supervisor in a single response turn.

## Operational Guardrails

- **Single-Turn Execution**: Complete ingestion within one tool call cycle.
- **No External Calls**: Do not initiate web searches during profile ingestion.