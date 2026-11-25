#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-.}"
cd "$TARGET_DIR"

CURRENT_MONTH=$(date +"%Y_%m")
CURRENT_DATE=$(date +"%Y-%m-%d")

echo "Initializing Universal Documentation and Memory System in: $(pwd)"

# 0. Initialize git repository if missing
if [ ! -d ".git" ]; then
  git init
  echo "Initialized git repository"
fi

# 1. Add .skills submodule if missing
if [ ! -d ".skills" ]; then
  echo "Adding .skills submodule (git@github.com:md-asharaf/skills.git)..."
  if git submodule add git@github.com:md-asharaf/skills.git .skills 2>/dev/null; then
    echo "Added .skills submodule via SSH"
  elif git submodule add https://github.com/md-asharaf/skills.git .skills 2>/dev/null; then
    echo "Added .skills submodule via HTTPS"
  else
    echo "Note: could not add .skills submodule automatically (network or git auth); configure manually if needed"
  fi
fi

# 2. Create directory structure
mkdir -p docs/designs docs/reports docs/archive
touch docs/designs/.gitkeep docs/reports/.gitkeep

# 2. Seed AGENTS.md (Agent Constitution & Rules)
if [ ! -f "AGENTS.md" ]; then
cat <<'EOF' > AGENTS.md
# AGENTS.md — Universal Agent Guide & Architecture Constitution

This file is the single entry point for every AI agent and contributor in this repository. Read it once per session, then read only the slices it points to.

---

## 1. Sources of Truth (Precedence Hierarchy)

| Tier | Source | Role |
| :--- | :--- | :--- |
| **1** | `SPEC.md` (or `SPECS.md`) | Primary product and system specification. Wins every conflict. Non-negotiable contract. |
| **2** | `.skills/` / Engineering Standards | Engineering standards (agentic, backend, frontend, monorepo). |
| **3** | Existing Codebase | Implementation reference. Code must adapt to the specification, never vice-versa. |

Live execution state lives in `TASK.md`. Read it first on every session start (< 500 tokens).

---

## 2. Non-Negotiable Core Invariants

1. **Zero Comments Policy:** No `//`, `/* */` in source code or test files. Code must be self-documenting through intention-revealing names, domain types, and pure modularization.
2. **Absolute Type Safety:** Zero `any` or untyped interface bypasses in application source code.
3. **Plain English Naming:** Zero technical buzzwords or jargon in domain types and public interfaces.
4. **Clean / Layered Architecture:** Strict unidirectional dependency flow (Transport -> Domain / Application -> Infrastructure).
5. **Zero Dual-Writes:** State mutations and asynchronous events must be committed within the same database transaction (Transactional Outbox).
6. **Honest Programmatic Verification:** Never declare a task complete without executing dynamic tests and quality gates with exit code 0.

---

## 3. Human-in-the-Loop Escalation (Stop and Ask)

The agent MUST pause and obtain explicit human confirmation before:
1. Running destructive database operations (DROP, TRUNCATE, irreversible migrations).
2. Modifying or breaking existing public API contracts or authentication flows.
3. Introducing new third-party libraries, services, or infrastructure dependencies.
4. When facing two contradictory requirements or an ambiguous architectural fork.

---

## 4. Universal Documentation & Memory Operating System

Every agent operates under a strict Hot vs Cold memory separation:

```text
Hot State (Live & Active):
└── TASK.md                     <-- Live state machine (<= 30 lines). Only Goal, Active Task, Immediate Queue, Blockers.

Cold State (Durable Knowledge):
├── SPEC.md (SPECS.md)          <-- Single Source of Truth for system architecture, schemas & contracts.
├── docs/DECISIONS.md           <-- Living Architecture Decision Records (ADRs). Why choices were made.
├── docs/BACKLOG.md             <-- Product feature backlog & long-term roadmap.
├── docs/AUDIT_BACKLOG.md       <-- Code smells, technical debt, and open audit queue.
├── docs/designs/               <-- Deep technical design specifications, RFCs & system blueprints.
├── docs/reports/               <-- Point-in-time audit reports, benchmark results & evaluations.
└── docs/archive/
    └── COMPLETED_YYYY_MM.md    <-- Monthly archive of completed tasks and commit hashes.
```

### Operational Rules for Agents:
1. **New Ideas & Features:** When a user suggests a new feature mid-session, append it to `docs/BACKLOG.md`. Never leave it in volatile chat memory.
2. **Audit Findings & Debt:** When an issue or code smell is noticed outside the active task, record it in `docs/AUDIT_BACKLOG.md`.
3. **Decisions & Design Choices:** When a design choice is agreed upon, record context, decision, and rejected alternatives in `docs/DECISIONS.md`.
4. **Deep Technical Blueprints:** Subsystem design proposals and RFCs belong in `docs/designs/`.
5. **Audits & Snapshots:** Point-in-time evaluations and audit reports belong in `docs/reports/` prefixed by date (`YYYY_MM_report_name.md`).
6. **Open Questions & Blockers:** When waiting for user input or facing an ambiguous decision, state it in `TASK.md` under `## 4. Waiting on User / Blockers` and prompt the user.
7. **Completed Tasks:** When a task is completed, record the commit in `docs/archive/COMPLETED_YYYY_MM.md` and immediately prune `TASK.md` to remain `<= 30 lines`.
EOF
echo "Created AGENTS.md"
fi

