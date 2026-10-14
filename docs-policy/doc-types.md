# Document Types

Each document in `docs/` has exactly one type. The type decides its
template, its lifecycle and who reads it. Mixing types in one document is the
most common reason docs become stale or misleading.

## Feature

- **Purpose**: Describe one capability end to end: what it does, its states
  and transitions, its API contract, its rules and its data model.
- **Lifecycle**: Changes together with the code of the feature.
- **Readers**: Developers changing the feature; agents implementing changes.
- **Template**: [templates/feature-doc.template.md](templates/feature-doc.template.md)
- **Must have**: TL;DR - Invariants, Status, Files Reference.
- **Examples**: draft workflow, component transfer, audit log, background
  task framework.

## Cross-cutting

- **Purpose**: Describe a concern that spans many features: architecture,
  authentication and permissions, versioning, caching, conventions.
- **Lifecycle**: Changes rarely; every feature doc may link to it.
- **Readers**: Everyone, including non-developers for overview sections.
- **Template**: [templates/cross-cutting-doc.template.md](templates/cross-cutting-doc.template.md)
- **Must have**: Audience map (which sections are for whom), invariants.
- **Examples**: architecture, roles and permissions, versioning system.

## Runbook / how-to

- **Purpose**: Step-by-step procedures someone executes: local setup,
  backups and restores, migrations, admin tools, troubleshooting.
- **Lifecycle**: Changes when commands, environments or tooling change.
- **Readers**: Developers and operators performing a task right now.
- **Template**: [templates/runbook.template.md](templates/runbook.template.md)
- **Must have**: Prerequisites, copy-pasteable commands, expected results,
  warnings before destructive steps.
- **Examples**: local development, devtools reference.

## Registry

- **Purpose**: Append-only list of entries with stable ids that other docs
  link to.
- **Lifecycle**: Entries are added and moved between sections, never
  rewritten or renumbered.
- **Format**: See "Known-issues registry" in [SKILL.md](SKILL.md).
- **Examples**: `known-issues.md`.

## Plan / log

- **Purpose**: Track a project with a beginning and an end: a refactor, a
  migration, a test-suite reorganization.
- **Lifecycle**: Active while the project runs; **archived when it ends**.
  Lasting decisions are folded into the "Design Rationale" of the relevant
  feature or cross-cutting doc before archiving.
- **Readers**: The people executing the project.
- **Examples**: "Refactor: decomposing the CRUD god class", "Test structure
  migration plan".

## Signals of misclassification

| Signal | Likely problem | Action |
|---|---|---|
| Phases, checkboxes, "Next steps", "Progress log" in a doc listed as active | Plan/log living as reference | Archive it, or split lasting content into a feature/cross-cutting doc |
| "Status: complete" on a plan | Finished plan not archived | Archive it |
| A feature doc with long benefit lists or performance comparisons | Rationale outweighs reference | Move rationale to a short "Design Rationale" section |
| A feature doc with full request/response bodies for every endpoint | Duplicating OpenAPI | Keep only auth, side effects, errors, cache |
| Known-issue descriptions or severities copied into a feature doc | Registry duplication | Replace with `KI-NNN` links |
| A doc describing how things "will" work | Proposal mixed with reference | Mark Status as Proposed, or move to a plan doc |
