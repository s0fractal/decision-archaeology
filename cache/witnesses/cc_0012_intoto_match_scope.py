#!/usr/bin/env python3
"""CC-0012: what an in-toto MATCH rule actually constrains.

Run under an interpreter that has `in-toto==3.1.0`:

    python3 -m venv cache/witnesses/intoto-venv
    cache/witnesses/intoto-venv/bin/pip install in-toto==3.1.0

`counterexample` builds a layout whose only rule points at a step that does not
exist, and passes if verification succeeds — a constraint that appears in a
signed policy and constrains nothing.

`control` adds the terminal `DISALLOW *` and passes if verification now refuses,
which shows the protection comes from closing the rule set rather than from the
MATCH itself.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

from in_toto.models.layout import Layout, Step          # noqa: E402
from in_toto.models.link import Link                    # noqa: E402
from in_toto.models.metadata import Metablock           # noqa: E402
from in_toto.verifylib import in_toto_verify            # noqa: E402
from securesystemslib.signer import CryptoSigner        # noqa: E402

EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
GHOST = ["MATCH", "*", "WITH", "PRODUCTS", "FROM", "a-step-that-does-not-exist"]


def verifies(rules) -> bool:
    signer = CryptoSigner.generate_ed25519()
    key = signer.public_key
    key_dict = dict(key.to_dict())
    key_dict["keyid"] = key.keyid

    work = Path(tempfile.mkdtemp())
    previous = Path.cwd()
    os.chdir(work)
    try:
        Path("out.tar").write_text("")
        step = Step(name="build")
        step.expected_command = []
        step.expected_products = rules
        step.pubkeys = [key.keyid]
        step.threshold = 1

        layout = Layout(steps=[step], inspect=[], keys={key.keyid: key_dict})
        layout.expires = "2030-01-01T00:00:00Z"
        signed_layout = Metablock(signed=layout)
        signed_layout.create_signature(signer)

        link = Metablock(signed=Link(name="build", materials={},
                                     products={"out.tar": {"sha256": EMPTY_SHA256}}))
        link.create_signature(signer)
        link.dump(f"build.{key.keyid[:8]}.link")

        try:
            in_toto_verify(signed_layout, {key.keyid: key_dict})
            return True
        except Exception as refused:               # noqa: BLE001 - the answer, not an error
            print(f"  refused: {type(refused).__name__}: {str(refused)[:80]}")
            return False
    finally:
        os.chdir(previous)
        shutil.rmtree(work, ignore_errors=True)


def main() -> int:
    half = sys.argv[1] if len(sys.argv) > 1 else "counterexample"
    if half == "counterexample":
        passed = verifies([GHOST])
        print("a rule pointing at a non-existent step:",
              "verification PASSED" if passed else "verification refused")
        return 0 if passed else 1
    passed = verifies([GHOST, ["DISALLOW", "*"]])
    print("the same rule with a terminal DISALLOW *:",
          "verification PASSED" if passed else "verification refused")
    return 0 if not passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
