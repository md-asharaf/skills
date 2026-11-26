#!/usr/bin/env python3
import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

SLASH = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".kt", ".kts", ".scala", ".cs", ".dart", ".swift", ".c", ".h", ".cc", ".cpp", ".hpp", ".php"}
HASH = {".py", ".rb", ".sh", ".bash", ".zsh", ".ex", ".exs", ".php"}
DASH = {".sql"}
BLOCK = SLASH | {".css", ".scss", ".less", ".sql"}
MARKUP = {".vue", ".svelte", ".html", ".astro"}
TYPESCRIPT = {".ts", ".tsx", ".vue", ".svelte", ".astro"}
SOURCE = SLASH | HASH | DASH | BLOCK | MARKUP
SKIP_DIRS = {"node_modules", "dist", "build", ".next", "vendor", "target", ".venv", "venv", "__pycache__", "coverage", ".turbo", ".git", ".skills"}
ALLOWED_COMMENTS = [re.compile(p) for p in [r"^#!", r"^///\s*<reference", r"^//go:", r"^#\s*-\*-.*coding", r"^/\*!?\s*@vite-ignore\s*\*/$", r"^--> statement-breakpoint$"]]
SCRIPT_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte", ".astro"}
REGEX_BEFORE = set("(,=:[!&|?{};+-*%<>~^") | {""}
REGEX_KEYWORDS = ("return", "typeof", "case", "in", "of", "delete", "void", "throw", "yield", "await")
SUPPRESSIONS = re.compile(
    r"eslint-disable|@ts-ignore|@ts-expect-error|@ts-nocheck|biome-ignore|\bnoqa\b|type:\s*ignore|pragma:\s*no cover"
    r"|//\s*nolint|@SuppressWarnings|#\[allow\(|#!\[allow\(|@phpstan-ignore|@psalm-suppress|#pragma warning disable"
    r"|\[SuppressMessage|//\s*ignore(_for_file)?:|istanbul ignore|c8 ignore|prettier-ignore|rubocop:disable|deno-lint-ignore"
)
TYPE_BYPASS = re.compile(r"\bas\s+unknown\s+as\b|\bas\s+any\b|:\s*any\b|<any>|\bas\s+never\b")
DOCS_ROOT = {"README.md", "BACKLOG.md", "AUDIT_BACKLOG.md", "DECISIONS.md", "designs", "reports", "archive"}
AUDIT_TYPES = {"FIX", "VERIFY", "DECIDE", "WATCH"}
TASK_SECTIONS = ["## 1. Goal", "## 2. Active Task", "## 3. Queued Tasks", "## 4. Waiting on User / Blockers"]


def starts_regex(before: str) -> bool:
    stripped = before.rstrip()
    return (stripped[-1:] in REGEX_BEFORE and not stripped.endswith(("++", "--"))) or stripped.endswith(REGEX_KEYWORDS)


SHELL = {".sh", ".bash", ".zsh"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_]\w*)\1")


def split_code(text: str, suffix: str) -> list[tuple[int, str, str]]:
    pieces: list[tuple[int, str, str]] = []
    code: list[str] = []
    line, i, size = 1, 0, len(text)
    slash = suffix in SLASH or suffix in MARKUP
    hashes = suffix in HASH
    blocks = suffix in BLOCK or suffix in MARKUP
    quotes = "\"'" if suffix in HASH | DASH else "\"'`"
    heredoc: str | None = None

    def flush() -> None:
        if "".join(code).strip():
            pieces.append((line, "code", "".join(code)))
        code.clear()

    def skip_to(end: int, kind: str | None) -> None:
        nonlocal i, line
        if kind:
            pieces.append((line, kind, text[i:end]))
        else:
            code.append("\"\"")
        line += text.count("\n", i, end)
        i = end

    while i < size:
        char = text[i]
        if char == "\n":
            flush()
            line += 1
            i += 1
            if heredoc:
                stop = re.compile(rf"^\t*{re.escape(heredoc)}$", re.MULTILINE).search(text, i)
                end = size if stop is None else stop.end()
                line += text.count("\n", i, end)
                i = end
                heredoc = None
            continue
        if suffix in SHELL and (match := HEREDOC.match(text, i)):
            heredoc = match.group(2)
            code.append(match.group(0))
            i = match.end()
        elif suffix == ".py" and text.startswith(('"""', "'''"), i):
            end = text.find(text[i:i + 3], i + 3)
            skip_to(size if end < 0 else end + 3, None)
        elif suffix in SCRIPT_SUFFIXES and char == "/" and text[i + 1:i + 2] not in ("/", "*") and starts_regex("".join(code)):
            j, in_class = i + 1, False
            while j < size and text[j] != "\n" and (in_class or text[j] != "/"):
                in_class = (in_class or text[j] == "[") and text[j] != "]"
                j += 2 if text[j] == "\\" else 1
            skip_to(min(j + 1, size), None)
        elif char in quotes and not (suffix in SHELL and text[i - 1:i] == "\\"):
            j = i + 1
            while j < size and text[j] != char and not (text[j] == "\n" and char != "`" and suffix not in SHELL):
                j += 2 if text[j] == "\\" and not (suffix in SHELL and char == "'") else 1
            skip_to(min(j + 1, size), None)
        elif blocks and text.startswith("/*", i):
            end = text.find("*/", i + 2)
            skip_to(size if end < 0 else end + 2, "comment")
        elif suffix in MARKUP and text.startswith("<!--", i):
            end = text.find("-->", i + 4)
            skip_to(size if end < 0 else end + 3, "comment")
        elif (
            (slash and text.startswith("//", i) and text[i - 1:i] != ":")
            or (hashes and char == "#" and not text.startswith("#[", i) and (i == 0 or text[i - 1] in " \t\n;(") and not (suffix in SHELL and text[i - 1:i] == "$"))
            or (suffix in DASH and text.startswith("--", i))
        ):
            end = text.find("\n", i)
            skip_to(size if end < 0 else end, "comment")
        else:
            code.append(char)
            i += 1
    flush()
    return pieces


