#!/usr/bin/env python3
import re
import sys
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2]
STANDARD = SKILLS_ROOT / "agentic-engineering-standard"
CHECKSUM = "5bc41815076e6ed6ef8fbecc9d9b75bcae31f39029ceb55da08086315316e3ba"
ASSET = "gitleaks_8.21.2_linux_x64.tar.gz"


def has_full_commit_pin(text: str) -> bool:
    actions = re.findall(r"^\s+-\s+uses:\s+(\S+)", text, re.MULTILINE)
    return bool(actions) and all(re.fullmatch(r".+@[0-9a-f]{40}", action) for action in actions)


def has_verified_archive(text: str) -> bool:
    download = text.find(ASSET)
    verify = text.find(CHECKSUM)
    extract = text.find("tar -x")
    return (
        download >= 0
        and verify > download
        and extract > verify
        and "sha256sum --check" in text
        and "gitleaks git" in text
    )


def main() -> int:
    template = (STANDARD / "enforcement/ci/verify.yml").read_text()
    shared = (SKILLS_ROOT / ".github/workflows/verify.yml").read_text()
    gitlab = (STANDARD / "enforcement/ci/gitlab-ci.yml").read_text()
    bitbucket = (STANDARD / "enforcement/ci/bitbucket-pipelines.yml").read_text()
    jenkins = (STANDARD / "enforcement/ci/Jenkinsfile").read_text()
    checks = [
        ("GitHub template has read-only token permissions", "permissions:\n  contents: read" in template),
        ("GitHub template pins checkout by commit", has_full_commit_pin(template)),
        ("GitHub template verifies Gitleaks before extracting", has_verified_archive(template)),
        ("GitHub Toolchain placeholder is quoted", "run: 'echo \"REPLACE_WITH_TOOLCHAIN:" in template),
        ("shared workflow has read-only token permissions", "permissions:\n  contents: read" in shared),
        ("shared workflow pins checkout by commit", has_full_commit_pin(shared)),
        ("shared workflow verifies Gitleaks before extracting", has_verified_archive(shared)),
        ("GitLab pins Gitleaks to a release", "gitleaks/gitleaks:v8.21.2" in gitlab),
        ("Bitbucket verifies Gitleaks before extracting", has_verified_archive(bitbucket)),
        ("Jenkins verifies Gitleaks before extracting", has_verified_archive(jenkins)),
    ]
    failures = [name for name, passed in checks if not passed]
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"{len(checks) - len(failures)}/{len(checks)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
