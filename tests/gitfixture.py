#!/usr/bin/env python3
"""A throwaway repository, for testing guards that must survive being committed.

The guards these tests exercise protect facts about the past. A guard compared
against the working tree looks identical to a correct one until the change is
committed, so the fixture commits.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _git(root: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(root), *arguments], check=True, capture_output=True)


def repository(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "config", "user.name", "fixture")
    return root


def commit(root: Path, files: dict[Path, str | dict], message: str) -> None:
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content if isinstance(content, str)
                        else json.dumps(content, ensure_ascii=False))
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", message)
