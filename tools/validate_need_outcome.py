#!/usr/bin/env python3
"""Validate need outcome receipts against the revisions they pin.

Artifact digests are checked against the blob at the outcome's own
`resolution.revision`, never against the working tree. An outcome is a record of
what resolved a need at a point in history; a later improvement to a resolved
artifact must not be able to break it, because the only cheap way to "fix" that
failure is to rewrite the record until it matches the present.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.history import deleted_since_first_commit  # noqa: E402


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


def blob_at_revision(revision: str, relative: Path, label: str) -> bytes:
    """Read one path as it existed at an exact revision of this repository."""
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "cat-file", "blob", f"{revision}:{relative.as_posix()}"],
        capture_output=True,
    )
    require(
        result.returncode == 0,
        f"{label}: cannot read {relative.as_posix()} at {revision}. The pinned "
        "revision and path must exist in this checkout; a shallow clone needs "
        "full history (actions/checkout with fetch-depth: 0).",
    )
    return result.stdout


def artifact(value: object, label: str, revision: str | None) -> None:
    require(isinstance(value, dict), f"{label}: expected object")
    exact_keys(value, {"path", "sha256"}, label)
    nonempty(value["path"], f"{label}.path")
    require(HEX64.fullmatch(str(value["sha256"])) is not None,
            f"{label}.sha256: expected SHA-256")
    if revision is None:
        return
    relative = Path(str(value["path"]))
    require(not relative.is_absolute() and ".." not in relative.parts,
            f"{label}: path must remain inside the repository")
    require((REPO_ROOT / relative).resolve().is_relative_to(REPO_ROOT.resolve()),
            f"{label}: resolved path escapes the repository")
    actual = hashlib.sha256(blob_at_revision(revision, relative, label)).hexdigest()
    require(actual == value["sha256"],
            f"{label}: digest does not match the artifact at {revision}")


def validate_outcome(outcome_path: Path, verify_content: bool) -> None:
    outcome = load_object(outcome_path)
    exact_keys(
        outcome,
        {
            "$schema", "schema", "request_id", "status", "classification",
            "target", "resolution", "replay", "rebuild", "recorded_at", "producer",
            "authority", "non_claims",
        },
        "outcome",
    )
    require(outcome["schema"] == "decision-archaeology.need-outcome@v1",
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
    artifact(target["disposition"], "target.disposition", None)   # another repository

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
    pinned = str(resolution["revision"]) if verify_content else None
    for index, value in enumerate(resolution["artifacts"]):
        artifact(value, f"resolution.artifacts[{index}]", pinned)

    replay = outcome["replay"]
    require(isinstance(replay, dict), "replay: expected object")
    exact_keys(replay, {"case_id", "command", "expected", "receipt"}, "replay")
    for field in ("case_id", "command", "expected"):
        nonempty(replay[field], f"replay.{field}")
    artifact(replay["receipt"], "replay.receipt", pinned)

    rebuild = outcome["rebuild"]
    require(isinstance(rebuild, dict), "rebuild: expected object")
    exact_keys(rebuild, {"revision", "path", "sha256", "command", "derived_from",
                         "excludes"}, "rebuild")
    require(HEX40.fullmatch(str(rebuild["revision"])) is not None,
            "rebuild.revision: expected exact commit")
    for field in ("command", "derived_from"):
        nonempty(rebuild[field], f"rebuild.{field}")
    require(str(rebuild["derived_from"]) in {str(value.get("path"))
                                             for value in resolution["artifacts"]},
            "rebuild.derived_from: must name one of the resolution artifacts, so the "
            "rebuild follows a published description rather than private notes")
    require(isinstance(rebuild["excludes"], list) and rebuild["excludes"],
            "rebuild.excludes: name at least one implementation the rebuild must not read")
    for index, excluded in enumerate(rebuild["excludes"]):
        nonempty(excluded, f"rebuild.excludes[{index}]")
    if verify_content:
        artifact({"path": rebuild["path"], "sha256": rebuild["sha256"]},
                 "rebuild", str(rebuild["revision"]))
        source = blob_at_revision(str(rebuild["revision"]), Path(str(rebuild["path"])),
                                  "rebuild")
        forbidden = {Path(str(name)).stem for name in rebuild["excludes"]}
        imported = set()
        for statement in ast.walk(ast.parse(source, filename=str(rebuild["path"]))):
            if isinstance(statement, ast.Import):
                imported.update(alias.name for alias in statement.names)
            elif isinstance(statement, ast.ImportFrom) and statement.module:
                imported.add(statement.module)
        offending = {name for name in imported if name.split(".")[-1] in forbidden}
        require(not offending,
                f"rebuild: imports what it is supposed to verify independently "
                f"({', '.join(sorted(offending))})")

    datetime.fromisoformat(str(outcome["recorded_at"]).replace("Z", "+00:00"))
    nonempty(outcome["producer"], "outcome.producer")
    require(outcome["authority"] == "outcome-linkage-only", "outcome: bad authority")
    require(isinstance(outcome["non_claims"], list) and outcome["non_claims"],
            "outcome.non_claims: expected non-empty list")
    for index, claim in enumerate(outcome["non_claims"]):
        nonempty(claim, f"outcome.non_claims[{index}]")


def no_outcome_was_deleted(root: Path) -> None:
    gone = deleted_since_first_commit(root, "outcomes/")
    require(not gone, f"{gone}: recorded outcomes were deleted; a closed need stays "
                      "closed in the record, whatever happened afterwards")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("outcomes", nargs="+", type=Path)
    parser.add_argument("--no-artifact-content", action="store_true",
                        help="validate structure only, without reading pinned blobs")
    args = parser.parse_args()
    no_outcome_was_deleted(REPO_ROOT)
    for outcome_path in args.outcomes:
        validate_outcome(outcome_path, not args.no_artifact_content)
        print(f"PASS: {outcome_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
