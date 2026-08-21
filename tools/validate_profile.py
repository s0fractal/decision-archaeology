#!/usr/bin/env python3
"""Enforce what a published Decision Archaeology profile must carry.

A profile exists so that two parties who share no code compile the same claim to
the same bytes. Semantics alone cannot establish that, and a green replay of the
author's own module cannot detect its absence: DA-SIGMA-0001's first profile
passed every vector while three doc-derived rebuilds produced three different
term hashes. So each profile must publish a byte-determining construction
listing and ship a rebuild that follows only that listing.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILES = REPO_ROOT / "profiles"
TESTS = REPO_ROOT / "tests"
LISTING = re.compile(r"^##+\s+Construction listing\b", re.MULTILINE)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def module_stem(document: Path) -> str:
    return document.stem.replace("-", "_")


def rebuild_path(document: Path, tests_dir: Path = TESTS) -> Path:
    return tests_dir / f"{module_stem(document)}_doc_replay_test.py"


def validate_profile(document: Path, run: bool, profiles_dir: Path = PROFILES,
                     tests_dir: Path = TESTS) -> None:
    label = document.name
    text = document.read_text()
    require(LISTING.search(text) is not None,
            f"{label}: no 'Construction listing' section; a profile must fix bytes, "
            "not only semantics")

    vectors_path = profiles_dir / f"{module_stem(document)}.vectors.json"
    require(vectors_path.is_file(),
            f"{label}: missing frozen vectors at {vectors_path.name}")
    vectors = json.loads(vectors_path.read_text())
    require(isinstance(vectors.get("vectors"), list) and vectors["vectors"],
            f"{vectors_path.name}: expected a non-empty vector list")

    reference = profiles_dir / f"{module_stem(document)}.py"
    rebuild = rebuild_path(document, tests_dir)
    require(rebuild.is_file(), f"{label}: missing doc-derived rebuild at {rebuild.name}")
    source = rebuild.read_text()
    if reference.is_file():
        tree = ast.parse(source, filename=str(rebuild))
        imported = set()
        for statement in ast.walk(tree):
            if isinstance(statement, ast.Import):
                imported.update(alias.name for alias in statement.names)
            elif isinstance(statement, ast.ImportFrom) and statement.module:
                imported.add(statement.module)
        offending = {name for name in imported
                     if name.split(".")[-1] == reference.stem}
        require(not offending,
                f"{rebuild.name}: imports the reference implementation "
                f"({', '.join(sorted(offending))}); a rebuild that reads what it "
                "verifies proves nothing")
        read_back = {node.value for node in ast.walk(tree)
                     if isinstance(node, ast.Constant) and isinstance(node.value, str)
                     and (node.value == reference.name
                          or f"profiles/{reference.name}" in node.value)}
        require(not read_back,
                f"{rebuild.name}: names {reference.name} as a path; a rebuild must "
                "follow the published listing, not the reference file")
    require(document.name in source or module_stem(document) in source,
            f"{rebuild.name}: does not name the document it rebuilds from")
    require(vectors_path.name in source,
            f"{rebuild.name}: does not check the frozen vectors")

    print(f"OK   {label}: listing, vectors, and doc-derived rebuild present")
    if run:
        result = subprocess.run([sys.executable, str(rebuild)], cwd=REPO_ROOT)
        require(result.returncode == 0, f"{rebuild.name}: doc-derived rebuild failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--structure-only", action="store_true",
                        help="check what a profile publishes without running its rebuild")
    args = parser.parse_args()
    documents = sorted(PROFILES.glob("*.md"))
    require(bool(documents), "profiles/: no profile documents found")
    for document in documents:
        validate_profile(document, run=not args.structure_only)
    print(f"PROFILES: ALL PASS ({len(documents)} profiles)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
