---
name: backend-engineering-standard
description: |
  Universal, framework-agnostic backend engineering standards, architectural patterns, and quality laws.
  Covers Hexagonal (Ports & Adapters) architecture, strict layered separation (Controller -> Service -> Repository),
  structured logging with redaction, typed domain errors,
  consistent JSON envelopes, SOLID/DRY/KISS/YAGNI, PostgreSQL schema & migration hygiene, dynamic SQL safety,
  statement minimization & set-based query efficiency (Zero N+1 roundtrips), transactional outbox patterns,
  direct S3 streaming, tenant isolation, SSRF security, idempotency, startup reconciliation, and automated
  programmatic verification gates.
---

# Universal Backend Engineering Standard & Craftsmanship Specification

**Classification:** Global Backend Architectural Standard & Engineering Constitution  
**Target Environments:** Node.js (Fastify, NestJS, Express, Hono), Go, Rust, Python (FastAPI), TypeScript  
**Core Invariant:** Production-grade, zero-tech-debt backend architecture built for long-term maintainability, absolute type safety, and bulletproof security.

> **Domain Separation Notice:** This standard governs server code: architecture, API contracts, errors, persistence, caching, security and backend tests.
> * Agent process, verification strategy, git, task state, and the code rules shared by every language: **`agentic-engineering-standard`**.
> * UI craftsmanship: **`frontend-engineering-standard`**. Workspace topology and build pipelines: **`universal-enterprise-monorepo`**.

---

## 1. Backend Code Invariants

The code rules for every language and layer (zero comments, absolute type safety, zero suppression directives, plain naming) live in `agentic-engineering-standard` §13. The backend adds:

### 1.1 Structured Logging with Automated PII Redaction
* **The Rule:** Zero `console.log`, `console.warn`, or `console.error` in committed code.
* **Architecture:** Use a structured JSON logger (e.g. Pino, Winston, Zerolog).
* **Automated Redaction:** Pass all logs through an interceptor that automatically redacts sensitive keys:
  - Passwords, authorization tokens, session cookies, refresh tokens, credit card details, API keys, and personal identifiers (PII).


## 2. Hexagonal Architecture: Transports, Ports, and Adapters

Backend applications are organized into unidirectional layers from low-level infrastructure to domain logic and transport.

### 2.1 The Three Core Architectural Rings

| Ring | Responsibilities & Components | Import Direction Law |
| :--- | :--- | :--- |
| **1. Transport Layer (Edge / Inbound)** | Controllers, Route Handlers, Middlewares, Event Subscribers, DTO Request Validation | Imports downward into Application / Domain only. Never touches Repositories, database clients, or external SDKs directly. |
| **2. Domain Layer (The Hexagonal Core)** | Domain Services, Entities, Use Cases, State Machines, Ports | Pure business rules. Imports downward into Ports; completely decoupled from databases, HTTP frameworks, SDKs, and file systems. |
| **3. Infrastructure Layer (Adapters / Outbound)** | Repositories, Database Clients, S3 Adapters, Payment Adapters, Email SDKs | Implements Domain Ports against specific technologies. Reached strictly via dependency injection. |

### 2.2 Clean Layered & Modular Architecture (Infrastructure vs Modules)
To prevent technical details from polluting business domains, backend code is cleanly partitioned:
* **Infrastructure Layer (`@infra` / `infrastructure/`):** Pure technical adapters with zero business logic (`database`, `cache`, `storage`, `outbound-http`, `email`, `limits`, `metrics`, `health`).
  - **Hard Invariant:** Technical adapters MUST NEVER import business modules.
* **Domain Modules Layer (`@modules` / `modules/`):** Business logic organized into cohesive domain modules (e.g. `identity`, `billing`, `notifications`, `catalog`).
  - **Layer Direction DAG:** `common` ← `infrastructure` ← `core-domain` ← `feature-modules`.
  - Core modules define abstract ports; outer feature modules and technical adapters provide concrete implementations or register handlers.
  - Dependencies must form a strict Directed Acyclic Graph (DAG) with zero rings (`cycles = 0`).

### 2.3 One Responsibility per File Kind

| File Kind | Primary Responsibility | Hard Architectural Invariants |
| :--- | :--- | :--- |
| **Controller / Transport** | HTTP/protocol handling, DTO validation, status code mapping | Makes exactly **one domain service call** per route. Never imports repositories, touches databases, or holds business rules. |
| **Domain Service** | Use cases, domain rules, state transitions, port coordination | Never contains raw SQL text, database client instances, direct HTTP SDKs, or filesystem primitives. Reaches outside world strictly via Ports. |
| **Repository** | Sole persistence gate, queries, schema mapping | One repository per aggregate root. Maps database rows (`snake_case`) to domain models (`camelCase`). Never decides authorization or exposes raw query builders. |
| **Port (Interface / Abstract Class)** | Abstract contract declaring external capabilities required by domain | Pure contract with zero implementation code. Declared in `<module>.ports.ts` inside domain. |
| **Adapter** | Concrete technical implementation of a Port | Located in infrastructure layer (`@infra` or adapter subfolder). Can be swapped without touching a single line of business logic. |
| **DTO (Data Transfer Object)** | Transport wire shape and request input validation | Terminates strictly at the Controller. Never imported by or passed into domain services or repositories. |
| **Pure Util** | Deterministic calculations (tax math, slug formatting) | Pure functions with zero database, network, or file-system I/O. |

### 2.4 Strict SOLID Engineering Laws for Backend Services

