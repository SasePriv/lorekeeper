"""Tests for the drift and size checks of docs-policy/scripts/doc_check.py.

Run from the repository root: python3 -m unittest discover tests
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "docs-policy" / "scripts"))
import doc_check  # noqa: E402

FEATURE_DOC = """# Feature

## TL;DR - Invariants

- Rule. Enforced in `src/app.py`.

## 8. Files Reference

| File | Purpose |
|---|---|
| `src/app.py` | Core logic |
| `src/handlers/` | Handlers |
| `src/legacy.py` | Old code <!-- doc-check: ignore --> |

## 9. Glossary

`src/other.py` is outside the Files Reference section.
"""


class RepoTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "repo"
        self.root.mkdir()
        self.write("docs/README.md", "# Documentation\n\n- [feature.md](feature.md)\n")
        self.write("docs/feature.md", FEATURE_DOC)
        for path in ("src/app.py", "src/handlers/a.py", "src/legacy.py", "src/other.py"):
            self.write(path, "x = 1\n")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, rel: str, text: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def git(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def init_git(self) -> None:
        self.git("init", "-q", "-b", "main")
        self.git("-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
        self.git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init")

    def commit(self, message: str) -> None:
        self.git("-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
        self.git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", message)

    def findings(self, check: str, **kwargs) -> list[doc_check.Finding]:
        checker = doc_check.DocChecker(self.root, None, **kwargs)
        return [f for f in checker.run() if f.check == check]


class DriftTest(RepoTestCase):
    def test_disabled_without_diff(self) -> None:
        self.init_git()
        self.write("src/app.py", "x = 2\n")
        self.assertEqual(self.findings("drift"), [])

    def test_changed_file_without_doc_update_warns(self) -> None:
        self.init_git()
        self.write("src/app.py", "x = 2\n")
        findings = self.findings("drift", diff_base="HEAD")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].level, "WARN")
        self.assertEqual(findings[0].file, "docs/feature.md")
        self.assertIn("`src/app.py`", findings[0].message)

    def test_doc_updated_in_same_change_is_quiet(self) -> None:
        self.init_git()
        self.write("src/app.py", "x = 2\n")
        self.write("docs/feature.md", FEATURE_DOC + "\nUpdated.\n")
        self.assertEqual(self.findings("drift", diff_base="HEAD"), [])

    def test_directory_entry_covers_new_files(self) -> None:
        self.init_git()
        self.write("src/handlers/b.py", "y = 1\n")
        findings = self.findings("drift", diff_base="HEAD")
        self.assertEqual(len(findings), 1)
        self.assertIn("`src/handlers/b.py`", findings[0].message)

    def test_ignored_line_and_files_outside_section_are_skipped(self) -> None:
        self.init_git()
        self.write("src/legacy.py", "x = 2\n")
        self.write("src/other.py", "x = 2\n")
        self.assertEqual(self.findings("drift", diff_base="HEAD"), [])

    def test_doccheckignore_pattern_skips_changed_file(self) -> None:
        self.write(".doccheckignore", "src/app.py\n")
        self.init_git()
        self.write("src/app.py", "x = 2\n")
        self.assertEqual(self.findings("drift", diff_base="HEAD"), [])

    def test_branch_base_includes_committed_changes(self) -> None:
        self.init_git()
        self.git("checkout", "-q", "-b", "feature")
        self.write("src/app.py", "x = 2\n")
        self.commit("change app")
        findings = self.findings("drift", diff_base="main")
        self.assertEqual(len(findings), 1)
        self.assertIn("`src/app.py`", findings[0].message)

    def test_unknown_base_is_an_error(self) -> None:
        self.init_git()
        findings = self.findings("drift", diff_base="origin/missing")
        self.assertEqual([f.level for f in findings], ["ERROR"])

    def test_not_a_git_repository_is_info(self) -> None:
        findings = self.findings("drift", diff_base="HEAD")
        self.assertEqual([f.level for f in findings], ["INFO"])


class SizeTest(RepoTestCase):
    def test_long_doc_is_info(self) -> None:
        self.write("docs/feature.md", FEATURE_DOC + "line\n" * 400)
        findings = self.findings("size")
        self.assertEqual([(f.level, f.file) for f in findings], [("INFO", "docs/feature.md")])

    def test_size_ok_marker_with_reason_silences(self) -> None:
        marker = "<!-- doc-check: size-ok state machine rules must be read together -->\n"
        self.write("docs/feature.md", marker + FEATURE_DOC + "line\n" * 400)
        self.assertEqual(self.findings("size"), [])

    def test_size_ok_marker_without_reason_is_reported(self) -> None:
        self.write("docs/feature.md", "<!-- doc-check: size-ok -->\n" + FEATURE_DOC + "line\n" * 400)
        findings = self.findings("size")
        self.assertEqual(len(findings), 1)
        self.assertIn("without a reason", findings[0].message)

    def test_custom_budget(self) -> None:
        self.assertEqual(len(self.findings("size", max_doc_lines=5)), 1)
        self.assertEqual(self.findings("size", max_doc_lines=1000), [])

    def test_long_agents_md_warns(self) -> None:
        self.write("AGENTS.md", "# AGENTS.md\n\nSee docs/README.md.\n" + "line\n" * 250)
        findings = self.findings("size")
        self.assertEqual([(f.level, f.file) for f in findings], [("WARN", "AGENTS.md")])


if __name__ == "__main__":
    unittest.main()
