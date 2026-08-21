#!/usr/bin/env python3
"""Validate Decision Archaeology need packets with the standard library."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


REQUEST_ID = re.compile(r"^DA-[A-Z0-9]+-[0-9]{4}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
REQUEST_STATUSES = {"draft", "filed", "triaged", "fulfilled", "declined", "blocked", "superseded"}
PLACEMENTS = {"unknown", "existing-contract", "application-adapter", "profile", "protocol"}
DISPOSITIONS = {
    "untriaged",
    "already-supported",
    "application-adapter",
    "profile-change",
    "protocol-candidate",
    "wrong-owner",
    "declined",
    "blocked",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text())
    require(isinstance(value, dict), f"{path}: expected JSON object")
    return value


def exact_keys(value: dict[str, object], expected: set[str], label: str) -> None:
    require(set(value) == expected, f"{label}: keys differ: {sorted(set(value) ^ expected)}")


def nonempty(value: object, label: str) -> None:
    require(isinstance(value, str) and bool(value.strip()), f"{label}: expected non-empty string")


def iso_datetime(value: object, label: str) -> None:
    nonempty(value, label)
    datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def validate_packet(packet: Path) -> None:
    manifest = load_object(packet / "manifest.json")
    disposition = load_object(packet / "disposition.json")

    exact_keys(
        manifest,
        {"$schema", "schema", "template", "id", "status", "source", "target", "need", "reproducer", "boundaries", "provenance", "paths"},
        "manifest",
    )
    require(manifest["schema"] == "decision-archaeology.need@v0", "manifest: wrong schema")
    require(re.fullmatch(r"decision-archaeology\.need-template@v0\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?", str(manifest["template"])) is not None, "manifest: bad template identity")
    require(REQUEST_ID.fullmatch(str(manifest["id"])) is not None, "manifest: bad request id")
    require(manifest["status"] in REQUEST_STATUSES, "manifest: bad status")

    source = manifest["source"]
    require(isinstance(source, dict), "source: expected object")
    exact_keys(source, {"repository", "revision", "case_id", "artifacts"}, "source")
    nonempty(source["repository"], "source.repository")
    require(HEX40.fullmatch(str(source["revision"])) is not None, "source.revision: expected exact commit")
    nonempty(source["case_id"], "source.case_id")
    require(isinstance(source["artifacts"], list) and source["artifacts"], "source.artifacts: expected non-empty list")
    for index, artifact in enumerate(source["artifacts"]):
        require(isinstance(artifact, dict), f"source.artifacts[{index}]: expected object")
        exact_keys(artifact, {"path", "sha256"}, f"source.artifacts[{index}]")
        nonempty(artifact["path"], f"source.artifacts[{index}].path")
        require(HEX64.fullmatch(str(artifact["sha256"])) is not None, f"source.artifacts[{index}].sha256: expected SHA-256")

    target = manifest["target"]
    require(isinstance(target, dict), "target: expected object")
    exact_keys(target, {"repository", "revision", "surface"}, "target")
    nonempty(target["repository"], "target.repository")
    require(HEX40.fullmatch(str(target["revision"])) is not None, "target.revision: expected exact commit")
    nonempty(target["surface"], "target.surface")

    need = manifest["need"]
    require(isinstance(need, dict), "need: expected object")
    exact_keys(need, {"blocked_operation", "current_behavior", "required_capability", "local_workaround", "why_workaround_is_insufficient", "candidate_placement"}, "need")
    for field in need.keys() - {"candidate_placement"}:
        nonempty(need[field], f"need.{field}")
    require(need["candidate_placement"] in PLACEMENTS, "need.candidate_placement: bad value")

    reproducer = manifest["reproducer"]
    require(isinstance(reproducer, dict), "reproducer: expected object")
    exact_keys(reproducer, {"command", "expected", "counterexample"}, "reproducer")
    for field, value in reproducer.items():
        nonempty(value, f"reproducer.{field}")

    boundaries = manifest["boundaries"]
    require(isinstance(boundaries, dict), "boundaries: expected object")
    exact_keys(boundaries, {"data_minimization", "non_claims"}, "boundaries")
    nonempty(boundaries["data_minimization"], "boundaries.data_minimization")
    require(isinstance(boundaries["non_claims"], list) and boundaries["non_claims"], "boundaries.non_claims: expected non-empty list")
    for index, claim in enumerate(boundaries["non_claims"]):
        nonempty(claim, f"boundaries.non_claims[{index}]")

    provenance = manifest["provenance"]
    require(isinstance(provenance, dict), "provenance: expected object")
    exact_keys(provenance, {"producer", "generated_at", "authority"}, "provenance")
    nonempty(provenance["producer"], "provenance.producer")
    iso_datetime(provenance["generated_at"], "provenance.generated_at")
    require(provenance["authority"] == "case-derived-demand-only", "provenance.authority: bad value")

    paths = manifest["paths"]
    require(paths == {"narrative": "request.md", "fixtures": "fixtures/", "disposition": "disposition.json"}, "paths: bad closed layout")
    require((packet / "request.md").is_file(), "packet: missing request.md")
    require((packet / "fixtures").is_dir(), "packet: missing fixtures/")

    exact_keys(disposition, {"$schema", "schema", "request_id", "status", "owner_surface", "rationale", "next_action", "decided_at", "decided_by", "authority"}, "disposition")
    require(disposition["schema"] == "decision-archaeology.need-disposition@v0", "disposition: wrong schema")
    require(disposition["request_id"] == manifest["id"], "disposition: request id mismatch")
    require(disposition["status"] in DISPOSITIONS, "disposition: bad status")
    for field in ("owner_surface", "rationale", "next_action"):
        nonempty(disposition[field], f"disposition.{field}")
    require(disposition["authority"] == "non-normative-routing-only", "disposition.authority: bad value")
    if disposition["status"] == "untriaged":
        require(disposition["decided_at"] is None and disposition["decided_by"] is None, "untriaged disposition must not name a decision")
    else:
        iso_datetime(disposition["decided_at"], "disposition.decided_at")
        nonempty(disposition["decided_by"], "disposition.decided_by")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packets", nargs="+", type=Path)
    args = parser.parse_args()
    for packet in args.packets:
        validate_packet(packet)
        print(f"PASS: {packet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
