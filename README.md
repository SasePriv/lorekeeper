# agent-skills

Reusable agent skills for keeping a repository's agent instructions
(`AGENTS.md`) and its `docs/` folder useful for both humans and AI agents.

The approach: `AGENTS.md` is small, always loaded, and holds the facts,
policies and invariants an agent must never miss. Everything else lives in
`docs/`, one document per topic, and is loaded on demand through an index.

## Skills

| Skill | Invocation | Purpose |
|---|---|---|
| [`agents-md-bootstrap`](agents-md-bootstrap/SKILL.md) | Explicit only (`/agents-md-bootstrap`) | Generates, aligns or audits `AGENTS.md` and the `docs/` scaffold of a repository. Asks the user for policies on every run. Vendors both skills into the repository. |
| [`docs-policy`](docs-policy/SKILL.md) | Automatic | Keeps `docs/` in sync with the code: one doc per topic, doc types, "if you change X update Y", known-issues registry (one file per issue, `ki.py` CLI), archiving, link/path checks. |

Both skills are designed to be **vendored into every target repository**
under `.agents/skills/`, so the policy travels with the code and works for
every collaborator and tool, not only on the machine where this repository
is installed.

## Layout

```
agent-skills/
├── agents-md-bootstrap/
│   ├── SKILL.md
│   ├── VERSION
│   ├── templates/                 # AGENTS.md, docs/README.md, single-file docs/known-issues.md
│   ├── reference/                 # annotated gold example of an AGENTS.md
│   └── scripts/vendor_skills.py   # copies both skills into <repo>/.agents/skills/
└── docs-policy/
    ├── SKILL.md
    ├── VERSION
    ├── doc-types.md
    ├── templates/                 # feature, cross-cutting, runbook docs; one known issue
    └── scripts/
        ├── doc_check.py           # path, link, index and known-issue checks
        └── ki.py                  # known-issues CLI: new, resolve, index, migrate
```

## Install

### Global (to invoke the bootstrap in repositories that do not have it yet)

Symlink both skills into the user-level skills folder, which Cursor reads:

```bash
ln -s ~/Documents/projects/agent-skills/agents-md-bootstrap ~/.agents/skills/agents-md-bootstrap
ln -s ~/Documents/projects/agent-skills/docs-policy ~/.agents/skills/docs-policy
```

Once this repository is published on a Git host, it can also be installed
with the skills CLI:

```bash
npx skills add <owner>/agent-skills@agents-md-bootstrap -g
npx skills add <owner>/agent-skills@docs-policy -g
```

### Per repository (vendoring)

Running `/agents-md-bootstrap` in a repository vendors both skills
automatically. To vendor or update them manually:

```bash
python3 agents-md-bootstrap/scripts/vendor_skills.py /path/to/repo           # install or upgrade
python3 agents-md-bootstrap/scripts/vendor_skills.py /path/to/repo --check   # report only
```

The script compares the `VERSION` file of each skill. It copies when the
skill is missing, upgrades when the vendored copy is older, and never
downgrades unless `--force` is passed.

## Updating a skill

1. Edit the skill in this repository.
2. Bump its `VERSION` (semver: patch for wording, minor for new rules or
   checks, major for changes that require re-aligning existing repos).
3. Re-run `vendor_skills.py` in each repository that uses it, or run
   `/agents-md-bootstrap` in audit mode to see which repositories are behind.

## Checking a repository's docs

```bash
python3 docs-policy/scripts/doc_check.py /path/to/repo
python3 docs-policy/scripts/doc_check.py /path/to/repo --json
```

Exit code is `1` when errors are found (`--strict` also fails on warnings).
False positives can be silenced with a `.doccheckignore` file at the
repository root (one `fnmatch` pattern per line) or with an inline
`<!-- doc-check: ignore -->` comment on the offending line.

## Managing known issues

The registry lives in `docs/known-issues/`: one `KI-NNN.md` per issue
(frontmatter + body) and a generated `README.md` index with open issues
first. Agents read the index and open single issues on demand; all writes go
through the CLI so ids and the index cannot drift. Run it from the
repository root, or pass `--root <repo>` after the subcommand:

```bash
KI="python3 .agents/skills/docs-policy/scripts/ki.py"
$KI new --title "Short title" --severity medium --location src/app.py
$KI resolve KI-007 --ref "!123" --note "Validated input in the handler"
$KI index            # regenerate after editing frontmatter by hand
$KI index --check    # exit 1 if the index is stale (CI-friendly)
$KI migrate          # split a legacy docs/known-issues.md into per-issue files
```

`migrate` archives the original file as `docs/archive/known-issues.md` and
lists the documents that still link to it. `doc_check.py` validates both the
per-file registry and the legacy single file.

## Requirements

- Python 3.10+ (scripts use the standard library only).
