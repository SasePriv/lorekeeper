---
name: docs-policy
description: Keeps a repository's docs/ folder and AGENTS.md in sync with the code. One document per topic, typed documents (feature, cross-cutting, runbook, registry, plan), a known-issues registry with stable KI-NNN ids (one file per issue, written through the ki.py CLI), archiving instead of deleting, and an automated path/link/index/drift check. Use when a change alters observable behavior (features, endpoints, data models, query filters, roles, permissions, dev/test/lint commands), moves, renames or deletes files, edits anything under docs/ or AGENTS.md, or uncovers tech debt, inconsistencies or deprecations. Not needed for internal refactors that keep behavior and file paths, test-only, formatting or lint changes.
license: MIT
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
12. **Split by cohesion, read by section.** ~300 lines is the signal to
    consider splitting a feature or cross-cutting doc, not a hard limit.
    Split when it holds independent subtopics (their own files and
    invariants, changed separately) and index each part. Keep it whole when
    its rules must be read together: keep the TL;DR and Table of Contents
    accurate, make every section self-contained, and put
    `<!-- doc-check: size-ok <reason> -->` at the top. When reading, start
    with "TL;DR - Invariants", then open only the section you need (grep its
    heading) instead of loading the whole doc.

## When no doc update is needed

- Internal refactors that change neither behavior nor file paths.
- Test-only changes, formatting and lint fixes.
- Dependency bumps that do not change any command.

Moving, renaming, splitting or deleting files is never in this list: every
"Files Reference" that mentions them must be updated, and the drift check
below reports the docs whose referenced files changed.

## Choosing the document type

Pick the type before writing. Full definitions and signals of
misclassification are in [doc-types.md](doc-types.md).

| Type | Use for | Template |
|---|---|---|
| Feature | A capability with lifecycle, API, rules, data model | [templates/feature-doc.template.md](templates/feature-doc.template.md) |
| Cross-cutting | Architecture, auth/permissions, versioning, conventions | [templates/cross-cutting-doc.template.md](templates/cross-cutting-doc.template.md) |
| Runbook / how-to | Local setup, operational procedures, admin tools | [templates/runbook.template.md](templates/runbook.template.md) |
| Registry | `docs/known-issues/` (one file per issue, stable ids) | [templates/known-issue.template.md](templates/known-issue.template.md), written by `ki.py` |
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
| Find tech debt, inconsistency or deprecation | `ki.py new`, then fill in the issue file |
| Fix a known issue | `ki.py resolve KI-NNN --ref <commit or PR>`, then describe the fix in "Resolution" |
| Finish a plan or refactor | Move its doc to `docs/archive/`; fold lasting decisions into the relevant doc's "Design Rationale" |

## Workflow when finishing a change

```
Docs checklist:
- [ ] Identified the topic doc(s) affected by this change (docs/README.md)
- [ ] Updated content, invariants and Files Reference
- [ ] Created/resolved known issues with ki.py if applicable
- [ ] New docs are indexed in docs/README.md
- [ ] doc_check.py --diff passes with no errors and every drift warning is reviewed
```

Run the check from the repository root (path of the vendored skill shown):

```bash
python3 .agents/skills/docs-policy/scripts/doc_check.py . --diff
```

`--diff` adds the drift check: a doc whose "Files Reference" lists a file
changed against `HEAD` (or against the merge base of `--diff <branch>`)
without the doc itself changing gets a `WARN`. Re-read that doc; update it,
or leave it as is if it is still accurate.

Fix every `ERROR`. Review each `WARN` and either fix it or silence a confirmed
false positive (pattern in `.doccheckignore` or
`<!-- doc-check: ignore -->` on the line). `INFO` items are suggestions, such
as plan-like docs that may need archiving or docs over the size budget.

## Known-issues registry

One file per issue plus a generated index:

```
docs/known-issues/
├── README.md     # generated by ki.py: Open table first, then Resolved
└── KI-NNN.md     # frontmatter (id, title, severity, status, location, detected, resolved_ref) + body
```

**Reading** (keep it cheap):

1. Read only the "Open" table of `docs/known-issues/README.md`. To find
   issues in the area you are changing, grep the index for its path.
2. Open a `KI-NNN.md` file only when the issue affects that code.
3. Resolved issues are history: open them only when a reference sends you there.

**Writing** always goes through the CLI, so ids and the index never drift
(`KI` below means `python3 .agents/skills/docs-policy/scripts/ki.py`):

```bash
KI new --title "Short title" --severity critical|medium|low --location path/to/file[,other/path]
KI resolve KI-NNN --ref <commit, MR or PR> [--note "What was changed"]
KI index            # only after editing an issue's frontmatter by hand
```

- `new` assigns the next id (never reused) and creates the file from the
  template. Fill in its `Symptom`, `Risk` and `Suggested fix` sections;
  `doc_check.py` warns while `TODO:` placeholders remain.
- `location` is repo-root-relative; open issues with stale locations are
  reported by `doc_check.py`.
- Never edit `docs/known-issues/README.md` by hand: `doc_check.py` fails when
  it does not match the issue files.
- Editing an issue's body needs no index update; only frontmatter changes do.

**Single-file registries.** Small repositories may keep the legacy single
file `docs/known-issues.md` ("Open issues" / "Resolved issues" sections, one
`### KI-NNN <emoji> <title>` entry each with **Location**, **Symptom**,
**Risk**, **Suggested fix** and **Detected** bullets). `doc_check.py`
supports both. To switch, run `KI migrate`: it splits the file into issue
files, archives the original as `docs/archive/known-issues.md` and lists the
references to update.

## Archiving

1. Move the file to `docs/archive/` (keep its name).
2. Add at the top: `> **Archived**: <reason>. Current reference: [<doc>](../<doc>.md).`
3. Remove its row from `docs/README.md` and fix links that pointed to it.
4. Run `doc_check.py`.

Archived docs are never edited for accuracy and are excluded from checks.
