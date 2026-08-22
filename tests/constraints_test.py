#!/usr/bin/env python3
"""Hostile boundary checks for what a cache entry is allowed to claim."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.constraints import load, validate  # noqa: E402


def rejected(function, label: str) -> None:
    try:
        function()
    except (ValueError, KeyError):
        print(f"OK   {label}")
        return
    raise AssertionError(f"accepted an entry claiming more than it proved: {label}")


def main() -> int:
    entries = load()
    validate(entries)

    promoted = copy.deepcopy(entries)
    for entry in promoted:
        if entry["type"] == "FAILED_ATTEMPT":
            entry["authority"] = "blocks-without-new-evidence"
    rejected(lambda: validate(promoted),
             "a failed attempt promoted to a rule that blocks a path")

    counselling = copy.deepcopy(entries)
    for entry in counselling:
        if entry["type"] == "INCONCLUSIVE":
            entry["authority"] = "informs-only"
    rejected(lambda: validate(counselling),
             "an inconclusive look offered as counsel")

    uncontrolled = copy.deepcopy(entries)
    for entry in uncontrolled:
        if entry["authority"] == "blocks-without-new-evidence":
            entry["witness"].pop("negative_control", None)
    rejected(lambda: validate(uncontrolled),
             "a blocking refutation with no executable negative control")

    theatrical = copy.deepcopy(entries)
    for entry in theatrical:
        if entry["authority"] == "blocks-without-new-evidence":
            entry["witness"] = {"counterexample": {"argv": ["true"]},
                                "negative_control": {"argv": ["true"]}}
    rejected(lambda: validate(theatrical),
             "a blocking entry whose halves run nothing")

    prose = copy.deepcopy(entries)
    prose[0]["witness"] = {"counterexample": "I ran it and it failed"}
    rejected(lambda: validate(prose),
             "a witness written as a sentence rather than an argv")

    unbounded = copy.deepcopy(entries)
    unbounded[0]["applies_until"] = "never"
    rejected(lambda: validate(unbounded),
             "an entry that never stops applying")

    opinion = copy.deepcopy(entries)
    for entry in opinion:
        if entry["type"] == "COST_WITNESS":
            entry.pop("measurement")
    rejected(lambda: validate(opinion),
             "a cost witness with no measurement behind it")

    misfiled = copy.deepcopy(entries)
    misfiled[0]["id"] = "CC-9999"
    rejected(lambda: validate(misfiled),
             "an entry whose identifier does not match its file")

    print("CONSTRAINT-BOUNDARY: ALL PASS (8/8)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
