#!/usr/bin/env python3
"""Check AGENTS.md and docs/ of a repository for drift against the code.

Checks:
  path   Backticked paths and `cd <dir>` targets in shell blocks exist.
  link   Relative Markdown links (and their #anchors) resolve.
  index  Every active docs/*.md is listed in docs/README.md, and AGENTS.md
         either points to docs/README.md or lists every active doc.
  ki     Every KI-NNN reference exists in the registry, ids are unique, and
         severities are not copied (or contradicted) elsewhere. The registry
         is docs/known-issues/ (one KI-NNN.md per issue, frontmatter validated,
         generated index must be current) or, if that directory does not
         exist, the single file docs/known-issues.md.
  plan   Active docs that look like plans/logs or carry manual dates (info).

Usage:
  python3 doc_check.py <repo-root> [--json] [--strict] [--verbose] [--registry PATH]

Exit code is 1 when errors are found (or warnings, with --strict).
Silence false positives with a .doccheckignore file at the repository root
(one fnmatch pattern per line, matched against the path or link target) or
with "doc-check: ignore" anywhere on the offending line.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote

sys.dont_write_bytecode = True  # vendored copies must not leave __pycache__ in the target repo
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ki  # noqa: E402

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".next",
    ".nuxt",
    "dist",
    "build",
    "coverage",
    "htmlcov",
}

FILE_EXTENSIONS = {
    ".py", ".pyi", ".ipynb", ".md", ".mdx", ".rst", ".txt",
    ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue", ".svelte",
    ".json", ".jsonc", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env",
    ".sh", ".bash", ".zsh", ".ps1", ".bat",
    ".go", ".rs", ".java", ".kt", ".kts", ".scala", ".rb", ".php", ".cs",
    ".c", ".h", ".cpp", ".hpp", ".swift", ".dart", ".lua", ".r",
    ".sql", ".cypher", ".cql", ".graphql", ".gql", ".proto",
    ".html", ".css", ".scss", ".sass", ".less",
    ".owl", ".ttl", ".rdf", ".xml", ".csv", ".lock",
    ".template", ".example", ".sample", ".dockerfile", ".tf", ".hcl",
}

SHELL_LANGS = {"", "bash", "sh", "shell", "zsh", "console", "terminal", "shell-session"}

SEVERITY_EMOJI = {"\U0001F534": "critical", "\U0001F7E1": "medium", "\U0001F7E2": "low"}
SEVERITY_WORDS = {"critical": "critical", "high": "critical", "medium": "medium", "low": "low"}

IGNORE_MARKER = "doc-check: ignore"

INLINE_CODE_RE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
HTML_ANCHOR_RE = re.compile(r"<a\s+(?:id|name)=\"([^\"]+)\"", re.IGNORECASE)
CD_RE = re.compile(r"(?:^|[;&|(]\s*|\s)cd\s+([^\s;&|)]+)")
KI_RE = re.compile(r"\bKI-(\d+)\b")
KI_HEADING_RE = re.compile(r"^#{2,6}\s+KI-(\d+)\b(.*)$")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
LINE_REF_RE = re.compile(r":\d+(?:-\d+)?$")
PLAN_HEADING_RE = re.compile(
    r"\b(progress log|migration plan|next steps|roadmap|phases?\s*\d*|milestones?)\b",
    re.IGNORECASE,
)
CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s+")
STATUS_COMPLETE_RE = re.compile(r"status\W{0,6}\s*\**\s*(complete|completed|done|finished)\b", re.IGNORECASE)
MANUAL_DATE_RE = re.compile(r"\*\*last updated\*\*\s*:", re.IGNORECASE)


@dataclass
class Finding:
    level: str  # ERROR | WARN | INFO
    check: str
    file: str
    line: int
    message: str


@dataclass
class DocLine:
    number: int
    text: str  # with HTML comments removed
    raw: str
    fenced: bool
    fence_lang: str


class RepoIndex:
    """Relative POSIX paths of every file and directory in the repository."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: set[str] = set()
        self.dirs: set[str] = set()
        for path in self._walk(root):
            rel = path.relative_to(root).as_posix()
            (self.dirs if path.is_dir() else self.files).add(rel)

    def _walk(self, directory: Path):
        try:
            entries = list(directory.iterdir())
        except OSError:
            return
        for entry in entries:
            if entry.is_dir() and not entry.is_symlink():
                if entry.name in SKIP_DIRS:
                    continue
                yield entry
                yield from self._walk(entry)
            else:
                yield entry

    def suffix_matches(self, token: str, is_dir: bool) -> list[str]:
        pool = self.dirs if is_dir else self.files
        suffix = "/" + token
        return sorted(p for p in pool if p == token or p.endswith(suffix))


