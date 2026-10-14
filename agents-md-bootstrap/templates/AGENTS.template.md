<!--
Template for AGENTS.md. Remove every HTML comment when generating.
Rules:
- Target under ~200 lines. Everything else belongs in docs/.
- Only verified facts and commands. Unverifiable items become TODO(<what>).
- Drop a section rather than padding it, except Critical Invariants.
- Paths are repo-root-relative.
-->
# AGENTS.md - {{project_name}}

<!-- One or two sentences: what the project is and who consumes it. -->
{{one_line_purpose}}

## Key Facts

<!-- Stack, runtime version, package manager, main tools. Short bullets. -->
- **Stack**: {{stack}}
- **Runtime**: {{runtime_and_version}}
- **Package manager**: {{package_manager}} (`{{manifest_path}}`)
- **Tooling**: {{lint_format_test_tools}}

## Non-negotiable Policies

<!-- Only the policies chosen by the user. Each one concrete and checkable. -->

### Git

**Never create a git commit without explicit confirmation from the user.**

Before committing:
1. Show the list of files that will be staged and the proposed commit message.
2. Wait for the user to say "go ahead", "commit", or equivalent explicit approval.
3. Only then run `git add` and `git commit`.

### Tests

<!-- From the test_policy answer. Name the areas and the exact command. -->
Integration tests are **mandatory** for any change touching {{critical_areas}}:

```bash
{{integration_test_command}}
```

## Dev Commands

<!-- Copy-pasteable, from the repository root unless stated. Prefer what CI runs. -->
```bash
{{install_command}}            # install dependencies
{{lint_format_command}}        # lint + format
{{test_command}}               # all tests
{{unit_test_command}}          # unit tests only
{{run_command}}                # run locally
```

<!-- Optional: short subsection per local workflow (devcontainer, docker compose).
     Link the full runbook instead of repeating it: docs/local-development.md -->

## Critical Invariants

<!-- Rules that cause bugs or data corruption when forgotten. Not descriptions.
     Include mandatory query filters, ordering constraints, "never X" rules,
     each with the file that enforces it. -->
- {{invariant}} (enforced in `{{path}}`)

## Project Structure

<!-- Packages and their responsibility only; agents can list files themselves.
     Two levels deep at most. -->
```
{{package_tree_with_one_line_responsibilities}}
```

## Documentation Policy

- Docs live in `docs/`, **one document per topic**, indexed in
  [docs/README.md](docs/README.md). Read the index to find the doc for the
  area you are changing.
- Any behavior change updates the matching doc **in the same change**.
<!-- per_file registry: -->
- Tech debt, inconsistencies and deprecations go to `docs/known-issues/`, one
  file per issue with a stable `KI-NNN` id, created with
  `python3 .agents/skills/docs-policy/scripts/ki.py new` (never edit its index
  by hand). Read only the Open table of `docs/known-issues/README.md`; other
  docs link the id only.
<!-- single_file registry: replace the bullet above with:
- Tech debt, inconsistencies and deprecations go to
  `docs/known-issues.md` with a stable `KI-NNN` id; other docs link the id only.
-->
- Superseded docs and finished plans move to `docs/archive/`; never delete them.
- Documentation and code comments are written in **{{docs_language}}**.
- Full rules, doc templates and the check script:
  `.agents/skills/docs-policy/SKILL.md`.

## Docs Index

See [docs/README.md](docs/README.md). Start there before reading or writing
any doc; it says which document to read for each kind of change.
