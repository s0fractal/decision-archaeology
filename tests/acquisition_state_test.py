#!/usr/bin/env python3
"""Hostile boundary checks for the acquisition state record."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.acquisition_state import validate  # noqa: E402

CASE = REPO_ROOT / "examples" / "barite-bid-rigging-2025" / "sources"
INDEX = CASE / "source-index.json"
STATE = CASE / "acquisition-state.json"


def rejected(function, label: str) -> None:
    try:
        function()
    except (ValueError, KeyError):
        print(f"OK   {label}")
        return
    raise AssertionError(f"accepted a dishonest acquisition state: {label}")


def written(directory: Path, name: str, value: dict) -> Path:
    path = directory / name
    path.write_text(json.dumps(value, ensure_ascii=False))
    return path


def main() -> int:
    validate(STATE, INDEX)
    state = json.loads(STATE.read_text())

    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)

        claimed = json.loads(json.dumps(state))
        for entry in claimed["sources"]:
            entry["custody"] = "independently-witnessed"
        rejected(lambda: validate(written(directory, "claimed.json", claimed), INDEX),
                 "custody claimed as witnessed without a witness")

        hidden = json.loads(json.dumps(state))
        for entry in hidden["sources"]:
            if entry["witness"] is not None:
                entry["custody"] = "unwitnessed"
                entry["witness"] = None
        rejected(lambda: validate(written(directory, "hidden.json", hidden), INDEX,
                                  previous=state),
                 "a recorded witness dropped without a stated reason")

        dropped = json.loads(json.dumps(state))
        dropped["sources"] = dropped["sources"][:-1]
        rejected(lambda: validate(written(directory, "dropped.json", dropped), INDEX),
                 "source silently missing from the state")

        invented = json.loads(json.dumps(state))
        invented["sources"][0]["id"] = "source.invented"
        rejected(lambda: validate(written(directory, "invented.json", invented), INDEX),
                 "source absent from the case's own index")

        quiet = json.loads(json.dumps(state))
        quiet["non_claims"] = []
        rejected(lambda: validate(written(directory, "quiet.json", quiet), INDEX),
                 "state published without its interpretation boundaries")

    print("ACQUISITION-STATE-BOUNDARY: ALL PASS (5/5)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
