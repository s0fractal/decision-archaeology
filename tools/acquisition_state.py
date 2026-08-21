#!/usr/bin/env python3
"""Record what can still be checked about a case's external sources — and by whom.

A case cites public records it does not own. Three questions decide whether a
citation survives: can the source still be fetched, does anyone hold the exact
bytes that were read, and is that anyone independent of the publisher. The
answers change without warning, and none of the stack's protocols owns them:
OAIP opens no sockets by design, and SEV's loss manifest describes what a
projection cannot express, not what the world is missing.

So this is an application-side record, deliberately narrow. It attests
retrievability and custody. It says nothing about whether a source supports any
claim made from it.
"""

from __future__ import annotations

import argparse
import gzip
import subprocess
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
import zlib
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "decision-archaeology.acquisition-state@v0"
AGENT = "decision-archaeology/0 (case source acquisition state)"
WAYBACK = "https://archive.org/wayback/available?url="
TIMEOUT = 45

ACCESS = {"direct", "blocked", "unreachable"}
CUSTODY = {
    # the case commits bytes whose digest is recorded here
    "retained-locally",
    # a digest is recorded, but checking it needs the publisher to still serve
    # identical bytes: nobody else holds a copy
    "publisher-verifiable",
    # a third party independent of the publisher holds bytes we digested
    "independently-witnessed",
    # no retained bytes, no recorded digest, no third-party copy
    "unwitnessed",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(url: str) -> tuple[int, bytes, bytes, str | None, str | None]:
    """Return (status, raw bytes, decoded bytes, content type, encoding)."""
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        raw = response.read()
        encoding = response.headers.get("Content-Encoding")
        decoded = raw
        if encoding == "gzip":
            decoded = gzip.decompress(raw)
        elif encoding == "deflate":
            decoded = zlib.decompress(raw)
        return response.status, raw, decoded, response.headers.get("Content-Type"), encoding


def direct_access(url: str) -> dict:
    try:
        status, raw, _, content_type, _ = fetch(url)
        return {"status": "direct", "http_status": status, "bytes": len(raw),
                "content_type": content_type, "note": None}
    except urllib.error.HTTPError as error:
        return {"status": "blocked" if error.code in (401, 403, 429) else "unreachable",
                "http_status": error.code, "bytes": None, "content_type": None,
                "note": f"HTTP {error.code} for an automated client"}
    except Exception as error:  # network-level failure is an observation, not a crash
        return {"status": "unreachable", "http_status": None, "bytes": None,
                "content_type": None, "note": f"{type(error).__name__}"}


def witness(url: str) -> dict | None:
    """Ask a public web archive whether anyone but the publisher holds a copy."""
    try:
        with urllib.request.urlopen(
            urllib.request.Request(WAYBACK + urllib.parse.quote(url, safe=""),
                                   headers={"User-Agent": AGENT}), timeout=TIMEOUT
        ) as response:
            closest = json.load(response).get("archived_snapshots", {}).get("closest")
    except Exception:
        return None
    if not closest or not closest.get("available"):
        return None
    stamp = closest["timestamp"]
    exact = f"http://web.archive.org/web/{stamp}id_/{url}"
    try:
        status, raw, decoded, content_type, encoding = fetch(exact)
    except Exception:
        return None
    if status != 200:
        return None
    return {"kind": "public-web-archive", "provider": "web.archive.org",
            "snapshot_url": closest["url"], "snapshot_timestamp": stamp,
            "exact_bytes_url": exact, "content_type": content_type,
            "content_encoding": encoding,
            "raw_bytes": len(raw), "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "decoded_bytes": len(decoded),
            "decoded_sha256": hashlib.sha256(decoded).hexdigest()}


def custody_of(source: dict, recorded_witness: dict | None) -> str:
    if source.get("retention") == "committed-raw":
        return "retained-locally"
    if recorded_witness is not None:
        return "independently-witnessed"
    if source.get("raw_sha256"):
        return "publisher-verifiable"
    return "unwitnessed"


def refresh(index_path: Path) -> dict:
    index = json.loads(index_path.read_text())
    entries = []
    for source in index["sources"]:
        url = source.get("url")
        if not url:
            continue
        found = witness(url)
        entries.append({
            "id": source["id"],
            "url": url,
            "authority": source["authority"],
            "access": direct_access(url),
            "witness": found,
            "custody": custody_of(source, found),
        })
    return {"schema": SCHEMA,
            "case_id": index_path.resolve().parents[1].name,
            "source_index": index_path.name,
            "checked_at": now(),
            "authority": "retrievability-and-custody-only",
            "non_claims": [
                "This records whether a source can still be retrieved and who holds "
                "its bytes; it does not establish that any source supports any claim.",
                "A blocked automated fetch is a fact about this client, not evidence "
                "that a publisher withheld anything.",
                "An archived copy attests bytes a third party captured at a time, not "
                "that the publisher served the same bytes to everyone.",
            ],
            "sources": entries}


def previously_committed(state_path: Path) -> dict | None:
    """The last committed version of this record, if the repository holds one.

    A witness is a fact about the past: someone independent held these bytes at
    that time. Dropping one silently would make the record describe the present
    instead, which is the failure an outcome receipt already taught us to close.
    """
    try:
        relative = state_path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return None
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"HEAD:{relative.as_posix()}"],
        capture_output=True)
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def validate(state_path: Path, index_path: Path, previous: dict | None = None) -> None:
    state = json.loads(state_path.read_text())
    require(state["schema"] == SCHEMA, "acquisition state: wrong schema")
    require(state["authority"] == "retrievability-and-custody-only",
            "acquisition state: bad authority")
    require(isinstance(state.get("non_claims"), list) and state["non_claims"],
            "acquisition state: non_claims must not be empty")
    datetime.fromisoformat(state["checked_at"].replace("Z", "+00:00"))

    index = json.loads(index_path.read_text())
    expected = {source["id"]: source for source in index["sources"] if source.get("url")}
    seen = set()
    for entry in state["sources"]:
        identifier = entry["id"]
        require(identifier in expected, f"{identifier}: not in the source index")
        require(identifier not in seen, f"{identifier}: duplicated")
        seen.add(identifier)
        require(entry["url"] == expected[identifier]["url"],
                f"{identifier}: url differs from the source index")
        require(set(entry) <= {"id", "url", "authority", "access", "witness", "custody",
                               "witness_withdrawn"},
                f"{identifier}: unknown fields {sorted(set(entry) - {'id', 'url', 'authority', 'access', 'witness', 'custody', 'witness_withdrawn'})}")
        require(entry["access"]["status"] in ACCESS, f"{identifier}: bad access status")
        require(entry["custody"] in CUSTODY, f"{identifier}: bad custody state")
        found = entry["witness"]
        if entry["custody"] == "independently-witnessed":
            require(isinstance(found, dict), f"{identifier}: witnessed without a witness")
            for field in ("snapshot_timestamp", "raw_sha256", "decoded_sha256"):
                require(bool(found.get(field)), f"{identifier}: witness lacks {field}")
        if entry["custody"] == "unwitnessed":
            require(found is None and not expected[identifier].get("raw_sha256"),
                    f"{identifier}: recorded as unwitnessed while evidence exists")
        if entry["custody"] == "publisher-verifiable":
            require(bool(expected[identifier].get("raw_sha256")),
                    f"{identifier}: publisher-verifiable without a recorded digest")
    require(seen == set(expected), f"acquisition state: sources differ: "
                                   f"{sorted(seen ^ set(expected))}")
    if previous is not None:
        witnessed = {entry["id"]: entry for entry in previous["sources"]
                     if entry.get("witness") is not None}
        current = {entry["id"]: entry for entry in state["sources"]}
        for identifier, before in witnessed.items():
            entry = current.get(identifier)
            require(entry is not None,
                    f"{identifier}: dropped from a record that witnessed it")
            if entry.get("witness") is None:
                withdrawn = entry.get("witness_withdrawn")
                require(isinstance(withdrawn, dict) and withdrawn.get("reason"),
                        f"{identifier}: a witness recorded at "
                        f"{before['witness']['snapshot_timestamp']} disappeared without "
                        "a stated reason; absence must be declared, not produced")

    counts = {}
    for entry in state["sources"]:
        counts[entry["custody"]] = counts.get(entry["custody"], 0) + 1
    summary = ", ".join(f"{count} {name}" for name, count in sorted(counts.items()))
    print(f"PASS: {state_path.name} — {len(seen)} sources ({summary})")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case", type=Path, help="case directory")
    parser.add_argument("--refresh", action="store_true",
                        help="re-check retrievability and custody over the network")
    arguments = parser.parse_args()
    index_path = arguments.case / "sources" / "source-index.json"
    state_path = arguments.case / "sources" / "acquisition-state.json"
    previous = previously_committed(state_path)
    if arguments.refresh:
        state = refresh(index_path)
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
        print(f"refreshed {state_path}")
    validate(state_path, index_path, previous)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
