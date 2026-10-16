# Lorekeeper

Keeps a repository's lore for humans and AI agents.

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
lorekeeper/
├── LICENSE                        # MIT
├── agents-md-bootstrap/
│   ├── SKILL.md
│   ├── LICENSE                    # MIT, copied when the skill is vendored
│   ├── VERSION
│   ├── templates/                 # AGENTS.md, docs/README.md, single-file docs/known-issues.md
│   │   └── ci/                    # docs-check job for GitHub Actions, GitLab CI, Azure Pipelines
│   ├── reference/                 # annotated gold example of an AGENTS.md
│   └── scripts/vendor_skills.py   # copies both skills into <repo>/.agents/skills/
├── docs-policy/
│   ├── SKILL.md
│   ├── LICENSE                    # MIT, copied when the skill is vendored
│   ├── VERSION
│   ├── doc-types.md
│   ├── templates/                 # feature, cross-cutting, runbook docs; one known issue
│   └── scripts/
│       ├── doc_check.py           # path, link, index, known-issue, size and drift checks
│       └── ki.py                  # known-issues CLI: new, resolve, index, migrate
└── tests/                         # tests for the scripts (not vendored)
```

## Install

Install both skills with the [skills CLI](https://github.com/vercel-labs/skills),
either globally or in a single repository.

**Globally** (`~/.agents/skills/`), to have `/agents-md-bootstrap` available
in every repository:

```bash
npx skills add SasePriv/lorekeeper -g --skill '*'
```

**In one repository** (`.agents/skills/`), from the repository root, so the
skills travel with the code and every collaborator gets them:

```bash
npx skills add SasePriv/lorekeeper --skill '*'
```

The CLI asks which agents to install for; pass `--agent cursor` (or any other
supported agent) to skip the prompt. To update later, run
`npx skills update -g` or `npx skills update` in the repository.

## Set up a repository (recommended)

Once installed, run `/agents-md-bootstrap` in your agent from the repository
you want to set up. It asks for the project's policies, generates or aligns
`AGENTS.md` and the `docs/` scaffold, offers a docs-check CI job, and vendors
both skills into `.agents/skills/` if they are not there yet. Run it again
later to audit the repository.

Without it, `docs-policy` still works, but the repository has no `AGENTS.md`
or `docs/` index for it to keep in sync.

## Contributing

To edit the skills, clone this repository and symlink both skills into the
user-level skills folder instead of installing them with the CLI, so local
changes and `git pull` take effect immediately:

```bash
git clone https://github.com/SasePriv/lorekeeper.git ~/lorekeeper
mkdir -p ~/.agents/skills
ln -s ~/lorekeeper/agents-md-bootstrap ~/.agents/skills/agents-md-bootstrap
ln -s ~/lorekeeper/docs-policy ~/.agents/skills/docs-policy
```

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
python3 docs-policy/scripts/doc_check.py /path/to/repo --diff               # + drift against local changes
python3 docs-policy/scripts/doc_check.py /path/to/repo --diff origin/main   # + drift for a branch / PR
```

`--diff` enables the drift check: when a file listed in a doc's
"Files Reference" changed (against `HEAD`, or against the merge base with the
given ref, plus uncommitted and untracked files) but the doc did not, it
reports a warning on that doc. It needs git and, in CI, the full history.
Put the repository path before `--diff`, since `--diff` takes an optional
value.

The size check reports active docs over `--max-doc-lines` (default 300) as
info and an `AGENTS.md` over 200 lines as a warning. The doc budget is a
signal, not a limit: a doc whose rules must be read together stays whole
with `<!-- doc-check: size-ok <reason> -->` at the top.

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

`migrate` archives the original file as `docs/archive/known-issues.md` and <!-- doc-check: ignore -->
lists the documents that still link to it. `doc_check.py` validates both the
per-file registry and the legacy single file.

## Running in CI

`/agents-md-bootstrap` detects the CI platform and offers to add a docs-check
job from `agents-md-bootstrap/templates/ci/`. Pushes run `doc_check.py`;
pull/merge requests add `--diff origin/<target branch>`; per-file registries
also run `ki.py index --check`.

## Tests

```bash
python3 -B -m unittest discover tests
```

## Requirements

- Python 3.10+ (scripts use the standard library only).
- git, only for `doc_check.py --diff`.

## License

[MIT](LICENSE). Copyright (c) 2026 SasePriv.
