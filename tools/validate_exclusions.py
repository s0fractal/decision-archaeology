#!/usr/bin/env python3
"""Validate a case's recorded absences, and keep its prose bound to them.

An absence a reader has to infer from silence is not a limitation, it is a
liability: it reads as completeness. So a case records what it does not
establish as data — kind, subject, boundary, and what would resolve it — and the
readable `exclusions.md` is rendered from that record rather than written beside
it. An exclusion cannot vanish either: dropping one requires retiring it with a
reason, the same rule that governs a witness and an outcome receipt.

That last rule is checked against the record's whole history, not against `HEAD`.
Comparing a record to `HEAD` guards an uncommitted working tree and nothing else,
because after the commit `HEAD` is the change.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.history import committed_versions, rewritten_facts, unexplained_vanished  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "decision-archaeology.exclusions@v0"
REQUIRED_BY_KIND = {
    "not-located": ("search_boundary",),
    "access-restricted": ("restriction_basis",),
    "reported-only": ("reported_by",),
    "deliberately-minimized": ("minimization_basis",),
    "method-limited": ("method", "not_examined"),
    "non-probative": (),
    "out-of-scope": (),
}
HEADINGS = {
    "not-located": "Searched for and not located",
    "access-restricted": "Exists but access is restricted",
    "reported-only": "Reported without a primary source in hand",
    "deliberately-minimized": "Held but deliberately not republished",
    "method-limited": "Checked by a method with a stated reach",
    "non-probative": "Present, and does not prove what it is often read to prove",
    "out-of-scope": "Outside the frozen question",
}
KIND_ORDER = list(HEADINGS)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def render(record: dict) -> str:
    """The readable rendering. Deterministic, so drift is a diff."""
    lines = ["# Exclusions and limits", "",
             "Rendered from `exclusions.json`; edit the record, not this file.", ""]
    by_kind = {}
    for exclusion in record["exclusions"]:
        by_kind.setdefault(exclusion["kind"], []).append(exclusion)
    for kind in KIND_ORDER:
        entries = sorted(by_kind.get(kind, []), key=lambda item: item["id"])
        if not entries:
            continue
        lines.append(f"## {HEADINGS[kind]}")
        lines.append("")
        for entry in entries:
            lines.append(f"- **{entry['id']} — {entry['subject']}.** {entry['statement']}")
            for field, label in (("search_boundary", "Searched"),
                                 ("restriction_basis", "Restriction"),
                                 ("reported_by", "Reported by"),
                                 ("minimization_basis", "Minimization"),
                                 ("method", "Method")):
                if entry.get(field):
                    lines.append(f"  - {label}: {entry[field]}")
            if entry.get("not_examined"):
                lines.append(f"  - Not examined: {'; '.join(entry['not_examined'])}")
            if entry.get("would_resolve"):
                lines.append(f"  - Would resolve it: {entry['would_resolve']}")
            if entry.get("affects"):
                lines.append(f"  - Affects: {', '.join(entry['affects'])}")
        lines.append("")
    retired = record.get("retired") or []
    if retired:
        lines.append("## Retired")
        lines.append("")
        for entry in sorted(retired, key=lambda item: item["id"]):
            lines.append(f"- **{entry['id']}** retired {entry['retired_at']}: {entry['reason']}")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def validate(record_path: Path, prose_path: Path, history: list[dict] | None = None,
             write: bool = False) -> None:
    record = json.loads(record_path.read_text())
    require(record["schema"] == SCHEMA, "exclusions: wrong schema")
    require(record["case_id"] == record_path.parent.name,
            f"exclusions: case_id {record['case_id']!r} does not name the case "
            f"directory {record_path.parent.name!r}")
    require(record["authority"] == "recorded-absence-only", "exclusions: bad authority")
    require(isinstance(record["exclusions"], list) and record["exclusions"],
            "exclusions: a case that excludes nothing has not looked")

    seen = set()
    for exclusion in record["exclusions"]:
        identifier = exclusion["id"]
        require(identifier not in seen, f"{identifier}: duplicated")
        seen.add(identifier)
        kind = exclusion["kind"]
        require(kind in REQUIRED_BY_KIND, f"{identifier}: unknown kind {kind!r}")
        for field in REQUIRED_BY_KIND[kind]:
            require(bool(exclusion.get(field)),
                    f"{identifier}: kind {kind!r} requires {field}")
        allowed = {"id", "kind", "subject", "statement", "would_resolve", "affects",
                   *REQUIRED_BY_KIND[kind]}
        extra = set(exclusion) - allowed
        require(not extra,
                f"{identifier}: fields {sorted(extra)} do not belong to kind {kind!r}")
        if kind in ("not-located", "access-restricted"):
            require(bool(exclusion.get("would_resolve")),
                    f"{identifier}: an absence that nothing would resolve is a claim, "
                    "not a limitation")

    retired = {entry["id"]: entry for entry in record.get("retired") or []}
    for identifier, entry in retired.items():
        datetime.fromisoformat(entry["retired_at"].replace("Z", "+00:00"))
        require(identifier not in seen, f"{identifier}: retired and still listed")

    for version in history or []:
        for exclusion in version.get("exclusions", []):
            identifier = exclusion["id"]
            require(identifier in seen or identifier in retired,
                    f"{identifier}: recorded in an earlier revision and now neither "
                    "listed nor retired; an absence must be declared, not deleted")
        for entry in version.get("retired") or []:
            require(entry["id"] in retired or entry["id"] in seen,
                    f"{entry['id']}: was retired in an earlier revision and has since "
                    "been dropped from the record")

    rewritten = rewritten_facts(history or [], "exclusions", "id",
                                ("kind", "subject", "statement", "search_boundary",
                                 "restriction_basis", "reported_by",
                                 "minimization_basis", "method", "not_examined",
                                 "would_resolve"),
                                record["exclusions"], set(retired))
    require(not rewritten,
            f"{rewritten}: recorded with different substance in an earlier revision. "
            "An absence is settled once published: a different absence is a new entry, "
            "and the old one is retired")

    vanished = unexplained_vanished(REPO_ROOT, "examples/*/exclusions.json")
    require(not vanished,
            f"{vanished}: exclusion records were committed at these paths and are "
            "gone; a record that moves declares `moved_from`")

    rendered = render(record)
    if write:
        prose_path.write_text(rendered)
    else:
        require(prose_path.is_file(), f"{prose_path.name} is missing")
        require(prose_path.read_text() == rendered,
                f"{prose_path.name} has drifted from exclusions.json; "
                "regenerate it with --write")
    kinds = ", ".join(f"{sum(1 for e in record['exclusions'] if e['kind'] == kind)} {kind}"
                      for kind in KIND_ORDER
                      if any(e["kind"] == kind for e in record["exclusions"]))
    print(f"PASS: {record_path.name} — {len(seen)} exclusions ({kinds})")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case", type=Path)
    parser.add_argument("--write", action="store_true",
                        help="regenerate the readable exclusions.md from the record")
    arguments = parser.parse_args()
    record_path = arguments.case / "exclusions.json"
    prose_path = arguments.case / "exclusions.md"
    record = json.loads(record_path.read_text())
    history = committed_versions(record_path, lambda value: value.get("case_id"),
                                 record.get("moved_from") or [])
    validate(record_path, prose_path, history, arguments.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
