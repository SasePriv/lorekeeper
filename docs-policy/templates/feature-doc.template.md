# <Feature Name>

<One paragraph: what the feature does, for whom, and why it exists.>

**Status**: Implemented | Partial (see KI-NNN) | Proposed
**Audience**: <e.g. backend developers (all sections), frontend developers (sections 3, 7)>
**Code entry point**: `path/to/main_module.ext`

For <related topic> see [`<other-doc>.md`](<other-doc>.md).

---

## TL;DR - Invariants

<3-8 rules that must never be broken. Each one names the file or function that enforces it.>

- <Rule>. Enforced in `path/to/file.ext` (`function_name`).
- <Mandatory filter / required test type / ordering constraint>.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Concepts and Lifecycle](#2-concepts-and-lifecycle)
3. [API Contract](#3-api-contract)
4. [Validations and Rules](#4-validations-and-rules)
5. [Data Model](#5-data-model)
6. [Design Rationale](#6-design-rationale)
7. [Known Issues](#7-known-issues)
8. [Files Reference](#8-files-reference)
9. [Glossary](#9-glossary)

---

## 1. Overview

<What problem it solves and the business goal.>

### Out of scope

- <What this feature deliberately does not do.>

## 2. Concepts and Lifecycle

<Key concepts, states and allowed transitions. Prefer a state diagram or a
role x action x state table over prose.>

## 3. API Contract

<Only what generated API specs (OpenAPI, etc.) cannot express.>

| Endpoint | Auth / role | Side effects | Errors (cause) |
|---|---|---|---|
| `METHOD /path` | <role> | <writes, audit entries, cache keys invalidated> | `409` <cause> |

## 4. Validations and Rules

<Business rules, uniqueness, conflict detection, cascades.>

## 5. Data Model

<Entities, properties, relations, indexes and the query filters that must be
applied when reading them.>

## 6. Design Rationale

<"Why not X" decisions that a future reader (or agent) might otherwise undo.>

## 7. Known Issues

- KI-NNN

## 8. Files Reference

| File | Purpose |
|---|---|
| `path/to/router.ext` | <Endpoints and guards> |
| `path/to/service.ext` | <Core logic> |
| `path/to/tests/test_feature.ext` | <What it covers> |

## 9. Glossary

| Term | Meaning |
|---|---|
| <Term> | <Definition used consistently in this doc> |
