#!/usr/bin/env bash
set -euo pipefail

SKILLS_SOURCE="${HOME}/coding/skills"
ENFORCEMENT="${SKILLS_SOURCE}/agentic-engineering-standard/enforcement"
MODE="setup"
TARGET_DIR="."
for arg in "$@"; do
  case "$arg" in
    --check) MODE="check" ;;
    *) TARGET_DIR="$arg" ;;
  esac
done
cd "$TARGET_DIR"

MONTH=$(date +"%Y_%m")
MONTH_DASH=$(date +"%Y-%m")
TODAY=$(date +"%Y-%m-%d")
CREATED=()
MISSING=()
OWNER=()

create() {
  local path="$1"
  if [ -e "$path" ]; then return 1; fi
  if [ "$MODE" = "check" ]; then MISSING+=("$path"); return 1; fi
  mkdir -p "$(dirname "$path")"
  cat > "$path"
  CREATED+=("$path")
}

if [ ! -d .git ]; then
  if [ "$MODE" = "check" ]; then MISSING+=("git repository"); else git init -q; CREATED+=("git repository"); fi
fi

if [ ! -e .skills ]; then
  if [ "$MODE" = "check" ]; then MISSING+=(".skills link"); else ln -s "$SKILLS_SOURCE" .skills; CREATED+=(".skills -> $SKILLS_SOURCE"); fi
fi
if ! grep -qxE '\.skills/?' .gitignore 2>/dev/null; then
  if [ "$MODE" = "check" ]; then MISSING+=(".skills in .gitignore"); else printf '\n.skills\n' >> .gitignore; CREATED+=(".skills in .gitignore"); fi
fi

create AGENTS.md <<'EOF' || true
# AGENTS.md

Single entry point for every agent and contributor. Read once per session, then only the slices it points to.

## 1. Sources of truth (highest first)
1. `SPEC.md`: the product and system specification. Wins every conflict.
2. This file and `.skills/` (agentic, backend, frontend, monorepo standards).
3. Existing code: a pattern source only where it follows 1 and 2; code that breaks them is a defect, never a pattern.

Live state is `TASK.md`; read it first in every session.

## 2. Project commands
- Format and lint: <fill in>
- Typecheck: <fill in>
- Tests: <fill in>
- Pre-commit gate: <fill in>

## 3. Patterns to copy
| The change needs | Copy this file |
| :--- | :--- |
| <fill in as the project grows> | |

## 4. Stop and ask
Destructive data or schema actions, public contract changes, new dependencies or infrastructure, conflicting rules, gates that cannot both pass.

## 5. Memory
`TASK.md` (hot, at most 30 lines), `docs/BACKLOG.md`, `docs/AUDIT_BACKLOG.md`, `docs/DECISIONS.md`, `docs/designs/`, `docs/reports/`, `docs/archive/COMPLETED_YYYY_MM.md`, in the schemas of the agentic standard §9.2.
EOF

create CLAUDE.md <<'EOF' || true
@AGENTS.md

# Claude Code in this repository

Rules: `AGENTS.md`, `SPEC.md` and the standards in `.skills/`. Enforcement layers: `.skills/agentic-engineering-standard/enforcement/README.md`.
EOF

create TASK.md <<EOF || true
# Active Task State

**Last Updated:** ${TODAY}

## 1. Goal
<one line, from SPEC.md>

## 2. Active Task
- [ ] <step>

