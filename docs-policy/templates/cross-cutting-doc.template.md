<!--
Template for a cross-cutting doc. Remove this comment when generating.
Budget: ~300 lines is the signal to consider splitting by subtopic (index
each part in docs/README.md). If the rules must be read together, keep it
whole and add an HTML comment "doc-check: size-ok <reason>" at the top. Readers load
the TL;DR first and then only the section they need, so keep each section
self-contained.
-->
# <Concern Name>

<One paragraph: which concern this covers (architecture, auth, versioning,
caching, ...) and why every feature depends on it.>

**Status**: Implemented | Partial (see KI-NNN) | Proposed
**Audience**: <e.g. stakeholders (sections 1-2), developers (sections 3-5), operators (section 6)>

---

## TL;DR - Invariants

- <Rule every feature must respect>. Enforced in `path/to/file.ext`.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Model](#2-model)
3. [How Features Use It](#3-how-features-use-it)
4. [Configuration](#4-configuration)
5. [Extending It](#5-extending-it)
6. [Design Rationale](#6-design-rationale)
7. [Known Issues](#7-known-issues)
8. [Files Reference](#8-files-reference)

---

## 1. Overview

<High-level picture. A diagram is usually worth more than prose here.>

## 2. Model

<The core concepts, flows or matrices (for example a permission matrix or a
versioning decision algorithm).>

## 3. How Features Use It

<The patterns feature code must follow, with a short canonical example.>

## 4. Configuration

<Environment variables, settings and their defaults. Never include secrets.>

## 5. Extending It

<Step-by-step: adding a new role / cache key / version field / component.>

## 6. Design Rationale

<Why this approach over the alternatives, in a few bullets.>

## 7. Known Issues

- KI-NNN

## 8. Files Reference

| File | Purpose |
|---|---|
| `path/to/file.ext` | <Purpose> |
