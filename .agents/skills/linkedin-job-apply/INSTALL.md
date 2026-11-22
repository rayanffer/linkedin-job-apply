# Install

The skill is the folder this file sits in. Copy it, don't rename it.

## 1. Put the folder where `agy` looks

```bash
# every workspace
mkdir -p ~/.gemini/config/skills
cp -r linkedin-job-apply ~/.gemini/config/skills/

# or just this project
mkdir -p .agents/skills
cp -r linkedin-job-apply .agents/skills/
```

The folder name becomes the command: `linkedin-job-apply` → `/linkedin-job-apply`.

## 2. Give the agent browser tools

The skill drives Chrome through the Chrome DevTools MCP server. Merge
`resources/mcp_config.json` into `~/.gemini/config/mcp_config.json` (create the file if it does
not exist):

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

- `--autoConnect` attaches to your already-running Chrome (Chrome 144+, enable remote debugging
  at `chrome://inspect/#remote-debugging`).
- If that flag gives you trouble, start Chrome yourself with
  `--remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-agent"`, sign in to LinkedIn and
  Gmail there, and replace the args with
  `["-y", "chrome-devtools-mcp@latest", "--browser-url", "http://127.0.0.1:9222"]`.

Restart `agy` afterwards, or run `/mcp` to check the server is connected.

## 3. Keep a `myinfo/` folder in the workspace

```
your-project/
├── myinfo/
│   ├── resume.pdf          <- you must add this
│   ├── profile.md          <- identity, contact, experience, notice period
│   ├── skills.md           <- what you may claim, with numbers
│   ├── email_template.md   <- tone and structure of the outreach mail
│   └── form_answers.md     <- canned answers for standard questions
└── logs/applications.jsonl <- written by the skill
```

A line containing `<<FILL ME>>` is treated as "unknown", so the field is left blank rather than
invented. If you still have the earlier zip, its `myinfo/` folder is already in this format.

## 4. Use it

```
/linkedin-job-apply

<paste the post text here>
```

or

```
/linkedin-job-apply https://www.linkedin.com/feed/update/urn:li:activity:7.../
```

You get back a Gmail draft left unsent, or a filled form left unsubmitted, plus a short report.
The skill never sends or submits — that stays with you.

## If it feels slow

Most of the wall-clock time in an agent run is round trips, not typing. The skill now spends:

- **email**: one navigation (the whole draft is in the URL), one `upload_file`, one verification
  snapshot.
- **form**: one navigation, one snapshot, one `fill_form`, one `upload_file`, one verification
  snapshot.

If it still drags, the other lever is the model doing the thinking:

```bash
agy --model <a fast model from your picker> --effort medium
```

A Flash-class model drafts a 120-word email perfectly well and returns much sooner than a
Pro-class one at high effort; `--effort medium` or `low` cuts the thinking time before the first
tool call. Both are per-session, so you can drop back to a heavier model for other work. You can
also switch models mid-session with `/model` where your version offers it.

Do not run `/browser` first and then the skill — that adds a hop for no benefit. The skill drives
the browser through the chrome-devtools tools directly.

## Checking it loaded

Run `/skills` in `agy`; `linkedin-job-apply` should be listed with its description. If it is
missing, the folder is one level too deep (it must sit directly inside `skills/`) or the
frontmatter is malformed — `description` is required.
