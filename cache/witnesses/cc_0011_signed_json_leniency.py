#!/usr/bin/env python3
"""CC-0011: does a lenient parser at a signed boundary actually split readers?

`counterexample` measures what mainstream parsers do with a duplicate member
name. The claim under test is that two honest consumers of the same signed bytes
end up with different documents — so this passes only if the parsers **disagree**.

`control` shows the same bytes are refused outright by a strict I-JSON reader,
which is what makes the leniency a choice rather than a necessity.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DOCUMENT = '{"products":{"a":1},"products":{"b":2}}'


def readings() -> dict[str, str]:
    """What each available parser makes of the same bytes."""
    found: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "dup.json"
        path.write_text(DOCUMENT)
        found["python"] = json.dumps(json.loads(DOCUMENT), sort_keys=True)
        probes = {
            "jq": ["jq", "-cS", ".", str(path)],
            "node": ["node", "-e",
                     f"const v=JSON.parse(require('fs').readFileSync({str(path)!r},'utf8'));"
                     "console.log(JSON.stringify(v))"],
            "ruby": ["ruby", "-rjson",
                     f"-e", f"puts JSON.generate(JSON.parse(File.read({str(path)!r})))"],
        }
        for name, argv in probes.items():
            if not shutil.which(argv[0]):
                continue
            result = subprocess.run(argv, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                try:
                    found[name] = json.dumps(json.loads(result.stdout), sort_keys=True)
                except json.JSONDecodeError:
                    continue
    return found


def main() -> int:
    half = sys.argv[1] if len(sys.argv) > 1 else "counterexample"
    if half == "counterexample":
        found = readings()
        for name, value in sorted(found.items()):
            print(f"  {name:8} -> {value}")
        distinct = set(found.values())
        print(f"{len(found)} parsers available, {len(distinct)} distinct reading(s)")
        # Passes only if the readers actually split. They did not, here.
        return 0 if len(distinct) > 1 else 1
    try:
        json.loads(DOCUMENT, object_pairs_hook=_reject_duplicates)
    except ValueError as refused:
        print("strict I-JSON reader refuses the document:", refused)
        return 0
    print("strict reader accepted a duplicate member — the control is broken")
    return 1


def _reject_duplicates(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate member name: {key}")
        seen[key] = value
    return seen


if __name__ == "__main__":
    raise SystemExit(main())
