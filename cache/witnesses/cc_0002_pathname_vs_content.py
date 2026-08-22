#!/usr/bin/env python3
"""CC-0002, as two halves against a throwaway repository.

`counterexample`: a guard that proves a recorded pathname still exists reports
nothing when the receipt at that path is replaced with different valid content.
`control`: comparing against the bytes first committed at that path does notice,
so the counterexample is a property of the guard rather than of the harness.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

FILED = {"receipt": "R-1", "producer": "the party that filed it",
         "recorded_at": "2026-08-21T00:00:00Z"}
REWRITTEN = {"receipt": "R-1", "producer": "somebody else, later",
             "recorded_at": "2027-01-01T00:00:00Z"}


def git(root: Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *arguments],
                          capture_output=True, check=False)


def scenario(root: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    git(root, "config", "user.email", "witness@example.invalid")
    git(root, "config", "user.name", "witness")
    path = root / "receipt.json"
    path.write_text(json.dumps(FILED))
    git(root, "add", "-A"); git(root, "commit", "-qm", "file the receipt")
    path.write_text(json.dumps(REWRITTEN))
    git(root, "add", "-A"); git(root, "commit", "-qm", "rewrite it in place")
    return path


def pathname_guard_notices(path: Path) -> bool:
    """The approach under test: the path was added once and still exists."""
    root = path.parent
    added = git(root, "log", "--diff-filter=A", "--format=", "--name-only", "--",
                path.name).stdout.decode().split()
    return any(not (root / name).exists() for name in added)


def content_guard_notices(path: Path) -> bool:
    """The control: compare with the bytes first committed at that path."""
    root = path.parent
    revisions = git(root, "log", "--diff-filter=A", "--format=%H", "--",
                    path.name).stdout.decode().split()
    if not revisions:
        return False
    blob = git(root, "cat-file", "blob", f"{revisions[-1]}:{path.name}")
    return hashlib.sha256(blob.stdout).digest() != hashlib.sha256(path.read_bytes()).digest()


def main() -> int:
    half = sys.argv[1] if len(sys.argv) > 1 else "counterexample"
    with tempfile.TemporaryDirectory() as temporary:
        path = scenario(Path(temporary) / "repo")
        if half == "counterexample":
            missed = not pathname_guard_notices(path)
            print("pathname survival check:",
                  "reported nothing" if missed else "reported the rewrite")
            return 0 if missed else 1
        caught = content_guard_notices(path)
        print("first-committed-bytes check:",
              "reported the rewrite" if caught else "reported nothing")
        return 0 if caught else 1


if __name__ == "__main__":
    raise SystemExit(main())
