#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BASE="$ROOT/agentic-engineering-standard"

python3 "$BASE/enforcement/hooks/guard_test.py"
python3 "$BASE/enforcement/hooks/inspection_log_test.py"
python3 "$BASE/enforcement/hooks/session_check_test.py"
python3 "$BASE/scripts/check_rules_test.py"
python3 "$BASE/scripts/setup_project_test.py"
python3 "$BASE/scripts/workflow_policy_test.py"
python3 "$BASE/scripts/check-rules.py" "$ROOT"
for script in "$BASE"/enforcement/templates/gates.sh "$BASE"/enforcement/templates/pre-commit "$BASE"/enforcement/templates/commit-msg; do bash -n "$script"; done
for file in "$BASE"/enforcement/templates/*.json; do python3 -m json.tool "$file" >/dev/null; done
for agent in "$BASE"/agents/*.md; do head -1 "$agent" | grep -qx -- "---" && grep -q "^name: " "$agent" || { echo "agent frontmatter missing: $agent"; exit 1; }; done
for script in "$BASE"/scripts/*.sh; do bash -n "$script"; done
for script in "$BASE"/scripts/*.py "$BASE"/enforcement/hooks/*.py; do python3 -m py_compile "$script"; done
python3 -m json.tool "$BASE/enforcement/managed-settings.json" >/dev/null
for skill in "$ROOT"/*/SKILL.md; do
  head -1 "$skill" | grep -qx -- '---' || { echo "missing frontmatter: $skill"; exit 1; }
  grep -q '^name: ' "$skill" && grep -q '^description: ' "$skill" || { echo "name or description missing: $skill"; exit 1; }
done
echo "skills checks passed"
