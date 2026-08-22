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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.history import (committed_versions, inside_repository, rewritten_facts,
                           unexplained_vanished)  # noqa: E402

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


def validate(gate_path: Path, write: bool = False,
             history: list[dict] | None = None) -> str:
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
                inside = inside_repository(REPO_ROOT, reference)
                require(reference in sources or (inside is not None and inside.exists()),
                        f"{identifier}: evidence {reference!r} resolves to nothing "
                        "inside this repository")
            require(not item.get("awaiting"),
                    f"{identifier}: a met requirement cannot still await missing "
                    "material; awaiting on a closed item would answer the inventory "
                    "with nothing")
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
                if item["status"] == "unmet" and item.get("blocking", True)
                for reference in item.get("awaiting", [])}
    for identifier, entry in material.items():
        if entry["status"] in MISSING_STATUSES:
            require(identifier in answered,
                    f"{identifier}: recorded as missing and answered by no open "
                    "requirement; missing material must keep a gate item open")

    reopened = {entry["id"]: entry for entry in gate.get("reopened") or []}
    withdrawn = {entry["id"]: entry for entry in gate.get("withdrawn") or []}
    for entry in list(reopened.values()) + list(withdrawn.values()):
        require(bool(entry.get("reason")), f"{entry['id']}: recorded without a reason")
    now_met = {item["id"] for item in gate["requirements"] if item["status"] == "met"}
    for version in history or []:
        for item in version.get("requirements", []):
            identifier = item["id"]
            require(identifier in seen or identifier in withdrawn,
                    f"{identifier}: a requirement recorded in an earlier revision was "
                    "removed without being withdrawn with a reason")
            if item["status"] == "met":
                require(identifier in now_met or identifier in reopened,
                        f"{identifier}: was met in an earlier revision and is not "
                        "recorded as reopened")

    rewritten = rewritten_facts(history or [], "requirements", "id",
                                ("requirement", "blocking"), gate["requirements"],
                                set(withdrawn))
    require(not rewritten,
            f"{rewritten}: demanded something different in an earlier revision. What a "
            "requirement demands is settled when it is published; only whether it is "
            "met may change")

    vanished = unexplained_vanished(REPO_ROOT, "candidates/*/admission.json")
    require(not vanished,
            f"{vanished}: admission records were committed at these paths and are "
            "gone; a candidate that moves declares `moved_from`")

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
    gate = json.loads(gate_path.read_text())
    history = committed_versions(gate_path, lambda value: value.get("candidate_id"),
                                 gate.get("moved_from") or [])
    validate(gate_path, arguments.write, history)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
