#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

fill_in() {
  echo "scripts/gates.sh: fill in $1 with the project's commands (GATES.md), then remove this line" >&2
  exit 1
}

fast_gates() {
  fill_in fast_gates
}

all_gates() {
  fill_in all_gates
}

case "${1:-staged}" in
  staged)
    command -v gitleaks >/dev/null || { echo "gitleaks is not installed; install it to commit" >&2; exit 1; }
    gitleaks git --staged --redact --no-banner .
    python3 scripts/checks/check-rules.py --staged
    fast_gates
    ;;
  ci)
    python3 scripts/checks/check-rules.py
    all_gates
    ;;
  *)
    echo "usage: scripts/gates.sh staged|ci" >&2
    exit 2
    ;;
esac
