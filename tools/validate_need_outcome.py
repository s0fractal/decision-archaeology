#!/usr/bin/env python3
"""Validate need outcome receipts and their local immutable artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUEST_ID = re.compile(r"^DA-[A-Z0-9]+-[0-9]{4}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
STATUSES = {"fulfilled", "declined", "blocked", "superseded"}
CLASSIFICATIONS = {
    "already-supported",
    "application-adapter",
    "profile-change",
    "protocol-candidate",
    "wrong-owner",
    "declined",
    "blocked",
}
STATUS_CLASSIFICATIONS = {
    "fulfilled": {"already-supported", "application-adapter", "profile-change"},
    "declined": {"declined", "wrong-owner"},
    "blocked": {"blocked", "protocol-candidate"},
    "superseded": CLASSIFICATIONS,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def exact_keys(value: dict[str, object], expected: set[str], label: str) -> None:
    require(set(value) == expected,
            f"{label}: keys differ: {sorted(map(repr, set(value) ^ expected))}")


def nonempty(value: object, label: str) -> None:
    require(isinstance(value, str) and bool(value.strip()),
            f"{label}: expected non-empty string")


def load_object(outcome_path: Path) -> dict[str, object]:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result = {}
        for key, value in pairs:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result

    outcome = json.loads(outcome_path.read_bytes(), object_pairs_hook=reject_duplicates)
    require(isinstance(outcome, dict), "outcome: expected object")
    return outcome


def artifact(value: object, label: str, verify_local: bool) -> None:
    require(isinstance(value, dict), f"{label}: expected object")
    exact_keys(value, {"path", "sha256"}, label)
    nonempty(value["path"], f"{label}.path")
    require(HEX64.fullmatch(str(value["sha256"])) is not None,
            f"{label}.sha256: expected SHA-256")
    if verify_local:
        relative = Path(str(value["path"]))
        require(not relative.is_absolute() and ".." not in relative.parts,
                f"{label}: path must remain inside the repository")
        artifact_path = (REPO_ROOT / relative).resolve()
        require(artifact_path.is_relative_to(REPO_ROOT.resolve()),
                f"{label}: resolved path escapes the repository")
        require(artifact_path.is_file(), f"{label}: local artifact is missing")
        actual = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        require(actual == value["sha256"], f"{label}: local artifact digest changed")


def validate_outcome(outcome_path: Path, verify_local: bool) -> None:
    outcome = load_object(outcome_path)
    exact_keys(
        outcome,
        {
            "$schema", "schema", "request_id", "status", "classification",
            "target", "resolution", "replay", "recorded_at", "producer",
            "authority", "non_claims",
        },
        "outcome",
    )
    require(outcome["schema"] == "decision-archaeology.need-outcome@v0",
            "outcome: wrong schema")
    nonempty(outcome["$schema"], "outcome.$schema")
    require(REQUEST_ID.fullmatch(str(outcome["request_id"])) is not None,
            "outcome: bad request id")
    require(outcome["status"] in STATUSES, "outcome: bad status")
    require(outcome["classification"] in CLASSIFICATIONS,
            "outcome: bad classification")
    require(outcome["classification"] in STATUS_CLASSIFICATIONS[outcome["status"]],
            "outcome: status and classification are inconsistent")

    target = outcome["target"]
    require(isinstance(target, dict), "target: expected object")
    exact_keys(target, {"repository", "disposition_revision", "disposition"}, "target")
    nonempty(target["repository"], "target.repository")
    require(str(target["repository"]).startswith("https://"),
            "target.repository: expected HTTPS repository")
    require(HEX40.fullmatch(str(target["disposition_revision"])) is not None,
            "target.disposition_revision: expected exact commit")
    artifact(target["disposition"], "target.disposition", False)

    resolution = outcome["resolution"]
    require(isinstance(resolution, dict), "resolution: expected object")
    exact_keys(resolution, {"repository", "revision", "profile", "artifacts"},
               "resolution")
    nonempty(resolution["repository"], "resolution.repository")
    require(str(resolution["repository"]).startswith("https://"),
            "resolution.repository: expected HTTPS repository")
    require(HEX40.fullmatch(str(resolution["revision"])) is not None,
            "resolution.revision: expected exact commit")
    nonempty(resolution["profile"], "resolution.profile")
    require(isinstance(resolution["artifacts"], list) and resolution["artifacts"],
            "resolution.artifacts: expected non-empty list")
    for index, value in enumerate(resolution["artifacts"]):
        artifact(value, f"resolution.artifacts[{index}]", verify_local)

    replay = outcome["replay"]
    require(isinstance(replay, dict), "replay: expected object")
    exact_keys(replay, {"case_id", "command", "expected", "receipt"}, "replay")
    for field in ("case_id", "command", "expected"):
        nonempty(replay[field], f"replay.{field}")
    artifact(replay["receipt"], "replay.receipt", verify_local)

    datetime.fromisoformat(str(outcome["recorded_at"]).replace("Z", "+00:00"))
    nonempty(outcome["producer"], "outcome.producer")
    require(outcome["authority"] == "outcome-linkage-only", "outcome: bad authority")
    require(isinstance(outcome["non_claims"], list) and outcome["non_claims"],
            "outcome.non_claims: expected non-empty list")
    for index, claim in enumerate(outcome["non_claims"]):
        nonempty(claim, f"outcome.non_claims[{index}]")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("outcomes", nargs="+", type=Path)
    parser.add_argument("--no-local-artifacts", action="store_true")
    args = parser.parse_args()
    for outcome_path in args.outcomes:
        validate_outcome(outcome_path, not args.no_local_artifacts)
        print(f"PASS: {outcome_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
