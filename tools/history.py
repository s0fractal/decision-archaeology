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


def committed_versions(path: Path) -> list[dict]:
    """Parsed JSON of every revision of `path`, newest first, oldest last."""
    root = repository_root(path)
    if root is None:
        return []
    try:
        relative = path.resolve().relative_to(root).as_posix()
    except ValueError:
        return []
    listed = _git(root, "log", "--follow", "--format=%H", "--", relative)
    if listed.returncode != 0:
        return []
    versions = []
    for revision in listed.stdout.decode().split():
        blob = _git(root, "cat-file", "blob", f"{revision}:{relative}")
        if blob.returncode != 0:
            continue
        try:
            value = json.loads(blob.stdout)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            versions.append(value)
    return versions


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
