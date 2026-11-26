#!/usr/bin/env bash
set -euo pipefail

SKILLS_SOURCE="${HOME}/coding/skills"
SKILLS_REMOTE="git@github.com:md-asharaf/skills.git"
ENFORCEMENT="${SKILLS_SOURCE}/agentic-engineering-standard/enforcement"
DONE=()
TODO=()

command -v python3 >/dev/null || { echo "python3 is required (the hooks are Python). Install it and run again."; exit 1; }
command -v git >/dev/null || { echo "git is required. Install it and run again."; exit 1; }

if [ ! -d "$SKILLS_SOURCE/.git" ]; then
  mkdir -p "$(dirname "$SKILLS_SOURCE")"
  git clone "$SKILLS_REMOTE" "$SKILLS_SOURCE"
  DONE+=("cloned the skills repository to $SKILLS_SOURCE")
fi

for target in "$HOME/.claude/skills" "$HOME/.agents/skills"; do
  mkdir -p "$target"
  for skill in "$SKILLS_SOURCE"/*/SKILL.md; do
    name=$(basename "$(dirname "$skill")")
    if [ "$(readlink -f "$target/$name" 2>/dev/null)" != "$(readlink -f "$(dirname "$skill")")" ]; then
      ln -sfn "$(dirname "$skill")" "$target/$name"
      DONE+=("linked $name into $target")
    fi
  done
done

mkdir -p "$HOME/.claude/agents"
for agent in "$SKILLS_SOURCE"/agentic-engineering-standard/agents/*.md; do
  [ -f "$agent" ] || continue
  link="$HOME/.claude/agents/$(basename "$agent")"
  if [ "$(readlink -f "$link" 2>/dev/null)" != "$(readlink -f "$agent")" ]; then
    ln -sfn "$agent" "$link"
    DONE+=("linked the $(basename "$agent" .md) agent into ~/.claude/agents")
  fi
done

SKILLS_HOOK="$SKILLS_SOURCE/.git/hooks/pre-commit"
if ! grep -qs "check-skills.sh" "$SKILLS_HOOK"; then
  printf '#!/usr/bin/env bash\nexec "%s/agentic-engineering-standard/scripts/check-skills.sh"\n' "$SKILLS_SOURCE" > "$SKILLS_HOOK"
  chmod +x "$SKILLS_HOOK"
  DONE+=("installed the skills repository pre-commit check")
fi

GLOBAL="$HOME/.claude/CLAUDE.md"
IMPORT="@~/coding/skills/agentic-engineering-standard/HARD-RULES.md"
if ! grep -qF "$IMPORT" "$GLOBAL" 2>/dev/null; then
  mkdir -p "$(dirname "$GLOBAL")"
  printf '\n# Global rules (every project on this machine)\n\nAlways loaded: the hard rules below. Backend and frontend standards load through each project'"'"'s directory CLAUDE.md imports (run /project-setup in a project). Enforcement: %s/README.md.\n%s\n' "$ENFORCEMENT" "$IMPORT" >> "$GLOBAL"
  DONE+=("added the hard-rules import to $GLOBAL")
fi

SETTINGS_OUTPUT=$(python3 - "$HOME/.claude/settings.json" "$ENFORCEMENT" <<'PY'
import json, re, sys
from pathlib import Path
path, enforcement = Path(sys.argv[1]), Path(sys.argv[2])
managed = json.loads((enforcement / "managed-settings.json").read_text())
data = json.loads(path.read_text()) if path.is_file() else {}
before = json.dumps(data, sort_keys=True)
perms = data.setdefault("permissions", {})
perms["deny"] = sorted(set(perms.get("deny", [])) | set(managed["permissions"]["deny"]))
perms["ask"] = sorted(set(perms.get("ask", [])) | set(managed["permissions"]["ask"]))
hooks = data.setdefault("hooks", {})
def ensure(event, entry):
    present = hooks.setdefault(event, [])
    commands = {h.get("command") for e in present for h in e.get("hooks", [])}
    if entry["hooks"][0]["command"] not in commands:
        present.append(entry)
ensure("PreToolUse", {"matcher": "Bash|Edit|Write|NotebookEdit", "hooks": [{"type": "command", "command": str(enforcement / "hooks/guard.py"), "timeout": 10}]})
ensure("PreToolUse", {"matcher": "Edit|Write|NotebookEdit", "hooks": [{"type": "command", "command": str(enforcement / "hooks/inspection-log.py"), "timeout": 10}]})
ensure("SessionStart", {"hooks": [{"type": "command", "command": str(enforcement / "hooks/session-check.py"), "timeout": 10}]})
risky = re.compile(r"\bpush\b|filter-branch|filter-repo|git rebase|git reset|--no-verify|(npm|pnpm|yarn) (install|add) \*")
flagged = [rule for rule in perms.get("allow", []) if risky.search(rule)]
if json.dumps(data, sort_keys=True) != before:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    print("CHANGED")
for rule in flagged:
    print(f"REVIEW allow rule that weakens the guard: {rule}")
PY
)
if grep -q "^CHANGED$" <<<"$SETTINGS_OUTPUT"; then DONE+=("merged deny and ask rules and the three hooks into ~/.claude/settings.json"); fi
while IFS= read -r line; do
  [[ "$line" == REVIEW* ]] && TODO+=("$line")
done <<<"$SETTINGS_OUTPUT"

case "$(uname -s)" in
  Darwin) MANAGED_DIR="/Library/Application Support/ClaudeCode" ;;
  *) MANAGED_DIR="/etc/claude-code" ;;
esac
if ! sed "s#/etc/claude-code#$MANAGED_DIR#g" "$ENFORCEMENT/managed-settings.json" | cmp -s - "$MANAGED_DIR/managed-settings.json" 2>/dev/null \
  || ! cmp -s "$ENFORCEMENT/hooks/guard.py" "$MANAGED_DIR/hooks/guard.py" 2>/dev/null \
  || ! cmp -s "$ENFORCEMENT/hooks/session-check.py" "$MANAGED_DIR/hooks/session-check.py" 2>/dev/null \
  || ! cmp -s "$ENFORCEMENT/hooks/inspection-log.py" "$MANAGED_DIR/hooks/inspection-log.py" 2>/dev/null; then
  TODO+=("Install the root-owned managed layer (the agent cannot change it):")
  TODO+=("  sudo install -d -m 755 \"$MANAGED_DIR/hooks\"")
  TODO+=("  sudo install -m 755 \"$ENFORCEMENT/hooks/guard.py\" \"$ENFORCEMENT/hooks/session-check.py\" \"$ENFORCEMENT/hooks/inspection-log.py\" \"$MANAGED_DIR/hooks/\"")
  TODO+=("  sed \"s#/etc/claude-code#$MANAGED_DIR#g\" \"$ENFORCEMENT/managed-settings.json\" | sudo tee \"$MANAGED_DIR/managed-settings.json\" >/dev/null")
fi

echo "Machine setup"
for item in "${DONE[@]}"; do echo "  + $item"; done
[ ${#DONE[@]} -eq 0 ] && echo "  (already up to date)"
if [ ${#TODO[@]} -gt 0 ]; then
  echo
  for item in "${TODO[@]}"; do echo "$item"; done
fi
echo
echo "Then in any project, start Claude Code and type: /project-setup"
