#!/usr/bin/env python3
"""Carry a case's Sigma check into Warrant as a re-runnable `ski@v1` reason.

Warrant needed nothing added for this. Its `ski@v1` runtime is Sigma-Glyph
Book I v0.5, its blob store IS the Sigma CAS, and the filer re-executes a claimed
verdict before it will file. So this is an adapter, not a request: it writes the
profile's term into a Warrant store, emits the check document, and proves the
round trip — file, re-execute, verify — with the pinned `warrant-verify` release.

Signing is deliberately left out of the repository. Filing needs an actor key,
which is an identity decision rather than a build artifact, so this module files
under an ephemeral key in a temporary store to prove the path works. What is
committed is the deterministic part: the check document a verifier re-runs.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from profiles.sigma_money_add_eq_v0 import (  # noqa: E402
    PROFILE_ID, _boolean_normal_hashes, encode,
)

ADAPTER_ID = "decision-archaeology.warrant-ski-reason@v0"
CASE_ROOT = REPO_ROOT / "examples" / "barite-bid-rigging-2025"
RECEIPT_PATH = CASE_ROOT / "receipts" / "warrant-ski-reason-v0.json"
SIGMA_RECEIPT = CASE_ROOT / "receipts" / "sigma-money-add-eq-v0.json"
ATP_BUDGET = 1_000_000
FILED_AT = 1755777600  # fixed so a filing is reproducible except for its key
CHECK_RESULT = re.compile(r"(pass|fail)\s+result=([0-9a-f]{64})\s+atp_spent=(\d+)")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def warrant(store: Path, *arguments: str, expect_verdict: bool = False) -> str:
    """Run the pinned CLI. `warrant check` exits nonzero on a `fail` verdict,
    which is an answer rather than an error, so those calls read the verdict."""
    executable = shutil.which("warrant")
    require(executable is not None,
            "the pinned warrant-verify release is not on PATH; run through mise")
    result = subprocess.run([executable, "--store", str(store), *arguments],
                            capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()
    if not expect_verdict:
        require(result.returncode == 0,
                f"warrant {' '.join(arguments[:2])} failed: {output}")
    return output


def check_document(claim: dict) -> tuple[dict, bytes, dict]:
    """The ski@v1 document a verifier re-runs, plus the nodes it needs."""
    encoded = encode(claim)
    true_hash, _ = _boolean_normal_hashes()
    document = {"atp": ATP_BUDGET, "expect": true_hash.hex(), "ski": 1,
                "term": encoded.term_hash.hex()}
    return document, encoded.term_hash, encoded.store.m


def populate(store: Path, nodes: dict, document: dict) -> str:
    blobs = store / "blobs"
    for digest, payload in nodes.items():
        (blobs / digest.hex()).write_bytes(payload)
    document_path = store / "check.json"
    document_path.write_text(json.dumps(document, sort_keys=True, separators=(",", ":")))
    return warrant(store, "blob", "add", str(document_path)).splitlines()[-1]


def round_trip(claim: dict, store: Path) -> dict:
    """File the check as a reason, re-execute it, and verify the record."""
    warrant(store, "init")
    document, _, nodes = check_document(claim)
    check_hash = populate(store, nodes, document)

    executed = warrant(store, "check", check_hash, expect_verdict=True)
    matched = CHECK_RESULT.search(executed)
    require(matched is not None, f"unexpected check output: {executed!r}")
    verdict, result_hash, atp_spent = matched.group(1), matched.group(2), int(matched.group(3))
    require(verdict == "pass", f"the case's own claim did not re-execute: {executed}")
    require(result_hash == document["expect"], "re-execution reached a different normal form")

    policy = warrant(store, "blob", "add",
                     str(REPO_ROOT / "profiles" / "sigma-money-add-eq-v0.md")).splitlines()[-1]
    subject = warrant(store, "blob", "add", str(SIGMA_RECEIPT)).splitlines()[-1]
    warrant(store, "keygen", "--out", str(store / "ephemeral.key"))
    record = warrant(
        store, "accept", "--subject", subject, "--under", policy, "--check", check_hash,
        "--runtime", "ski@v1", "--verdict", "pass",
        "--note", "barite exact-sum check executed under sigma-money-add-eq@v0",
        "--reason", "Attests execution of the arithmetic check only, not the AMCU finding.",
        "--actor", "ephemeral@decision-archaeology", "--key", str(store / "ephemeral.key"),
        "--ts", str(FILED_AT),
    ).splitlines()[-1]

    report = json.loads(warrant(store, "verify", "--json"))
    require(report["errors"] == 0, f"verification reported errors: {report['findings']}")

    return {"schema": "decision-archaeology.warrant-ski-reason@v0",
            "adapter": ADAPTER_ID,
            "case_id": "barite-bid-rigging-2025",
            "source_receipt": SIGMA_RECEIPT.relative_to(CASE_ROOT).as_posix(),
            "profile": PROFILE_ID,
            "warrant": {"package": "warrant-verify", "version": version("warrant-verify"),
                        "runtime": "ski@v1", "body_version": "0.2"},
            "check": document,
            "check_blob_sha256": check_hash,
            "execution": {"verdict": verdict, "result_hash": result_hash,
                          "atp_spent": atp_spent},
            "filing": {"record_verified": True, "warnings": report["warnings"],
                       "note": "Filed under an ephemeral key to prove the path; a "
                               "published record needs a real actor key, which is an "
                               "identity decision and not a repository artifact."},
            "authority": "deterministic-execution-only",
            "non_claims": [
                "Re-execution attests the arithmetic predicate only; it says nothing "
                "about coordination, intent, guilt, or the AMCU finding.",
                "Warrant carries this reason under its existing ski@v1 runtime; no "
                "change to Warrant is claimed, requested, or adopted here.",
            ]}


def refuses_a_false_claim(claim: dict, store: Path) -> None:
    """The filer must re-execute: a claim that does not hold cannot be filed."""
    warrant(store, "init")
    mutated = dict(claim)
    whole, fraction = str(claim["expected"]).split(".")
    mutated["expected"] = f"{whole}.{int(fraction) + 1:0{len(fraction)}d}"
    document, _, nodes = check_document(mutated)
    check_hash = populate(store, nodes, document)
    executed = warrant(store, "check", check_hash, expect_verdict=True)
    require(executed.startswith("fail"),
            f"a one-minor-unit mutation still passed: {executed}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args()

    claim = json.loads(SIGMA_RECEIPT.read_text())["claim"]
    with tempfile.TemporaryDirectory() as temporary:
        receipt = round_trip(claim, Path(temporary) / "store")
        refuses_a_false_claim(claim, Path(temporary) / "mutated")

    rendered = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    if args.write_receipt:
        RECEIPT_PATH.write_text(rendered)
    else:
        require(RECEIPT_PATH.is_file(), "the committed Warrant reason receipt is missing")
        require(RECEIPT_PATH.read_text() == rendered,
                "the committed Warrant reason receipt is stale")
    print(f"WARRANT-SKI-REASON: {receipt['execution']['verdict']} at "
          f"{receipt['execution']['atp_spent']:,} ATP, record verified, "
          "one-minor-unit mutation refused")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
