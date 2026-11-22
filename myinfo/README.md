# myinfo/

Everything the skill is allowed to know about you. Nothing else is sent to the model.

| File | Used for |
|---|---|
| `resume.pdf` | attached to the Gmail draft, uploaded to the form's CV field. **You add this** — it is git-ignored and must never be committed to a public repo. |
| `profile.md` | identity, contact details, experience, notice period, relocation |
| `skills.md` | what the agent may claim about you, with numbers |
| `email_template.md` | tone and structure of the outreach mail |
| `form_answers.md` | canned answers for standard application questions |

Rules the agent follows with these files:

- A line containing `<<FILL ME>>` is stripped before use, so that field counts as unknown. The
  agent leaves the matching form field empty and tells you.
- The `Do NOT claim` section of `skills.md` is a hard block — the agent will not assert those.
- Nothing here is ever written to by the agent. It is read-only input.
