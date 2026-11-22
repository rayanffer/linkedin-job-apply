"""Lint the skill bundle the way Antigravity will load it.

    python3 tests/check_skill.py
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Works in either layout: this repo (.agents/skills/...) or an unpacked bundle folder.
SKILL_DIR = ROOT / ".agents" / "skills" / "linkedin-job-apply"
if not SKILL_DIR.is_dir():
    SKILL_DIR = ROOT / "linkedin-job-apply"
SKILL = SKILL_DIR / "SKILL.md"

failures: list[str] = []


def check(label: str, cond: bool, extra: str = "") -> None:
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f" :: {extra}"))
    if not cond:
        failures.append(label)


print("bundle")
check("folder name is the slash command", SKILL_DIR.name == "linkedin-job-apply", SKILL_DIR.name)
check("SKILL.md exists at the bundle root", SKILL.is_file())
check("scripts/log_run.py present", (SKILL_DIR / "scripts" / "log_run.py").is_file())
check("resources/mcp_config.json present", (SKILL_DIR / "resources" / "mcp_config.json").is_file())
check("scripts/extract.py present", (SKILL_DIR / "scripts" / "extract.py").is_file())

print("frontmatter")
text = SKILL.read_text(encoding="utf-8")
check("starts with ---", text.startswith("---\n"), text[:20])
match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
check("frontmatter block is closed", match is not None)
meta = yaml.safe_load(match.group(1)) if match else {}

check("has a description", bool(meta.get("description")), meta)
desc = str(meta.get("description", ""))
check("description is not a one-word stub", len(desc) > 80, len(desc))
for keyword in ("linkedin", "post", "resume", "gmail", "form"):
    check(f"description mentions {keyword!r}", keyword in desc.lower())
check("name matches the folder", meta.get("name") == SKILL_DIR.name, meta.get("name"))
check(
    "name is lowercase-hyphen",
    bool(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", str(meta.get("name", "")))),
    meta.get("name"),
)

print("body")
body = text[match.end():] if match else ""
check("has a body beyond frontmatter", len(body) > 1500, len(body))
for phrase in ("Never send or submit", "Never use LinkedIn Easy Apply", "Never invent a fact"):
    check(f"hard rule present: {phrase!r}", phrase in body)
check("no citation markers leaked in", "[cite:" not in text)
check("mentions the log script", "log_run.py" in body)
check("mentions the extract script", "scripts/extract.py" in body)
check("email path uses the compose URL", "tf=cm" in body)
check("form path uses one fill_form call", "fill_form" in body)
check("caps snapshots", "Two snapshots per page" in body)
check("keeps the compose-URL fallback", "Fallback" in body and "click Compose" in body)
check("mentions the mcp config resource", "resources/mcp_config.json" in body)
check("reports in a fixed shape", "STATUS:" in body and "NEEDS YOU:" in body)

print("resources")
config = json.loads((SKILL_DIR / "resources" / "mcp_config.json").read_text(encoding="utf-8"))
server = config.get("mcpServers", {}).get("chrome-devtools", {})
check("mcp config is valid json with a chrome-devtools server", bool(server), config)
check("mcp server is a stdio command", server.get("command") == "npx", server)

print("extract script")
extract = SKILL_DIR / "scripts" / "extract.py"
POST = (
    "We are hiring a Software Engineer - React Native.\n"
    "Send your CV to careers@thinkdigitally.com\n"
    "Apply: boards.greenhouse.io/acme/jobs/4012\n"
    "Profile: linkedin.com/in/asad-m-jawed\n"
    "Blog: acme.com/blog/scaling\n"
    "noreply@acme.com logo@2x.png"
)
run = subprocess.run(
    [sys.executable, str(extract)], input=POST, capture_output=True, text=True
)
check("extract exits 0", run.returncode == 0, run.stderr[-300:])
data = json.loads(run.stdout) if run.returncode == 0 else {}
check("finds the recruiter address", data.get("emails") == ["careers@thinkdigitally.com"], data)
check(
    "finds the ATS link from a bare domain",
    data.get("apply_urls") == ["https://boards.greenhouse.io/acme/jobs/4012"],
    data,
)
check("rejects noreply and image filenames", "noreply@acme.com" in data.get("rejected", {}).get("emails", []), data)

empty = subprocess.run(
    [sys.executable, str(extract)], input="Great post, thanks!", capture_output=True, text=True
)
check(
    "a post with no contact yields empty lists",
    json.loads(empty.stdout) == {"emails": [], "apply_urls": [], "rejected": {"emails": [], "urls": []}},
    empty.stdout,
)

jsonmode = subprocess.run(
    [sys.executable, str(extract)],
    input=json.dumps({"text": "mail hr@acme.io", "hrefs": ["mailto:talent@acme.io", "https://jobs.lever.co/acme/x"]}),
    capture_output=True,
    text=True,
)
jdata = json.loads(jsonmode.stdout) if jsonmode.returncode == 0 else {}
check("json input mode reads text and hrefs", "talent@acme.io" in jdata.get("emails", []) and jdata.get("apply_urls"), jdata)

print("log script")
with tempfile.TemporaryDirectory() as tmp:
    workspace = pathlib.Path(tmp)
    (workspace / "myinfo").mkdir()
    script = SKILL_DIR / "scripts" / "log_run.py"

    help_run = subprocess.run(
        [sys.executable, str(script), "--help"], capture_output=True, text=True
    )
    check("--help exits 0", help_run.returncode == 0, help_run.stderr[-300:])

    run = subprocess.run(
        [
            sys.executable,
            str(script),
            "--mode",
            "email",
            "--target",
            "careers@thinkdigitally.com",
            "--post-url",
            "https://www.linkedin.com/feed/update/urn:li:activity:1/",
            "--author",
            "Asad Jawed",
            "--status",
            "drafted",
            "--notes",
            "draft left unsent",
        ],
        capture_output=True,
        text=True,
        cwd=workspace,
    )
    check("run exits 0", run.returncode == 0, run.stderr[-300:])

    log = workspace / "logs" / "applications.jsonl"
    check("writes logs/applications.jsonl next to myinfo/", log.is_file(), run.stdout)
    check("prints the path it wrote", str(log.resolve()) in run.stdout, run.stdout)

    if log.is_file():
        lines = log.read_text(encoding="utf-8").splitlines()
        check("exactly one line", len(lines) == 1, lines)
        row = json.loads(lines[0])
        check(
            "row is a complete object",
            set(row) == {"ts", "mode", "target", "post_url", "author", "status", "notes"},
            row,
        )
        check("target recorded", row["target"] == "careers@thinkdigitally.com", row)
        check("timestamp is ISO-ish", bool(re.match(r"\d{4}-\d{2}-\d{2}T", row["ts"])), row["ts"])

    bad = subprocess.run(
        [sys.executable, str(script), "--mode", "nope", "--target", "x", "--status", "drafted"],
        capture_output=True,
        text=True,
        cwd=workspace,
    )
    check("rejects an unknown mode", bad.returncode != 0, bad.returncode)

print()
if failures:
    print(f"{len(failures)} FAILED: {failures}")
    raise SystemExit(1)
print("skill bundle is valid")
