---
name: universal-enterprise-monorepo
description: |
  Universal, framework-agnostic architectural standard and orchestration playbook for enterprise monorepos.
  Covers multi-package workspace topologies, package dependency DAGs, pnpm/Turborepo/Nx orchestration,
  strict workspace protocol boundaries, anti-phantom dependency hoisting, shared configuration packages,
  remote build caching, and Docker container pruning. Use alongside backend-engineering-standard and
  frontend-engineering-standard for fullstack projects.
---

# Universal Monorepo Architecture & Workspace Orchestration Standard

**Classification:** Global Monorepo Architecture & Multi-Package Engineering Constitution  
**Target Environments:** pnpm workspaces, Turborepo, Nx, Bun workspaces, Yarn/npm workspaces  
**Core Invariant:** Strictly decoupled multi-package workspace topology with deterministic build caching, zero circular workspace dependencies, and zero phantom imports.

> **Domain Separation Notice:**  
> This standard governs multi-package monorepo workspace mechanics and build pipelines.  
> * For server architecture, persistence, hexagonal layering, and API design: consult **`backend-engineering-standard`**.  
> * For UI craftsmanship, design tokens, component primitives, and view lifecycles: consult **`frontend-engineering-standard`**.  
> * For AI agent governance, token discipline, memory state machines, and git rules: consult **`agentic-engineering-standard`**.

---

## 1. Monorepo Topology & Directory Anatomy

Enterprise monorepos are strictly partitioned into deployable applications (`apps/`) and reusable internal shared packages (`packages/`).

```text
.github/
  workflows/ci.yml          # Automated monorepo CI pipeline
.husky/
  pre-commit                # Root git hook executing verification gates
apps/
  api/                      # Backend Service (Node.js, Go, Python, Rust)
    src/
    tests/                  # Isolated tests (zero tests inside src/)
    package.json
  web/                      # Customer-Facing Web App (Next.js, Remix, Astro, Vue)
    src/
    package.json
  admin-dashboard/          # Operational / Back-office Admin UI (React/Vite, Next.js)
    src/
    package.json
  background-worker/        # Asynchronous Job & Event Consumer
    src/
    package.json
packages/
  types/                    # Pure compile-time contracts, DTO types, enums, API shapes
  database/                 # ORM schema, migrations, seeds, database connection client
  ui/                       # Shared design system primitives & components
  config-typescript/        # Base tsconfig configurations (base, node, react, library)
  config-eslint/            # Shared linter configurations & rule presets
  config-tailwind/          # Shared design tokens, theme configurations, CSS presets
  shared-utils/             # Pure deterministic utilities (formatting, math, validators)
scripts/
  verify-all.mjs            # Monorepo-wide programmatic quality gate runner
.npmrc                      # Package manager hoisting & peer dependency settings
docker-compose.yml          # Local infrastructure services (Postgres, Redis, MinIO)
package.json                # Monorepo root manifest
pnpm-workspace.yaml         # Workspace member definitions
turbo.json                  # Turborepo task pipeline orchestration
```

---

## 2. Workspace Boundary Laws & The Dependency Graph DAG

The dependency graph of a monorepo must be clean, deterministic, and strictly acyclic.

### 2.1 The Unidirectional Dependency Law (Apps -> Packages)
* **The Rule:** Deployable applications (`apps/*`) depend on and consume shared internal libraries (`packages/*`).
* **Hard Invariant:** Shared internal packages in `packages/*` **MUST NEVER import from `apps/*`**.
* Shared packages must remain completely agnostic of the applications that consume them.

### 2.2 The Internal Package DAG Law (Zero Cross-Package Cycles)
* Dependencies between packages in `packages/*` must form a strict Directed Acyclic Graph (DAG):
  $$\text{packages/ui} \longrightarrow \text{packages/types}$$
  $$\text{packages/database} \longrightarrow \text{packages/types}$$
  $$\text{apps/api} \longrightarrow \text{packages/database} \longrightarrow \text{packages/types}$$
* **Circular Dependencies Banned:** Circular dependencies between workspace packages (e.g. Package A depends on Package B, and Package B depends on Package A) are a fatal architectural flaw that causes build deadlocks and runtime initialization crashes.

### 2.3 Package Purity & Leaf Classifications

