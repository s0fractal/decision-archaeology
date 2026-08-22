#!/usr/bin/env python3
"""CC-0001, run as two halves against a throwaway repository.

`counterexample` exercises the REFUTED approach — compare a record with
`git show HEAD:<path>` — and passes only if that approach fails to notice an
entry deleted in a committed change. `control` runs the same scenario through a
guard that reads the record's whole history, and passes only if that one does
notice. Without the control, "the check did not complain" would be indistinguish-
able from "the harness is broken".
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

RECORD = {"entries": [{"id": "A", "fact": "recorded first"},
                      {"id": "B", "fact": "recorded first"}]}


def git(root: Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *arguments],
                          capture_output=True, check=False)


def scenario(root: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    git(root, "config", "user.email", "witness@example.invalid")
    git(root, "config", "user.name", "witness")
    path = root / "record.json"
    path.write_text(json.dumps(RECORD))
    git(root, "add", "-A"); git(root, "commit", "-qm", "record")
    shrunk = {"entries": [entry for entry in RECORD["entries"] if entry["id"] != "B"]}
    path.write_text(json.dumps(shrunk))
    git(root, "add", "-A"); git(root, "commit", "-qm", "drop B")
    return path


def refuted_guard_notices(path: Path) -> bool:
    """The approach under test: compare the record with HEAD."""
    root = path.parent
    blob = git(root, "show", f"HEAD:{path.name}")
    if blob.returncode != 0:
        return False
    previous = {entry["id"] for entry in json.loads(blob.stdout)["entries"]}
    current = {entry["id"] for entry in json.loads(path.read_text())["entries"]}
    return bool(previous - current)


def history_guard_notices(path: Path) -> bool:
    """The control: read every revision of the record, not only HEAD."""
    root = path.parent
    revisions = git(root, "log", "--format=%H", "--", path.name).stdout.decode().split()
    current = {entry["id"] for entry in json.loads(path.read_text())["entries"]}
    for revision in revisions:
        blob = git(root, "cat-file", "blob", f"{revision}:{path.name}")
        if blob.returncode != 0:
            continue
        if {entry["id"] for entry in json.loads(blob.stdout)["entries"]} - current:
            return True
    return False


def main() -> int:
    half = sys.argv[1] if len(sys.argv) > 1 else "counterexample"
    with tempfile.TemporaryDirectory() as temporary:
        path = scenario(Path(temporary) / "repo")
        if half == "counterexample":
            missed = not refuted_guard_notices(path)
            print("HEAD comparison after the commit:",
                  "did not notice the deletion" if missed else "noticed it")
            return 0 if missed else 1
        caught = history_guard_notices(path)
        print("whole-history comparison:",
              "noticed the deletion" if caught else "did not notice it")
        return 0 if caught else 1


if __name__ == "__main__":
    raise SystemExit(main())