def tracked_files(root: Path, staged: bool) -> list[Path]:
    command = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"] if staged else ["git", "ls-files"]
    output = subprocess.run(command, cwd=root, capture_output=True, text=True, check=True).stdout
    return [root / name for name in output.splitlines() if name and not set(Path(name).parts) & SKIP_DIRS]


def allowed(path: str, rule: str, allow: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, entry.split(" ")[0]) and (len(entry.split(" ")) == 1 or entry.split(" ")[1] == rule) for entry in allow)


def check_code(root: Path, files: list[Path], allow: list[str]) -> list[str]:
    problems: list[str] = []
    for path in files:
        suffix = path.suffix.lower()
        if suffix not in SOURCE or not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        is_test = bool(re.search(r"(^|/)(tests?|__tests__|spec)/|[._-](test|spec)\.", relative))
        for line, kind, piece in split_code(path.read_text(errors="replace"), suffix):
            stripped = piece.strip()
            if kind == "comment":
                if SUPPRESSIONS.search(stripped):
                    rule = "suppression"
                elif any(pattern.search(stripped) for pattern in ALLOWED_COMMENTS) or (line == 1 and stripped.startswith("#!")):
                    continue
                else:
                    rule = "comment"
                if not allowed(relative, rule, allow):
                    problems.append(f"{relative}:{line} {rule}: {stripped.splitlines()[0][:80]}")
            elif SUPPRESSIONS.search(piece) and not allowed(relative, "suppression", allow):
                problems.append(f"{relative}:{line} suppression: {stripped[:80]}")
            elif suffix in TYPESCRIPT and (match := TYPE_BYPASS.search(piece)) and not (is_test and "never" in match.group(0)) and not allowed(relative, "type-bypass", allow):
                problems.append(f"{relative}:{line} type-bypass: {stripped[:80]}")
    return problems


def check_task(root: Path, task_max: int) -> list[str]:
    task = root / "TASK.md"
    if not task.is_file():
        return []
    lines = task.read_text().splitlines()
    problems = [f"TASK.md: {len(lines)} lines, the limit is {task_max} (move done work to docs/archive)"] if len(lines) > task_max else []
    problems += [f"TASK.md: missing section '{section}'" for section in TASK_SECTIONS if section not in lines]
    return problems


def check_docs(root: Path) -> list[str]:
    docs = root / "docs"
    if not docs.is_dir():
        return []
    problems = [f"docs/{entry.name}: not allowed at the docs root (agentic standard §9.2)" for entry in docs.iterdir() if entry.name not in DOCS_ROOT and not entry.name.startswith(".")]
    for entry in (docs / "archive").glob("*") if (docs / "archive").is_dir() else []:
        if not re.fullmatch(r"COMPLETED_\d{4}_\d{2}\.md|\..*", entry.name):
            problems.append(f"docs/archive/{entry.name}: archive files are COMPLETED_YYYY_MM.md")
    for entry in (docs / "reports").glob("*") if (docs / "reports").is_dir() else []:
        if not re.fullmatch(r"\d{4}_\d{2}_[a-z0-9_]+\.md|benchmarks|\..*", entry.name):
            problems.append(f"docs/reports/{entry.name}: reports are YYYY_MM_<topic>.md")
    audit = docs / "AUDIT_BACKLOG.md"
    if audit.is_file():
        text = audit.read_text()
        if "## Counts" not in text:
            problems.append("docs/AUDIT_BACKLOG.md: missing '## Counts'")
        for number, row in enumerate(text.splitlines(), 1):
            cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
            if row.startswith("|") and len(cells) > 1 and re.fullmatch(r"[A-Z]+-\d+", cells[0]) and cells[1] not in AUDIT_TYPES:
                problems.append(f"docs/AUDIT_BACKLOG.md:{number} type '{cells[1]}' is not one of FIX, VERIFY, DECIDE, WATCH")
    decisions = docs / "DECISIONS.md"
    if decisions.is_file():
        for number, row in enumerate(decisions.read_text().splitlines(), 1):
            if row.startswith("## ") and not re.match(r"## ADR-\d{3,}: .+", row):
                problems.append(f"docs/DECISIONS.md:{number} headings are '## ADR-NNN: <title> (YYYY-MM-DD)'")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Language-independent checks of the agentic standard (§9, §13).")
    parser.add_argument("--staged", action="store_true", help="check only staged files")
    parser.add_argument("--skip-code", action="store_true", help="skip comments, suppressions and type bypasses (the project's own gate covers them)")
    parser.add_argument("--task-max", type=int, default=40)
    parser.add_argument("--allow", default="scripts/checks/rules-allow.txt", help="lines of '<glob> [rule]'; a gate file")
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    allow_file = root / args.allow
    allow = [line.strip() for line in allow_file.read_text().splitlines() if line.strip()] if allow_file.is_file() else []
    problems = [] if args.skip_code else check_code(root, tracked_files(root, args.staged), allow)
    problems += check_task(root, args.task_max) + check_docs(root)
    for problem in problems:
        print(problem)
    print(f"check-rules: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
