---
name: project-setup
description: Set up, repair or audit any new or existing project, in any language and of any shape (backend, frontend, both, monorepo, or a folder of separate repositories), so the owner's standards and their enforcement apply to every rule and feature. Use when the owner says "setup project", "/project-setup", "apply my rules here", "check my setup", or when the session-start check says the project is not set up.
---

# Project setup

Brings a repository to the owner's standard and keeps it there. Every step follows `~/coding/skills/agentic-engineering-standard/HARD-RULES.md`; nothing here relaxes a rule to save tokens. Read `~/coding/skills/agentic-engineering-standard/enforcement/README.md` and `GATES.md` before step 4.

## Steps

1. **Report first.** In the repository root run `~/coding/skills/agentic-engineering-standard/scripts/setup-project.sh --check` and show the report. In a folder of separate repositories the script reports each one; set each up on its own. When detection misses or mislabels a part, rerun with `--backend <dir>` and `--frontend <dir>` (repeatable).
2. **Scaffold what is missing.** Run the script without `--check`. It creates only missing files and inserts missing import lines; it never overwrites `SPEC.md`, `AGENTS.md`, `CLAUDE.md` or any other file. It also creates the pointer files other agents read (`GEMINI.md`, `.github/copilot-instructions.md`, `.cursor/rules/standards.mdc`) and copies the language-independent rule check to `scripts/checks/check-rules.py`.
3. **Move existing knowledge, losing nothing** (existing repositories). Per agentic standard §9.2 and §9.4: TODO lists, notes, audit lists, long task files, and other agents' instruction files (`.cursorrules`, `.cursor/rules/`, `.github/copilot-instructions.md`, `GEMINI.md`, `.windsurfrules`, an older `AGENTS.md`) are read in full. Rules go into `AGENTS.md`, the rest into their `docs/` homes in the mandatory schemas. Check afterwards that every rule, commit hash, item id, migration number and decision appears in its new home. Show the moves as a diff and wait for the owner's yes before deleting or rewriting any existing file.
4. **Fill the placeholders with facts, never guesses.**
   - **Commands:** read the manifests (`package.json`, `Makefile`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `composer.json`, `pubspec.yaml`, build files) and the README, run each command, and record only those that work.
   - **Patterns to copy:** search the code for the existing job or queue, email or message sender, HTTP client, repository or data access, transaction, list-with-total, error, and UI component patterns. List the file to copy for each, in `AGENTS.md` and in the directory `CLAUDE.md` of the part it belongs to. Leave a row out when the project has no such pattern yet, and say so.
   - **Spec:** a new project without a real `SPEC.md` gets one written with the owner before any feature work; an existing spec is read, never rewritten.
5. **Gates for every rule.** For each rule of the four standards and of the project's `AGENTS.md`, choose its gate from `GATES.md` for the detected languages and write an `Enforced by:` line next to the rule (`review` where no machine check exists yet). Then close each "Still missing" item with the owner, one at a time:
   - `scripts/gates.sh` from `enforcement/templates/gates.sh`, with `staged` and `ci` modes, wrapping the project's existing gate runner if it has one and calling `scripts/checks/check-rules.py` (with `--skip-code` when the project's own gate already checks comments and suppressions).
   - Pre-commit and commit-msg hooks from `enforcement/templates/` (or the project's Husky, lefthook or pre-commit equivalents) that call it.
   - CI from `enforcement/ci/` (GitHub, GitLab, Bitbucket or Jenkins) with the real toolchain in place of `REPLACE_WITH_TOOLCHAIN`.
   - Lint rules and custom checks: before turning one on, run it and tell the owner how many existing violations it reports; fix them or record each in `docs/AUDIT_BACKLOG.md` with the gate's allowlist naming them.
   - Gate, hook, lint, CI, dependency and permission files are protected: the guard asks the owner before each change. Show the diff first.
6. **Repositories the owner does not control** (a client's or a team's): keep the agent files local (gitignored) unless the repository already tracks them, propose gates and CI as a change for the repository's owners, and never change their branch rules.
7. **Commit** (after step 8) the project files with explicit paths after `git diff --stat`, in the project's commit format. Never push.
8. **Review:** run the `standards-reviewer` agent on the staged setup diff before the commit of step 7.
9. **Report:** what was created or moved, what is still missing and why, the gate table, the rules still enforced only by review, and the owner actions from the script, word for word.

## Running it again

Run `/project-setup` again after changing the skills repository, adding a new app or package, or switching a language: it only reports and adds what is missing, so it doubles as a drift check.
