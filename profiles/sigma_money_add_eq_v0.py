#!/usr/bin/env python3
"""Decision Archaeology's application-owned Sigma money-addition profile."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path

from sigma_glyph import Store, c1, eval_hash, sha, term_bytes, term_hash


PROFILE_ID = "decision-archaeology.sigma-money-add-eq@v0"
VECTORS_SCHEMA = "decision-archaeology.sigma-money-add-eq-vectors@v0"
SIGMA_GLYPH_VERSION = "0.6.7"
SIGMA_GLYPH_REVISION = "16a1355142d0234ba0dcc519d674bb26b42a1d82"
WIDTH = 64
ATP_BUDGET = 1_000_000
CLAIM_DOMAIN = PROFILE_ID.encode("ascii") + b"\x00"
VECTORS_PATH = Path(__file__).with_name("sigma_money_add_eq_v0.vectors.json")
CLAIM_KEYS = {"schema", "unit", "decimal_places", "addends", "expected"}
UNIT = re.compile(r"^[A-Z][A-Z0-9._-]{0,15}$")

V = lambda name: ("var", name)  # noqa: E731
L = lambda name, body: ("lam", name, body)  # noqa: E731
A = lambda function, argument: ("lapp", function, argument)  # noqa: E731


@dataclass
class EncodedCheck:
    claim_bytes: bytes
    claim_sha256: bytes
    bound_claim_atom: bytes
    term_hash: bytes
    store: Store


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _amount_pattern(decimal_places: int) -> re.Pattern[str]:
    if decimal_places == 0:
        return re.compile(r"^(0|[1-9][0-9]*)$")
    return re.compile(rf"^(0|[1-9][0-9]*)\.[0-9]{{{decimal_places}}}$")


def _minor_units(value: object, decimal_places: int) -> int:
    require(isinstance(value, str), "amounts must be decimal strings")
    require(_amount_pattern(decimal_places).fullmatch(value) is not None,
            f"non-canonical amount: {value!r}")
    if decimal_places:
        whole, fraction = value.split(".")
        result = int(whole) * (10 ** decimal_places) + int(fraction)
    else:
        result = int(value)
    require(result < 2 ** WIDTH, f"amount does not fit unsigned {WIDTH}-bit encoding")
    return result


def canonical_claim(claim: object) -> bytes:
    """Validate and serialize a closed profile claim byte-for-byte."""
    require(isinstance(claim, dict), "claim must be an object")
    differing_keys = set(claim) ^ CLAIM_KEYS
    require(not differing_keys,
            f"claim keys differ: {sorted(map(repr, differing_keys))}")
    require(claim["schema"] == PROFILE_ID, "wrong claim schema")
    require(isinstance(claim["unit"], str) and UNIT.fullmatch(claim["unit"]) is not None,
            "unit must match [A-Z][A-Z0-9._-]{0,15}")
    decimal_places = claim["decimal_places"]
    require(type(decimal_places) is int and 0 <= decimal_places <= 9,
            "decimal_places must be an integer from 0 through 9")
    addends = claim["addends"]
    require(isinstance(addends, list) and len(addends) == 2,
            "v0 requires exactly two addends")
    a = _minor_units(addends[0], decimal_places)
    b = _minor_units(addends[1], decimal_places)
    _minor_units(claim["expected"], decimal_places)
    require(a + b < 2 ** WIDTH, f"addition overflows unsigned {WIDTH}-bit encoding")
    return json.dumps(
        claim, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def _put(store: Store, term: tuple) -> bytes:
    if term[0] == "thunk":
        return term[1]
    if term[0] == "app":
        _put(store, term[1])
        _put(store, term[2])
    return store.put(term_bytes(term))


def _compile(store: Store, lambda_term: tuple) -> tuple:
    return "thunk", _put(store, c1(lambda_term))


def _node(store: Store, function: tuple, *arguments: tuple) -> tuple:
    term = function
    for argument in arguments:
        term = "app", term, argument
        _put(store, term)
        term = "thunk", term_hash(term)
    return term


def _gates(store: Store) -> dict[str, tuple]:
    true = _compile(store, L("a", L("b", V("a"))))
    false = _compile(store, L("a", L("b", V("b"))))
    nand = _compile(store, L("a", A(A(V("a"), false), true)))
    xor = _compile(store, L("a", L("b", A(A(V("a"), A(nand, V("b"))), V("b")))))
    conjunction = _compile(store, L("a", L("b", A(A(V("a"), V("b")), false))))
    disjunction = _compile(store, L("a", L("b", A(A(V("a"), true), V("b")))))
    xnor = _compile(store, L("a", L("b", A(nand, A(A(xor, V("a")), V("b"))))))
    return {
        "TRUE": true,
        "FALSE": false,
        "NOT": nand,
        "XOR": xor,
        "AND": conjunction,
        "OR": disjunction,
        "XNOR": xnor,
    }


def _addition_equals(store: Store, gates: dict[str, tuple], a: int, b: int,
                     expected: int) -> tuple:
    bit = lambda value: gates["TRUE"] if value else gates["FALSE"]  # noqa: E731
    carry = gates["FALSE"]
    sums = []
    for index in range(WIDTH):
        a_i, b_i = bit((a >> index) & 1), bit((b >> index) & 1)
        half = _node(store, gates["XOR"], a_i, b_i)
        sums.append(_node(store, gates["XOR"], half, carry))
        carry = _node(
            store,
            gates["OR"],
            _node(store, gates["AND"], a_i, b_i),
            _node(store, gates["AND"], carry, half),
        )
    verdict = _node(store, gates["NOT"], carry)
    for index in range(WIDTH):
        verdict = _node(
            store,
            gates["AND"],
            verdict,
            _node(store, gates["XNOR"], sums[index], bit((expected >> index) & 1)),
        )
    return verdict


def encode(claim: object) -> EncodedCheck:
    """Compile a valid claim to one claim-bound Sigma-Glyph term."""
    claim_bytes = canonical_claim(claim)
    decimal_places = claim["decimal_places"]
    a = _minor_units(claim["addends"][0], decimal_places)
    b = _minor_units(claim["addends"][1], decimal_places)
    expected = _minor_units(claim["expected"], decimal_places)

    store = Store()
    gates = _gates(store)
    predicate = _addition_equals(store, gates, a, b, expected)
    claim_digest = sha(claim_bytes)
    bound_atom = sha(CLAIM_DOMAIN + claim_bytes)
    claim_literal = "lit", bound_atom
    k_glyph = "lit", sha(b"K")
    root = _node(store, k_glyph, predicate, claim_literal)
    return EncodedCheck(claim_bytes, claim_digest, bound_atom, root[1], store)


def _boolean_normal_hashes() -> tuple[bytes, bytes]:
    store = Store()
    gates = _gates(store)
    true_result, _ = eval_hash(gates["TRUE"][1], ATP_BUDGET, store)
    false_result, _ = eval_hash(gates["FALSE"][1], ATP_BUDGET, store)
    return term_hash(true_result), term_hash(false_result)


def evaluate(claim: object) -> dict[str, object]:
    encoded = encode(claim)
    result, spent = eval_hash(encoded.term_hash, ATP_BUDGET, encoded.store)
    result_digest = term_hash(result)
    true_hash, false_hash = _boolean_normal_hashes()
    if result_digest == true_hash:
        verdict = "C1-TRUE"
    elif result_digest == false_hash:
        verdict = "C1-FALSE"
    else:
        raise RuntimeError(
            f"evaluation did not reach a profile boolean normal form: {result_digest.hex()}"
        )
    return {
        "profile": PROFILE_ID,
        "sigma_glyph": {
            "package": "sigma-glyph",
            "version": SIGMA_GLYPH_VERSION,
            "revision": SIGMA_GLYPH_REVISION,
        },
        "claim_sha256": encoded.claim_sha256.hex(),
        "bound_claim_atom": encoded.bound_claim_atom.hex(),
        "term_hash": encoded.term_hash.hex(),
        "result_hash": result_digest.hex(),
        "verdict": verdict,
        "atp_budget": ATP_BUDGET,
        "atp_spent": spent,
    }


def _vector_claim(addends: list[str], expected: str) -> dict[str, object]:
    return {
        "schema": PROFILE_ID,
        "unit": "UAH",
        "decimal_places": 2,
        "addends": addends,
        "expected": expected,
    }


def build_vectors() -> dict[str, object]:
    claims = [
        ("small-true", _vector_claim(["1.00", "2.00"], "3.00")),
        ("barite-published-true", _vector_claim(
            ["178530840.00", "157960871.70"], "336491711.70"
        )),
        ("barite-one-minor-unit-false", _vector_claim(
            ["178530840.00", "157960871.70"], "336491711.69"
        )),
        (
            "u64-long-carry-true",
            {
                "schema": PROFILE_ID,
                "unit": "COUNT",
                "decimal_places": 0,
                "addends": ["9223372036854775807", "1"],
                "expected": "9223372036854775808",
            },
        ),
    ]
    return {
        "schema": VECTORS_SCHEMA,
        "profile": PROFILE_ID,
        "vectors": [
            {"id": vector_id, "claim": claim, "expected": evaluate(claim)}
            for vector_id, claim in claims
        ],
    }


def render_vectors(vectors: dict[str, object]) -> str:
    return json.dumps(vectors, ensure_ascii=False, indent=2) + "\n"


def selftest(vectors: dict[str, object]) -> None:
    require(version("sigma-glyph") == SIGMA_GLYPH_VERSION,
            "loaded sigma-glyph package does not match the profile pin")
    verdicts = [vector["expected"]["verdict"] for vector in vectors["vectors"]]
    require(verdicts == ["C1-TRUE", "C1-TRUE", "C1-FALSE", "C1-TRUE"],
            "positive or negative vector did not reach its required boolean normal form")

    claim = vectors["vectors"][0]["claim"]
    reordered = dict(reversed(list(claim.items())))
    require(canonical_claim(claim) == canonical_claim(reordered),
            "object insertion order changed canonical claim bytes")
    changed_unit = {**claim, "unit": "USD"}
    require(encode(claim).term_hash != encode(changed_unit).term_hash,
            "unit metadata is not bound into the term hash")

    invalid_claims = [
        {**claim, "addends": ["01.00", "2.00"]},
        {**claim, "addends": ["1.0", "2.00"]},
        {**claim, "decimal_places": True},
        {**claim, "unexpected": "field"},
        {**claim, "addends": ["18446744073709551615.00", "2.00"]},
    ]
    non_string_key = dict(claim)
    non_string_key[1] = "field"
    invalid_claims.append(non_string_key)
    for invalid in invalid_claims:
        try:
            canonical_claim(invalid)
        except ValueError:
            continue
        raise AssertionError(f"invalid profile claim was accepted: {invalid}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-vectors", action="store_true")
    args = parser.parse_args()
    vectors = build_vectors()
    selftest(vectors)
    rendered = render_vectors(vectors)
    if args.write_vectors:
        VECTORS_PATH.write_text(rendered)
    else:
        if VECTORS_PATH.read_text() != rendered:
            raise AssertionError("committed Sigma profile vectors are stale")
    print(f"SIGMA-MONEY-ADD-EQ-V0: ALL PASS ({len(vectors['vectors'])} vectors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
