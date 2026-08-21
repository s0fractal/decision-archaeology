#!/usr/bin/env python3
"""Hostile boundary checks for the profile publication rule."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.validate_profile import validate_profile  # noqa: E402


LISTING_DOC = """# Example profile v0

## Construction listing (byte-determining)

1. Compile the gates in this order and refer to them by hash.
"""

REBUILD = '''"""Rebuild from example-profile-v0.md, checking example_profile_v0.vectors.json."""
print("ok")
'''


def rejected(function, label: str) -> None:
    try:
        function()
    except ValueError:
        print(f"OK   {label}")
        return
    raise AssertionError(f"accepted a profile that should not publish: {label}")


def scaffold(root: Path, document_text: str, rebuild_text: str,
             with_reference: bool = True) -> tuple[Path, Path, Path]:
    profiles, tests = root / "profiles", root / "tests"
    profiles.mkdir(parents=True); tests.mkdir(parents=True)
    document = profiles / "example-profile-v0.md"
    document.write_text(document_text)
    (profiles / "example_profile_v0.vectors.json").write_text(
        json.dumps({"vectors": [{"id": "only", "claim": {}, "expected": {}}]}))
    if with_reference:
        (profiles / "example_profile_v0.py").write_text("VALUE = 1\n")
    (tests / "example_profile_v0_doc_replay_test.py").write_text(rebuild_text)
    return document, profiles, tests


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        document, profiles, tests = scaffold(Path(temporary) / "ok", LISTING_DOC, REBUILD)
        validate_profile(document, run=False, profiles_dir=profiles, tests_dir=tests)

        document, profiles, tests = scaffold(
            Path(temporary) / "no-listing", "# Example profile v0\n\nSemantics only.\n", REBUILD)
        rejected(lambda: validate_profile(document, run=False, profiles_dir=profiles,
                                          tests_dir=tests),
                 "profile without a construction listing")

        document, profiles, tests = scaffold(
            Path(temporary) / "imports", LISTING_DOC,
            REBUILD + "from profiles.example_profile_v0 import VALUE\n")
        rejected(lambda: validate_profile(document, run=False, profiles_dir=profiles,
                                          tests_dir=tests),
                 "rebuild that imports the reference implementation")

        document, profiles, tests = scaffold(
            Path(temporary) / "reads", LISTING_DOC,
            REBUILD + 'SOURCE = "profiles/example_profile_v0.py"\n')
        rejected(lambda: validate_profile(document, run=False, profiles_dir=profiles,
                                          tests_dir=tests),
                 "rebuild that reads the reference implementation as a path")

        document, profiles, tests = scaffold(
            Path(temporary) / "no-vectors", LISTING_DOC, REBUILD)
        (profiles / "example_profile_v0.vectors.json").unlink()
        rejected(lambda: validate_profile(document, run=False, profiles_dir=profiles,
                                          tests_dir=tests),
                 "profile without frozen vectors")

    print("PROFILE-PUBLICATION-BOUNDARY: ALL PASS (5/5)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
