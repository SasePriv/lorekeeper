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
| [`docs-policy`](docs-policy/SKILL.md) | Automatic | Keeps `docs/` in sync with the code: one doc per topic, doc types, "if you change X update Y", known-issues registry, archiving, link/path checks. |

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
│   ├── templates/                 # AGENTS.md, docs/README.md, docs/known-issues.md
│   ├── reference/                 # annotated gold example of an AGENTS.md
│   └── scripts/vendor_skills.py   # copies both skills into <repo>/.agents/skills/
└── docs-policy/
    ├── SKILL.md
    ├── VERSION
    ├── doc-types.md
    ├── templates/                 # feature, cross-cutting, runbook docs
    └── scripts/doc_check.py       # path, link, index and known-issue checks
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

## Requirements

- Python 3.10+ (scripts use the standard library only).
