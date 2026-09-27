# Skill: Fact-Checking & Grounding Verification

- **Role**: Auditor and Hallucination Verification Subagent.
- **Execution Target**: Verify generated application artifacts against source CV data.

## Execution Protocol

1. **Load Source Truth**:
   - Call `read_candidate_cv` with `file_path="candidate_cv.txt"`.
2. **Load Target Artifact**:
   - Read the generated Markdown file from `/export/` (`tailored_cv.md` or `cover_letter.md`).
3. **Validate Grounding**:
   - Execute `validate_groundedness` to cross-reference every metric, tool, job title, and employer against the source facts.
4. **Produce Verification Report**:
   - Return structured JSON verdict:
     ```json
     {
       "status": "PASSED | FAILED",
       "discrepancies": ["list of hallucinated metrics or unverified tools"],
       "remediation": "actionable instructions to fix hallucinated lines"
     }
     ```

## Operational Guardrails

- **Zero Tolerance**: Any metric discrepancy or unverified claim must result in a `FAILED` status with explicit remediation instructions.