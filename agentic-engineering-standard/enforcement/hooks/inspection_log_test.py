#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).with_name("inspection-log.py")

LOG = "### Primary Source Inspection Log\n- Pattern: `src/jobs/send-email.job.ts`"
HEADING_ONLY = "Primary Source Inspection Log: done"


def assistant(text: str) -> dict:
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def thinking(text: str) -> dict:
    return {"type": "assistant", "message": {"content": [{"type": "thinking", "thinking": text}]}}


BOUNDARY = {"type": "system", "subtype": "compact_boundary"}

CASES = [
    ("no log yet", [assistant("Starting.")], "src/a.ts", "deny"),
    ("log written", [assistant(LOG)], "src/a.ts", "allow"),
    ("heading without a file", [assistant(HEADING_ONLY)], "src/a.ts", "deny"),
    ("log only in thinking", [thinking(LOG)], "src/a.ts", "deny"),
    ("log before compaction", [assistant(LOG), BOUNDARY], "src/a.ts", "deny"),
    ("log after compaction", [assistant(LOG), BOUNDARY, assistant(LOG)], "src/a.ts", "allow"),
    ("docs edit", [assistant("x")], "docs/notes.md", "allow"),
    ("config edit", [assistant("x")], "package.json", "allow"),
    ("python edit", [assistant("x")], "app/main.py", "deny"),
    ("outside a repository", [assistant("x")], "OUTSIDE", "allow"),
    ("retry after the reminder", [assistant("x")], "src/a.ts", "allow-on-retry"),
]


def run(entries: list[dict], relative: str, attempts: int = 1) -> str:
    with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as outside, tempfile.TemporaryDirectory() as home:
        (Path(repo) / ".git").mkdir()
        transcript = Path(repo) / "transcript.jsonl"
        transcript.write_text("\n".join(json.dumps(entry) for entry in entries) + "\n")
        target = Path(outside) / "a.ts" if relative == "OUTSIDE" else Path(repo) / relative
        payload = {"session_id": "s1", "tool_name": "Edit", "tool_input": {"file_path": str(target)}, "transcript_path": str(transcript)}
        decision = ""
        for _ in range(attempts):
            result = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True, text=True, check=True, env={**os.environ, "HOME": home})
            decision = json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] if result.stdout.strip() else "allow"
        return decision


def main() -> int:
    failures = []
    for name, entries, path, expected in CASES:
        actual = run(entries, path, 2) if expected == "allow-on-retry" else run(entries, path)
        if actual != expected.removesuffix("-on-retry"):
            failures.append((name, expected, actual))
    for name, expected, actual in failures:
        print(f"FAIL {name}: expected {expected}, got {actual}")
    print(f"{len(CASES) - len(failures)}/{len(CASES)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
