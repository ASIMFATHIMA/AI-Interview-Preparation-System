# Career Agent Responsibilities

## Shared rule

Agents receive a read-only `CandidateProfileContext`. They may create their own reports, drafts, sessions, and recommendations, but they must not overwrite source profile facts or parsed resume records without an explicit user action.

Passwords, password hashes, JWTs, and other credentials are never included in agent context.

## Agent ownership

| Agent | Responsibility | Primary outputs |
| --- | --- | --- |
| Job-Resume Matching Agent | Compare a job description with verified profile and resume evidence. | Match score, matching skills, missing requirements, explanation |
| Skill Gap Agent | Compare target-role requirements with current skills and recommend prioritized learning. | Skill gaps, priorities, learning plan, evidence |
| Resume Agent | Parse, normalize, review, and tailor resume content without inventing claims. | Structured resume, feedback, tailored versions |
| Cover Letter Agent | Write a truthful, job-specific letter from profile and resume evidence. | Cover letter, personalization points, unsupported-claim warnings |
| Interview Agent | Generate role-specific practice and assess answers. | Questions, model answers, feedback, readiness score |
| Career Assistant | Coordinate agent outputs and turn user requests into next actions. | Recommendations, workflow summaries, tasks |

## Candidate profile sections

The shared profile context contains:

- Identity and contact: student ID, name, email, phone, location
- Academic background: degree, field of study, institution
- Professional links: GitHub, LinkedIn, portfolio
- Resume evidence: skills, education, experience, projects, certifications, achievements
- Career preferences: target roles, industries, locations, work modes, companies, authorization
- Provenance metadata: resume update time and source records

The parsed resume tables remain the source of truth for extracted evidence. Preferences are user-provided signals and should be treated separately from verified resume facts.