1. **Single Responsibility Principle (SRP):**
   - Single responsibility is decided by **reasons to change** (actors, business use cases, cohesion), never by code length or line count.
   - A class or service serving two different business actors MUST be split into two separate classes.
2. **Open/Closed Principle (OCP):**
   - Domain features are open for extension but closed for modification.
   - Open variations (storage providers, payment gateways, notification channels, automation triggers) use a **Registry or Strategy Pattern** owned by the stable core module.
   - Exhaustive pattern matching over a closed, specified union type is acceptable without dynamic registries.
3. **Liskov Substitution Principle (LSP):**
   - Adapters MUST completely honor their Port's contract.
   - Swapping a concrete adapter (e.g. swapping an in-memory queue for BullMQ, or S3 storage for MinIO) must never break application invariants or alter domain behavior.
4. **Interface Segregation Principle (ISP):**
   - Consumers depend on small, role-specific, focused ports rather than monolithic "god-interfaces".
   - Split broad capabilities into granular ports (e.g. `UserReaderPort` and `UserWriterPort` rather than a single bloated `UserServicePort`).
5. **Dependency Inversion Principle (DIP):**
   - High-level business modules MUST NOT depend on low-level infrastructure modules; both depend on abstractions (Ports).
   - Abstractions MUST NOT depend on details; details depend on abstractions.

### 2.5 Strict DRY, KISS, YAGNI, and Separation of Concerns

