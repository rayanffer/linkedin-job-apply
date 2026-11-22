#!/usr/bin/env python3
"""Append one run to logs/applications.jsonl.

Called by the linkedin-job-apply skill. Keeps the log machine-readable instead of having the
model hand-write JSON, which it gets wrong at exactly the wrong moment.

    python3 scripts/log_run.py --mode email --target careers@acme.com \
        --post-url "https://www.linkedin.com/feed/update/urn:li:activity:1/" \
        --author "Asad Jawed" --status drafted --notes "draft left unsent"
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

FIELDS = ("ts", "mode", "target", "post_url", "author", "status", "notes")


def find_log_dir(start: pathlib.Path) -> pathlib.Path:
    """logs/ next to myinfo/, walking up from the working directory."""
    for folder in [start, *start.parents]:
        if (folder / "myinfo").is_dir():
            return folder / "logs"
    return start / "logs"


def main() -> int:
    parser = argparse.ArgumentParser(description="Append one job-application run to the log.")
    parser.add_argument("--mode", required=True, choices=["email", "form"])
    parser.add_argument("--target", required=True, help="email address or apply URL")
    parser.add_argument("--post-url", default="", help="post URL, or 'pasted text'")
    parser.add_argument("--author", default="", help="name on the post")
    parser.add_argument("--status", required=True, choices=["drafted", "filled", "blocked", "error"])
    parser.add_argument("--notes", default="", help="one short line")
    parser.add_argument("--log-dir", default="", help="override the output directory")
    args = parser.parse_args()

    base = pathlib.Path(args.log_dir).expanduser() if args.log_dir else find_log_dir(pathlib.Path.cwd())
    base.mkdir(parents=True, exist_ok=True)
    path = base / "applications.jsonl"

    row = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "mode": args.mode,
        "target": args.target,
        "post_url": args.post_url,
        "author": args.author,
        "status": args.status,
        "notes": args.notes.replace("\n", " ")[:500],
    }

    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(path.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
