#!/usr/bin/env bash
set -euo pipefail

SKILLS_SOURCE="${HOME}/coding/skills"
ENFORCEMENT="${SKILLS_SOURCE}/agentic-engineering-standard/enforcement"
SCRIPTS="${SKILLS_SOURCE}/agentic-engineering-standard/scripts"
MODE="setup"
TARGET_DIR="."
FORCED_BACKEND=()
FORCED_FRONTEND=()
while [ $# -gt 0 ]; do
  case "$1" in
    --check) MODE="check" ;;
    --backend) FORCED_BACKEND+=("$2"); shift ;;
    --frontend) FORCED_FRONTEND+=("$2"); shift ;;
    *) TARGET_DIR="$1" ;;
  esac
  shift
done
cd "$TARGET_DIR"

if [ ! -d .git ] && ! git rev-parse --git-dir >/dev/null 2>&1; then
  CHILD_REPOS=()
  for child in */; do
    [ -d "${child}.git" ] && CHILD_REPOS+=("${child%/}")
  done
  if [ ${#CHILD_REPOS[@]} -gt 0 ]; then
    echo "$(pwd) is a folder of ${#CHILD_REPOS[@]} separate repositories: ${CHILD_REPOS[*]}. Setting up each one on its own; nothing is created in this folder."
    echo
    for child in "${CHILD_REPOS[@]}"; do
      args=()
      [ "$MODE" = "check" ] && args+=(--check)
      "$0" "${args[@]}" "$(pwd)/${child}"
      echo
    done
    exit 0
  fi
fi

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

Every agent (Claude Code, Codex, Cursor, Copilot, Gemini and others) follows `.skills/agentic-engineering-standard/HARD-RULES.md` and, before committing, reviews its diff against `.skills/agentic-engineering-standard/enforcement/REVIEW.md`.

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

POINTER="Read and follow AGENTS.md and .skills/agentic-engineering-standard/HARD-RULES.md before any change. Server code also follows .skills/backend-engineering-standard/SKILL.md, UI code .skills/frontend-engineering-standard/SKILL.md (read the matching sections before the first edit). Before committing, review the diff against .skills/agentic-engineering-standard/enforcement/REVIEW.md. Never push; the owner pushes."

create GEMINI.md <<'EOF' || true
@AGENTS.md
@.skills/agentic-engineering-standard/HARD-RULES.md
EOF

create .github/copilot-instructions.md <<EOF || true
${POINTER}
EOF

create .cursor/rules/standards.mdc <<EOF || true
---
description: Owner standards for every change
alwaysApply: true
---
${POINTER}
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

if [ ! -f scripts/checks/check-rules.py ]; then
  if [ "$MODE" = "check" ]; then MISSING+=("scripts/checks/check-rules.py (language-independent rule check)"); else mkdir -p scripts/checks; cp "${SCRIPTS}/check-rules.py" scripts/checks/check-rules.py; chmod +x scripts/checks/check-rules.py; CREATED+=("scripts/checks/check-rules.py"); fi
elif ! cmp -s "${SCRIPTS}/check-rules.py" scripts/checks/check-rules.py; then
  MISSING+=("scripts/checks/check-rules.py is older than the skills copy: cp ${SCRIPTS}/check-rules.py scripts/checks/ (a gate file: the owner approves)")
fi
if [ -f AGENTS.md ] && ! grep -qs "HARD-RULES.md" AGENTS.md; then
  MISSING+=("AGENTS.md does not point other agents to .skills/agentic-engineering-standard/HARD-RULES.md and enforcement/REVIEW.md")
fi

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
block = (["\n"] if at else []) + [line + "\n"]
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

DETECTED=$(python3 "${SCRIPTS}/detect-project.py" .)
ECOSYSTEMS=$(python3 -c "import json,sys;print(', '.join(json.loads(sys.argv[1])['ecosystems']) or 'none detected')" "$DETECTED")
if [ ${#FORCED_BACKEND[@]} -gt 0 ] || [ ${#FORCED_FRONTEND[@]} -gt 0 ]; then
  BACKEND_DIRS=("${FORCED_BACKEND[@]}")
  FRONTEND_DIRS=("${FORCED_FRONTEND[@]}")
else
  mapfile -t BACKEND_DIRS < <(python3 -c "import json,sys;[print(p['dir']) for p in json.loads(sys.argv[1])['parts'] if 'backend' in p['roles']]" "$DETECTED")
  mapfile -t FRONTEND_DIRS < <(python3 -c "import json,sys;[print(p['dir']) for p in json.loads(sys.argv[1])['parts'] if 'frontend' in p['roles']]" "$DETECTED")
fi
for dir in "${BACKEND_DIRS[@]}"; do
  [ -n "$dir" ] && link_standard "$dir" backend-engineering-standard "Server rules"
done
for dir in "${FRONTEND_DIRS[@]}"; do
  [ -n "$dir" ] && link_standard "$dir" frontend-engineering-standard "UI rules"
done
if python3 -c "import json,sys;sys.exit(0 if json.loads(sys.argv[1])['workspace'] else 1)" "$DETECTED"; then
  link_standard . universal-enterprise-monorepo "Repository rules"
fi
if [ ${#BACKEND_DIRS[@]} -eq 0 ] && [ ${#FRONTEND_DIRS[@]} -eq 0 ]; then
  MISSING+=("no server or UI part detected: rerun with --backend <dir> and/or --frontend <dir> once the code exists")
fi

if ls .github/workflows/*.y*ml .gitlab-ci.yml .gitlab-ci.yaml .circleci/config.yml Jenkinsfile azure-pipelines.yml bitbucket-pipelines.yml >/dev/null 2>&1; then :; else
  MISSING+=("CI that runs the gates (templates in ${ENFORCEMENT}/ci: verify.yml for GitHub, gitlab-ci.yml, bitbucket-pipelines.yml, Jenkinsfile)")
fi
if grep -rqs "REPLACE_WITH_TOOLCHAIN\|Replace this step with the setup actions" .github .gitlab-ci.yml bitbucket-pipelines.yml Jenkinsfile 2>/dev/null; then
  MISSING+=("CI still has the template Toolchain step: replace it with the project's language setup")
fi
if [ ! -x scripts/gates.sh ]; then
  MISSING+=("scripts/gates.sh with 'staged' and 'ci' modes, called by both the pre-commit hook and CI (template: ${ENFORCEMENT}/templates/gates.sh)")
fi
if [ -f .husky/pre-commit ] || [ -f lefthook.yml ] || [ -f lefthook.yaml ] || [ -f .pre-commit-config.yaml ] || [ -x .git/hooks/pre-commit ]; then :; else
  MISSING+=("pre-commit hook running ./scripts/gates.sh staged (template: ${ENFORCEMENT}/templates/pre-commit)")
fi
if [ -f .husky/commit-msg ] || grep -qs "commit-msg" lefthook.y*ml .pre-commit-config.yaml 2>/dev/null || [ -x .git/hooks/commit-msg ]; then :; else
  MISSING+=("commit-msg hook, single-line Conventional Commit (template: ${ENFORCEMENT}/templates/commit-msg)")
fi
if ! grep -rqs "gitleaks\|trufflehog" .husky .pre-commit-config.yaml lefthook.y*ml .github .gitlab-ci.yml 2>/dev/null; then
  MISSING+=("secret scan (gitleaks) in the hook and CI")
fi
if ! ls cspell.json .cspell.json cspell.config.* >/dev/null 2>&1; then
  MISSING+=("jargon check: cspell with flagWords in the hook and CI (template: ${ENFORCEMENT}/templates/cspell.json; run with --report flagged)")
fi
case ",${ECOSYSTEMS}," in *typescript*)
  grep -rqs "no-floating-promises" --include='eslint.config.*' --include='.eslintrc*' --exclude-dir=node_modules --exclude-dir=.skills --exclude-dir=dist . 2>/dev/null \
    || MISSING+=("typescript: @typescript-eslint/no-floating-promises (ignoreVoid false) and no-misused-promises");;
esac
case ",${ECOSYSTEMS}," in *python*)
  ls mypy.ini pyrightconfig.json >/dev/null 2>&1 || grep -qs "tool.mypy\|tool.pyright" pyproject.toml \
    || MISSING+=("python: strict type checking (mypy --strict or pyright strict)");;
esac
case ",${ECOSYSTEMS}," in *go*)
  ls .golangci.y*ml >/dev/null 2>&1 || MISSING+=("go: golangci-lint with errcheck, depguard, forbidigo, noctx");;
esac
MISSING+=("for every rule of the standards, pick its gate for: ${ECOSYSTEMS} (${ENFORCEMENT}/GATES.md) and record it as an 'Enforced by:' line in AGENTS.md")

if ! cmp -s "${ENFORCEMENT}/managed-settings.json" /etc/claude-code/managed-settings.json 2>/dev/null \
  || ! cmp -s "${ENFORCEMENT}/hooks/guard.py" /etc/claude-code/hooks/guard.py 2>/dev/null \
  || ! cmp -s "${ENFORCEMENT}/hooks/session-check.py" /etc/claude-code/hooks/session-check.py 2>/dev/null \
  || ! cmp -s "${ENFORCEMENT}/hooks/inspection-log.py" /etc/claude-code/hooks/inspection-log.py 2>/dev/null; then
  OWNER+=("Install or update the managed layer (machine-wide): sudo install -d -m 755 /etc/claude-code/hooks && sudo install -m 755 ${ENFORCEMENT}/hooks/guard.py ${ENFORCEMENT}/hooks/session-check.py ${ENFORCEMENT}/hooks/inspection-log.py /etc/claude-code/hooks/ && sudo install -m 644 ${ENFORCEMENT}/managed-settings.json /etc/claude-code/managed-settings.json")
fi
if [ ! -e "$HOME/.claude/agents/standards-reviewer.md" ]; then
  OWNER+=("Link the reviewer agent: run ${SCRIPTS}/install-machine.sh")
fi
if git remote get-url origin >/dev/null 2>&1 || [ -n "$(git remote 2>/dev/null)" ]; then
  OWNER+=("On the remote: protect the default branch, require the CI check, require your review for .github/ changes")
fi
OWNER+=("Push yourself after reading the diff: ! git push")

echo "Project setup report ($(pwd), mode: ${MODE})"
echo "Detected: ${ECOSYSTEMS}; server parts: ${BACKEND_DIRS[*]:-none}; UI parts: ${FRONTEND_DIRS[*]:-none}"
echo
echo "Created (${#CREATED[@]}):"
for item in "${CREATED[@]}"; do echo "  + ${item}"; done
echo
echo "Still missing (${#MISSING[@]}):"
for item in "${MISSING[@]}"; do echo "  - ${item}"; done
echo
echo "Owner actions (${#OWNER[@]}):"
for item in "${OWNER[@]}"; do echo "  ! ${item}"; done
