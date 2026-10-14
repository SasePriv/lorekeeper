<!--
Template for docs/README.md. Remove every HTML comment when generating.
One row per active document in docs/. "Read when" names the change or
question that should make a reader (or agent) open the document.
Types: feature | cross-cutting | runbook | registry | plan (see docs-policy/doc-types.md).
-->
# Documentation

Reference documentation for {{project_name}}. Each document covers a single
topic; there is no duplication between them. Agent-facing rules live in
[`../AGENTS.md`](../AGENTS.md).

## Active Documents

| Document | Type | Read when |
|---|---|---|
| [known-issues/README.md](known-issues/README.md) | registry | You find tech debt, an inconsistency or a deprecation, or need context on a `KI-NNN` reference (read the Open table only) |

<!-- single_file registry instead: | [known-issues.md](known-issues.md) | registry | You find tech debt, an inconsistency or a deprecation, or need context on a `KI-NNN` reference | -->
<!-- | [architecture.md](architecture.md) | cross-cutting | You need the big picture: components, data flow, environments | -->
<!-- | [local-development.md](local-development.md) | runbook | You set up the project locally or change dev tooling | -->
<!-- | [<feature>.md](<feature>.md) | feature | You change <feature>: <main modules> | -->

## Archive

Historical or superseded documents are in [`archive/`](archive/). They are
kept for reference but no longer reflect the current state of the system.