| Package Type | Directory Example | Allowed Dependencies | Prohibited Dependencies |
| :--- | :--- | :--- | :--- |
| **Shared Contracts** | `packages/types` | Zero dependencies (pure compile-time TypeScript contracts, constants, enums). | Must never import runtime libraries, database drivers, or UI frameworks. |
| **Tooling Configs** | `packages/config-typescript`, `packages/config-eslint` | Zero internal package dependencies (leaf packages). | Must never depend on domain packages or application code. |
| **Persistence Library** | `packages/database` | May depend on `packages/types` and database drivers / ORMs. | Must never depend on UI packages, HTTP frameworks, or frontend code. |
| **Design System** | `packages/ui` | May depend on `packages/types`, styling engines, and frontend primitives. | Must never depend on backend libraries, database clients, or server SDKs. |
| **Deployable App** | `apps/api`, `apps/web` | May depend on any required internal `packages/*` and runtime dependencies. | Must never be imported by another package or application. |

---

## 3. Package Manager & Workspace Protocol Discipline

Monorepos must eliminate phantom dependencies, duplicate version drift, and manual linking bugs.

### 3.1 Single Lockfile Authority
* The entire monorepo is governed by a **single root lockfile** (`pnpm-lock.yaml`, `bun.lockb`, or `yarn.lock`).
* Sub-workspaces must never have independent lockfiles.
* Never manually edit or hand-merge lockfile contents. Always regenerate lockfiles via package manager commands.

### 3.2 Explicit Workspace Protocol (`workspace:*`)
* All internal package dependencies must explicitly use the package manager workspace protocol:
  ```json
  {
    "dependencies": {
      "@repo/types": "workspace:*",
      "@repo/database": "workspace:*",
      "@repo/ui": "workspace:*"
    }
  }
  ```
* Never hardcode arbitrary semantic version strings (e.g. `"^1.2.0"`) for sibling packages inside the same monorepo.

### 3.3 Anti-Phantom Dependency Law (`shamefully-hoist=false`)
* **Phantom Dependency Anti-Pattern:** A workspace imports a package that is not declared in its own `package.json`, accidentally resolving it because a sibling workspace installed it and the package manager hoisted it to the root `node_modules`.
* **Enforcement via `.npmrc`:**
  ```ini
  shamefully-hoist=false
  strict-peer-dependencies=true
  auto-install-peers=true
  ```
* Every workspace MUST explicitly declare every direct third-party library and internal package it imports in its own `package.json`.

### 3.4 Single Version Policy (Catalog & Dependency Synchronization)
* Shared third-party dependencies (e.g. `typescript`, `react`, `zod`, `eslint`, `tailwindcss`, `vitest`) must resolve to identical versions monorepo-wide.
* Use pnpm Catalogs (`pnpm-workspace.yaml` `catalog:`) or synchronization tools (e.g. `syncpack`) to ensure zero version drift across workspaces:
  ```yaml
  # pnpm-workspace.yaml
  packages:
    - "apps/*"
    - "packages/*"

  catalog:
    typescript: "^5.5.0"
    zod: "^3.23.0"
    react: "^18.3.1"
  ```
  ```json
  // apps/web/package.json
  {
    "dependencies": {
      "react": "catalog:",
      "zod": "catalog:"
    }
  }
  ```

---

## 4. Task Orchestration Pipelines (Turborepo / Nx)

Monorepo task runners coordinate builds, tests, linters, and typechecks across workspaces with deterministic caching.

### 4.1 Topological Task Dependencies (`turbo.json`)
* Tasks declare dependency relationships to guarantee correct execution order:
  - `build` tasks must wait for upstream internal package dependencies to build first (`"dependsOn": ["^build"]`).
  - `test` and `lint` tasks can run in parallel across independent packages.