* **DRY (Don't Repeat Yourself):**
  - Exactly one implementation per helper and one owner per concept.
  - Generic helpers live in the shared building-block layer (`common/`); domain helpers live in their owning module.
  - A type shared by multiple modules is declared once in the lowest common layer that needs it.
* **KISS (Keep It Simple):**
  - Choose the simplest design that satisfies the specification.
  - Zero indirection, speculative abstraction, or configurability without a present, documented need.
* **YAGNI (You Aren't Gonna Need It):**
  - Build only what the specification or active task requires today.
  - Zero speculative options, unused parameters, hypothetical hooks, or generic frameworks for imagined future cases. Future roadmap items live in roadmap plans, not in speculative production code.
* **Separation of Concerns (SoC):**
  - Cross-cutting concerns (logging, authentication, error mapping, metrics, request tracing) are handled by interceptors, filters, guards, and decorators—never duplicated in domain services.

### 2.6 Dependency Injection & Zero Global State

* **Constructor Injection Only:** All collaborators (services, repositories, ports) are received via class constructors or factory functions and bound in the dependency injection container.
* **Zero Service Instantiation:** Classes never instantiate their own collaborators using `new Service()`, `new Repository()`, or `new DatabaseClient()`.
* **Zero Global Mutable State:** Singletons with mutable properties are strictly forbidden. Pure helpers receive values as parameters.
* **Process Environment Access Rule:** Direct reads of `process.env` are restricted strictly to application bootstrap and dedicated configuration services. Services depend on injected configuration objects, never on direct environment reads.

### 2.7 CQRS Read-Side Separation for High-Performance Queries (Cross-Domain Reads)
While command/write paths strictly enforce domain aggregate boundaries through their owning domain services, high-throughput read operations (dashboards, consolidated views, exports, search grids) MUST NOT incur N+1 roundtrips by orchestrating multiple domain services in memory.
* **The Cross-Domain Read Law:** When an API response requires composite data owned by multiple modules, the reading module's repository is permitted to execute a single, read-only SQL join or sub-select across the relevant tables.
* **Invariants for CQRS Reads:**
  1. **Strictly Read-Only:** The reading repository MUST NEVER write, update, or delete data owned by another module.
  2. **Owned Projection Shape:** The query returns a plain, immutable read-model or DTO shape owned strictly by the reading module; it never returns or mutates another module's internal domain entity.
  3. **Stable Columns Only:** The query selects only columns documented as public/stable in the target module's schema contract.
  4. **Single-Statement Execution:** The composite projection must execute in a single SQL statement rather than multiple roundtrips.

---

## 3. Module Anatomy, Structure & File Discipline

### 3.1 The Single-File vs. Folder Rule (No Folders with 1 File)
* **Allowed Root Module Files:** A module root may contain ONLY:
  - `index.ts`
  - `<module>.module.ts`
  - `<module>.controller.ts`
  - `<module>.service.ts`
  - `<module>.repository.ts`
  - `<module>.interface.ts`
  - `<module>.ports.ts`
  - `<module>.errors.ts`
  - `<module>.constants.ts`
* **Single File at Module Root:** If a module has exactly **one** controller, service, or repository, it MUST live directly at the root of that module named after the module:
  - `<module>.controller.ts`
  - `<module>.service.ts`
  - `<module>.repository.ts`
* **Multi-File Layer Folders:** If and only if a module has **two or more** controllers, services, or repositories, they move into subdirectories (`controllers/`, `services/`, `repositories/`).
* **The Hard Invariant:** A layer folder MUST NEVER contain a single file. Having a folder with only 1 file inside is considered a design defect.
* **Naming:** Files inside subdirectories are kebab-case and named after the class they export (e.g. `services/order-notification.service.ts`).

### 3.2 Contract-Driven Decoupling & Shared Boundary Hygiene (The Anti-Barrel Trap Law)
An `index.ts` barrel that exports heavy runtime classes (`Controller`, `Service`, `Repository`, database pools) MUST NEVER be imported by sibling modules to consume shared artifacts. Bundling lightweight contracts with heavy runtime implementations creates circular dependency deadlocks and runtime `undefined` initialization crashes.

| 🔴 Banned (Composite Barrel Import) | 🟢 Mandatory (Direct Contract Import) | Why It Matters |
| :--- | :--- | :--- |
| `import { OrderStatus } from '../orders'` | `import { OrderStatus } from '../orders/orders.constants'` | Prevents loading heavy services/controllers |
| `import type { Order } from '../orders'` | `import type { Order } from '../orders/orders.interface'` | Pure compile-time import with zero runtime side-effects |
| `import { OrderPort } from '../orders'` | `import { OrderPort } from '../orders/orders.ports'` | Decouples abstract contract from concrete implementation |

* **The 5 Shared Contract Categories:**
  1. **Types & Interfaces (`<module>.interface.ts`):** Pure compile-time shapes (zero runtime JavaScript).
  2. **Ports & DI Tokens (`<module>.ports.ts`):** Abstract contracts and injection symbols declaring *what* capability is required.
  3. **Constants & Enums (`<module>.constants.ts`):** Shared discrete values (`OrderStatus.PAID`, regex validators, status unions, limits).
  4. **Domain Errors & Codes (`<module>.errors.ts`):** Machine-readable error codes and domain exceptions.
  5. **Pure Utility Functions (`<module>.util.ts`):** Deterministic helpers (tax math, slug generation) with zero database/network I/O.
* **Direct File Imports Across Boundaries:** When Module A needs any of the 5 shared contract categories from Module B, it MUST import directly from that specific contract file, NEVER from Module B's composite `index.ts` barrel.
* **Barrels Are Reserved for Composition Roots:** Module `index.ts` barrels exist strictly for the application composition root (dependency injection bootstrapping) and integration test harnesses. They are forbidden for inter-module feature communication.
* **Common Layer Elevation (DAG Invariant):** If a shared contract (constant, type, port, utility) is required by multiple independent domains, it must be elevated downward into a shared common/contracts layer (`packages/types`, `@shared/constants`, `@infra/ports`). Dependencies must always form a strict Directed Acyclic Graph (DAG) with zero rings.

### 3.3 The DTO Boundary Law (DTOs Terminate at the Controller)
* DTOs define HTTP wire format and input validation schemas only.
* **Hard Invariant:** DTOs strictly terminate at the Controller boundary:
  - Controllers validate request DTOs and map them to domain types.
  - Services, repositories, and utilities **MUST NOT import, export, or accept DTO classes or request DTO shapes**.
  - All domain service and repository parameters MUST be typed using pure domain types declared in `<module>.interface.ts`.

### 3.4 The Absolute Ban on Import & Export Aliasing
* Never rename imports or exports:
  - 🔴 `import { User as UserModel } from './user'` ➔ **BANNED**
  - 🔴 `export { Order as OrderEntity }` ➔ **BANNED**
* Entities, types, and services must be named cleanly and unambiguously at their declaration site so they never require aliasing at consumption points.

### 3.5 Minimal Export Surface (File-Private by Default)
* Nothing may be marked with `export` unless it is actively imported outside its declaring file.
* **Zero Speculative Exports:** Never export functions, constants, or types "just in case" or for imagined future callers (YAGNI). Unexported symbols stay file-private.
* **Zero Backward-Compatibility Exports:** Never preserve deprecated aliases or re-named types for backward compatibility.

---

## 4. Error Architecture, Contracts & Exceptions Catalogue

Every failure in domain logic MUST be expressed as a strongly-typed domain exception. Never throw generic `Error("...")`, raw strings, or framework-specific HTTP exceptions inside business services.

### 4.1 Base Domain Exception & The 13 Typed Subclasses

All domain exceptions inherit from a single abstract base class `DomainException` and map deterministically to standard HTTP status codes:

| Typed Domain Exception | HTTP Status | Purpose & Usage Example |
| :--- | :---: | :--- |
| `BadRequestDomainException` | `400` | Malformed request semantics, invalid query syntax, or illegal parameters |
| `UnauthorizedDomainException` | `401` | Missing, invalid, or expired authentication session / credentials |
| `ForbiddenDomainException` | `403` | Authenticated user lacks permission tier to execute action |
| `NotFoundDomainException` | `404` | Target record, module, or entity does not exist (or tenant non-disclosure) |
| `ConflictDomainException` | `409` | Duplicate unique constraint, concurrent modification, or slot full |
| `GoneDomainException` | `410` | Resource existed but has been permanently purged or expired |
| `PayloadTooLargeDomainException` | `413` | Request body, upload size, or bulk operation exceeds maximum cap |
| `ValidationDomainException` | `422` | Syntactically valid request failed domain semantic rules / constraints |
| `TooManyRequestsDomainException` | `429` | Rate limit quota exceeded; client must wait before retrying |
| `InternalDomainException` | `500` | Unexpected internal server failure (logged internally, sanitized for client) |
| `InvariantViolationException` | `500` | Critical assertion failure; **client message is strictly redacted** |
| `BadGatewayDomainException` | `502` | Upstream third-party integration failure (email, SMS, payment gateway) |
| `ServiceUnavailableDomainException` | `503` | Database pool exhausted, background worker queue busy, or maintenance mode |
| `ConfigurationError` | *Process Boot* | Missing environment variables or illegal startup wiring (halts bootstrap) |

### 4.2 Stable Machine-Readable Error Codes & 1:1 Mapping Law
* Every thrown error carries a stable, uppercase string code from the single shared error catalogue (`ERROR_CODES`).
* **Strict 1:1 Mapping:** Exactly one HTTP status per error code (never reuse an error code across different status codes).
* **The Client Branching Contract:** API clients, frontend apps, and SDKs **MUST branch on `code`**, NEVER on `message`.

### 4.3 Uniform JSON Error Envelope
Every error response emitted across all API surfaces strictly conforms to the uniform JSON envelope:

```json
{
  "statusCode": 400,
  "code": "FIELD_VALIDATION_FAILED",
  "message": "The provided fields failed validation checks.",
  "details": {
    "email": ["Email address is invalid"],
    "slug": ["Slug must contain only lowercase letters and hyphens"]
  },
  "requestId": "req_01JABC123DEF456",
  "timestamp": "2026-11-11T12:00:00.000Z",
  "path": "/api/v1/admin/records"
}
```

### 4.4 The Multi-Tenant Resource Non-Disclosure Law (404 over 403)
* When an authenticated user requests a resource belonging to another tenant or project, the API MUST return **`404 Not Found`** (`NotFoundDomainException`), NEVER `403 Forbidden`.
* **Why:** Returning `403 Forbidden` leaks confidential metadata by confirming to an attacker that the targeted resource ID actually exists in the database. Returning `404 Not Found` maintains complete tenant isolation and resource non-disclosure.

### 4.5 Invariant Violation Protection (Internal Query & Stack Redaction)
* Raw SQL queries, database credentials, internal file paths, column names, and stack traces MUST NEVER be leaked in HTTP responses.
* When unexpected runtime exceptions occur, catch them at the global exception filter, log the full error stack and SQL context internally alongside the unique `requestId`, and return a sanitized `INTERNAL_SERVER_ERROR` envelope with the tracking ID.

---

## 5. API Response Contracts, Tracing & Protocols

### 5.1 Standard Response Envelopes
All successful API responses adhere to standard wire envelopes:
* **Single Resource:**
  ```json
  {
    "data": {
      "id": "rec_01JABC",
      "title": "Universal Architecture",
      "slug": "universal-architecture",
      "version": 1
    }
  }
  ```
* **Collection / Paginated Query Results:**
  ```json
  {
    "data": [
      { "id": "rec_01JABC", "title": "First Item" },
      { "id": "rec_01JDEF", "title": "Second Item" }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 25,
      "total": 100,
      "totalPages": 4
    }
  }
  ```
* **Asynchronous Queued Operations (HTTP 202 Accepted):**
  ```json
  {
    "data": {
      "jobId": "job_01JXYZ",
      "status": "PENDING"
    }
  }
  ```

### 5.2 Request Correlation & Trace IDs (`req_...` & `X-Request-Id`)
* Every incoming HTTP request is assigned a globally unique `requestId` (prefixed `req_...`) generated at the edge gateway or root middleware.
* The `requestId` is bound to the async execution context (e.g. Node.js `AsyncLocalStorage`).
* The server attaches `X-Request-Id` to all outgoing HTTP response headers.
* The `requestId` is automatically injected into all structured log lines, error envelopes, and audit log entries for end-to-end trace correlation.

### 5.3 API Versioning & Explicit Routing Namespaces
All API routes should be explicitly versioned (e.g. `/api/v1`) and partitioned into clean access boundaries:
* **Public / Consumer APIs (e.g. `/api/v1/public` or `/api/v1/storefront`):** High-volume, heavily cached, read-optimized, or anonymous entry points.
* **Authenticated Customer APIs (e.g. `/api/v1/app` or `/api/v1/me`):** Scoped strictly to the authenticated user and tenant session.
* **Administrative / Operator APIs (e.g. `/api/v1/admin`):** High-privilege management endpoints with strict authorization and detailed audit logging.
* **Webhook Ingestion APIs (e.g. `/api/v1/webhooks`):** Signature-verified, idempotency-tracked inbound integration hooks.
* **Breaking Changes:** Breaking API modifications require incrementing the route version prefix (`/api/v2`) rather than mutating existing contracts in-place.

### 5.4 Tiered Rate Limiting
Tiered rate limiting is enforced via Redis across all API surfaces:
* **Authentication Endpoints:** Strict burst and sliding-window limits (e.g. 5 attempts / minute for login and password resets).
* **Public Endpoints:** Site-key and IP-scoped quotas (e.g. 600 requests / minute for public content; cache hits refund consumed quota).
* **Admin & Media Endpoints:** Protective caps on concurrent uploads and bulk operations.

### 5.5 Explicit Payload Caps (Strict 413)
* Explicit payload limits protect server memory and network buffers against denial-of-service:
  - JSON body maximum (e.g. 1 MB).
  - Rich text fields maximum (e.g. 500 KB).
  - Bulk operation item counts (e.g. max 100 items per bulk request).
* Endpoints immediately reject oversized payloads with **`413 PAYLOAD_TOO_LARGE`** before parsing complete payloads into memory.

### 5.6 Distributed Idempotency (`Idempotency-Key` Check-and-Set)
* All non-idempotent mutating HTTP endpoints (`POST /orders`, `POST /charges`, `POST /transfers`) must accept an `Idempotency-Key` header.
* Store the key in Redis or PostgreSQL with an atomic check-and-set operation:
  - **In-flight request:** If a duplicate key arrives while the initial request is processing, return `409 CONFLICT`.
  - **Completed request:** If a duplicate key arrives after completion, return the cached identical response without re-executing business logic.
* Background jobs enforce idempotency using composite unique execution keys: `(jobId, targetVersion)`. If already executed, the job resolves as a no-op success.

### 5.7 Direct-to-Storage Presigned Uploads (Zero Memory Buffering)
* **The Rule:** Application web servers must NEVER buffer uploaded file payloads in server memory or temporary disks.
* **The 4-Step Pattern:**
  1. Client requests a presigned upload URL from the API: `POST /api/v1/uploads/presign`.
  2. API validates file metadata (MIME type, size cap), generates a short-lived presigned PUT URL directly to object storage (S3/R2).
  3. Client uploads the binary payload directly from browser/app to object storage.
  4. Client notifies the API upon completion: `POST /api/v1/uploads/confirm`.

### 5.8 Outbound Resiliency, Strict Timeouts & Circuit Breakers
Any backend communication with external third-party services (payment gateways, transactional email, SMS, search indexes, external webhooks) MUST be guarded against cascading thread/connection exhaustion:
* **Non-Negotiable Timeouts:** Every outbound HTTP/RPC request MUST have an explicit, short connection timeout (target 2–3s) and read timeout (target 5–10s). Infinite or default 60s timeouts are strictly forbidden.
* **Fail-Fast Circuit Breaker Pattern:** When downstream external calls fail repeatedly (e.g. 5 consecutive 5xx responses or timeouts within 30 seconds), the circuit breaker MUST trip OPEN:
  - Immediately reject subsequent calls with `BadGatewayDomainException` (`502`) without opening network sockets or tying up server threads.
  - After a cooldown period (e.g. 30s), enter HALF-OPEN state, allowing a single probe request to check downstream recovery.
* **Retry Discipline:** Only retry idempotent HTTP methods (`GET`, `PUT`, `DELETE`). Non-idempotent `POST` requests MUST NOT be retried unless protected by a verified upstream idempotency key. Always use exponential backoff with full jitter to avoid the "thundering herd" problem.

---

## 6. Database & Persistence Hygiene

### 6.1 Database Schema Ownership & Managed Migrations
* **Versioned Migrations Only:** Database schema changes must be driven exclusively through version-controlled, journaled migrations (e.g. Drizzle, Prisma, Flyway, Goose, Alembic).
* **Never Ad-Hoc DDL:** Hand-installing SQL or running manual `ALTER TABLE` commands in production databases is strictly forbidden.
* **Relational Integrity Over Unstructured Blobs:** Relational entity data must be modeled into proper typed columns and indexes rather than opaque, unstructured JSON blobs whenever filtering, sorting, or relational integrity is required.

### 6.2 Standard Entity Audit & Lifecycle Columns
Every core business entity table in relational databases should carry standard lifecycle and concurrency columns:
1. `id`: Primary key (UUID v4/v7, nanoid, or ULID).
2. `version`: Monotonic integer incremented on every update (optimistic concurrency locking).
3. `status`: Explicit state machine enum (e.g. `ACTIVE`, `PENDING`, `ARCHIVED`).
4. `created_at`: `TIMESTAMPTZ` set on insert.
5. `updated_at`: `TIMESTAMPTZ` updated on every modification.
6. `deleted_at`: `TIMESTAMPTZ` nullable for soft deletes.

### 6.3 Units of Work, Database Transactions & The Short Transaction Bounds Law
* **Unit of Work Pattern:** Multi-table mutations must execute within an explicit transaction runner:
  ```typescript
  await repository.transaction(async (tx) => {
    await orderRepo.updateStatus(tx, orderId, 'PAID');
    await auditRepo.record(tx, auditEvent);
    await outboxRepo.insert(tx, outboxEvent);
  });
  ```
* **The Short Transaction Bounds Law (<100ms):**
  - Database transactions MUST be kept extremely short (target <100ms) to avoid connection pool starvation and lock contention.
  - **Zero Network I/O Inside Transactions:** External HTTP calls, email dispatches, object storage uploads, and webhook deliveries are **strictly forbidden inside database transactions**.
  - Defer all external side-effects to the Transactional Outbox.

### 6.4 Append-Only Event Logs (Audit Trails & Outbox Tables)
* Historical records that must never be rewritten (audit logs, transactional outbox events, accounting ledgers) are strictly append-only.
* **Immutable Rows:** Append-only tables are written in the same transaction as the change they describe. They are never updated or deleted in place except via documented data retention policies.
* Current business state resides in normal relational tables, which remain the single source of truth.

### 6.5 The Transactional Outbox Pattern
Any domain mutation that triggers downstream side-effects (cache invalidation, transactional emails, webhooks, search indexing) MUST write an outbox event in the **exact same database transaction** as the mutation:

```sql
BEGIN;
UPDATE orders SET status = 'PAID' WHERE id = 'ord_123';
INSERT INTO audit_logs (entity_type, entity_id, action) VALUES ('order', 'ord_123', 'PAID');
INSERT INTO outbox_events (event_name, payload) VALUES ('order.paid', '{"orderId":"ord_123"}');
COMMIT;
```

An asynchronous background worker polls or listens for outbox events, dispatches the external side-effects with exponential retry backoff, and marks events as processed.

### 6.6 Race-Safe Concurrency: The OCC vs. PCC Decision Matrix
Concurrent writes must be governed by an explicit concurrency strategy matched to the contention profile:

| Concurrency Model | Mechanism & SQL Pattern | When to Use (Contention Profile) | Behavior on Collision |
| :--- | :--- | :--- | :--- |
| **Optimistic Concurrency Control (OCC)** | Monotonic `version` check:<br>`UPDATE tbl SET val = $1, version = version + 1 WHERE id = $2 AND version = $expected` | Low to medium contention (CMS articles, user settings, profile updates). | Zero DB lock overhead. If version changed, returns count 0 $\rightarrow$ throws `409 CONFLICT` (`ConflictDomainException`). |
| **Pessimistic Row-Level Locking (PCC)** | Explicit lock ordering:<br>`SELECT * FROM tbl WHERE id = $1 FOR UPDATE` | High contention, low tolerance for retries (financial wallet balances, flash-sale stock decrement). | Serializes concurrent transactions at row level. Targets must sort IDs deterministically (`ORDER BY id`) to prevent deadlocks. |
| **PostgreSQL Advisory Locks** | Logical namespace lock:<br>`SELECT pg_advisory_xact_lock(hashtext('counter_' \|\| $1))` | Monotonic counter allocation, sequential invoice/receipt IDs, background job single-flighting. | Serializes tasks across application instances without taking heavy table-wide schema or row locks. Automatically released on transaction end. |

### 6.7 Dynamic SQL Safety (Zero Injection Surface)
* Every dynamic query must use parameterized inputs:
  - Dynamic identifiers (table names, column names) MUST pass through a strict identifier-quoting / allowlist sanitization helper (`quoteIdentifier(name)`).
  - Dynamic values MUST be passed as bound query parameters (`$1, $2, ?`).
  - Never concatenate untrusted strings or user inputs into SQL query text.

### 6.8 Strict Case Mapping
* **Database Columns:** Strictly `snake_case` (e.g. `order_total_cents`, `created_at`).
* **Application DTOs & Domain Models:** Strictly `camelCase` (e.g. `orderTotalCents`, `createdAt`).
* The repository layer deterministically transforms casing in both directions.

### 6.9 Soft Deletes & Partial Unique Indexes
* When soft deletes are supported (`deleted_at IS NOT NULL`), always use PostgreSQL partial unique indexes:
  ```sql
  CREATE UNIQUE INDEX idx_users_email_active ON users(email) WHERE deleted_at IS NULL;
  ```
  This ensures deleted records do not block active users from registering with the same unique identifier.

### 6.10 Forward-Only Migration Hygiene & Non-Destructive Schema Evolution
* **Forward-Only Migrations:** All schema changes ship as versioned, journaled migration files. Hand-installing SQL in databases is strictly forbidden.
* **Applied Migrations Are Immutable:** Never edit or rename a migration that has been merged or applied. Fix forward with a new compensating migration.
* **Destructive Change Safety:** Migrations must NEVER silently drop columns or tables containing production data. Dropping fields requires a 3-step migration plan:
  1. Deprecate and make nullable in code.
  2. Stop reading/writing in application code.
  3. Drop column in a subsequent migration after data backup.

### 6.11 Database Connection Management & Pool Telemetry
* Use a robust connection pool (e.g. `pg-pool`). Never create a new database connection per HTTP request.
* Monitor pool health metrics: pool size, active connections, waiting queue count, query latency, and connection error rates.

### 6.12 High-Efficiency Database Querying & The Statement Minimization Principle (Zero-N+1 Roundtrips Law)
In distributed cloud environments (AWS RDS, GCP Cloud SQL), network latency between the application server and the database is 1ms–3ms per roundtrip. Iterative row-by-row queries (RBAR) starve database connection pools and compound latency. Every repository implementation MUST adhere to the **Statement Minimization Principle**: consolidate operations into the minimal number of atomic SQL roundtrips using relational set operations.

1. **Set-Based Processing Over RBAR (Row-By-Agonizing-Row):**
   - **The Anti-Pattern (RBAR):** Iterating over an array in application code (`for (const item of items) { await db.query(...) }`). For $N$ items, this issues $O(N)$ network roundtrips.
   - **The Law:** Batch operations (inserts, updates, soft-deletes, restores, purges, reorders) MUST be $O(1)$ constant database statements regardless of batch size.
   - **Relational Set Primitives:** Use `unnest($1::uuid[], $2::int[])` or parameterized multi-row `VALUES` to join in-flight payloads directly into SQL statements:
     ```sql
     UPDATE target_table AS t
        SET status = 'ACTIVE', version = t.version + 1, updated_at = CURRENT_TIMESTAMP
       FROM unnest($1::uuid[]) AS batch(id)
      WHERE t.id = batch.id;
     ```

2. **Deterministic Lock Ordering for Multi-Row Mutations:**
   - Any multi-row update, delete, or lock MUST sort target identifiers deterministically (`ORDER BY id FOR UPDATE`):
     ```sql
     FROM (SELECT id FROM target_table WHERE id = ANY($1::uuid[]) ORDER BY id FOR UPDATE) AS locked
    WHERE t.id = locked.id;
     ```
   - **Why:** Eliminates concurrency deadlocks caused by two parallel transactions acquiring row locks in differing sequences.

3. **Composite Query Composition (CTE-Partitioned Page-With-Total Pattern):**
   - When returning paginated records alongside total item counts (`{ data, pagination: { total, totalPages } }`), NEVER issue two separate queries (`SELECT * ... LIMIT` followed by `SELECT count(*)`).
   - Consolidate data pagination and total counting into a single composite query using Common Table Expressions (CTEs) and an outer `LEFT JOIN`:
     ```sql
     WITH __page AS MATERIALIZED (
       SELECT *, row_number() OVER () AS __position FROM target_table WHERE deleted_at IS NULL LIMIT $1 OFFSET $2
     ), __page_count AS (
       SELECT count(*)::int AS total FROM target_table WHERE deleted_at IS NULL
     )
     SELECT __page.*, __page_count.total
       FROM __page_count LEFT JOIN __page ON true
      ORDER BY __page.__position;
     ```
   - **Zero-Row Guarantee:** If the query matches 0 rows or the offset exceeds the table size, `LEFT JOIN` guarantees that `total` is still returned with an empty record set rather than returning an empty row set with missing metadata.

4. **Correlated Subquery & JSON Aggregation (Composite Entity Projection):**
   - When loading an aggregate root with nested child entities (e.g. an Order with line items, payments, fulfilments, and refunds, or Shop Settings with credentials and shipping rules), avoid multiple roundtrips and avoid flat outer joins that duplicate parent row data ($M \times N$ Cartesian explosion).
   - Use PostgreSQL correlated subqueries with `json_agg` and `json_build_object`:
     ```sql
     SELECT o.*,
       COALESCE((
         SELECT json_agg(json_build_object('id', l.id, 'sku', l.sku, 'quantity', l.quantity))
         FROM order_lines l WHERE l.order_id = o.id
       ), '[]'::json) AS lines
     FROM orders o WHERE o.id = $1;
     ```
   - Projects aggregate root and child trees atomically in **1 single query roundtrip**.

5. **Atomic In-Place State Mutation (`UPDATE ... RETURNING ...`):**
   - Never issue a `SELECT` query solely to fetch the "before" state of an entity before applying an `UPDATE`.
   - Use PostgreSQL's `RETURNING` clause combined with `row_to_json()` to capture both pre-mutation and post-mutation state in one atomic step:
     ```sql
     UPDATE target_table AS t
        SET status = $2, version = t.version + 1, updated_at = CURRENT_TIMESTAMP
       FROM (SELECT * FROM target_table WHERE id = $1 FOR UPDATE) AS before
      WHERE t.id = before.id
     RETURNING t.*, row_to_json(before.*) AS __before, row_to_json(t.*) AS __after;
     ```
   - Provides full audit trail diffing, optimistic concurrency version bumping, and row locking in a single roundtrip.

6. **Exception-Driven Constraint Enforcement (EAFP over LBYL):**
   - **The Anti-Pattern (Look Before You Leap):** Running a preliminary `SELECT count(*) WHERE slug = $1` or `WHERE code = $1` to check for collisions before executing an insert or update. This introduces a Time-Of-Check-To-Time-Of-Use (TOCTOU) race condition and wastes an unnecessary roundtrip.
   - **The Law (Easier to Ask for Forgiveness than Permission):** Rely on database-level unique constraints and partial indexes. Execute the mutation directly; catch native unique constraint violations (`23505`), extract the colliding constraint name, and translate it into a typed `ConflictDomainException`.

7. **Sparse Multi-Table Existence Scanning (`UNION ALL EXISTS` Pattern):**
   - When verifying whether an entity (e.g. an uploaded media asset, a tag, or an option) is referenced across multiple polymorphic or dynamic tables before deletion, NEVER iterate over tables with sequential `SELECT 1` queries.
   - Compose a single multi-table existence query:
     ```sql
     SELECT 0 AS position WHERE EXISTS (SELECT 1 FROM table_a WHERE media_id = $1)
     UNION ALL
     SELECT 1 AS position WHERE EXISTS (SELECT 1 FROM table_b WHERE media_id = $1);
     ```
   - Returns all referencing tables in **1 single network roundtrip**.

8. **Bulk Parameter Budgeting & Memory Guardrails:**
   - Single-statement batching must never lead to unbounded memory allocation or PostgreSQL parameter exhaustion.
   - Relational parameter cap: PostgreSQL supports a maximum of 65,535 parameters per statement. Chunk large bulk inserts into maximum 500-row statement batches.
   - Enforce explicit DTO caps: All batch and bulk API endpoints MUST enforce `@ArrayMaxSize(100)` (or lower) to prevent query memory exhaustion.

---

## 7. Startup Reconciliation, Schema Drift & Health Probes

### 7.1 Application Boot Reconciliation Workflow
Never assume the database schema or background queues are in a valid state upon server boot. Before listening for incoming HTTP traffic, every backend service must execute an automated startup reconciliation check:
1. Verify database and cache connectivity.
2. Verify all pending migrations have been executed.
3. Compare metadata definitions against the physical database catalog to detect schema drift early.
4. Reconcile stuck background jobs (e.g. mark jobs abandoned by crashed pods from `RUNNING` back to `PENDING`).
5. Clear stale in-process cache entries.

### 7.2 Schema Drift Detection & Trapping
* Causes of drift: failed deployments, manual database adjustments, interrupted migrations, or restored backups.
* The migration or schema verification runner must be able to compare expected schema definitions against actual database catalog definitions and report `MATCHED` or `DRIFT_DETECTED` with specific remediation diffs.

### 7.3 Canonical Health Probes
Expose standard Kubernetes/cloud health endpoints:
* **`GET /health/live` (Liveness Probe):** Returns `200 OK` if the process is alive and event loop is responsive.
* **`GET /health/ready` (Readiness Probe):** Returns `200 OK` only when database pools are healthy, caches are connected, and startup reconciliation has succeeded. Returns `503 SERVICE_UNAVAILABLE` when dependencies are disconnected.

### 7.4 Graceful Process Shutdown & In-Flight Connection Drain
To support zero-downtime rolling deployments, processes MUST handle termination signals (`SIGTERM`, `SIGINT`) gracefully without terminating in-flight requests or corrupting transactions:
1. **Signal Interception:** On `SIGTERM`, immediately flip the readiness probe to return `503 SERVICE_UNAVAILABLE` so upstream load balancers / ingress controllers stop routing new traffic.
2. **In-Flight Drain Window:** Stop accepting new HTTP connections; allow in-flight HTTP requests to complete within a bounded drain period (target 15–30s timeout).
3. **Background Worker Pause:** Signal background job processors to stop picking up new jobs and allow active job steps to finish.
4. **Clean Resource Teardown:** Once HTTP and worker threads are idle, close database connection pools (`await pool.end()`), Redis clients, and file descriptors cleanly. Exit process with code `0`. If drain exceeds the hard timeout, force exit with code `1`.

---

## 8. Caching Strategy & Invalidation Pipelines

### 8.1 Read-Through Caching with Deterministic Cache Keys
* Cache query responses using deterministic keys incorporating tenant, version, and query hashes:
  `cache:v1:<tenantId>:<dataVersion>:<querySha256>`
* Set explicit TTLs (e.g. 600s) and maximum cached object size limits (e.g. 512 KB).

### 8.2 Event-Driven Cache Invalidation via Outbox & Version Bumping
* Cache invalidation is event-driven, not timer-dependent.
* When entity data or tenant configuration is modified, increment a monotonic entity/tenant version counter in the database.
* The version bump immediately invalidates all cached keys for that scope without requiring expensive cache-flush commands (`KEYS *` or `FLUSHDB`).

### 8.3 Short-Lived In-Memory Caches with Instant Mutation Purge
* In-process caches (e.g. session tokens, feature toggles) must have ultra-short TTLs (max 5 seconds).
* Database notification listeners (`LISTEN / NOTIFY` or Redis pub/sub) trigger instant purge of in-process caches upon state changes.

### 8.4 HTTP Cache-Control Semantics
* Authenticated endpoints and visitor sessions send:  
  `Cache-Control: private, no-store`
* Public asset downloads via signed redirects send:  
  `Cache-Control: public, max-age=60`

---

## 9. Security & Multi-Tenant Egress Isolation

### 9.1 Multi-Tenant Isolation at the Repository Boundary
* Every database query that accesses tenant data MUST be filtered by the tenant identifier (`tenant_id` / `project_id`) at the repository boundary:
  ```sql
  SELECT * FROM documents WHERE tenant_id = $1 AND id = $2;
  ```
* Tenant context is extracted from authenticated session tokens by middleware and passed through request contexts. It must never be accepted from unverified request body parameters.

### 9.2 Server-Side Request Forgery (SSRF) DNS Egress Filtering
* Any endpoint that fetches external URLs or dispatches webhooks MUST pass destination hostnames through a DNS pre-resolution filter before opening a network socket:
  - Block IPv4 loopbacks (`127.0.0.0/8`) and IPv6 loopbacks (`::1`).
  - Block RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
  - Block link-local addresses and cloud instance metadata endpoints (`169.254.169.254`, `fe80::/10`).
  - Block multicast and broadcast ranges.

### 9.3 Defense in Depth & Mass-Assignment Protection
* Controllers strictly map validated DTO fields to domain objects.
* Never pass raw unvalidated request bodies directly to database insert or update queries.
* Sensitive internal fields (`id`, `createdAt`, `tenantId`, `role`, `version`) are never updatable via generic update payloads.

---

## 10. Testing, Verification & Quality Gates

Test-driven process (red-green-refactor, regression-first fixes, behaviour names, zero flaky tests, tests outside `src/`) is defined in `agentic-engineering-standard` §10. The backend adds:

### 10.2 The Mandatory 6-Dimension Backend Test Matrix
Every backend feature MUST be covered across these 6 critical dimensions:
1. **Domain Business Logic:** Validates all state transitions, calculations, and invariants.
2. **Authorization & Access Boundaries:** Tests that role and permission checks enforce least privilege and access boundaries across user roles.
3. **Multi-Tenant Isolation:** Proves Tenant A cannot read, mutate, or soft-delete Tenant B's data under any circumstance.
4. **Dynamic SQL Injection Safety:** Tests query builders with hostile identifier and value payloads (SQL injection attempts).
5. **Schema & Migration Integrity:** Tests migrations against real PostgreSQL instances to prove forward compatibility.
6. **Error Contract Determinism:** Proves every domain exception serializes to its assigned machine-readable code and HTTP status.

### 10.3 Test Organization & Sandboxing Standards
* **Test Folders:**
  - `tests/unit/`: Pure logic, zero network, mock external ports.
  - `tests/integration/`: Real database tests using isolated schemas or testcontainers. Tests MUST NOT share mutable state or depend on run order.
  - `tests/e2e/`: Full HTTP API black-box requests.

### 10.4 Mandatory Runtime Boot Smoke Test
* Static compilation does not prove working software.
* Every backend service MUST be proven to boot cleanly in an automated smoke test script on an ephemeral port and successfully answer an HTTP probe (`GET /health/live`, `/health/ready`, `x-request-id`, unauthenticated probes) before any commit is accepted.

### 10.5 Backend Checks in the Pre-Commit Gate
Gate order and the targeted-versus-full rule: `agentic-engineering-standard` §4. Workspace commands: `universal-enterprise-monorepo` §7. The backend audit additionally proves:
1. Layer direction and zero module rings (§2), and no folder holding a single file (§3.1).
2. Database access and SQL text only in repositories, external I/O only in adapters (§2.3).
3. Every thrown error is a typed domain exception with a catalogued code (§4).
4. The boot smoke above passes.