class GitIgnore:
    def __init__(self, root: Path) -> None:
        self.patterns: list[str] = []
        gitignore = root / ".gitignore"
        if gitignore.is_file():
            for raw in gitignore.read_text(encoding="utf-8", errors="replace").splitlines():
                line = raw.strip()
                if line and not line.startswith(("#", "!")):
                    self.patterns.append(line.strip("/"))

    def matches(self, rel_path: str) -> bool:
        parts = rel_path.split("/")
        for pattern in self.patterns:
            for i, part in enumerate(parts):
                if fnmatch.fnmatch(part, pattern) or fnmatch.fnmatch("/".join(parts[: i + 1]), pattern):
                    return True
        return False


class DocChecker:
    def __init__(self, root: Path, registry: Path | None, verbose: bool = False) -> None:
        self.root = root.resolve()
        self.verbose = verbose
        self.relative_paths: dict[Path, list[tuple[int, str, str]]] = {}
        self.index = RepoIndex(self.root)
        self.gitignore = GitIgnore(self.root)
        self.ignore_patterns = self._load_ignore_patterns()
        self.registry_dir, self.registry = self._resolve_registry(registry)
        self.issues = ki.load_issues(self.registry_dir) if self.registry_dir else []
        self.resolved_issue_files = {i.path for i in self.issues if i.status == "resolved"}
        self.findings: list[Finding] = []
        self.docs = self._collect_docs()
        self.parsed = {doc: self._parse(doc) for doc in self.docs}
        self._anchor_cache: dict[Path, set[str]] = {}
        self._siblings: list[Path] | None = None

    @property
    def siblings(self) -> list[Path]:
        if self._siblings is None:
            try:
                self._siblings = sorted(
                    p for p in self.root.parent.iterdir()
                    if p.is_dir() and p != self.root and not p.name.startswith(".")
                )
            except OSError:
                self._siblings = []
        return self._siblings

    # ----------------------------------------------------------- collection

    def _resolve_registry(self, registry: Path | None) -> tuple[Path | None, Path | None]:
        """Return (per-file registry directory, single-file registry); exactly one is set."""
        if registry is not None:
            return (registry, None) if registry.is_dir() else (None, registry)
        directory = self.root / ki.DEFAULT_DIR
        if directory.is_dir():
            return directory, None
        return None, self.root / ki.DEFAULT_LEGACY

    def is_registry_doc(self, doc: Path) -> bool:
        if self.registry_dir is not None:
            return doc.parent == self.registry_dir
        return doc == self.registry

    def registry_label(self) -> str:
        target = self.registry_dir or self.registry
        return self.rel(target) if target is not None and self._inside(target) else str(target)

    def _load_ignore_patterns(self) -> list[str]:
        ignore_file = self.root / ".doccheckignore"
        if not ignore_file.is_file():
            return []
        lines = ignore_file.read_text(encoding="utf-8").splitlines()
        return [line.strip() for line in lines if line.strip() and not line.startswith("#")]

    def _collect_docs(self) -> list[Path]:
        docs: list[Path] = []
        for rel in sorted(self.index.files):
            path = self.root / rel
            name = path.name
            if rel.startswith("docs/archive/"):
                continue
            is_doc = rel.startswith("docs/") and name.endswith(".md")
            is_agents = name in {"AGENTS.md", "CLAUDE.md"} and not path.is_symlink()
            is_root_readme = rel == "README.md"
            is_copilot = rel == ".github/copilot-instructions.md"
            if is_doc or is_agents or is_root_readme or is_copilot:
                docs.append(path)
        return docs

    def _parse(self, doc: Path) -> list[DocLine]:
        lines: list[DocLine] = []
        fenced = False
        fence_marker = ""
        fence_lang = ""
        in_comment = False
        text = doc.read_text(encoding="utf-8", errors="replace")
        for number, raw in enumerate(text.splitlines(), start=1):
            stripped = raw.strip()
            marker = stripped[:3]
            if not in_comment and marker in ("```", "~~~"):
                if not fenced:
                    fenced, fence_marker = True, marker
                    fence_lang = stripped[3:].strip().split(" ")[0].lower()
                    continue
                if marker == fence_marker:
                    fenced, fence_marker, fence_lang = False, "", ""
                    continue
            visible = raw
            if not fenced:
                visible, in_comment = self._strip_comments(raw, in_comment)
            lines.append(DocLine(number, visible, raw, fenced, fence_lang))
        return lines

    @staticmethod
    def _strip_comments(line: str, in_comment: bool) -> tuple[str, bool]:
        out: list[str] = []
        pos = 0
        while pos < len(line):
            if in_comment:
                end = line.find("-->", pos)
                if end == -1:
                    return "".join(out), True
                pos, in_comment = end + 3, False
            else:
                start = line.find("<!--", pos)
                if start == -1:
                    out.append(line[pos:])
                    break
                out.append(line[pos:start])
                pos, in_comment = start + 4, True
        return "".join(out), in_comment

    # -------------------------------------------------------------- helpers

    def rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def add(self, level: str, check: str, doc: Path, line: int, message: str) -> None:
        self.findings.append(Finding(level, check, self.rel(doc), line, message))

    def ignored(self, token: str) -> bool:
        return any(fnmatch.fnmatch(token, pattern) for pattern in self.ignore_patterns)

    @staticmethod
    def exists(base: Path, token: str) -> bool:
        try:
            return (base / token).exists()
        except OSError:  # unreadable directories next to the repo (e.g. snap's private /tmp)
            return False

    # ----------------------------------------------------------- path check

    @staticmethod
    def normalize_path_token(token: str) -> str | None:
        t = token.strip()
        if not t or len(t) > 200:
            return None
        if any(c in t for c in " <>{}*$|\"'()[],;=?!@#%^&+\\…"):
            return None
        if "..." in t or "://" in t or t.startswith(("/", "~", "-", "http")):
            return None
        t = LINE_REF_RE.sub("", t)
        if ":" in t:
            return None
        if t.startswith("./"):
            t = t[2:]
        t = t.rstrip("/")
        if not t or t in {".", ".."}:
            return None
        return t

    @staticmethod
    def looks_like_file(token: str) -> bool:
        name = token.rsplit("/", 1)[-1]
        if name.startswith(".") and len(name) > 1:
            return True
        return Path(name).suffix.lower() in FILE_EXTENSIONS

    def check_path_token(self, doc: Path, line: int, raw: str) -> None:
        token = self.normalize_path_token(raw)
        if token is None or self.ignored(token):
            return
        is_file = self.looks_like_file(token)
        has_slash = "/" in token
        if not is_file and not has_slash:
            return

        first_segment = token.split("/", 1)[0]
        if has_slash and first_segment == self.root.name:
            token = token.split("/", 1)[1]
            first_segment = token.split("/", 1)[0]

        bases = [self.root, doc.parent]
        if any(self.exists(base, token) for base in bases):
            return

        if has_slash and any(s.name == first_segment for s in self.siblings):
            if not self.exists(self.root.parent, token):
                self.add("WARN", "path", doc, line,
                         f"`{raw}` points to sibling repository `{first_segment}` but does not exist there")
            return

        matches = self.index.suffix_matches(token, is_dir=not is_file)
        repo_like = any(self.exists(base, first_segment) for base in bases)

        if not has_slash and token.startswith(".") and not matches:
            return  # extension or attribute access such as `.cypher` / `.nodes`
        if not is_file and not repo_like and not matches:
            return  # e.g. MIME types or owner/repo names, not repository paths

        if matches:
            if not has_slash:
                return  # bare file name that exists somewhere in the repo
            if len(matches) == 1:
                self.relative_paths.setdefault(doc, []).append((line, raw, matches[0]))
            else:
                self.add("WARN", "path", doc, line,
                         f"`{raw}` is ambiguous: {len(matches)} files match by suffix "
                         f"(e.g. {matches[0]}); use a repo-root-relative path")
            return

        if self.gitignore.matches(token):
            self.add("WARN", "path", doc, line,
                     f"`{raw}` does not exist but is gitignored (created locally?)")
            return

        sibling = next((s for s in self.siblings if self.exists(s, token)), None) if has_slash else None
        if sibling is not None:
            self.add("INFO", "path", doc, line,
                     f"`{raw}` is not in this repository; found in sibling repository "
                     f"`{sibling.name}` (prefix the path with `{sibling.name}/`)")
            return

        if has_slash or repo_like:
            self.add("ERROR", "path", doc, line, f"`{raw}` does not exist")
        else:
            self.add("INFO", "path", doc, line,
                     f"file name `{raw}` not found anywhere in the repo (stale, or a generic mention?)")

    def check_cd_targets(self, doc: Path, doc_line: DocLine) -> None:
        text = doc_line.text.strip()
        if text.startswith("$ "):
            text = text[2:]
        if text.startswith("#"):
            return
        for match in CD_RE.finditer(text):
            target = match.group(1).strip("'\"")
            if target.startswith(("-", "~", "$", "/", "..")) or target in {".", ""}:
                continue
            if any(c in target for c in "<>{}*"):
                continue
            if self.ignored(target):
                continue
            if not any(self.exists(base, target) for base in (self.root, doc.parent)):
                self.add("ERROR", "path", doc, doc_line.number,
                         f"`cd {target}`: directory does not exist")

    def check_paths(self) -> None:
        for doc, lines in self.parsed.items():
            if doc in self.resolved_issue_files:
                continue  # resolved issues are history and may cite files that no longer exist
            for doc_line in lines:
                if IGNORE_MARKER in doc_line.raw:
                    continue
                if doc_line.fenced:
                    if doc_line.fence_lang in SHELL_LANGS:
                        self.check_cd_targets(doc, doc_line)
                    continue
                for match in INLINE_CODE_RE.finditer(doc_line.text):
                    self.check_path_token(doc, doc_line.number, match.group(1))
        self.report_relative_paths()

    def report_relative_paths(self) -> None:
        for doc, entries in self.relative_paths.items():
            if self.verbose:
                for line, raw, match in entries:
                    self.add("INFO", "path", doc, line,
                             f"`{raw}` is not relative to the repo root; resolves to {match}")
                continue
            line, raw, match = entries[0]
            self.add("INFO", "path", doc, line,
                     f"{len(entries)} path(s) are relative to a subdirectory, not the repo root "
                     f"(e.g. `{raw}` -> {match}); use --verbose to list them")

    # ----------------------------------------------------------- link check

    @staticmethod
    def slugify(heading: str) -> str:
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)
        text = text.strip().lower()
        text = re.sub(r"[^\w\- ]", "", text)
        return text.replace(" ", "-")

    def anchors(self, doc: Path) -> set[str]:
        if doc in self._anchor_cache:
            return self._anchor_cache[doc]
        lines = self.parsed.get(doc) or self._parse(doc)
        seen: dict[str, int] = {}
        result: set[str] = set()
        for doc_line in lines:
            if doc_line.fenced:
                continue
            for anchor in HTML_ANCHOR_RE.findall(doc_line.text):
                result.add(anchor.lower())
            heading = HEADING_RE.match(doc_line.text)
            if not heading:
                continue
            slug = self.slugify(heading.group(2))
            count = seen.get(slug, 0)
            result.add(slug if count == 0 else f"{slug}-{count}")
            seen[slug] = count + 1
        self._anchor_cache[doc] = result
        return result

    def check_links(self) -> None:
        for doc, lines in self.parsed.items():
            for doc_line in lines:
                if doc_line.fenced or IGNORE_MARKER in doc_line.raw:
                    continue
                text = INLINE_CODE_RE.sub("", doc_line.text)
                for match in LINK_RE.finditer(text):
                    self.check_link_target(doc, doc_line.number, match.group(1))

    def check_link_target(self, doc: Path, line: int, target: str) -> None:
        if SCHEME_RE.match(target) or target.startswith("//") or self.ignored(target):
            return
        path_part, _, anchor = target.partition("#")
        path_part = unquote(path_part)
        if path_part:
            base = self.root if path_part.startswith("/") else doc.parent
            resolved = (base / path_part.lstrip("/")).resolve()
            if not resolved.exists():
                self.add("ERROR", "link", doc, line, f"link target `{target}` does not exist")
                return
        else:
            resolved = doc
        if anchor and resolved.is_file() and resolved.suffix.lower() == ".md":
            if anchor.lower() not in self.anchors(resolved):
                self.add("WARN", "link", doc, line,
                         f"anchor `#{anchor}` not found in {self.rel(resolved) if self._inside(resolved) else resolved}")

    def _inside(self, path: Path) -> bool:
        try:
            path.relative_to(self.root)
        except ValueError:
            return False
        return True

    # ---------------------------------------------------------- index check

    def check_index(self) -> None:
        docs_dir = self.root / "docs"
        if not docs_dir.is_dir():
            return
        active = sorted(p for p in docs_dir.glob("*.md") if p.name.lower() != "readme.md")
        subdirs = sorted(p for p in docs_dir.iterdir() if p.is_dir() and p.name != "archive")
        readme = docs_dir / "README.md"

        if readme.is_file():
            text = readme.read_text(encoding="utf-8", errors="replace")
            for doc in active:
                if doc.name not in text:
                    self.add("ERROR", "index", readme, 1, f"`docs/{doc.name}` is not listed in docs/README.md")
            for sub in subdirs:
                mentioned = f"{sub.name}/" in text or any(f.name in text for f in sub.rglob("*") if f.is_file())
                if not mentioned:
                    self.add("WARN", "index", readme, 1, f"`docs/{sub.name}/` is not referenced in docs/README.md")
        elif active:
            self.add("WARN", "index", docs_dir, 0, "docs/ has no README.md index")

        agents = self.root / "AGENTS.md"
        if not agents.is_file():
            self.add("INFO", "index", self.root, 0, "repository has no AGENTS.md")
            return
        agents_text = agents.read_text(encoding="utf-8", errors="replace")
        if "docs/README.md" in agents_text:
            return
        for doc in active:
            if f"docs/{doc.name}" not in agents_text and doc.name not in agents_text:
                self.add("WARN", "index", agents, 1,
                         f"AGENTS.md lists docs itself but omits `docs/{doc.name}`; "
                         "point it to docs/README.md instead")

    # ------------------------------------------------------------- KI check

    def load_registry(self) -> dict[str, tuple[str | None, int]]:
        if self.registry_dir is not None:
            return self.load_registry_dir()
        defined: dict[str, tuple[str | None, int]] = {}
        if self.registry is None or not self.registry.is_file():
            return defined
        for doc_line in self.parsed.get(self.registry) or self._parse(self.registry):
            if doc_line.fenced:
                continue
            match = KI_HEADING_RE.match(doc_line.text)
            if not match:
                continue
            ki_id = f"KI-{match.group(1)}"
            if ki_id in defined:
                self.add("ERROR", "ki", self.registry, doc_line.number,
                         f"{ki_id} is defined more than once (first at line {defined[ki_id][1]})")
                continue
            defined[ki_id] = (self.severity_of(match.group(2)), doc_line.number)
        return defined

    def load_registry_dir(self) -> dict[str, tuple[str | None, int]]:
        defined: dict[str, tuple[str | None, int]] = {}
        directory = self.registry_dir
        for issue in self.issues:
            for problem in ki.validate_issue(issue):
                self.add("ERROR", "ki", issue.path, 1, problem)
            if "TODO:" in issue.body:
                self.add("WARN", "ki", issue.path, 1, "issue still contains TODO placeholders")
            if not issue.id:
                continue
            if issue.id in defined:
                self.add("ERROR", "ki", issue.path, 1, f"{issue.id} is defined more than once")
                continue
            defined[issue.id] = (issue.meta.get("severity") or None, 1)

        index_path = directory / ki.INDEX_NAME
        hint = f"run: {ki.CLI_HINT} index"
        if not index_path.is_file():
            self.add("ERROR", "ki", directory, 0, f"registry index {ki.INDEX_NAME} is missing; {hint}")
        elif index_path.read_text(encoding="utf-8") != ki.render_index(self.issues):
            self.add("ERROR", "ki", index_path, 1, f"index is stale or edited by hand; {hint}")

        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix == ".md" and path.name != ki.INDEX_NAME \
                    and not ki.ISSUE_FILE_RE.match(path.name):
                self.add("WARN", "ki", path, 1, "file in the registry is not named KI-NNN.md")
        return defined

    @staticmethod
    def severity_of(text: str) -> str | None:
        for emoji, severity in SEVERITY_EMOJI.items():
            if emoji in text:
                return severity
        cleaned = re.sub(r"[^a-z]", "", text.lower())
        return SEVERITY_WORDS.get(cleaned)

    def check_known_issues(self) -> None:
        defined = self.load_registry()
        registry_known = self.registry_dir is not None or (self.registry is not None and self.registry.is_file())
        reported_missing_registry = False
        for doc, lines in self.parsed.items():
            is_registry = self.is_registry_doc(doc)
            for doc_line in lines:
                if doc_line.fenced or IGNORE_MARKER in doc_line.raw:
                    continue
                ids = {f"KI-{n}" for n in KI_RE.findall(doc_line.text)}
                if not ids:
                    continue
                if not registry_known:
                    if not reported_missing_registry:
                        self.add("WARN", "ki", doc, doc_line.number,
                                 f"KI ids are referenced but {self.registry_label()} does not exist")
                        reported_missing_registry = True
                    continue
                for ki_id in sorted(ids):
                    if ki_id not in defined:
                        self.add("ERROR", "ki", doc, doc_line.number, f"{ki_id} is not defined in the registry")
                if not is_registry and doc_line.text.lstrip().startswith("|"):
                    self.check_copied_severity(doc, doc_line, ids, defined)

    def check_copied_severity(self, doc: Path, doc_line: DocLine, ids: set[str],
                              defined: dict[str, tuple[str | None, int]]) -> None:
        cells = [cell.strip() for cell in doc_line.text.strip().strip("|").split("|")]
        copied = next((s for s in (self.severity_of(cell) for cell in cells) if s), None)
        if copied is None:
            return
        for ki_id in sorted(ids & defined.keys()):
            registry_severity = defined[ki_id][0]
            if registry_severity and registry_severity != copied:
                self.add("ERROR", "ki", doc, doc_line.number,
                         f"{ki_id} severity here is '{copied}' but the registry says '{registry_severity}'; "
                         "link the id only")
            else:
                self.add("WARN", "ki", doc, doc_line.number,
                         f"{ki_id} severity is copied from the registry; link the id only")

    # ----------------------------------------------------------- plan check

    def check_plan_like(self) -> None:
        docs_dir = self.root / "docs"
        for doc, lines in self.parsed.items():
            if doc.parent != docs_dir or doc.name.lower() == "readme.md" or self.is_registry_doc(doc):
                continue
            signals: list[str] = []
            checkboxes = sum(1 for dl in lines if not dl.fenced and CHECKBOX_RE.match(dl.text))
            if checkboxes:
                signals.append(f"{checkboxes} checkboxes")
            plan_headings = sorted({
                m.group(1).lower()
                for dl in lines
                if not dl.fenced and (h := HEADING_RE.match(dl.text)) and (m := PLAN_HEADING_RE.search(h.group(2)))
            })
            if plan_headings:
                signals.append("headings: " + ", ".join(plan_headings))
            head = "\n".join(dl.text for dl in lines[:30])
            if STATUS_COMPLETE_RE.search(head):
                signals.append("status says complete")
            if signals:
                self.add("INFO", "plan", doc, 1,
                         "looks like a plan/log (" + "; ".join(signals) + "); archive it if the work is finished")
            for dl in lines[:30]:
                if MANUAL_DATE_RE.search(dl.text):
                    self.add("INFO", "plan", doc, dl.number, "manual 'Last updated' field; rely on version control")
                    break

    # ---------------------------------------------------------------- run

    def run(self) -> list[Finding]:
        self.check_paths()
        self.check_links()
        self.check_index()
        self.check_known_issues()
        self.check_plan_like()
        order = {"ERROR": 0, "WARN": 1, "INFO": 2}
        self.findings.sort(key=lambda f: (f.file, f.line, order[f.level], f.message))
        return self.findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: current directory)")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    parser.add_argument("--strict", action="store_true", help="exit 1 on warnings too")
    parser.add_argument("--registry", type=Path,
                        help="known-issues directory or file (default: docs/known-issues/ if it exists, "
                             "else docs/known-issues.md)")
    parser.add_argument("--verbose", action="store_true", help="list every subdirectory-relative path")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    registry = (root / args.registry).resolve() if args.registry else None
    checker = DocChecker(root, registry, verbose=args.verbose)
    findings = checker.run()

    summary = {level: sum(1 for f in findings if f.level == level) for level in ("ERROR", "WARN", "INFO")}
    if args.json:
        print(json.dumps({
            "root": str(checker.root),
            "files_scanned": [checker.rel(d) for d in checker.docs],
            "summary": summary,
            "findings": [asdict(f) for f in findings],
        }, indent=2, ensure_ascii=False))
    else:
        for f in findings:
            location = f"{f.file}:{f.line}" if f.line else (f.file or ".")
            print(f"{location}: {f.level} [{f.check}] {f.message}")
        if findings:
            print()
        print(f"Summary: {summary['ERROR']} errors, {summary['WARN']} warnings, "
              f"{summary['INFO']} info ({len(checker.docs)} files scanned)")

    failed = summary["ERROR"] > 0 or (args.strict and summary["WARN"] > 0)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
