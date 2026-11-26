#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BASE="$ROOT/agentic-engineering-standard"

python3 "$BASE/enforcement/hooks/guard_test.py"
for script in "$BASE"/scripts/*.sh; do bash -n "$script"; done
for script in "$BASE"/scripts/*.py "$BASE"/enforcement/hooks/*.py; do python3 -m py_compile "$script"; done
python3 -m json.tool "$BASE/enforcement/managed-settings.json" >/dev/null
for skill in "$ROOT"/*/SKILL.md; do
  head -1 "$skill" | grep -qx -- '---' || { echo "missing frontmatter: $skill"; exit 1; }
  grep -q '^name: ' "$skill" && grep -q '^description: ' "$skill" || { echo "name or description missing: $skill"; exit 1; }
done
echo "skills checks passed"
