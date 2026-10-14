# Known Issues & Technical Debt

Registry of inconsistencies, deprecations and follow-ups detected while
working on the codebase. Each entry has a stable `KI-NNN` identifier so
other documents can link to it.

**Status legend**: 🔴 critical · 🟡 medium · 🟢 low

---

## Open issues

<!-- Newest first. Remove this comment when adding the first entry.

### KI-001 🟡 Short title

- **Location**: `path/to/file.ext` (`function_name`).
- **Symptom**: What goes wrong and how it is observed.
- **Risk**: Impact if left unfixed.
- **Suggested fix**: Concrete next step.
- **Detected**: <Month Year>, <context>.
-->

## Resolved issues

<!-- Entries moved here when fixed, with a "Resolved" line. -->

## Adding a new entry

1. Pick the next `KI-NNN` id (zero-padded, sequential, never reused).
2. Choose severity: 🔴 critical / 🟡 medium / 🟢 low.
3. Fill the four mandatory fields: **Location**, **Symptom**, **Risk**,
   **Suggested fix**.
4. Add a **Detected** line with the month/year and a short context.
5. Other documents link the id only; never copy the description or severity.
6. When the issue is fixed, move the entry to *Resolved issues* and append a
   **Resolved** line with the commit / PR reference.
