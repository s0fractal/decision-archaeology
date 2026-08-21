#!/usr/bin/env python3
"""Decide, mechanically, whether a candidate may be published as a case.

Failing the gate is a result. The risk this guards against is the opposite of a
false negative: a polished graph over scarce sources reads as an established
finding, and every incentive — including an agent's — points at ticking the last
box. So a met requirement must name evidence that resolves, an unmet requirement
keeps the candidate in quarantine, and every material the inventory records as
missing must be answered by a requirement that is still open.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "decision-archaeology.admission-gate@v0"
INVENTORY_STATUSES = {
    "public-attributable",
    "public-attributable-secondary",
    "public-attributable-counterclaim",
    "reported-only",
    "potentially-restricted",
    "missing-primary-source",
    "missing-exact-identity",
    "missing-time-bound-snapshot",
    "disproven",
}
MISSING_STATUSES = {
    "reported-only",
    "potentially-restricted",
    "missing-primary-source",
    "missing-exact-identity",
    "missing-time-bound-snapshot",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def previously_committed(path: Path) -> dict | None:
    try:
        relative = path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return None
    result = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"HEAD:{relative.as_posix()}"],
                            capture_output=True)
    return json.loads(result.stdout) if result.returncode == 0 else None


def render(gate: dict, verdict: str) -> str:
    lines = [f"# Admission gate — {gate['candidate_id']}", "",
             "Rendered from `admission.json`; edit the record, not this file.", "",
             f"**Verdict: {verdict}**", "",
             "A requirement counts as met only when it names evidence that resolves.",
             ""]
    for item in sorted(gate["requirements"], key=lambda entry: entry["id"]):
        mark = "x" if item["status"] == "met" else " "
        blocking = "" if item.get("blocking", True) else " _(not blocking)_"
        lines.append(f"- [{mark}] **{item['id']}**{blocking} — {item['requirement']}")
        for reference in item.get("evidence", []):
            lines.append(f"  - evidence: `{reference}`")
        if item.get("open_because"):
            lines.append(f"  - open because: {item['open_because']}")
        for reference in item.get("awaiting", []):
            lines.append(f"  - awaiting: `{reference}`")
    lines.append("")
    return "\n".join(lines)


def validate(gate_path: Path, write: bool = False, previous: dict | None = None) -> str:
    gate = json.loads(gate_path.read_text())
    require(gate["schema"] == SCHEMA, "admission gate: wrong schema")
    require(gate["authority"] == "publication-eligibility-only",
            "admission gate: bad authority")
    candidate = gate_path.parent
    require(candidate.name == gate["candidate_id"], "admission gate: candidate id mismatch")

    inventory = json.loads((candidate / "source-inventory.json").read_text())
    sources = {}
    for source in inventory["sources"]:
        require(source["status"] in INVENTORY_STATUSES,
                f"{source['id']}: unknown inventory status {source['status']!r}")
        sources[source["id"]] = source
    material = {}
    for entry in inventory.get("required_material", []):
        require(entry["status"] in INVENTORY_STATUSES,
                f"{entry['id']}: unknown material status {entry['status']!r}")
        material[entry["id"]] = entry

    seen, unmet = set(), []
    for item in gate["requirements"]:
        identifier = item["id"]
        require(identifier not in seen, f"{identifier}: duplicated")
        seen.add(identifier)
        require(item["status"] in {"met", "unmet"}, f"{identifier}: bad status")
        if item["status"] == "met":
            references = item.get("evidence") or []
            require(references,
                    f"{identifier}: marked met with no evidence; a tick nothing "
                    "resolves is how source scarcity becomes false certainty")
            for reference in references:
                resolved = reference in sources or (REPO_ROOT / reference).exists()
                require(resolved, f"{identifier}: evidence {reference!r} resolves to nothing")
        else:
            require(bool(item.get("open_because")),
                    f"{identifier}: an unmet requirement must say what is missing")
            for reference in item.get("awaiting", []):
                require(reference in material,
                        f"{identifier}: awaits {reference!r}, which the inventory "
                        "does not record as missing material")
            if item.get("blocking", True):
                unmet.append(identifier)

    answered = {reference for item in gate["requirements"]
                for reference in item.get("awaiting", [])}
    for identifier, entry in material.items():
        if entry["status"] in MISSING_STATUSES:
            require(identifier in answered,
                    f"{identifier}: recorded as missing and answered by no open "
                    "requirement; missing material must keep a gate item open")

    if previous is not None:
        was_met = {item["id"] for item in previous["requirements"] if item["status"] == "met"}
        now_met = {item["id"] for item in gate["requirements"] if item["status"] == "met"}
        require(not (was_met - now_met - {item["id"] for item in gate.get("reopened", [])}),
                f"{sorted(was_met - now_met)}: a met requirement was un-ticked without "
                "being recorded in `reopened`")

    verdict = "NOT ADMITTED" if unmet else "ADMISSIBLE"
    published = REPO_ROOT / "examples" / gate["candidate_id"]
    require(not (unmet and published.exists()),
            f"{gate['candidate_id']}: published under examples/ with "
            f"{len(unmet)} blocking requirements unmet")

    rendered = render(gate, verdict)
    prose_path = candidate / "admission.md"
    if write:
        prose_path.write_text(rendered)
    else:
        require(prose_path.is_file(), "admission.md is missing")
        require(prose_path.read_text() == rendered,
                "admission.md has drifted from admission.json; regenerate it with --write")

    met = len(seen) - len(unmet)
    print(f"{verdict}: {gate['candidate_id']} — {met}/{len(seen)} requirements met, "
          f"{len(unmet)} blocking")
    return verdict


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    gate_path = arguments.candidate / "admission.json"
    validate(gate_path, arguments.write, previously_committed(gate_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
