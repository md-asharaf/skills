---
name: project-setup
description: Set up or audit any new or existing project with the owner's standards and their enforcement (memory files in the mandatory schemas, directory imports of the backend and frontend standards, gates, CI, owner actions). Use when the owner says "setup project", "/project-setup", "apply my rules here", or when the session-start check says the project is not set up.
---

# Project setup

Brings a repository to the owner's standard in one pass. Every step follows `~/coding/skills/agentic-engineering-standard/HARD-RULES.md`; nothing here relaxes a rule to save tokens.

## Steps

1. **Report first.** Run `~/coding/skills/agentic-engineering-standard/scripts/setup-project.sh --check` in the repository root and show the owner the report.
2. **Scaffold what is missing.** Run the script without `--check`. It only creates missing files and inserts missing import lines; it never overwrites or truncates a file. `SPEC.md`, `AGENTS.md` and `CLAUDE.md` that already exist stay as they are.
3. **Existing repositories: move clutter losslessly.** Follow the agentic standard §9.2 and §9.4: scattered TODOs, notes, audit lists and long task files go to their `docs/` homes in the mandatory schemas. Zero details are dropped: check afterwards that every commit hash, item id, migration number and decision appears in its new home. Show the moves to the owner before deleting any old file.
4. **Fill the placeholders with facts, not guesses.**
   - Project commands in `AGENTS.md`: read `package.json`, `Makefile` or the equivalent, run each command, and write only the ones that work.
   - Patterns to copy: find the existing job or queue, email sender, repository, transaction and list-with-total patterns by searching the code, and list the file to copy for each. Leave a row out when the project has no such pattern yet.
   - In a repository whose `AGENTS.md` already exists, propose these additions as a diff and wait for the owner's yes.
5. **Close each "Still missing" item, one at a time, with the owner.**
   - CI: start from `~/coding/skills/agentic-engineering-standard/enforcement/ci/verify.yml` with the project's real commands.
   - Pre-commit hook: run the project's fast gates on staged files.
   - Lint rules: measure how many existing violations a new rule reports before turning it on, and tell the owner the count.
   - Gate, hook, lint, CI and permission files are protected: the guard asks the owner before each change. Show the diff first.
6. **Commit** the project files with explicit paths after `git diff --stat`, in the project's commit format. Never push.
7. **Report:** what was created, what is still missing and why, the gate table, and the owner actions from the script, word for word.

## Owner actions (the agent cannot do these)

- Install or update the managed layer with sudo (the exact command is in the report).
- Protect the default branch, require the CI check, require review of `.github/` changes.
- Push after reading the diff.
