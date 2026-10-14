#!/usr/bin/env python3
"""Vendor the agents-md-bootstrap and docs-policy skills into a repository.

Copies each skill into <repo>/.agents/skills/<name>/ and compares VERSION files:

  missing    -> install
  older      -> upgrade (replace the vendored copy)
  same       -> skip; reported as "modified" if the files differ
  newer      -> skip (never downgrade)

--force replaces the vendored copy in every case. --check reports what would
happen without writing and exits 1 when any skill is missing, outdated or
modified.

Usage:
  python3 vendor_skills.py <repo-root> [--check] [--force] [--dest .agents/skills]
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

SKILLS = ("agents-md-bootstrap", "docs-policy")
IGNORED = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
PAST_TENSE = {"install": "installed", "upgrade": "upgraded", "replace": "replaced"}


def read_version(skill_dir: Path) -> tuple[int, ...] | None:
    version_file = skill_dir / "VERSION"
    if not version_file.is_file():
        return None
    text = version_file.read_text(encoding="utf-8").strip()
    try:
        return tuple(int(part) for part in text.split("."))
    except ValueError:
        return None


def fmt(version: tuple[int, ...] | None) -> str:
    return ".".join(map(str, version)) if version else "unversioned"


def trees_differ(left: Path, right: Path) -> bool:
    comparison = filecmp.dircmp(left, right, ignore=["__pycache__", ".DS_Store"])
    return _differs(comparison)


def _differs(comparison: filecmp.dircmp) -> bool:
    if comparison.left_only or comparison.right_only or comparison.funny_files:
        return True
    _, mismatch, errors = filecmp.cmpfiles(
        comparison.left, comparison.right, comparison.common_files, shallow=False
    )
    if mismatch or errors:
        return True
    return any(_differs(sub) for sub in comparison.subdirs.values())


def decide(source: Path, target: Path, force: bool) -> tuple[str, str]:
    """Return (action, detail). Action is install|upgrade|replace|skip|linked|modified|newer."""
    src_version = read_version(source)
    if not target.exists():
        return "install", fmt(src_version)
    if target.resolve() == source.resolve():
        return "linked", ("source and target are the same directory; to upgrade, run this script "
                          "from the agent-skills repository instead of the vendored copy")
    dst_version = read_version(target)
    if force:
        return "replace", f"{fmt(dst_version)} -> {fmt(src_version)} (forced)"
    if dst_version is None or (src_version is not None and dst_version < src_version):
        return "upgrade", f"{fmt(dst_version)} -> {fmt(src_version)}"
    if src_version is not None and dst_version > src_version:
        return "newer", f"vendored {fmt(dst_version)} is newer than source {fmt(src_version)}; not downgrading"
    if trees_differ(source, target):
        return "modified", f"{fmt(dst_version)} has local changes; use --force to overwrite"
    return "skip", f"{fmt(dst_version)} up to date"


def copy_skill(source: Path, target: Path) -> None:
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, ignore=IGNORED)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("repo", type=Path, help="target repository root")
    parser.add_argument("--check", action="store_true", help="report only, do not write")
    parser.add_argument("--force", action="store_true", help="replace vendored copies regardless of version")
    parser.add_argument("--dest", default=".agents/skills", help="skills folder inside the repo (default: .agents/skills)")
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    if not repo.is_dir():
        print(f"error: {repo} is not a directory", file=sys.stderr)
        return 2

    skills_root = Path(__file__).resolve().parent.parent.parent
    dest_root = repo / args.dest
    needs_action = False

    for name in SKILLS:
        source = skills_root / name
        target = dest_root / name
        if not (source / "SKILL.md").is_file():
            print(f"{name}: ERROR source not found at {source}", file=sys.stderr)
            needs_action = True
            continue

        action, detail = decide(source, target, args.force)
        rel_target = target.relative_to(repo).as_posix()

        if action in {"install", "upgrade", "replace"}:
            needs_action = True
            if args.check:
                print(f"{name}: would {action} ({detail}) -> {rel_target}")
            else:
                copy_skill(source, target)
                print(f"{name}: {PAST_TENSE[action]} ({detail}) -> {rel_target}")
        elif action == "modified":
            needs_action = True
            print(f"{name}: modified ({detail})")
        else:
            print(f"{name}: {action} ({detail})")

    return 1 if args.check and needs_action else 0


if __name__ == "__main__":
    sys.exit(main())
