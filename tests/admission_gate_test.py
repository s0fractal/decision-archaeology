#!/usr/bin/env python3
"""Hostile boundary checks for candidate admission."""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tests.gitfixture import commit, repository  # noqa: E402
from tools.admission_gate import render, validate  # noqa: E402
from tools.history import committed_versions, unexplained_vanished  # noqa: E402

CANDIDATE = REPO_ROOT / "candidates" / "kherson-fortifications"


def rejected(function, label: str) -> None:
    try:
        function()
    except (ValueError, KeyError):
        print(f"OK   {label}")
        return
    raise AssertionError(f"admitted what should have stayed in quarantine: {label}")


def scaffold(root: Path, gate: dict, verdict: str = "NOT ADMITTED",
             prose: str | None = None) -> Path:
    directory = root / CANDIDATE.name
    directory.mkdir(parents=True, exist_ok=True)
    shutil.copy(CANDIDATE / "source-inventory.json", directory / "source-inventory.json")
    gate_path = directory / "admission.json"
    gate_path.write_text(json.dumps(gate, ensure_ascii=False))
    (directory / "admission.md").write_text(render(gate, verdict) if prose is None else prose)
    return gate_path


def main() -> int:
    validate(CANDIDATE / "admission.json")
    gate = json.loads((CANDIDATE / "admission.json").read_text())

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)

        ticked = json.loads(json.dumps(gate))
        for item in ticked["requirements"]:
            item["status"] = "met"
            item.pop("open_because", None)
            item.pop("awaiting", None)
        rejected(lambda: validate(scaffold(root / "ticked", ticked, "ADMISSIBLE")),
                 "every requirement ticked with no evidence")

        invented = json.loads(json.dumps(gate))
        invented["requirements"][0].update({"status": "met",
                                            "evidence": ["candidate.does.not.exist"]})
        invented["requirements"][0].pop("open_because", None)
        invented["requirements"][0].pop("awaiting", None)
        rejected(lambda: validate(scaffold(root / "invented", invented)),
                 "evidence that resolves to nothing")

        orphaned = json.loads(json.dumps(gate))
        orphaned["requirements"] = [item for item in orphaned["requirements"]
                                    if item["id"] != "AG-001"]
        rejected(lambda: validate(scaffold(root / "orphaned", orphaned)),
                 "missing material left with no open requirement")

        silent = json.loads(json.dumps(gate))
        silent["requirements"][1].pop("open_because")
        rejected(lambda: validate(scaffold(root / "silent", silent)),
                 "an unmet requirement that does not say what is missing")

        stray = json.loads(json.dumps(gate))
        stray["requirements"][1]["awaiting"] = ["missing.not-in-inventory"]
        rejected(lambda: validate(scaffold(root / "stray", stray)),
                 "awaiting material the inventory does not record")

        outside = copy.deepcopy(gate)
        escaped = outside["requirements"][0]
        escaped.update({"status": "met", "evidence": ["/etc/hosts"]})
        escaped.pop("open_because")
        rejected(lambda: validate(scaffold(root / "outside", outside)),
                 "an absolute path outside the repository offered as evidence")

        traversal = copy.deepcopy(gate)
        escaping = traversal["requirements"][0]
        escaping.update({"status": "met", "evidence": ["../../etc/hosts"]})
        escaping.pop("open_because"); escaping.pop("awaiting")
        rejected(lambda: validate(scaffold(root / "traversal", traversal)),
                 "evidence that climbs out of the repository")

        closed = copy.deepcopy(gate)
        still_awaiting = closed["requirements"][0]
        still_awaiting.update({"status": "met",
                               "evidence": ["candidate.suspilne.counterposition"]})
        still_awaiting.pop("open_because")
        rejected(lambda: validate(scaffold(root / "closed", closed)),
                 "a met requirement still awaiting missing material")

        untick = json.loads(json.dumps(gate))
        for item in untick["requirements"]:
            if item["id"] == "AG-006":
                item["status"] = "unmet"
                item["open_because"] = "quietly withdrawn"
                item.pop("evidence", None)
        rejected(lambda: validate(scaffold(root / "untick", untick), history=[gate]),
                 "a met requirement un-ticked without being reopened")

        # after a commit, a HEAD comparison compares the record with itself
        committed = repository(root / "committed")
        candidate = committed / "kherson-fortifications"
        candidate.mkdir(parents=True, exist_ok=True)
        shutil.copy(CANDIDATE / "source-inventory.json", candidate / "source-inventory.json")
        commit(committed, {candidate / "admission.json": gate,
                           candidate / "admission.md": render(gate, "NOT ADMITTED")}, "gate")
        removed = copy.deepcopy(gate)
        removed["requirements"] = [item for item in removed["requirements"]
                                   if item["id"] != "AG-008"]
        commit(committed, {candidate / "admission.json": removed,
                           candidate / "admission.md": render(removed, "NOT ADMITTED")},
               "drop AG-008")
        rejected(lambda: validate(candidate / "admission.json",
                                  history=committed_versions(candidate / "admission.json")),
                 "an open requirement deleted in a later commit")

        drifted = json.loads(json.dumps(gate))
        rejected(lambda: validate(scaffold(root / "drifted", drifted,
                                           prose="# Admission gate\n\nAll good.\n")),
                 "prose that drifted from the record")

        # a move that also edits the record: rename detection is a heuristic, so
        # the record must declare where it came from, and the past follows it
        moved = repository(root / "moved")
        first = moved / "candidates" / "kherson-fortifications"
        first.mkdir(parents=True, exist_ok=True)
        shutil.copy(CANDIDATE / "source-inventory.json", first / "source-inventory.json")
        commit(moved, {first / "admission.json": gate,
                       first / "admission.md": render(gate, "NOT ADMITTED")}, "gate")
        second = moved / "candidates" / "kherson-2"
        subprocess.run(["git", "-C", str(moved), "mv", str(first), str(second)],
                       check=True, capture_output=True)
        renamed = copy.deepcopy(gate)
        renamed["candidate_id"] = "kherson-2"
        renamed["requirements"] = [item for item in renamed["requirements"]
                                   if item["id"] != "AG-008"]
        commit(moved, {second / "admission.json": renamed,
                       second / "admission.md": render(renamed, "NOT ADMITTED")},
               "move and drop AG-008 at once")
        undeclared = unexplained_vanished(moved, "candidates/*/admission.json")
        assert undeclared == ["candidates/kherson-fortifications/admission.json"], undeclared
        print("OK   a record moved without declaring where it came from")

        declared = copy.deepcopy(renamed)
        declared["moved_from"] = ["candidates/kherson-fortifications/admission.json"]
        commit(moved, {second / "admission.json": declared,
                       second / "admission.md": render(declared, "NOT ADMITTED")},
               "declare the move")
        assert not unexplained_vanished(moved, "candidates/*/admission.json")
        rejected(lambda: validate(second / "admission.json",
                                  history=committed_versions(
                                      second / "admission.json",
                                      lambda value: value.get("candidate_id"),
                                      declared["moved_from"])),
                 "a requirement dropped during a declared move")

    print("ADMISSION-GATE-BOUNDARY: ALL PASS (13/13)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
