# linkedin-job-apply

An [Antigravity](https://antigravity.google/docs/skills/) agent skill that turns a LinkedIn hiring
post into either a Gmail draft addressed to the recruiter, or a filled-in application form — and
stops there. You send and submit; the agent never does.

```
/linkedin-job-apply

<paste the post text or its URL>
```

## Why this repo is shaped this way

The skill lives at `.agents/skills/linkedin-job-apply/`, which is where Antigravity looks for
workspace skills. Clone this repo and run `agy` from its root and the skill loads with no install
step — `/skills` will list it.

To make it available in every project instead, copy the folder out:

```bash
cp -r .agents/skills/linkedin-job-apply ~/.gemini/config/skills/
```

## What it does

1. **Gets the post** — pasted text, or a URL it opens. Expands a "…see more" post first, because
   the apply link is often inside the hidden part.
2. **Extracts the contact** with `scripts/extract.py` rather than by reading and guessing:
   `noreply@`, `example.*`, image filenames, profile links and hashtag links are dropped, and a
   direct Greenhouse/Lever/Workday link is ranked above a LinkedIn job URL.
3. **Email route** — one navigation to a pre-filled Gmail compose URL, then attach the CV, then
   stop. The draft stays unsent.
4. **Form route** — one navigation, one snapshot, one `fill_form` call for every field it can
   answer, upload the CV, then stop. Nothing is submitted.
5. **Logs one line** to `logs/applications.jsonl` per run.

Speed is a design constraint, not an afterthought: two snapshots per page at most, no screenshots,
and no per-field round trips.

## What it will not do

- Never clicks Send, Submit, Apply now, Finish or Confirm. Never presses Enter in a form.
- Never uses LinkedIn Easy Apply (its last step submits).
- Never invents a phone number, employer, salary, notice period or years of experience.
- Never enters credentials, never solves a CAPTCHA, never writes to `myinfo/`.

## Setup

### 1. Give the agent browser tools

The skill drives your Chrome through the Chrome DevTools MCP server. Merge
`resources/mcp_config.json` into `~/.gemini/config/mcp_config.json`:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--autoConnect"]
    }
  }
}
```

`--autoConnect` attaches to your running Chrome (Chrome 144+, enable remote debugging at
`chrome://inspect/#remote-debugging`). If that gives you trouble, start Chrome yourself with
`--remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-agent"`, sign in to LinkedIn and
Gmail there, and use `--browser-url http://127.0.0.1:9222` instead.

### 2. Fill in `myinfo/`

```
myinfo/
├── resume.pdf          <- you add this; git-ignored, never committed
├── profile.md          <- identity, contact, experience, notice period
├── skills.md           <- what the agent may claim, with numbers
├── email_template.md   <- tone and structure of the outreach mail
└── form_answers.md     <- canned answers for standard questions
```

Every `<<FILL ME>>` line is treated as "unknown", so that field is left blank rather than
invented. `resume.pdf` is in `.gitignore` on purpose — do not commit your CV to a public repo.

### 3. Check it loaded

Run `/skills` in `agy`; `linkedin-job-apply` should be listed with its description. If it is
missing, the frontmatter is malformed (`description` is required) or the folder is nested one
level too deep.

## If it feels slow

Most of an agent run is round trips, not typing. The skill spends one navigation plus one
verification snapshot on an email, and the same plus one `fill_form` on a form.

The other lever is the model doing the thinking:

```bash
agy --model <a fast model from your picker> --effort medium
```

A Flash-class model writes a 120-word email perfectly well and returns much sooner than a
Pro-class one at high effort.

## Tests

The bundle is linted the way Antigravity loads it — frontmatter, hard rules, MCP config, and both
scripts actually running:

```bash
pip install pyyaml
python3 tests/check_skill.py
```

## Layout

```
.agents/skills/linkedin-job-apply/
├── SKILL.md              the protocol the agent follows
├── INSTALL.md            install notes, including the slow-run tips
├── scripts/extract.py    post text -> {emails, apply_urls}
├── scripts/log_run.py    appends one JSONL row per run
└── resources/mcp_config.json
myinfo/                   your details (templates committed, resume ignored)
tests/check_skill.py      linter
```
