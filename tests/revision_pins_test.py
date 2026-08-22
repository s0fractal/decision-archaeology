#!/usr/bin/env python3
"""Hostile boundary checks for what the repository claims about its own past."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.revision_pins import PINS, validate  # noqa: E402


def rejected(function, label: str) -> None:
    try:
        function()
    except (ValueError, KeyError):
        print(f"OK   {label}")
        return
    raise AssertionError(f"accepted a dishonest claim about retention: {label}")


def written(directory: Path, name: str, value: dict) -> Path:
    path = directory / name
    path.write_text(json.dumps(value, ensure_ascii=False))
    return path


def main() -> int:
    validate(PINS)
    pins = json.loads(PINS.read_text())

    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)

        dropped = copy.deepcopy(pins)
        dropped["revisions"] = dropped["revisions"][:-1]
        rejected(lambda: validate(written(directory, "dropped.json", dropped)),
                 "a revision a receipt depends on, left out of the pins")

        claimed = copy.deepcopy(pins)
        for entry in claimed["revisions"]:
            entry["custody"] = "independently-witnessed"
        rejected(lambda: validate(written(directory, "claimed.json", claimed)),
                 "retention claimed with no observation behind it")

        contradictory = copy.deepcopy(pins)
        contradictory["revisions"][0]["observation"] = {
            "kind": "public-web-archive", "provider": "web.archive.org",
            "snapshot_timestamp": "20260101000000"}
        rejected(lambda: validate(written(directory, "contradictory.json", contradictory)),
                 "an observation carried while recorded as unwitnessed")

        unknown = copy.deepcopy(pins)
        unknown["revisions"][0]["revision"] = "0" * 40
        rejected(lambda: validate(written(directory, "unknown.json", unknown)),
                 "a pinned revision this checkout cannot read")

        witnessed = copy.deepcopy(pins)
        witnessed["revisions"][0]["custody"] = "independently-witnessed"
        witnessed["revisions"][0]["observation"] = {
            "kind": "public-web-archive", "provider": "web.archive.org",
            "observed_url": "https://example.invalid/", "snapshot_url": "…",
            "snapshot_timestamp": "20260101000000"}
        rejected(lambda: validate(written(directory, "erased.json", pins),
                                  history=[witnessed]),
                 "an observation recorded earlier and quietly dropped")

        quiet = copy.deepcopy(pins)
        quiet["non_claims"] = []
        rejected(lambda: validate(written(directory, "quiet.json", quiet)),
                 "retention published without its interpretation boundaries")

    print("REVISION-PIN-BOUNDARY: ALL PASS (6/6)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
