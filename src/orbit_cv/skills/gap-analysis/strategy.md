# Skill: Career Gap Analysis & Upskilling Plan

- **Role**: Strategic Career Development Subagent.
- **Execution Target**: Evaluate skill gaps against target jobs and generate actionable upskilling roadmaps.

## Execution Protocol

1. **Load Market Gaps**:
   - Call `read_context_file` to retrieve `missing_skills` and requirements.
2. **Draft Upskilling Roadmap**:
   - Create a structured markdown document listing the identified gaps.
3. **Export Artifact**:
   - Call `export_document(content_markdown=plan_md, output_format="md", filename_prefix="upskilling_plan")`.