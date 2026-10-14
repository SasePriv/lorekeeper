# Gold Example: AGENTS.md

A real `AGENTS.md` from a FastAPI + Neo4j service, sanitized (internal
hostnames, identity-provider ids and tokens removed) and with the fixes that
an audit found applied: stale paths corrected, the docs list replaced by a
pointer to `docs/README.md`, and the structure tree reduced to packages.

Imitate its **shape and density**, not its content. The notes after the
example explain why each section is there.

---

````markdown
# AGENTS.md - graph-catalog-api

Backend REST API that manages a knowledge graph of digital products and
their relations, driven by an OWL ontology. Consumed by a Vue.js frontend
and by external projects through an API-key protected endpoint.

## Key Facts

- **Stack**: FastAPI + Neo4j (graph DB) + Redis (cache) + OWL ontology
- **Runtime**: Python 3.12+
- **Package manager**: uv (`pyproject.toml` at repo root)
- **Tooling**: Ruff (lint/format), pytest (test), custom migration CLI

## Non-negotiable Policies

### Git

**Never create a git commit without explicit confirmation from the user.**

Before committing:
1. Show the list of files that will be staged and the proposed commit message.
2. Wait for the user to say "go ahead", "commit", or equivalent explicit approval.
3. Only then run `git add` and `git commit`.

### Tests

Integration tests are **mandatory** for any CRUD change that touches
versioning, soft-delete, or relation lifecycle:

```bash
uv run pytest backend/tests/integration/ -v
```

Integration tests use `testcontainers`; no manual database setup is needed.

## Dev Commands

```bash
uv sync                                          # install all deps including dev
uv run ruff check --fix && uv run ruff format    # lint + format
uv run pytest                                    # all tests
uv run pytest -m unit                            # unit tests only
docker compose up                                # API (hot reload) + Neo4j + Redis
```

Migrations (from `backend/migrations/`):

```bash
cd backend/migrations
./migration.py status      # pending migrations
./migration.py upgrade     # apply all
./migration.py downgrade   # roll back the last one
```

Full local setup (devcontainer and docker compose workflows, auth, debugging):
`docs/local-development.md`.

## Critical Invariants

- **The OWL ontology is the single source of truth.** Entity types,
  properties and relations are derived at runtime; never hardcode an entity
  type (`backend/api/ontology/`).
- **Versioning is always active.** Every read of productive data must apply:

  ```cypher
  WHERE n.is_deleted = false AND n.is_latest = true
  WHERE r.is_current = true OR r.is_current IS NULL
  ```

- **Connectors are never persisted.** They are abstract OR-groups in the
  ontology; relations always point to concrete leaf types, resolved with
  `get_final_labels_from_connector()` (`backend/api/helper/relation_rules.py`).
  Children of a connector are cascade soft-deleted with their parent
  (`backend/api/crud/soft_delete.py`).

## Project Structure

```
backend/
├── api/
│   ├── crud/        # persistence: node CRUD, drafts, versioning, soft-delete (facade: crud_ols_graph.py)
│   ├── ontology/    # OWL parsing and structure
│   ├── routers/     # API endpoints
│   ├── schemas/     # Pydantic models
│   ├── services/    # business services (cache, audit, scope checks)
│   └── helper/      # pure logic: relation rules, diffs, Cypher filters
├── migrations/      # database migrations + CLI
└── tests/           # unit / integration / e2e
```

## Documentation Policy

- Docs live in `docs/`, **one document per topic**, indexed in
  [docs/README.md](docs/README.md). Read the index to find the doc for the
  area you are changing.
- Any behavior change updates the matching doc **in the same change**.
- Tech debt, inconsistencies and deprecations go to `docs/known-issues/`, one
  file per issue with a stable `KI-NNN` id, created with
  `python3 .agents/skills/docs-policy/scripts/ki.py new` (never edit its index
  by hand). Read only the Open table of `docs/known-issues/README.md`; other
  docs link the id only.
- Superseded docs and finished plans move to `docs/archive/`; never delete them.
- Documentation and code comments are written in **English**.
- Full rules, doc templates and the check script:
  `.agents/skills/docs-policy/SKILL.md`.

## Docs Index

See [docs/README.md](docs/README.md). Start there before reading or writing
any doc; it says which document to read for each kind of change.
````

---

## Why each section is there

- **Purpose paragraph**: lets an agent decide in two lines whether its
  assumptions about the project are right.
- **Key Facts**: prevents the most common wrong guesses (pip vs uv, Python
  version, which test runner).
- **Non-negotiable Policies**: concrete, checkable rules. "Never commit
  without confirmation" is followed; "be careful with git" is not.
- **Dev Commands**: copy-pasteable and verified. A wrong command here
  (for example a `cd` into a directory that no longer exists) fails on the
  first step, so every command must exist in a manifest, script or CI file.
- **Critical Invariants**: the only domain content in `AGENTS.md`. These
  are rules that corrupt data when forgotten (the mandatory Cypher filters),
  each pointing to the file that enforces it. Explanations stay in
  `docs/versioning-system.md`.
- **Project Structure**: packages and responsibilities only. File-level
  trees drift fastest and agents can list directories themselves.
- **Documentation Policy**: the short "what"; the "how" is in the vendored
  `docs-policy` skill, which travels with the repository. The known-issues
  registry is one file per issue: the original single file had grown to
  ~500 lines, 70% of it resolved history an agent had to load to see eight
  open issues. Its generated index costs a few hundred tokens instead.
- **Docs Index**: a pointer, not a list. A second list of docs in
  `AGENTS.md` drifts away from `docs/README.md` (the original version of
  this file omitted three active docs).

## Matching docs/README.md excerpt

```markdown
| Document | Type | Read when |
|---|---|---|
| [architecture.md](architecture.md) | cross-cutting | You need the big picture: components, cache, auth flow, environments |
| [versioning-system.md](versioning-system.md) | cross-cutting | You write or change any query or mutation on productive data |
| [draft-system.md](draft-system.md) | feature | You touch draft creation, submission, approval or promotion (`backend/api/crud/draft_service.py`, `draft_promotion.py`) |
| [roles-and-permissions.md](roles-and-permissions.md) | cross-cutting | You add an endpoint or change who can call one |
| [local-development.md](local-development.md) | runbook | You set up the project locally or change dev tooling |
| [known-issues/README.md](known-issues/README.md) | registry | You find tech debt or meet a `KI-NNN` reference (read the Open table only) |
```
