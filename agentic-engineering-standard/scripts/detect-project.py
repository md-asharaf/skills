#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SKIP = {".git", "node_modules", "vendor", "dist", "build", "target", ".venv", "venv", ".next", ".turbo", "coverage", ".dart_tool", "Pods", ".skills"}
MAX_DEPTH = 3

FRONTEND_JS = {"react", "react-dom", "vue", "svelte", "@sveltejs/kit", "@angular/core", "next", "nuxt", "solid-js", "preact", "astro", "@remix-run/react", "expo", "react-native", "@builder.io/qwik", "lit"}
BACKEND_JS = {"@nestjs/core", "express", "fastify", "koa", "hono", "@hapi/hapi", "@adonisjs/core", "elysia", "@trpc/server", "@apollo/server"}
FRONTEND_RUST = re.compile(r"\b(yew|leptos|dioxus|tauri)\b")


def classify(directory: Path) -> tuple[set[str], set[str]]:
    roles: set[str] = set()
    ecosystems: set[str] = set()
    package = directory / "package.json"
    if package.is_file():
        try:
            data = json.loads(package.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = {}
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {}), **data.get("peerDependencies", {})}
        uses_ts = "typescript" in deps or (directory / "tsconfig.json").is_file()
        ecosystems.add("typescript" if uses_ts else "javascript")
        if FRONTEND_JS & deps.keys():
            roles.add("frontend")
        if BACKEND_JS & deps.keys():
            roles.add("backend")
    python_files = [directory / name for name in ("pyproject.toml", "requirements.txt", "setup.py", "Pipfile")]
    if any(path.is_file() for path in python_files):
        ecosystems.add("python")
        roles.add("backend")
    if (directory / "go.mod").is_file():
        ecosystems.add("go")
        roles.add("backend")
    cargo = directory / "Cargo.toml"
    if cargo.is_file():
        ecosystems.add("rust")
        roles.add("frontend" if FRONTEND_RUST.search(cargo.read_text(errors="ignore")) else "backend")
    if (directory / "pom.xml").is_file() or any(directory.glob("build.gradle*")):
        gradle = " ".join(p.read_text(errors="ignore") for p in directory.glob("build.gradle*"))
        ecosystems.add("jvm")
        roles.add("frontend" if "com.android.application" in gradle else "backend")
    if any(directory.glob("*.csproj")) or any(directory.glob("*.sln")):
        ecosystems.add("dotnet")
        roles.add("backend")
    if (directory / "composer.json").is_file():
        ecosystems.add("php")
        roles.add("backend")
    if (directory / "Gemfile").is_file():
        ecosystems.add("ruby")
        roles.add("backend")
    pubspec = directory / "pubspec.yaml"
    if pubspec.is_file():
        ecosystems.add("dart")
        roles.add("frontend" if "flutter:" in pubspec.read_text(errors="ignore") else "backend")
    if any(directory.glob("*.xcodeproj")) or (directory / "Package.swift").is_file():
        ecosystems.add("swift")
        roles.add("frontend")
    return roles, ecosystems


def is_workspace(root: Path) -> bool:
    if any((root / name).is_file() for name in ("pnpm-workspace.yaml", "turbo.json", "nx.json", "lerna.json", "go.work", "rush.json")):
        return True
    package = root / "package.json"
    if package.is_file():
        try:
            if "workspaces" in json.loads(package.read_text()):
                return True
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    cargo = root / "Cargo.toml"
    return cargo.is_file() and "[workspace]" in cargo.read_text(errors="ignore")


def ignored_names(root: Path, current: Path, dirs: list[str]) -> set[str]:
    if not dirs or not (root / ".git").exists():
        return set()
    rel = Path(current).relative_to(root)
    candidates = [str(rel / name) if str(rel) != "." else name for name in dirs]
    result = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "--stdin"],
        input="\n".join(candidates) + "\n",
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        return set()
    ignored = set()
    for line in result.stdout.splitlines():
        name = Path(line.strip()).name
        if name:
            ignored.add(name)
    return ignored


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    parts = []
    ecosystems: set[str] = set()
    for current, dirs, _files in os.walk(root):
        depth = len(Path(current).relative_to(root).parts)
        if depth < MAX_DEPTH:
            candidates = [d for d in dirs if d not in SKIP and not d.startswith(".")]
            ignored = ignored_names(root, Path(current), candidates)
            dirs[:] = [d for d in candidates if d not in ignored]
        else:
            dirs[:] = []
        roles, found = classify(Path(current))
        ecosystems |= found
        if roles:
            parts.append({"dir": str(Path(current).relative_to(root)) or ".", "roles": sorted(roles)})
    print(json.dumps({"workspace": is_workspace(root), "ecosystems": sorted(ecosystems), "parts": parts}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
