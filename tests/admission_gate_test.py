#!/usr/bin/env python3
"""Hostile boundary checks for candidate admission."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.admission_gate import render, validate  # noqa: E402

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

        untick = json.loads(json.dumps(gate))
        for item in untick["requirements"]:
            if item["id"] == "AG-006":
                item["status"] = "unmet"
                item["open_because"] = "quietly withdrawn"
                item.pop("evidence", None)
        rejected(lambda: validate(scaffold(root / "untick", untick), previous=gate),
                 "a met requirement un-ticked without being reopened")

        drifted = json.loads(json.dumps(gate))
        rejected(lambda: validate(scaffold(root / "drifted", drifted,
                                           prose="# Admission gate\n\nAll good.\n")),
                 "prose that drifted from the record")

    print("ADMISSION-GATE-BOUNDARY: ALL PASS (7/7)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
