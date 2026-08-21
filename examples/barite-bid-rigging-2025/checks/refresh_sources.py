#!/usr/bin/env python3
"""Project the two official Prozorro records into the minimized case fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path
from urllib.request import Request, urlopen


CASE_ROOT = Path(__file__).resolve().parents[1]
DEFENDANTS = {"35341905", "45333199"}
ENDPOINTS = {
    "UA-2025-02-03-015471-a": (
        "0a4450deb1e849d9b7a9fed0d5aaaa6a",
        "https://public-api.prozorro.gov.ua/api/2.5/tenders/"
        "0a4450deb1e849d9b7a9fed0d5aaaa6a",
    ),
    "UA-2025-03-17-004896-a": (
        "d7e17c2e71d249bd8f021d684d1ec6f3",
        "https://public-api.prozorro.gov.ua/api/2.5/tenders/"
        "d7e17c2e71d249bd8f021d684d1ec6f3",
    ),
}


def amount(value: object) -> str:
    return format(Decimal(str(value)), ".2f")


def quantity(value: object) -> str:
    decimal_value = Decimal(str(value))
    if decimal_value == decimal_value.to_integral():
        return str(int(decimal_value))
    return format(decimal_value.normalize(), "f")


def fetch(url: str) -> tuple[dict[str, object], str]:
    request = Request(url, headers={"User-Agent": "decision-archaeology/0"})
    with urlopen(request, timeout=30) as response:
        raw = response.read()
    return json.loads(raw)["data"], hashlib.sha256(raw).hexdigest()


def project(data: dict[str, object]) -> dict[str, object]:
    bids = []
    defendant_hashes: dict[str, set[str]] = {key: set() for key in DEFENDANTS}
    for bid in data.get("bids", []):
        tenderer = bid["tenderers"][0]
        company_id = tenderer["identifier"]["id"]
        bids.append(
            {
                "company_id": company_id,
                "company_name": tenderer["name"],
                "submitted_at": bid["date"],
                "lot_values": sorted(
                    [
                        {
                            "lot_id": entry["relatedLot"],
                            "amount_uah_vat_included": amount(entry["value"]["amount"]),
                        }
                        for entry in bid.get("lotValues", [])
                    ],
                    key=lambda entry: entry["lot_id"],
                ),
            }
        )
        if company_id in defendant_hashes:
            defendant_hashes[company_id].update(
                document["hash"]
                for document in bid.get("documents", [])
                if document.get("hash")
            )

    shared_hashes = sorted(set.intersection(*defendant_hashes.values()))
    return {
        "tender_id": data["tenderID"],
        "internal_id": data["id"],
        "status": data["status"],
        "expected_amount_uah_vat_included": amount(data["value"]["amount"]),
        "items": sorted(
            [
                {
                    "lot_id": item["relatedLot"],
                    "quantity": quantity(item["quantity"]),
                    "unit_code": item["unit"]["code"],
                }
                for item in data.get("items", [])
            ],
            key=lambda entry: entry["lot_id"],
        ),
        "lots": sorted(
            [
                {
                    "lot_id": lot["id"],
                    "status": lot["status"],
                    "expected_amount_uah_vat_included": amount(lot["value"]["amount"]),
                }
                for lot in data.get("lots", [])
            ],
            key=lambda entry: entry["lot_id"],
        ),
        "bids": sorted(bids, key=lambda entry: entry["company_id"]),
        "awards": sorted(
            [
                {
                    "lot_id": award["lotID"],
                    "status": award["status"],
                    "company_id": award["suppliers"][0]["identifier"]["id"],
                    "amount_uah_vat_included": amount(award["value"]["amount"]),
                }
                for award in data.get("awards", [])
            ],
            key=lambda entry: (entry["lot_id"], entry["status"]),
        ),
        "contracts": sorted(
            [
                {
                    "id": contract["id"],
                    "contract_id": contract["contractID"],
                    "status": contract["status"],
                    "amount_uah_vat_included": amount(contract["value"]["amount"]),
                }
                for contract in data.get("contracts", [])
            ],
            key=lambda entry: entry["id"],
        ),
        "defendant_document_hash_intersection": {
            "company_ids": sorted(DEFENDANTS),
            "count": len(shared_hashes),
            "hashes": shared_hashes,
        },
    }


def live_projection() -> tuple[list[dict[str, object]], dict[str, str]]:
    records = []
    hashes = {}
    for tender_id, (internal_id, url) in ENDPOINTS.items():
        data, digest = fetch(url)
        if data["tenderID"] != tender_id or data["id"] != internal_id:
            raise RuntimeError(f"identity mismatch for {tender_id}")
        records.append(project(data))
        hashes[tender_id] = digest
    return sorted(records, key=lambda entry: entry["tender_id"]), hashes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--print", action="store_true", dest="print_projection")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.print_projection == args.check:
        parser.error("choose exactly one of --print or --check")

    records, hashes = live_projection()
    if args.print_projection:
        print(json.dumps({"records": records, "raw_sha256": hashes}, ensure_ascii=False, indent=2))
        return 0

    committed = json.loads((CASE_ROOT / "sources" / "prozorro-projection.json").read_text())
    source_index = json.loads((CASE_ROOT / "sources" / "source-index.json").read_text())
    expected_hashes = {
        source["external_id"]: source["raw_sha256"]
        for source in source_index["sources"]
        if source["kind"] == "official-api-record"
    }
    if records != committed["records"]:
        raise SystemExit("FAIL: live Prozorro projection drifted from the committed fixture")
    if hashes != expected_hashes:
        raise SystemExit("FAIL: live Prozorro response bytes drifted from acquisition receipts")
    print("PASS: 2 live Prozorro records match projection and acquisition hashes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