# 3. Seed CLAUDE.md
if [ ! -f "CLAUDE.md" ]; then
cat <<'EOF' > CLAUDE.md
@AGENTS.md

# Claude Code in this repository

This repository follows the autonomous agent governance defined in `AGENTS.md` and the universal engineering standards in `.skills/agentic-engineering-standard`.

## Master Sources of Truth
- Primary Product & System Specification: `SPEC.md` (wins every conflict).
- Architecture & Quality Standards: `AGENTS.md` and `.skills/`.
- Live Execution State Machine: `TASK.md` (strictly <= 30 lines).
- Universal Memory System: `docs/BACKLOG.md` (features), `docs/AUDIT_BACKLOG.md` (debt), `docs/DECISIONS.md` (ADRs), `docs/designs/`, `docs/reports/`, and `docs/archive/`.

## Quality Verification Commands
- Quick gate: targeted unit test / linter before file switches
- Full gate: test suite and build verification with exit code 0
EOF
echo "Created CLAUDE.md"
fi

# 4. Seed TASK.md (Hot State <= 30 lines)
if [ ! -f "TASK.md" ]; then
cat <<EOF > TASK.md
# Active Task State
**Last Updated:** ${CURRENT_DATE}

## 1. Goal
Initialize project foundation and core architecture per SPEC.md.

## 2. Active Task
- [ ] Setup initial project repository and dependencies
- [ ] Configure linting, formatting, and quality verification gates

## 3. Queued Tasks
- Core domain model implementation
- Full Backlog: docs/BACKLOG.md | Tech Debt: docs/AUDIT_BACKLOG.md

## 4. Waiting on User / Blockers
- None currently. Decisions archived in docs/DECISIONS.md.
EOF
echo "Created TASK.md"
fi

# 5. Seed SPEC.md (only if neither SPEC.md nor SPECS.md exists)
if [ ! -f "SPEC.md" ] && [ ! -f "SPECS.md" ]; then
cat <<EOF > SPEC.md
# System Specification & Architecture Contract

**Status:** Target Specification  
**Version:** 1.0.0 (${CURRENT_DATE})

## 1. Product Overview & Core Objectives
- Primary problem being solved
- Target users and core workflows

## 2. Architecture & Tech Stack Invariants
- Runtime environment & programming language
- Data persistence & transactional integrity rules
- Public API contract & error envelope conventions
EOF
echo "Created SPEC.md"
fi

# 6. Seed docs/BACKLOG.md
if [ ! -f "docs/BACKLOG.md" ]; then
cat <<EOF > docs/BACKLOG.md
# Product Feature Backlog & Roadmap

## 1. Future Roadmap & Milestones
- [ ] Milestone 1: Core System Foundation
- [ ] Milestone 2: Feature Implementation
- [ ] Milestone 3: Production Readiness & Quality Gates

## 2. Unscheduled Ideas (Inbox)
- Candidate features and user suggestions recorded mid-flight
EOF
echo "Created docs/BACKLOG.md"
fi

# 7. Seed docs/AUDIT_BACKLOG.md
if [ ! -f "docs/AUDIT_BACKLOG.md" ]; then
cat <<EOF > docs/AUDIT_BACKLOG.md
# Audit & Technical Debt Backlog

Open audit findings, code smells, and performance debt tracked for phased remediation.

| ID | Date | Component | Severity | Description |
| :--- | :--- | :--- | :--- | :--- |
| AUD-01 | ${CURRENT_DATE} | System | Low | Initial system baseline audit pending |
EOF
echo "Created docs/AUDIT_BACKLOG.md"
fi

# 8. Seed docs/DECISIONS.md
if [ ! -f "docs/DECISIONS.md" ]; then
cat <<EOF > docs/DECISIONS.md
# Architectural Decision Records (ADR) Log

Living record of architectural choices, trade-offs, and rationale.

## ${CURRENT_DATE} — Initial Architecture Bootstrap
- **Context:** Project initialization.
- **Decision:** Adopted Universal Documentation & Memory Operating System.
- **Reason:** Enforces hot-cold memory separation, prevents context bloat, and provides deterministic HITL coordination.
- **Rejected Alternatives:** Unstructured single-file documentation, chat-only memory.
EOF
echo "Created docs/DECISIONS.md"
fi

# 9. Seed docs/archive/COMPLETED_YYYY_MM.md
ARCHIVE_FILE="docs/archive/COMPLETED_${CURRENT_MONTH}.md"
if [ ! -f "$ARCHIVE_FILE" ]; then
cat <<EOF > "$ARCHIVE_FILE"
# Completed Tasks Archive — ${CURRENT_MONTH}

Monthly historical archive of completed milestones, closed remediation items, and git commit hashes.

| Commit | Date | Milestone / Task | Verification Status |
| :--- | :--- | :--- | :--- |
| initial | ${CURRENT_DATE} | Repository bootstrap and memory system setup | Verified |
EOF
echo "Created $ARCHIVE_FILE"
fi

echo "Universal Documentation and Memory System successfully initialized!"
