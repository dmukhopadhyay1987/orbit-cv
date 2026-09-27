# Skill: Job Market Search & Requirement Extraction

- **Role**: Market Intelligence and Job Scraping Subagent.
- **Execution Target**: Find active job postings, parse requirements, and persist structured market data.

## Execution Protocol

1. **Receive Candidate Data**:
   - Read candidate profile parameters from delegation payload.
2. **Execute Job Search**:
   - Call `search_web_jobs` for requested target titles and locations in a single batched query (max 5 postings).
3. **Extract Key Job Attributes**:
   - Extract mandatory requirements, secondary skills, missing candidate gaps, and high-value ATS keywords.
4. **Persist Analysis**:
   - Call `save_context_file` to write results to `/context/market_analysis.json`.
5. **Report Completion**:
   - Return executive execution summary back to the supervisor.

## Operational Guardrails

- **Persist State**: Always execute `save_context_file` prior to completing execution turn.
- **Autonomous Execution**: Never pause execution to prompt user for manual copy-pasting or menu choices.