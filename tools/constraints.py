#!/usr/bin/env python3
"""A cache of things not worth paying for twice — and of what that does not mean.

The point is not to collect dead ends. It is to stop paying, twice, for a wall
someone already walked into, without turning a local dead end into a universal
prohibition. So the type of an entry decides what it is allowed to do:

    REFUTATION      a claim was shown false; blocks the claim without new evidence
    BOUNDARY        a design says no; blocks nothing, redirects
    COST_WITNESS    a measurement; informs a choice, forbids no path
    FAILED_ATTEMPT  one way did not work; says nothing about other ways
    INCONCLUSIVE    looked, learned little; may never be cited as a reason to stop
    UNRUNNABLE      could not be tested here; the weakest thing a record can say
    SUPERSEDED      replaced by a later entry

Evidence burden follows claim strength. Only a REFUTATION may block, and only if
it carries a runnable witness AND a negative control — a check that cannot fail
is not evidence that something is impossible.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRIES = REPO_ROOT / "cache" / "entries"
SCHEMA = "decision-archaeology.constraint@v0"
TYPES = {"REFUTATION", "BOUNDARY", "COST_WITNESS", "FAILED_ATTEMPT",
         "INCONCLUSIVE", "UNRUNNABLE", "SUPERSEDED"}
MAY_BLOCK = {"REFUTATION"}
MAY_INFORM = {"REFUTATION", "BOUNDARY", "COST_WITNESS"}
NEEDS_WITNESS = {"REFUTATION", "BOUNDARY", "COST_WITNESS", "FAILED_ATTEMPT"}
NEEDS_MEASUREMENT = {"COST_WITNESS"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load() -> list[dict]:
    entries = []
    for path in sorted(ENTRIES.glob("*.json")):
        document = json.loads(path.read_text())
        document["_path"] = path.relative_to(REPO_ROOT).as_posix()
        entries.append(document)
    return entries


def validate(entries: list[dict]) -> None:
    seen = set()
    for entry in entries:
        label = entry["_path"]
        require(entry["schema"] == SCHEMA, f"{label}: wrong schema")
        require(re.fullmatch(r"CC-[0-9]{4}", entry["id"]) is not None, f"{label}: bad id")
        require(entry["id"] not in seen, f"{entry['id']}: duplicated")
        require(Path(label).stem == entry["id"], f"{label}: filename does not name the entry")
        seen.add(entry["id"])
        kind = entry["type"]
        require(kind in TYPES, f"{entry['id']}: unknown type {kind!r}")

        authority = entry["authority"]
        if authority == "blocks-without-new-evidence":
            require(kind in MAY_BLOCK,
                    f"{entry['id']}: a {kind} may not block a path. Only a refuted claim "
                    "may, and a dead end is not a refutation")
        if authority == "informs-only":
            require(kind in MAY_INFORM, f"{entry['id']}: a {kind} carries no counsel")

        if kind in NEEDS_WITNESS:
            witness = entry.get("witness")
            require(isinstance(witness, dict),
                    f"{entry['id']}: a {kind} needs a runnable witness")
        if kind in MAY_BLOCK:
            require(entry["witness"].get("negative_control"),
                    f"{entry['id']}: may block a path and carries no negative control; a "
                    "check that cannot fail is not evidence that something is impossible")
        if kind in NEEDS_MEASUREMENT:
            require(isinstance(entry.get("measurement"), dict),
                    f"{entry['id']}: a cost witness without a measurement is an opinion")

        require(len(entry["applies_until"].split()) >= 4,
                f"{entry['id']}: applies_until must say what would end this entry's reach")
        require(entry["cost"]["to_discover"] and entry["cost"]["to_recheck"],
                f"{entry['id']}: both costs are required — the cache is only worth "
                "consulting when re-checking is cheaper than re-discovering")

    blocking = [e for e in entries if e["authority"] == "blocks-without-new-evidence"]
    informing = [e for e in entries if e["authority"] == "informs-only"]
    print(f"PASS: {len(entries)} entries — {len(blocking)} may block, "
          f"{len(informing)} inform, {len(entries) - len(blocking) - len(informing)} "
          "record only")


def run_witnesses(entries: list[dict], only_blocking: bool) -> int:
    failures = 0
    for entry in entries:
        witness = entry.get("witness")
        if not witness:
            continue
        if only_blocking and entry["authority"] != "blocks-without-new-evidence":
            continue
        result = subprocess.run(witness["command"], shell=True, cwd=REPO_ROOT,
                                capture_output=True, text=True)
        state = "ok" if result.returncode == 0 else "FAILED"
        if result.returncode != 0:
            failures += 1
            print(f"  {entry['id']} witness {state}: {witness['command']}")
            print(f"    {(result.stderr or result.stdout).strip().splitlines()[-1][:160]}")
        else:
            print(f"  {entry['id']} witness {state}")
    return failures


def lookup(entries: list[dict], query: str) -> None:
    """What is already known about this, before spending anything on it."""
    words = {word.lower() for word in re.findall(r"[a-z0-9-]+", query.lower())
             if len(word) > 2}
    scored = []
    for entry in entries:
        haystack = " ".join([entry["claim"], " ".join(entry.get("tags", [])),
                             entry["environment"]["what"]]).lower()
        score = sum(1 for word in words if word in haystack)
        if score:
            scored.append((score, entry))
    if not scored:
        print("nothing recorded — this wall, if it is one, has not been walked into here")
        return
    for score, entry in sorted(scored, key=lambda pair: -pair[0])[:5]:
        print(f"\n{entry['id']}  {entry['type']}  ({entry['authority']})")
        print(f"  claim:   {entry['claim']}")
        print(f"  holds in: {entry['environment']['what']} "
              f"[{', '.join(entry['environment']['versions'])}]")
        print(f"  stops applying: {entry['applies_until']}")
        print(f"  recheck cost: {entry['cost']['to_recheck']}")
        if entry["type"] != "REFUTATION":
            print("  note: this does not forbid the path; it only tells you what happened")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["verify", "lookup", "witnesses"])
    parser.add_argument("query", nargs="*", default=[])
    parser.add_argument("--all", action="store_true",
                        help="run every witness, not only those of blocking entries")
    arguments = parser.parse_args()
    entries = load()
    if arguments.action == "verify":
        validate(entries)
        return 0
    if arguments.action == "witnesses":
        validate(entries)
        failures = run_witnesses(entries, only_blocking=not arguments.all)
        require(failures == 0, f"{failures} witnesses no longer hold")
        print("WITNESSES: all hold")
        return 0
    lookup(entries, " ".join(arguments.query))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
