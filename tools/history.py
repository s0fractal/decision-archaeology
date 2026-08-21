#!/usr/bin/env python3
"""Read every committed version of a record, not just the current one.

A guard that compares a record against `HEAD` protects an uncommitted working
tree and nothing else: once the change is committed, `HEAD` is the change. A fact
about the past can only be protected against the past, so these helpers read a
file's whole history and let a validator require that whatever was once recorded
is still present or explicitly retired.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *arguments], capture_output=True)


def repository_root(path: Path) -> Path | None:
    directory = path.resolve().parent
    if not directory.is_dir():
        return None
    result = _git(directory, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        return None
    return Path(result.stdout.decode().strip())


SHA = re.compile(r"^[0-9a-f]{40}$")


def _revisions_with_paths(root: Path, relative: str) -> list[tuple[str, str]]:
    """(revision, path-at-that-revision), newest first.

    A record keeps its identity across a move, so the history has to be read at
    the name the file carried in each revision. Reading every revision at the
    *current* name silently truncates the history at a rename — and a rename
    that also edits the record would then hide whatever the edit removed.
    """
    listed = _git(root, "log", "--follow", "--format=%H", "--name-status", "--", relative)
    if listed.returncode != 0:
        return []
    commits: list[tuple[str, list[list[str]]]] = []
    for line in listed.stdout.decode().splitlines():
        line = line.rstrip("\n")
        if SHA.match(line.strip()):
            commits.append((line.strip(), []))
        elif line.strip() and commits:
            commits[-1][1].append(line.split("\t"))
    pairs, path = [], relative
    for revision, changes in commits:
        pairs.append((revision, path))
        for change in changes:
            if change[0].startswith("R") and len(change) >= 3 and change[2] == path:
                path = change[1]
                break
    return pairs


def _read_json(root: Path, revision: str, relative: str) -> dict | None:
    blob = _git(root, "cat-file", "blob", f"{revision}:{relative}")
    if blob.returncode != 0:
        return None
    try:
        value = json.loads(blob.stdout)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _by_identity(root: Path, name: str, identity, wanted) -> list[dict]:
    """Every committed record of this identity, wherever it has ever lived.

    Rename detection is a similarity heuristic, and a move that also edits the
    record can drop below it — so the record's own declared identity, not its
    path, is what the history is gathered by.
    """
    listed = _git(root, "log", "--format=%H", "--", f"*/{name}", name)
    if listed.returncode != 0:
        return []
    found = []
    for revision in listed.stdout.decode().split():
        tree = _git(root, "ls-tree", "-r", "--name-only", revision)
        if tree.returncode != 0:
            continue
        for relative in tree.stdout.decode().splitlines():
            if not (relative == name or relative.endswith("/" + name)):
                continue
            value = _read_json(root, revision, relative)
            if value is not None and identity(value) == wanted:
                found.append(value)
    return found


def unexplained_vanished(root: Path, pattern: str) -> list[str]:
    """Paths matching `pattern` that were committed once, are gone, and are
    claimed by no surviving record.

    A move is legitimate; an undeclared one is indistinguishable from a deletion
    that took the record's past with it. Rename detection is a similarity
    heuristic and a move that also edits the record can fall below it, so a
    record that moves says where it moved from.
    """
    listed = _git(root, "log", "--diff-filter=A", "--format=", "--name-only", "--", pattern)
    if listed.returncode != 0:
        return []
    declared: set[str] = set()
    for surviving in sorted(root.glob(pattern)):
        try:
            document = json.loads(surviving.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(document, dict):
            declared.update(document.get("moved_from") or [])
    gone = []
    for relative in dict.fromkeys(listed.stdout.decode().split()):
        if not (root / relative).exists() and relative not in declared:
            gone.append(relative)
    return sorted(gone)


def committed_versions(path: Path, identity=None, extra_paths=()) -> list[dict]:
    """Every committed version of this record, newest first.

    Collected two ways and merged: by following the path through renames, and —
    when the record declares an identity — by that identity across the whole
    history, so a move that outruns rename detection cannot truncate the past.
    """
    root = repository_root(path)
    if root is None:
        return []
    try:
        relative = path.resolve().relative_to(root).as_posix()
    except ValueError:
        return []
    versions = []
    for followed in [relative, *extra_paths]:
        for revision, historical in _revisions_with_paths(root, followed):
            value = _read_json(root, revision, historical)
            if value is not None:
                versions.append(value)
    if identity is not None:
        try:
            wanted = identity(json.loads(path.read_text()))
        except (OSError, json.JSONDecodeError):
            wanted = None
        if wanted is not None:
            versions.extend(_by_identity(root, path.name, identity, wanted))
    seen, unique = set(), []
    for value in versions:
        key = json.dumps(value, sort_keys=True)
        if key not in seen:
            seen.add(key)
            unique.append(value)
    return unique


def inside_repository(root: Path, reference: str) -> Path | None:
    """Resolve a repository-relative reference, or None if it escapes."""
    candidate = Path(reference)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root.resolve()):
        return None
    return resolved


def deleted_since_first_commit(root: Path, prefix: str, suffix: str = ".json") -> list[str]:
    """Paths under `prefix` that were committed once and no longer exist.

    A record of a past routing decision is not made false by being deleted; it is
    only made invisible, which is worse.
    """
    listed = _git(root, "log", "--diff-filter=A", "--format=", "--name-only", "--", prefix)
    if listed.returncode != 0:
        return []
    gone = []
    for line in dict.fromkeys(listed.stdout.decode().split()):
        if line.endswith(suffix) and not (root / line).exists():
            gone.append(line)
    return sorted(gone)


def first_committed_bytes(root: Path, relative: str) -> bytes | None:
    """The bytes this path carried when it first entered the repository."""
    listed = _git(root, "log", "--diff-filter=A", "--format=%H", "--", relative)
    if listed.returncode != 0:
        return None
    revisions = listed.stdout.decode().split()
    if not revisions:
        return None
    blob = _git(root, "cat-file", "blob", f"{revisions[-1]}:{relative}")
    return blob.stdout if blob.returncode == 0 else None
