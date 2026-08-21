#!/usr/bin/env python3
"""Offline, deterministic checks for the barite calibration case."""

from __future__ import annotations

import argparse
import json
import re
from decimal import Decimal
from pathlib import Path


CASE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFENDANTS = {"35341905", "45333199"}


def load_json(path: Path) -> object:
    return json.loads(path.read_text())


def load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def check_manifest() -> dict[str, object]:
    manifest = load_json(CASE_ROOT / "case.json")
    schema = load_json(REPO_ROOT / "schemas" / "case.schema.json")
    required = set(schema["required"])
    require(required <= set(manifest), "case.json is missing required schema fields")
    require(manifest["schema"] == "decision-archaeology.case@v0", "wrong case schema")
    require(
        re.fullmatch(r"decision-archaeology\.case-template@v0\.[0-9]+\.[0-9]+", manifest["template"])
        is not None,
        "invalid template identity",
    )
    require(manifest["template"] == "decision-archaeology.case-template@v0.1.0", "unexpected template")
    require(manifest["status"] == "active", "published example must be active")
    require(manifest["visibility"] == "public", "case visibility must be public")
    require(set(manifest) <= set(schema["properties"]), "case.json contains unknown schema fields")
    require(
        manifest["dependencies"]
        == [
            {
                "id": "python",
                "version": "3.13.15",
                "role": "standard-library offline and live case checks",
            }
        ],
        "case dependency identity changed",
    )
    for path_name, relative_path in manifest["paths"].items():
        expected = schema["properties"]["paths"]["properties"][path_name]["const"]
        require(relative_path == expected, f"wrong {path_name} path")
        if path_name != "exclusions":
            require((CASE_ROOT / relative_path).is_dir(), f"missing {relative_path}")
    require((CASE_ROOT / manifest["paths"]["exclusions"]).is_file(), "missing exclusions file")
    return manifest


def build_report() -> dict[str, object]:
    manifest = check_manifest()
    projection = load_json(CASE_ROOT / "sources" / "prozorro-projection.json")
    source_index = load_json(CASE_ROOT / "sources" / "source-index.json")
    observations = load_jsonl(CASE_ROOT / "observations" / "observations.jsonl")
    claims = load_jsonl(CASE_ROOT / "claims" / "claims.jsonl")
    decision = load_json(CASE_ROOT / "decisions" / "amcu-535-r.json")

    sources = {entry["id"] for entry in source_index["sources"]}
    observation_ids = {entry["id"] for entry in observations}
    require(len(sources) == len(source_index["sources"]), "duplicate source id")
    require(len(observation_ids) == len(observations), "duplicate observation id")
    for observation in observations:
        require(set(observation["source_ids"]) <= sources, f"unknown source in {observation['id']}")
        require(observation["epistemic_status"] in {"FACT", "ATTRIBUTED_CLAIM"}, "bad observation status")
    for claim in claims:
        require(set(claim["supporting_observations"]) <= observation_ids, f"unknown support in {claim['id']}")
        require(claim["epistemic_status"] in {"FACT", "HYPOTHESIS", "REFUTATION"}, "bad claim status")

    records = {entry["tender_id"]: entry for entry in projection["records"]}
    require(set(records) == {"UA-2025-02-03-015471-a", "UA-2025-03-17-004896-a"}, "wrong tender set")
    exact_sum = sum(Decimal(entry["expected_amount_uah_vat_included"]) for entry in records.values())
    require(exact_sum == Decimal("336491711.70"), "unexpected exact expected-value sum")
    official_whole_hryvnia = Decimal("336491711")
    require(exact_sum - official_whole_hryvnia == Decimal("0.70"), "official amount comparison changed")

    for tender_id, record in records.items():
        participants = {bid["company_id"] for bid in record["bids"]}
        require(DEFENDANTS <= participants, f"both AMCU respondents did not bid in {tender_id}")
        overlap = record["defendant_document_hash_intersection"]
        require(overlap["company_ids"] == sorted(DEFENDANTS), "wrong document-hash parties")
        require(overlap["count"] == 0 and overlap["hashes"] == [], "document hashes now overlap")

    second = records["UA-2025-03-17-004896-a"]
    require(len(second["items"]) == 1, "second tender item count changed")
    item = second["items"][0]
    require(item["quantity"] == "11283" and item["unit_code"] == "TNE", "second tender quantity changed")
    prices = {
        bid["company_id"]: Decimal(bid["lot_values"][0]["amount_uah_vat_included"])
        for bid in second["bids"]
    }
    exact_price_delta = prices["37351098"] - prices["35341905"]
    unit_price_delta = exact_price_delta / Decimal(item["quantity"])
    require(exact_price_delta == Decimal("11283.00"), "comparison price delta changed")
    require(unit_price_delta == Decimal("1.00"), "comparison is not exactly 1 UAH/t")
    compared_companies = {"35341905", "37351098"}
    require(compared_companies != DEFENDANTS, "1 UAH/t comparison unexpectedly equals respondent pair")
    require(len(compared_companies & DEFENDANTS) == 1, "refutation no longer isolates one non-respondent")

    require(decision["decision_number"] == "535-р", "wrong AMCU decision number")
    require(decision["case_number"] == "145-26.13/35-26", "wrong AMCU case number")
    require(set(decision["respondent_company_ids"]) == DEFENDANTS, "wrong AMCU respondents")
    require(set(decision["tender_ids"]) == set(records), "decision-to-tender scope mismatch")

    checks = [
        {"id": "manifest-shape", "status": "PASS", "value": manifest["template"]},
        {"id": "official-scope", "status": "PASS", "value": sorted(records)},
        {"id": "expected-value-exact-sum", "status": "PASS", "value": format(exact_sum, ".2f")},
        {
            "id": "official-prose-amount-gap",
            "status": "PASS",
            "value": format(exact_sum - official_whole_hryvnia, ".2f"),
        },
        {"id": "respondents-participated-in-both", "status": "PASS", "value": sorted(DEFENDANTS)},
        {"id": "defendant-document-md5-intersection", "status": "PASS", "value": 0},
        {
            "id": "one-uah-per-tonne-refutation",
            "status": "PASS",
            "value": {
                "delta_uah_per_tonne": format(unit_price_delta, ".2f"),
                "compared_company_ids": sorted(compared_companies),
                "excluded_respondent_company_id": next(iter(DEFENDANTS - compared_companies)),
            },
        },
        {"id": "decision-scope-binding", "status": "PASS", "value": "535-р"},
    ]
    return {
        "schema": "decision-archaeology.check-report@v0",
        "case_id": manifest["id"],
        "input": "sources/prozorro-projection.json",
        "checks": checks,
        "summary": {"passed": len(checks), "failed": 0},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    report = build_report()
    artifact_path = CASE_ROOT / "artifacts" / "check-report.json"
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.write_report:
        artifact_path.write_text(rendered)
    else:
        require(artifact_path.read_text() == rendered, "committed check report is stale")
    print(f"PASS: {report['summary']['passed']}/{len(report['checks'])} deterministic checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
