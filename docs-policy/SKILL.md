---
name: docs-policy
description: Keeps a repository's docs/ folder and AGENTS.md in sync with the code. One document per topic, typed documents (feature, cross-cutting, runbook, registry, plan), a known-issues registry with stable KI-NNN ids, archiving instead of deleting, and an automated path/link/index check. Use when implementing or changing behavior, adding or removing features, endpoints, data models, roles or dev commands, moving or renaming files, editing anything under docs/ or AGENTS.md, or discovering tech debt, inconsistencies or deprecations.
---

# Docs Policy

Documentation in this repository serves two readers: humans and AI agents.
`AGENTS.md` is always loaded and stays short; `docs/` holds one document per
topic and is loaded on demand through the index in `docs/README.md`.

## Core rules

1. **One document per topic.** Extend the existing doc for a topic instead of
   creating an overlapping one. Check `docs/README.md` first.
2. **Same change, same docs.** Any behavior change updates the matching doc in
   the same change. A change is not done while its doc is stale.
3. **Every active doc is indexed.** New docs get a row in `docs/README.md`
   with a "Read when..." description. `AGENTS.md` points to `docs/README.md`
   instead of keeping its own list.
4. **Files Reference is mandatory** in feature docs and is re-checked on every
   change: moved, renamed or split files must be updated there.
5. **Link known issues by id only.** Write `see KI-012`; never copy the
   description or severity of a known issue into another doc. Copies drift.
6. **Archive, never delete.** Superseded docs and finished plans move to
   `docs/archive/`. Active docs must describe the current system only.
7. **Document what the code and generated specs cannot say.** For APIs,
   document auth, side effects, cache invalidation and error causes; leave
   full request/response schemas to OpenAPI or equivalent.
8. **No manual "Last updated" fields.** Version control tracks dates; a manual
   date nobody updates gives false confidence.
9. **Invariants first.** Each feature doc starts with a short
   "TL;DR - Invariants" block: the rules that must never be broken, each with
   the file that enforces it. Rules critical enough to cause bugs everywhere
   also go in `AGENTS.md` under "Critical Invariants".
10. **Paths are repo-root-relative.** Write `backend/api/x.py`, not
    `api/x.py`. Paths in another repository start with that repository's
    name. Hypothetical paths in examples use placeholders
    (`tests/unit/test_<job>.py`) so they are not mistaken for real files.
11. **Language.** Follow the documentation language declared in `AGENTS.md`
    (English unless stated otherwise).

## Choosing the document type

Pick the type before writing. Full definitions and signals of
misclassification are in [doc-types.md](doc-types.md).

| Type | Use for | Template |
|---|---|---|
| Feature | A capability with lifecycle, API, rules, data model | [templates/feature-doc.template.md](templates/feature-doc.template.md) |
| Cross-cutting | Architecture, auth/permissions, versioning, conventions | [templates/cross-cutting-doc.template.md](templates/cross-cutting-doc.template.md) |
| Runbook / how-to | Local setup, operational procedures, admin tools | [templates/runbook.template.md](templates/runbook.template.md) |
| Registry | `known-issues.md` (append-only, stable ids) | Format below |
| Plan / log | Refactors, migrations, multi-phase projects | Free form; archive when finished |

## If you change X, update Y

| Change | Update |
|---|---|
| Add / change / remove an endpoint | Feature doc "API Contract"; permissions doc if auth changed |
| Change a data model, schema, index or query filter | Feature doc "Data Model"; `AGENTS.md` "Critical Invariants" if it is a mandatory filter or rule |
| Add or change a role or permission | Cross-cutting permissions doc; affected feature docs |
| Add a feature | New feature doc from the template + row in `docs/README.md` |
| Move, rename or split files | Every "Files Reference" and backticked path that mentions them (run the check below) |
| Change dev, test, lint or migration commands | `AGENTS.md` "Dev Commands" and the local-development runbook |
| Find tech debt, inconsistency or deprecation | New entry in `docs/known-issues.md` |
| Fix a known issue | Move the entry to "Resolved issues" with the fix reference |
| Finish a plan or refactor | Move its doc to `docs/archive/`; fold lasting decisions into the relevant doc's "Design Rationale" |

## Workflow when finishing a change

```
Docs checklist:
- [ ] Identified the topic doc(s) affected by this change (docs/README.md)
- [ ] Updated content, invariants and Files Reference
- [ ] Added/resolved known-issues entries if applicable
- [ ] New docs are indexed in docs/README.md
- [ ] doc_check.py passes with no errors
```

Run the check from the repository root (path of the vendored skill shown):

```bash
python3 .agents/skills/docs-policy/scripts/doc_check.py .
```

Fix every `ERROR`. Review each `WARN` and either fix it or silence a confirmed
false positive (pattern in `.doccheckignore` or
`<!-- doc-check: ignore -->` on the line). `INFO` items are suggestions, such
as plan-like docs that may need archiving.

## Known-issues registry

`docs/known-issues.md` has an "Open issues" and a "Resolved issues" section.
Each entry:

```markdown
### KI-NNN <severity> <Short title>

- **Location**: `path/to/file.py` (`function_name`).
- **Symptom**: What goes wrong and how it is observed.
- **Risk**: Impact if left unfixed.
- **Suggested fix**: Concrete next step.
- **Detected**: <Month Year>, <context>.
```

- Ids are sequential and never reused; take the highest existing id + 1.
- Severity: `🔴` critical, `🟡` medium, `🟢` low.
- On fix: move the entry to "Resolved issues" and append
  `- **Resolved**: <commit or PR reference>`.
- Newest entries go first within each section.

If the file does not exist, create it with a title, a one-paragraph purpose,
the severity legend, both sections and an "Adding a new entry" section that
repeats the rules above.

## Archiving

1. Move the file to `docs/archive/` (keep its name).
2. Add at the top: `> **Archived**: <reason>. Current reference: [<doc>](../<doc>.md).`
3. Remove its row from `docs/README.md` and fix links that pointed to it.
4. Run `doc_check.py`.

Archived docs are never edited for accuracy and are excluded from checks.