## 3. Queued Tasks
- Full backlog: \`docs/BACKLOG.md\`
- Open items: \`docs/AUDIT_BACKLOG.md\`

## 4. Waiting on User / Blockers
- None.
EOF

if [ ! -f SPEC.md ] && [ ! -f SPECS.md ]; then
  create SPEC.md <<EOF || true
# System Specification

**Version:** 0.1.0 (${TODAY})

## 1. Product overview
- Problem, users, core workflows

## 2. Architecture invariants
- Runtime and language
- Data persistence and transaction rules
- Public API contract and error envelope
EOF
fi

create docs/README.md <<'EOF' || true
# Project knowledge base

`BACKLOG.md` features and roadmap, `AUDIT_BACKLOG.md` open items, `DECISIONS.md` decisions, `designs/` blueprints, `reports/` point-in-time audits, `archive/` completed work by month.
EOF

create docs/BACKLOG.md <<'EOF' || true
# Product Backlog & Roadmap

## 1. Scheduled Phases
| Phase | Target | Scope | Design Doc |
| :--- | :--- | :--- | :--- |

## 2. Queued Features

## 3. Parked Ideas
EOF

create docs/AUDIT_BACKLOG.md <<'EOF' || true
# Audit Backlog

| ID | Type | Date | Source | Where | Summary |
| :--- | :--- | :--- | :--- | :--- | :--- |

## Counts
- FIX: 0 | VERIFY: 0 | DECIDE: 0 | WATCH: 0 | Total: 0
EOF

create docs/DECISIONS.md <<EOF || true
# Architecture Decision Records (ADRs)

## ADR-001: Agent rules and enforcement layers (${TODAY})
- **Context:** Agents skip written rules unless something outside them checks.
- **Decision:** Follow \`.skills\` standards; enforce through managed settings, directory imports, project gates, CI and owner review before push.
- **Rejected:** Rules in documents only.
- **Status:** Approved
EOF

create "docs/archive/COMPLETED_${MONTH}.md" <<EOF || true
# Completed Tasks — ${MONTH_DASH}

## 1. Completed Milestones & Commits

## 2. Closed Audit Items
| ID | Closed | Outcome | Commit | Summary |
| :--- | :--- | :--- | :--- | :--- |
EOF

for dir in docs/designs docs/reports; do
  if [ ! -d "$dir" ]; then
    if [ "$MODE" = "check" ]; then MISSING+=("$dir/"); else mkdir -p "$dir"; touch "$dir/.gitkeep"; CREATED+=("$dir/"); fi
  fi
done

link_standard() {
  local dir="$1" standard="$2" title="$3"
  [ -d "$dir" ] || return 0
  local rel
  rel=$(python3 -c "import os,sys;print(os.path.relpath(sys.argv[1],sys.argv[2]))" "$(pwd)/.skills/${standard}/SKILL.md" "$(pwd)/${dir}")
  local line="@${rel}"
  local file="${dir}/CLAUDE.md"
  if [ -f "$file" ] && grep -qF "$line" "$file"; then return 0; fi
  if [ "$MODE" = "check" ]; then MISSING+=("${file} import of ${standard}"); return 0; fi
  if [ -f "$file" ]; then
    python3 - "$file" "$line" <<'PY'
import sys
path, line = sys.argv[1], sys.argv[2]
lines = open(path).read().splitlines(True)
at = 1 if lines and lines[0].startswith("#") else 0
block = ["\n", line + "\n"]
if at >= len(lines) or lines[at].strip():
    block.append("\n")
lines[at:at] = block
open(path, "w").write("".join(lines))
PY
  else
    printf '# %s\n\n%s\n\nBefore the first edit of a task here, write the Primary Source Inspection Log in chat: the standard sections read and the existing file followed.\n' "$title" "$line" > "$file"
  fi
  CREATED+=("${file} import of ${standard}")
}

for dir in apps/api apps/server apps/backend api server backend services/api; do
  link_standard "$dir" backend-engineering-standard "Server rules"
done
for dir in apps/web apps/dashboard apps/admin apps/frontend apps/client web client frontend dashboard; do
  link_standard "$dir" frontend-engineering-standard "UI rules"
done

if ls .github/workflows/*.y*ml >/dev/null 2>&1; then :; else MISSING+=("CI workflow (template: ${ENFORCEMENT}/ci/verify.yml, fill in the project commands)"); fi
if [ -f .husky/pre-commit ] || [ -f lefthook.yml ] || [ -x .git/hooks/pre-commit ]; then :; else MISSING+=("pre-commit hook running the project gates"); fi
if [ -f package.json ] && grep -q '"typescript"' package.json 2>/dev/null; then
  if ! grep -rqs "no-floating-promises" eslint.config.* .eslintrc* 2>/dev/null; then
    MISSING+=("type-aware lint: @typescript-eslint/no-floating-promises with ignoreVoid false, and no-misused-promises")
  fi
fi

if ! cmp -s "${ENFORCEMENT}/managed-settings.json" /etc/claude-code/managed-settings.json 2>/dev/null \
  || ! cmp -s "${ENFORCEMENT}/hooks/guard.py" /etc/claude-code/hooks/guard.py 2>/dev/null \
  || ! cmp -s "${ENFORCEMENT}/hooks/session-check.py" /etc/claude-code/hooks/session-check.py 2>/dev/null; then
  OWNER+=("Install or update the managed layer (machine-wide): sudo install -d -m 755 /etc/claude-code/hooks && sudo install -m 755 ${ENFORCEMENT}/hooks/guard.py ${ENFORCEMENT}/hooks/session-check.py /etc/claude-code/hooks/ && sudo install -m 644 ${ENFORCEMENT}/managed-settings.json /etc/claude-code/managed-settings.json")
fi
if git remote get-url origin >/dev/null 2>&1 || [ -n "$(git remote 2>/dev/null)" ]; then
  OWNER+=("On the remote: protect the default branch, require the CI check, require your review for .github/ changes")
fi
OWNER+=("Push yourself after reading the diff: ! git push")

echo "Project setup report ($(pwd), mode: ${MODE})"
echo
echo "Created (${#CREATED[@]}):"
for item in "${CREATED[@]}"; do echo "  + ${item}"; done
echo
echo "Still missing (${#MISSING[@]}):"
for item in "${MISSING[@]}"; do echo "  - ${item}"; done
echo
echo "Owner actions (${#OWNER[@]}):"
for item in "${OWNER[@]}"; do echo "  ! ${item}"; done
