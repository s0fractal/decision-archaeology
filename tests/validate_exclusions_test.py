#!/usr/bin/env python3
"""Hostile boundary checks for recorded absences."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.validate_exclusions import render, validate  # noqa: E402

CASE = REPO_ROOT / "examples" / "barite-bid-rigging-2025"
RECORD = CASE / "exclusions.json"
PROSE = CASE / "exclusions.md"


def rejected(function, label: str) -> None:
    try:
        function()
    except (ValueError, KeyError):
        print(f"OK   {label}")
        return
    raise AssertionError(f"accepted a dishonest exclusion record: {label}")


def scaffold(directory: Path, record: dict, prose: str | None = None) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    record_path = directory / "exclusions.json"
    record_path.write_text(json.dumps(record, ensure_ascii=False))
    prose_path = directory / "exclusions.md"
    prose_path.write_text(render(record) if prose is None else prose)
    return record_path, prose_path


def main() -> int:
    validate(RECORD, PROSE)
    record = json.loads(RECORD.read_text())

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)

        drifted = json.loads(json.dumps(record))
        paths = scaffold(root / "drift", drifted, prose="# Exclusions and limits\n")
        rejected(lambda: validate(*paths), "prose that drifted from the record")

        unresolvable = json.loads(json.dumps(record))
        for entry in unresolvable["exclusions"]:
            entry.pop("would_resolve", None)
        rejected(lambda: validate(*scaffold(root / "unresolvable", unresolvable)),
                 "an absence with nothing that would resolve it")

        boundless = json.loads(json.dumps(record))
        for entry in boundless["exclusions"]:
            if entry["kind"] == "not-located":
                entry.pop("search_boundary")
        rejected(lambda: validate(*scaffold(root / "boundless", boundless)),
                 "not-located without a search boundary")

        smuggled = json.loads(json.dumps(record))
        smuggled["exclusions"][2]["search_boundary"] = "everywhere"
        rejected(lambda: validate(*scaffold(root / "smuggled", smuggled)),
                 "a field that does not belong to the declared kind")

        vanished = json.loads(json.dumps(record))
        vanished["exclusions"] = vanished["exclusions"][:-1]
        rejected(lambda: validate(*scaffold(root / "vanished", vanished), previous=record),
                 "an exclusion dropped without being retired")

        emptied = json.loads(json.dumps(record))
        emptied["exclusions"] = []
        rejected(lambda: validate(*scaffold(root / "emptied", emptied)),
                 "a case that claims to exclude nothing")

        retired = json.loads(json.dumps(record))
        retired["retired"] = [{"id": retired["exclusions"][0]["id"],
                               "reason": "still listed above",
                               "retired_at": "2026-08-21T12:00:00Z"}]
        rejected(lambda: validate(*scaffold(root / "retired", retired)),
                 "an exclusion both live and retired")

    print("EXCLUSIONS-BOUNDARY: ALL PASS (7/7)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
