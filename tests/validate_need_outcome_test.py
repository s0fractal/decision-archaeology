#!/usr/bin/env python3
"""Hostile boundary checks for decision-archaeology.need-outcome@v1."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.validate_need_outcome import load_object, validate_outcome  # noqa: E402


OUTCOME = REPO_ROOT / "outcomes" / "DA-SIGMA-0001.json"


def rejected(function, label: str) -> None:
    try:
        function()
    except (ValueError, json.JSONDecodeError):
        print(f"OK   {label}")
        return
    raise AssertionError(f"accepted hostile outcome: {label}")


def main() -> int:
    validate_outcome(OUTCOME, True)
    print("OK   valid outcome and pinned artifact digests")

    with tempfile.TemporaryDirectory() as temporary:
        temporary_path = Path(temporary)
        raw = OUTCOME.read_text()
        duplicate = raw.replace(
            '  "schema": "decision-archaeology.need-outcome@v1",',
            '  "schema": "decision-archaeology.need-outcome@v1",\n'
            '  "schema": "decision-archaeology.need-outcome@v1",',
            1,
        )
        duplicate_path = temporary_path / "duplicate.json"
        duplicate_path.write_text(duplicate)
        rejected(lambda: load_object(duplicate_path), "duplicate JSON key")

        mismatched = json.loads(raw)
        mismatched["status"] = "blocked"
        mismatched_path = temporary_path / "mismatched.json"
        mismatched_path.write_text(json.dumps(mismatched))
        rejected(
            lambda: validate_outcome(mismatched_path, False),
            "inconsistent status and classification",
        )

        tampered = json.loads(raw)
        tampered["resolution"]["artifacts"][0]["sha256"] = "0" * 64
        tampered_path = temporary_path / "tampered.json"
        tampered_path.write_text(json.dumps(tampered))
        rejected(
            lambda: validate_outcome(tampered_path, True),
            "digest that does not match the pinned revision",
        )

        unknown = json.loads(raw)
        unknown["resolution"]["revision"] = "0" * 40
        unknown_path = temporary_path / "unknown.json"
        unknown_path.write_text(json.dumps(unknown))
        rejected(
            lambda: validate_outcome(unknown_path, True),
            "resolution revision missing from this checkout",
        )

        unnamed = json.loads(raw)
        unnamed["rebuild"]["derived_from"] = "notes/private-scratch.md"
        unnamed_path = temporary_path / "unnamed.json"
        unnamed_path.write_text(json.dumps(unnamed))
        rejected(
            lambda: validate_outcome(unnamed_path, True),
            "rebuild derived from something the outcome does not publish",
        )

        drifted = json.loads(raw)
        drifted["rebuild"]["sha256"] = "0" * 64
        drifted_path = temporary_path / "drifted.json"
        drifted_path.write_text(json.dumps(drifted))
        rejected(
            lambda: validate_outcome(drifted_path, True),
            "rebuild digest that does not match its pinned revision",
        )

        traversal = json.loads(raw)
        traversal["resolution"]["artifacts"][0]["path"] = "../outside"
        traversal_path = temporary_path / "traversal.json"
        traversal_path.write_text(json.dumps(traversal))
        rejected(
            lambda: validate_outcome(traversal_path, True),
            "repository path traversal",
        )

    print("NEED-OUTCOME-BOUNDARY: ALL PASS (8/8)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
