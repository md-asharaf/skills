# Enforcing the standards on AI agents

Written rules alone are not enough: an agent can skip a rule it has not loaded, follow the nearest code instead, or edit a gate until it passes. This folder holds the layers that do not depend on the agent choosing to comply. Install all of them; each one covers gaps in the others.

| Layer | Who can change it | What it stops |
| :--- | :--- | :--- |
| 1. Managed settings (`/etc/claude-code`) | Only the owner, with sudo | Pushing, `--no-verify`, applying migrations, bypass mode; asks the owner before any edit to a gate, hook, lint, CI or permission file; injects the owner rules into every session |
| 2. Directory `CLAUDE.md` imports | Owner (protected by layer 1) | Backend or UI work without the matching standard in context |
| 3. Project gates (lint, typecheck, custom checks, pre-commit hook) | Owner (protected by layer 1) | Every rule a machine can detect, before the commit exists |
| 4. CI on the remote | Owner | Anything that slipped past the local hook, on a machine the agent never touches |
| 5. Review: the reviewer agent (the project's own, else `standards-reviewer`) before each commit, the owner before each push, both with `REVIEW.md` | Owner | Judgement rules no check can detect (wrong pattern, needless reads, unclear names) |

## Quick start

**Once per machine** (needs `git`, `python3`, Claude Code, and SSH access to `github.com:md-asharaf/skills`):

```bash
git clone git@github.com:md-asharaf/skills.git ~/coding/skills   # skip when it is already there
~/coding/skills/agentic-engineering-standard/scripts/install-machine.sh
```

Then run the sudo lines the installer prints (the managed layer), and start a new Claude Code session.

**In any project, what to type:**

| Situation | Type |
| :--- | :--- |
| New, empty folder | `/project-setup`, then describe the product so the agent writes `SPEC.md` with you before any feature work |
| Existing project, never set up (the session-start check says so) | `/project-setup` |
| Existing project, set up before; after changing the skills repository, adding an app, or a new language | `/project-setup` (it reports drift and adds only what is missing) |
| Folder holding several separate repositories | `/project-setup` in the folder (each repository is set up on its own) |
| Detection got a part wrong | `/project-setup --backend <dir> --frontend <dir>` |
| Someone else's repository (client or team) | `/project-setup`; agent files stay local, gates and CI are proposed to the repository's owners |
| Daily work after setup | Ask for the task in plain words. The rules, imports, hooks and gates apply on their own |
| After the agent commits | Read `git diff origin/main..HEAD`, then `! git push` |

The skills folder is shared by every project through the `.skills` link, so a change there reaches every project at once; rerun the managed-layer sudo lines when `managed-settings.json` or a hook changes (`setup-project.sh` and `install-machine.sh` tell you).

## 1. Install the managed layer (once per machine)

Run these yourself. The agent has no sudo, so it cannot change them afterwards.

```bash
sudo install -d -m 755 /etc/claude-code/hooks
sudo install -m 755 ~/coding/skills/agentic-engineering-standard/enforcement/hooks/guard.py ~/coding/skills/agentic-engineering-standard/enforcement/hooks/session-check.py ~/coding/skills/agentic-engineering-standard/enforcement/hooks/inspection-log.py /etc/claude-code/hooks/
sudo install -m 644 ~/coding/skills/agentic-engineering-standard/enforcement/managed-settings.json /etc/claude-code/managed-settings.json
```

Start a new Claude Code session and check with `/permissions` and `/hooks` that the managed rules and the three hooks are listed. When you change a file in this folder, run the same commands again: the copies in `/etc/claude-code` are what counts. `setup-project.sh` tells you when they are out of date. After any change to `guard.py`, run `hooks/guard_test.py`; every case must pass.

The session-start check (`hooks/session-check.py`) runs in every repository: when `.skills`, `TASK.md`, `AGENTS.md` or `docs/AUDIT_BACKLOG.md` is missing, it tells the agent to say so and offer `/project-setup` before any other work. It also reports drift: a managed layer older than this folder, unpushed skills commits, a project copy of `check-rules.py` older than the skills copy, and a `TASK.md` over 40 lines.

The inspection-log check (`hooks/inspection-log.py`) runs before every file edit: the first edit of a code file in a session, and the first after each compaction, is refused once with the rule text unless the conversation already holds a Primary Source Inspection Log naming a file. The retry goes through, so it can never lock the agent out; it puts the rule in front of the agent at the moment it matters. Run `hooks/inspection_log_test.py` after changing it.

What the guard does (`hooks/guard.py`, run before every shell command and file edit):

- **Denies:** `git push`, `--no-verify`, `git commit -n`, `HUSKY=0`, `core.hooksPath`, history rewrites (`filter-branch`, `filter-repo`), `drizzle-kit migrate` or `push`, bypass mode.
- **Asks you:** any write to a gate, hook, lint, CI or permission file or to an agent instruction file (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/`), by file edit or by shell, `git reset --hard`, `rebase`, `clean -f`, discarding changes, deleting branches, recursive `rm`, `psql`.

You push yourself after reading the diff: type `! git push` in the session, or push from your own terminal.

## 2. Load the standards by directory (once per project, done by `/project-setup`)

Agents read a folder's `CLAUDE.md` and `AGENTS.md` when working in that folder. Because the backend and frontend manuals are 23–50 KB each, keep directory files concise pointers with `grep -n '^##'` instead of `@`-expanding full `SKILL.md` files inline:

```markdown
<!-- apps/api/CLAUDE.md and apps/api/AGENTS.md -->
Read matching sections of `../../.skills/backend-engineering-standard/SKILL.md` (locate with `grep -n '^##'`) before the first edit.

<!-- apps/web/CLAUDE.md and apps/web/AGENTS.md -->
Read matching sections of `../../.skills/frontend-engineering-standard/SKILL.md` (locate with `grep -n '^##'`) before the first edit.
```

`.skills` is a gitignored symlink to `~/coding/skills`. Keep root `AGENTS.md` as a thin router (`<= 12 KB`): project facts, commands, keyword-only `SPEC.md` topic map (no line numbers, no decision summaries), and `Patterns to copy`. Keep `CLAUDE.md` importing `@AGENTS.md`, and keep `GEMINI.md` expanding only `@AGENTS.md` and `@.skills/agentic-engineering-standard/HARD-RULES.md` (staying under Antigravity's 24 KB limit) with plain pointers to full `SKILL.md` files. Every rule that a machine can check belongs in layer 3, not in prose.

## 3. Project gates (checklist)

A rule that a machine can check is a gate; a rule written only in a document is a request. Each project needs, in its pre-commit hook and in CI:

- Formatter and linter with zero warnings, typecheck of source and tests.
- Type-aware lint for promises: `@typescript-eslint/no-floating-promises` (with `ignoreVoid: false`) and `no-misused-promises`.
- Architecture checks: layer direction, no import cycles, responsibilities per file kind.
- Side-effect check: email, SMS, webhook and provider senders are called only from job handlers or adapters.
- Query checks: no awaited database call inside a loop in services and repositories, except entries in a reviewed allowlist file that is itself a gate file.
- The rules of the agentic standard §13 (no comments, no `any`, no suppressions).
- Commit message check.

Allowlists and gate configuration are gate files: the guard asks you before the agent changes them.

## 4. CI

Copy `ci/verify.yml` to `.github/workflows/verify.yml` (or `ci/gitlab-ci.yml`, `ci/bitbucket-pipelines.yml`, `ci/Jenkinsfile`), replace the `Toolchain` step with the project's languages, and keep the single `./scripts/gates.sh ci` step (`GATES.md`). Protect the default branch so the check must pass, and require your review for changes under `.github/`.

## 5. Owner review

Before each commit of server or UI code the agent runs the reviewer agent on the staged diff: the project's own in `.claude/agents/` when it defines one (it must follow `REVIEW.md` and only add project rules), else `standards-reviewer` (linked into `~/.claude/agents` by `install-machine.sh`) and fixes its blockers. Before every push, read `git diff origin/main..HEAD` (or the pull request) against the same `REVIEW.md`. Every problem found twice becomes a check in layer 3.

## Limits

- The guard matches command text. A determined command can hide a write (a script file it writes and runs later); layer 3 and layer 4 still run on whatever gets committed, and layer 5 reads it.
- Managed settings and the hooks bind Claude Code only. Other agents read `AGENTS.md` and their pointer files (`GEMINI.md`, `.github/copilot-instructions.md`, `.cursor/rules/standards.mdc`) and are held by layers 3 to 5.
- The inspection-log check reads the session transcript, which does not always keep the text written just before a tool call; that is why it reminds once instead of blocking every edit. It proves the reminder was shown, not that the log is good: review checks that.
- In auto mode, an "ask" from the guard may be approved by the mode's classifier instead of by you; use the default mode when gate files are being changed.
- No layer judges design. Review stays the owner's job.