```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "inputs": ["src/**", "package.json", "tsconfig.json"],
      "outputs": ["dist/**", ".next/**", "!.next/cache/**", "build/**"]
    },
    "typecheck": {
      "dependsOn": ["^build"],
      "inputs": ["src/**", "tests/**", "tsconfig*.json"]
    },
    "lint": {
      "inputs": ["src/**", "tests/**", ".eslintrc*", "biome.json"]
    },
    "test": {
      "dependsOn": ["^build"],
      "inputs": ["src/**", "tests/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

### 4.2 Explicit Cache Inputs & Outputs
* **Deterministic Cache Keys:** Turborepo hashes inputs (source files, environment variables, dependencies) to calculate task cache keys.
* **Outputs Declaration:** Always declare task build outputs explicitly (`dist/**`, `build/**`). Omitting outputs prevents the task runner from replaying build artifacts from cache on subsequent runs.
* **Non-Cacheable Tasks:** Tasks that run continuously or interactively (e.g. `dev`, `watch`) MUST set `"cache": false` and `"persistent": true`.

### 4.3 Environment Variable Dependency Hashing
* If a build task depends on environment variables (e.g. `NEXT_PUBLIC_API_URL`), declare them in `turbo.json`:
  - `"env": ["NEXT_PUBLIC_API_URL", "DATABASE_URL"]`: Invalidate cache when these variables change.
  - `"globalEnv": ["NODE_ENV", "CI"]`: Variables that affect all tasks.
* Uncontrolled, undeclared environment variables lead to false cache hits serving stale configurations.

---

## 5. Shared Configuration Architecture

Tooling configurations must be declared once in `packages/config-*` and inherited by all workspaces to guarantee whole-codebase uniformity.

### 5.1 Shared TypeScript Configurations (`packages/config-typescript`)
Create composable, immutable tsconfig bases:
* `packages/config-typescript/base.json`: Strict compiler flags (`strict: true`, `noImplicitAny: true`, `exactOptionalPropertyTypes: true`).
* `packages/config-typescript/node.json`: Extends `base.json`, targeting Node.js runtimes (`module: NodeNext`, `moduleResolution: NodeNext`).
* `packages/config-typescript/react.json`: Extends `base.json`, targeting React/DOM environments (`jsx: react-jsx`, `lib: ["DOM", "DOM.Iterable", "ESNext"]`).

Workspaces extend the shared base directly:
```json
// apps/api/tsconfig.json
{
  "extends": "@repo/config-typescript/node.json",
  "compilerOptions": {
    "outDir": "./dist"
  },
  "include": ["src/**/*"]
}
```

### 5.2 Shared Linter & Formatter Presets
* Monorepos must share a single linter and formatter rule preset (`packages/config-eslint` or root `biome.json`).
* **Zero Per-Package Linter Fragmentation:** Individual workspace packages MUST NOT define conflicting custom linter rules that disagree with other workspaces. Every workspace in the monorepo speaks the exact same linting standard.

---

## 6. Monorepo CI Caching & Container Pruning

Monorepo CI pipelines must execute only affected workspaces and optimize container deployment builds.

### 6.1 Remote Caching in CI
* Connect the task runner to a remote cache (Turborepo Remote Cache, AWS S3, or self-hosted cache server).
* Pull requests that touch only `apps/web` will execute tests and builds for `apps/web` and its dependencies, immediately retrieving cached results for `apps/api` without redundant recompilation.

### 6.2 Docker Container Pruning (`turbo prune`)
* Building a Docker image for a specific app (e.g. `apps/api`) inside a monorepo must not copy the entire multi-gigabyte monorepo into the Docker context.
* **The Pruning Workflow:**
  1. Run `turbo prune --scope=api --docker` in a builder stage.
  2. This generates a pruned folder `out/`:
     - `out/json`: Package manifests and lockfile containing only `apps/api` and its internal dependency closure.
     - `out/full`: Source code for `apps/api` and its dependencies only.
  3. Install dependencies using `out/json` first to maximize Docker layer caching:
     ```dockerfile
     FROM node:20-alpine AS installer
     WORKDIR /app
     COPY --from=builder /app/out/json/ .
     RUN pnpm install --frozen-lockfile

     COPY --from=builder /app/out/full/ .
     RUN pnpm turbo run build --filter=api
     ```

---

## 7. Monorepo Verification & Audit Gates

Before merging code or deploying, the root monorepo quality gate must programmatically verify workspace integrity.

### 7.1 Monorepo Orchestration Commands
Root `package.json` scripts orchestrate the entire workspace:
* `pnpm build`: Runs `turbo run build` across all workspaces.
* `pnpm typecheck`: Runs `turbo run typecheck` across all workspaces (0 compiler errors).
* `pnpm lint`: Runs `turbo run lint` across all workspaces (0 linter warnings or errors).
* `pnpm test`: Runs `turbo run test` across all workspaces (100% test pass rate).
* `pnpm verify`: Executes the programmatic audit script (`node scripts/verify-all.mjs`).

### 7.2 Programmatic Monorepo Audit Checklist
The automated monorepo audit script MUST verify:
1. **Workspace Dependency Integrity:** No package depends on an undeclared workspace.
2. **DAG Validation:** No circular references exist between internal packages (`dpdm` cycle count = 0).
3. **No Cross-Layer Imports:** No internal package in `packages/*` imports from `apps/*`.
4. **Test Isolation:** Enforces `agentic-engineering-standard` §10.4 (zero test files inside any workspace's `src/`).
5. **Lockfile Sync:** The root lockfile is strictly in sync with all workspace `package.json` manifests (`pnpm install --frozen-lockfile` exits 0).
