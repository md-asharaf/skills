# Enforcing the standards on AI agents

Written rules alone are not enough: an agent can skip a rule it has not loaded, follow the nearest code instead, or edit a gate until it passes. This folder holds the layers that do not depend on the agent choosing to comply. Install all of them; each one covers gaps in the others.

| Layer | Who can change it | What it stops |
| :--- | :--- | :--- |
| 1. Managed settings (`/etc/claude-code`) | Only the owner, with sudo | Pushing, `--no-verify`, applying migrations, bypass mode; asks the owner before any edit to a gate, hook, lint, CI or permission file; injects the owner rules into every session |
| 2. Directory `CLAUDE.md` imports | Owner (protected by layer 1) | Backend or UI work without the matching standard in context |
| 3. Project gates (lint, typecheck, custom checks, pre-commit hook) | Owner (protected by layer 1) | Every rule a machine can detect, before the commit exists |
| 4. CI on the remote | Owner | Anything that slipped past the local hook, on a machine the agent never touches |
| 5. Owner review of every diff before push | Owner | Judgement rules no check can detect (wrong pattern, needless reads, unclear names) |

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
sudo install -m 755 ~/coding/skills/agentic-engineering-standard/enforcement/hooks/guard.py ~/coding/skills/agentic-engineering-standard/enforcement/hooks/session-check.py /etc/claude-code/hooks/
sudo install -m 644 ~/coding/skills/agentic-engineering-standard/enforcement/managed-settings.json /etc/claude-code/managed-settings.json
```

Start a new Claude Code session and check with `/permissions` and `/hooks` that the managed rules and both hooks are listed. When you change a file in this folder, run the same commands again: the copies in `/etc/claude-code` are what counts. `setup-project.sh` tells you when they are out of date. After any change to `guard.py`, run `hooks/guard_test.py`; every case must pass.

The session-start check (`hooks/session-check.py`) runs in every repository: when `.skills`, `TASK.md`, `AGENTS.md` or `docs/AUDIT_BACKLOG.md` is missing, it tells the agent to say so and offer `/project-setup` before any other work.

What the guard does (`hooks/guard.py`, run before every shell command and file edit):

- **Denies:** `git push`, `--no-verify`, `git commit -n`, `HUSKY=0`, `core.hooksPath`, history rewrites (`filter-branch`, `filter-repo`), `drizzle-kit migrate` or `push`, bypass mode.
- **Asks you:** any write to a gate, hook, lint, CI or permission file (by file edit or by shell), `git reset --hard`, `rebase`, `clean -f`, discarding changes, deleting branches, recursive `rm`, `psql`.

You push yourself after reading the diff: type `! git push` in the session, or push from your own terminal.

## 2. Load the standards by directory (once per project, done by `/project-setup`)

Claude Code loads a folder's `CLAUDE.md` when the agent works on files in that folder. Put the standard there, so it is in context without the agent having to remember it:

```markdown
<!-- apps/api/CLAUDE.md (or server/, backend/) -->
@../../.skills/backend-engineering-standard/SKILL.md

<!-- apps/web/CLAUDE.md (or client/, frontend/) -->
@../../.skills/frontend-engineering-standard/SKILL.md
```

`.skills` is a gitignored symlink to `~/coding/skills`. Keep the project's own `CLAUDE.md` and `AGENTS.md` short: project facts, the commands to run, and pointers to the pattern files to copy. Every rule that can be checked belongs in layer 3, not in prose.

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

Copy `ci/verify.yml` to `.github/workflows/verify.yml` (or the same three steps for GitLab, Bitbucket or Jenkins), replace the `Toolchain` step with the project's languages, and keep the single `./scripts/gates.sh ci` step (`GATES.md`). Protect the default branch so the check must pass, and require your review for changes under `.github/`.

## 5. Owner review

Before every push, read `git diff origin/main..HEAD` (or the pull request). Ask: did it follow the existing pattern, does it read anything twice, does any side effect skip the job queue, does any name need history to understand? Every problem found twice becomes a check in layer 3.

## Limits

- The guard matches command text. A determined command can hide a write (a script file it writes and runs later); layer 3 and layer 4 still run on whatever gets committed, and layer 5 reads it.
- Managed settings bind Claude Code only. Other agents are held by layers 3 to 5.
- No layer judges design. Review stays the owner's job.
