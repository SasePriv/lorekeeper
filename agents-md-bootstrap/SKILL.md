---
name: agents-md-bootstrap
description: Generates, aligns or audits a repository's AGENTS.md and docs/ scaffold following a progressive-disclosure layout (short always-loaded AGENTS.md, one doc per topic under docs/, indexed by docs/README.md, known-issues registry). Asks the user for policies on every run, never invents commands or paths, and vendors the agents-md-bootstrap and docs-policy skills into the repository. Use when the user invokes /agents-md-bootstrap or asks to create, standardize, align or audit AGENTS.md or the docs structure of a project.
disable-model-invocation: true
---

# AGENTS.md Bootstrap

Sets up or realigns a repository so that agents and humans share the same
entry point:

- `AGENTS.md`: short, always loaded. Facts, policies, commands, critical
  invariants, and a pointer to the docs index.
- `docs/README.md`: canonical index, one row per doc with "Read when...".
- `docs/<topic>.md`: one document per topic, loaded on demand.
- `docs/known-issues.md`: tech-debt registry with stable `KI-NNN` ids.
- `docs/archive/`: superseded docs and finished plans.
- `.agents/skills/{agents-md-bootstrap,docs-policy}/`: vendored skills.

`<skill-dir>` below means the directory containing this `SKILL.md`. The
`docs-policy` skill is its sibling: `<skill-dir>/../docs-policy`.

## Hard rules

1. **Never invent.** Every command, path and tool written to `AGENTS.md` must
   be verified in the repository (file exists, script defined, CI step
   present). Anything unverifiable is written as `TODO(<what is missing>)`
   and listed in the final summary.
2. **Ask before deciding policies.** Policies come from the user's answers,
   not from defaults applied silently.
3. **Report before changing** in align mode. Only approved items are applied.
4. **Preserve project knowledge.** Domain invariants, critical query
   filters, gotchas and project-specific sections in an existing `AGENTS.md`
   are kept (moved if needed, never dropped).
5. **Scaffold, do not fabricate docs.** Create the index, registry and
   archive; never mass-generate feature docs. `architecture.md` only if the
   user asks for it, and only from code that was actually read.
6. **No commits.** Show the changed files and a proposed commit message; the
   user decides.
7. **Write the files in the documentation language** chosen by the user.

## Workflow

```
Bootstrap progress:
- [ ] 1. Discovery
- [ ] 2. Ask the user
- [ ] 3. Run the selected mode (generate | align | audit)
- [ ] 4. Vendor skills (generate / align)
- [ ] 5. Verify
- [ ] 6. Summarize
```

### 1. Discovery (read-only)

Collect, without writing anything:

- **Repository root**: the workspace root, or the git top-level directory.
- **Stack and package manager**: `pyproject.toml`, `uv.lock`, `poetry.lock`,
  `requirements*.txt`, `package.json` + lockfile, `go.mod`, `Cargo.toml`,
  `pom.xml`, `build.gradle*`, `Gemfile`, `composer.json`, `*.csproj`.
- **Commands**: scripts in `package.json`, `[tool.*]` sections and scripts
  in `pyproject.toml`, `Makefile` / `justfile` / `Taskfile.yml` targets,
  `docker-compose*.yml` services, devcontainer config, CI workflows
  (`.github/workflows/`, `.gitlab-ci.yml`, `azure-pipelines.yml`). Prefer the
  commands CI runs: they are known to work.
- **Test setup**: test directories, markers, integration test requirements.
- **Existing instruction files**: `AGENTS.md` (also nested ones),
  `CLAUDE.md`, `.cursorrules`, `.cursor/rules/`, `.github/copilot-instructions.md`.
- **Docs**: `docs/`, `docs/README.md`, `docs/known-issues.md`,
  `docs/archive/`, root `README.md`.
- **Vendored skills**: `.agents/skills/` and the output of
  `python3 <skill-dir>/scripts/vendor_skills.py <repo-root> --check`.
- **Critical areas**: modules where a mistake corrupts data or breaks
  security (persistence, migrations, auth, billing, versioning). These feed
  the test-policy question.

If an `AGENTS.md` or `docs/` exists, also run:

```bash
python3 <skill-dir>/../docs-policy/scripts/doc_check.py <repo-root>
```

### 2. Ask the user

Ask everything in **one** AskQuestion call. Put the recommended option first
and mark it "(Recommended)". Fill options from discovery. If the AskQuestion
tool is unavailable, ask the same questions conversationally and wait.

