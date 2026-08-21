#!/usr/bin/env python3
"""Hostile boundary checks for decision-archaeology.need-outcome@v1."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tests.gitfixture import commit, repository  # noqa: E402
from tools.validate_need_outcome import (  # noqa: E402
    load_object, no_outcome_was_deleted, outcomes_are_immutable, validate_outcome,
)


OUTCOME = REPO_ROOT / "outcomes" / "DA-SIGMA-0001.2.json"


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

        recorded = repository(temporary_path / "committed")
        outcome = recorded / "outcomes" / "DA-SIGMA-0001.json"
        original = json.loads(raw)
        original.pop("supersedes", None)
        commit(recorded, {outcome: original}, "record the outcome")
        outcome.unlink()
        commit(recorded, {}, "delete the outcome")
        rejected(lambda: no_outcome_was_deleted(recorded),
                 "a recorded outcome deleted in a later commit")

        rewritten = repository(temporary_path / "rewritten")
        receipt = rewritten / "outcomes" / "DA-SIGMA-0001.json"
        commit(rewritten, {receipt: original}, "record the outcome")
        edited = json.loads(json.dumps(original))
        edited["producer"] = "somebody else, later"
        edited["recorded_at"] = "2027-01-01T00:00:00Z"
        commit(rewritten, {receipt: edited}, "rewrite the receipt in place")
        rejected(lambda: outcomes_are_immutable(rewritten),
                 "a committed receipt rewritten under the same name")

        misnamed = repository(temporary_path / "misnamed")
        commit(misnamed, {misnamed / "outcomes" / "DA-SIGMA-0002.json": original},
               "a receipt whose filename names another request")
        rejected(lambda: outcomes_are_immutable(misnamed),
                 "a receipt whose filename does not match its request id")

        cycle = repository(temporary_path / "cycle")
        looping = {"schema": "decision-archaeology.need-outcome@v1",
                   "request_id": "DA-X-0001"}
        commit(cycle, {cycle / "outcomes" / "DA-X-0001.2.json":
                       {**looping, "supersedes": "outcomes/DA-X-0001.3.json"},
                       cycle / "outcomes" / "DA-X-0001.3.json":
                       {**looping, "supersedes": "outcomes/DA-X-0001.2.json"}},
               "two receipts superseding each other")
        rejected(lambda: outcomes_are_immutable(cycle),
                 "a supersession cycle, which would leave no receipt validated at all")

        unnumbered = repository(temporary_path / "unnumbered")
        commit(unnumbered, {unnumbered / "outcomes" / "DA-X-0001.2.json": dict(looping)},
               "a numbered receipt that supersedes nothing")
        rejected(lambda: outcomes_are_immutable(unnumbered),
                 "a numbered receipt that supersedes nothing")

        backwards = repository(temporary_path / "backwards")
        later = backwards / "outcomes" / "DA-X-0001.2.json"
        commit(backwards, {later: {**looping, "supersedes": "outcomes/DA-X-0001.json"}},
               "the correction lands first")
        commit(backwards, {backwards / "outcomes" / "DA-X-0001.json": dict(looping)},
               "and what it corrects lands after it")
        rejected(lambda: outcomes_are_immutable(backwards),
                 "a receipt superseding one recorded after it")

        orphan = repository(temporary_path / "orphan")
        claiming = json.loads(json.dumps(original))
        claiming["supersedes"] = "outcomes/DA-SIGMA-0001.9.json"
        commit(orphan, {orphan / "outcomes" / "DA-SIGMA-0001.json": claiming}, "orphan")
        rejected(lambda: outcomes_are_immutable(orphan),
                 "a receipt superseding one that was never recorded")

    print("NEED-OUTCOME-BOUNDARY: ALL PASS (15/15)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
