#!/usr/bin/env python3
"""Say how much of this repository's own past is retained by anybody else.

Every guard here is enforced by reading git history, so all of them end at the
same boundary: a rewritten history removes a fact and the evidence of its removal
together. Closing that needs a witness outside this repository, which is a
dependency decision (`docs/proposals/external-pin.md`) and is not taken here.

What is taken here is the half that needs no dependency — naming the gap. A
revision that records depend on is pinned as `unwitnessed` until some party that
is not us is known to hold an observation of it, exactly as a case's source is
recorded as unwitnessed until an archive holds a capture. An honest zero is worth
more than an aspiration.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.history import committed_versions, rewritten_facts  # noqa: E402

SCHEMA = "decision-archaeology.revision-pins@v0"
PINS = REPO_ROOT / "pins" / "revisions.json"
COMMIT_URL = "https://github.com/s0fractal/decision-archaeology/commit/"
WAYBACK = "https://archive.org/wayback/available?url="
AGENT = "decision-archaeology/0 (revision pin probe)"
CUSTODY = {"independently-witnessed", "unwitnessed"}
TIMEOUT = 30


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cited_revisions() -> dict[str, list[str]]:
    """Revisions the repository's own records depend on being able to read."""
    cited: dict[str, list[str]] = {}
    for path in sorted((REPO_ROOT / "outcomes").glob("*.json")):
        document = json.loads(path.read_text())
        relative = path.relative_to(REPO_ROOT).as_posix()
        cited.setdefault(document["resolution"]["revision"], []).append(
            f"{relative}#resolution")
        if "rebuild" in document:
            cited.setdefault(document["rebuild"]["revision"], []).append(
                f"{relative}#rebuild")
    return {revision: sorted(why) for revision, why in sorted(cited.items())}


def known_locally(revision: str) -> bool:
    return subprocess.run(["git", "-C", str(REPO_ROOT), "cat-file", "-e", f"{revision}^{{commit}}"],
                          capture_output=True).returncode == 0


def archived(revision: str) -> dict | None:
    """Ask whether a public archive already holds this commit page.

    Read-only on purpose: asking what a third party kept is an observation,
    while asking it to keep something is publication, and that is the decision
    the proposal leaves open.
    """
    url = COMMIT_URL + revision
    try:
        request = urllib.request.Request(WAYBACK + urllib.parse.quote(url, safe=""),
                                         headers={"User-Agent": AGENT})
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            closest = json.load(response).get("archived_snapshots", {}).get("closest")
    except Exception:
        return None
    if not closest or not closest.get("available"):
        return None
    return {"kind": "public-web-archive", "provider": "web.archive.org",
            "observed_url": url, "snapshot_url": closest["url"],
            "snapshot_timestamp": closest["timestamp"]}


def refresh() -> dict:
    entries = []
    for revision, why in cited_revisions().items():
        observation = archived(revision)
        entries.append({
            "revision": revision,
            "relied_on_by": why,
            "custody": "independently-witnessed" if observation else "unwitnessed",
            "observation": observation,
        })
    return {"schema": SCHEMA,
            "checked_at": now(),
            "authority": "revision-retention-only",
            "non_claims": [
                "This records who is known to retain an observation of a revision; "
                "it does not make a revision authentic, correct, or adopted.",
                "An unwitnessed revision is not a compromised one. It is one whose "
                "survival depends entirely on this repository's own history.",
                "No observation is created here. Asking an archive what it kept is "
                "not asking it to keep anything.",
            ],
            "revisions": entries}


def validate(path: Path, history: list[dict] | None = None) -> None:
    pins = json.loads(path.read_text())
    require(pins["schema"] == SCHEMA, "revision pins: wrong schema")
    require(pins["authority"] == "revision-retention-only", "revision pins: bad authority")
    require(isinstance(pins.get("non_claims"), list) and pins["non_claims"],
            "revision pins: non_claims must not be empty")
    datetime.fromisoformat(pins["checked_at"].replace("Z", "+00:00"))

    cited = cited_revisions()
    recorded = {}
    for entry in pins["revisions"]:
        revision = entry["revision"]
        require(revision not in recorded, f"{revision}: recorded twice")
        recorded[revision] = entry
        require(entry["custody"] in CUSTODY, f"{revision}: bad custody state")
        require(known_locally(revision),
                f"{revision}: relied on by {entry['relied_on_by']} and not present in "
                "this checkout; the record depends on a revision nobody here can read")
        if entry["custody"] == "independently-witnessed":
            observation = entry["observation"]
            require(isinstance(observation, dict) and observation.get("snapshot_timestamp"),
                    f"{revision}: witnessed with no observation")
        else:
            require(entry["observation"] is None,
                    f"{revision}: carries an observation while recorded as unwitnessed")
    missing = sorted(set(cited) - set(recorded))
    require(not missing,
            f"{missing}: relied on by a record and absent from the pins; a revision "
            "a receipt depends on must state who retains it")

    rewritten = rewritten_facts(history or [], "revisions", "revision",
                               ("relied_on_by",), pins["revisions"])
    require(not rewritten, f"{rewritten}: why a revision is relied on was rewritten")
    for version in history or []:
        for before in version.get("revisions", []):
            if before.get("observation") is None:
                continue
            entry = recorded.get(before["revision"])
            require(entry is not None,
                    f"{before['revision']}: dropped from a record that witnessed it")
            require(entry.get("observation") is not None,
                    f"{before['revision']}: an observation recorded at "
                    f"{before['observation']['snapshot_timestamp']} disappeared")

    unwitnessed = sum(1 for entry in pins["revisions"] if entry["custody"] == "unwitnessed")
    total = len(pins["revisions"])
    print(f"PASS: {path.name} — {total} load-bearing revisions, "
          f"{total - unwitnessed} independently witnessed, {unwitnessed} retained by "
          "nobody but this repository")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true",
                        help="re-check whether anyone else is known to hold these revisions")
    arguments = parser.parse_args()
    PINS.parent.mkdir(exist_ok=True)
    history = committed_versions(PINS)
    if arguments.refresh:
        PINS.write_text(json.dumps(refresh(), ensure_ascii=False, indent=2) + "\n")
    validate(PINS, history)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