| id | Prompt | Options |
|---|---|---|
| `mode` | What should I do with this repository? | `generate` - create AGENTS.md and docs scaffold (recommended when no AGENTS.md); `align` - compare the existing AGENTS.md/docs with the reference layout and propose changes (recommended when AGENTS.md exists); `audit` - report only, write nothing |
| `git_policy` | Git policy for agents in this repo? | `confirm` - never commit without explicit user approval (Recommended); `free` - agents may commit; `none` - do not include a git policy |
| `test_policy` | Which areas require integration tests for any change? (multi-select) | One option per detected critical area, plus `none` |
| `docs_scaffold` | Which docs/ scaffold should exist? | `standard` - docs/README.md + known-issues.md + archive/ (Recommended); `standard_arch` - standard + architecture.md drafted from the code; `none` |
| `other_instructions` | Other instruction files were found: <list>. What should I do? | `pointer` - replace their content with a short pointer to AGENTS.md (Recommended); `keep` - leave them untouched; `claude_symlink` - also create CLAUDE.md pointing to AGENTS.md. Omit this question if none were found, but still offer `claude_symlink` as a separate yes/no if CLAUDE.md is missing. |
| `docs_language` | Language for AGENTS.md and docs/? | `en` - English (Recommended); `match` - the language of the existing docs; `other` |

In `audit` mode only `mode` is required; skip the rest.

### 3a. Mode: generate

1. Read [templates/AGENTS.template.md](templates/AGENTS.template.md) and the
   gold example [reference/example-agents-md.md](reference/example-agents-md.md).
2. Fill each section from discovery. Remove the template's guidance
   comments. Drop sections with nothing verified to say instead of padding
   them; keep "Critical Invariants" even if it only has one `TODO`.
3. Apply the answers: git policy, test policy, documentation language.
4. Scaffold `docs/` per `docs_scaffold` using
   [templates/docs-README.template.md](templates/docs-README.template.md) and
   [templates/known-issues.template.md](templates/known-issues.template.md).
   Index every existing doc found in `docs/` with a "Read when..." line and
   its type (see `docs-policy/doc-types.md`).
5. Handle other instruction files per `other_instructions` (see
   "Pointer files" below).

### 3b. Mode: align

1. Build a **gap report** comparing the repository with the template:
   - Missing or misordered sections of `AGENTS.md`.
   - Commands or paths that fail verification (from `doc_check.py` and
     discovery).
   - Content duplicated across `AGENTS.md`, `.github/copilot-instructions.md`,
     `CLAUDE.md`, `README.md` and `docs/` (same structure tree, same command
     list, same rules).
   - Docs index problems: `AGENTS.md` keeping its own doc list, docs missing
     from `docs/README.md`, entries without "Read when...".
   - Docs-policy violations: copied KI severities, plan-like docs that should
     be archived, manual "Last updated" fields, missing Files Reference.
   - Vendored skills missing or outdated.
2. Present the report as a numbered list grouped by file, each item with the
   proposed change. Then ask with AskQuestion (`allow_multiple: true`) which
   items to apply; offer "all" and "none".
3. Apply only the approved items. Keep project-specific content (rule 4):
   when restructuring, move sections rather than rewriting them.
4. **Idempotency check**: re-run the gap analysis on the result. A second
   pass must produce no new items; if it does, fix the template mapping, not
   the repository.

### 3c. Mode: audit

Produce the same gap report as align mode plus the full `doc_check.py`
output and the `vendor_skills.py --check` result. Write nothing. End with the
command to run align mode.

### 4. Vendor skills (generate and align)

```bash
python3 <skill-dir>/scripts/vendor_skills.py <repo-root>
```

This copies both skills into `<repo-root>/.agents/skills/`, upgrading older
copies and never downgrading. Report what it installed, upgraded or skipped.
The generated `AGENTS.md` must reference `.agents/skills/docs-policy/SKILL.md`
in its Documentation Policy section.

### 5. Verify

1. Run `doc_check.py` on the repository. Fix every `ERROR` introduced by
   this run; list pre-existing errors in the summary instead of silently
   fixing unrelated docs (they belong to an align item the user approves).
2. Re-read the generated `AGENTS.md` and check:
   - Under ~200 lines; no section the agent could trivially rediscover by
     listing directories.
   - Every command appears in a manifest, script or CI file.
   - "Critical Invariants" contains rules, not descriptions.
   - The docs index is a pointer to `docs/README.md`, not a second list.

### 6. Summarize

Report: mode, files created/changed, `TODO`s left for the user, pre-existing
doc problems not fixed, vendored skill versions, and the proposed commit
(file list + message). Do not commit.

## Pointer files

When `other_instructions` is `pointer`, replace the file content with:

```markdown
# <Tool> instructions

The canonical agent instructions for this repository are in
[AGENTS.md](<relative path to AGENTS.md>). Read it first; it links to the
documentation index in docs/README.md.
```

Before replacing, move any content that is not already in `AGENTS.md` or
`docs/` into the right place (rule 4), and list what was moved.

For `claude_symlink`, create `CLAUDE.md` as a symlink to `AGENTS.md`; if
symlinks are not suitable (Windows checkouts), create a file containing
only `@AGENTS.md`.

## Additional resources

- Template: [templates/AGENTS.template.md](templates/AGENTS.template.md)
- Gold example: [reference/example-agents-md.md](reference/example-agents-md.md)
- Docs index template: [templates/docs-README.template.md](templates/docs-README.template.md)
- Registry template: [templates/known-issues.template.md](templates/known-issues.template.md)
- Documentation rules and doc types: the sibling `docs-policy` skill
