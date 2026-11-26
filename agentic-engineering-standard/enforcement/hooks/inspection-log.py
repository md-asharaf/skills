#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

CODE_SUFFIXES = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte", ".astro",
    ".py", ".go", ".rs", ".java", ".kt", ".kts", ".scala", ".php", ".cs", ".fs",
    ".dart", ".rb", ".swift", ".m", ".c", ".h", ".cc", ".cpp", ".hpp", ".ex", ".exs",
    ".sql", ".sh", ".bash", ".zsh", ".css", ".scss", ".sass", ".less", ".html",
}
LOG_HEADING = re.compile(r"inspection\s+log", re.IGNORECASE)
FILE_REFERENCE = re.compile(r"[\w.-]+/[\w./-]*\.\w{1,6}\b|`[\w./-]+\.\w{1,6}`")
MARKERS = Path.home() / ".cache" / "claude-inspection-log"
REASON = (
    "Inspection log first (owner rule 1, hard rule 2): before the first code edit of this session, "
    "write the Primary Source Inspection Log in chat, naming the standard or spec sections you read "
    "and the existing pattern file you follow (with its path). Then retry this edit. "
    "This reminder is shown once per session and after each compaction."
)


def inside_repository(path: Path) -> bool:
    return any((candidate / ".git").exists() for candidate in [path, *path.parents])


def is_boundary(entry: dict) -> bool:
    return entry.get("type") == "system" and entry.get("subtype") == "compact_boundary"


def assistant_texts(entry: dict) -> list[str]:
    if entry.get("type") != "assistant":
        return []
    content = entry.get("message", {}).get("content", [])
    if isinstance(content, str):
        return [content]
    return [block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text"]


def scan(transcript: Path) -> tuple[bool, int]:
    texts: list[str] = []
    boundaries = 0
    for line in transcript.read_text(errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict):
            continue
        if is_boundary(entry):
            texts = []
            boundaries += 1
            continue
        texts.extend(assistant_texts(entry))
    return any(LOG_HEADING.search(text) and FILE_REFERENCE.search(text) for text in texts), boundaries


def first_reminder(session: str, boundaries: int) -> bool:
    marker = MARKERS / f"{re.sub(r'[^\w-]', '_', session)}-{boundaries}"
    if marker.exists():
        return False
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()
    return True


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    transcript = payload.get("transcript_path")
    if not isinstance(file_path, str) or not isinstance(transcript, str):
        return 0
    target = Path(file_path)
    if target.suffix.lower() not in CODE_SUFFIXES or not inside_repository(target.parent):
        return 0
    transcript_path = Path(transcript)
    if not transcript_path.is_file():
        return 0
    logged, boundaries = scan(transcript_path)
    if logged or not first_reminder(str(payload.get("session_id") or transcript_path.stem), boundaries):
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": REASON,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
