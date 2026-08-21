#!/usr/bin/env python3
"""Rebuild the money-add-equality terms from the PROFILE DOCUMENT alone.

This is a doc-derived reimplementation, not an independent gate: it is written
in this repository, from sigma-money-add-eq-v0.md, section "Construction
listing", and it deliberately does not import `profiles.sigma_money_add_eq_v0`.
What it machine-checks is one property the profile exists for — that the
published listing determines the term bytes, so a second implementer reproduces
the frozen hashes instead of an extensionally equal term of their own.

The property is not hypothetical. Before the listing was written, a doc-derived
rebuild of the barite claim produced term e247e909... where the reference
produced 293c4942..., and swapping one textbook-equivalent gate definition
produced 34cf0dc0... — same verdict every time, three different identities.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from sigma_glyph import Store, c1, eval_hash, sha, term_bytes, term_hash

REPO_ROOT = Path(__file__).resolve().parents[1]
VECTORS = REPO_ROOT / "profiles" / "sigma_money_add_eq_v0.vectors.json"
PROFILE_ID = "decision-archaeology.sigma-money-add-eq@v0"
WIDTH = 64
ATP_BUDGET = 1_000_000

V = lambda name: ("var", name)                       # noqa: E731
L = lambda name, body: ("lam", name, body)           # noqa: E731
A = lambda function, argument: ("lapp", function, argument)  # noqa: E731


def put(store: Store, term: tuple) -> bytes:
    if term[0] == "thunk":
        return term[1]
    if term[0] == "app":
        put(store, term[1])
        put(store, term[2])
    return store.put(term_bytes(term))


def compile_store(store: Store, lambda_term: tuple) -> tuple:
    """Listing step 1: compile through C1, store, and refer to it by hash."""
    return "thunk", put(store, c1(lambda_term))


def node(store: Store, function: tuple, *arguments: tuple) -> tuple:
    term = function
    for argument in arguments:
        term = "app", term, argument
        put(store, term)
        term = "thunk", term_hash(term)
    return term


def gates(store: Store) -> dict[str, tuple]:
    """Listing step 2: each gate is compiled and stored BEFORE it is referenced
    by a later gate, so later gates embed a hash and never an inlined lambda."""
    true = compile_store(store, L("a", L("b", V("a"))))
    false = compile_store(store, L("a", L("b", V("b"))))
    negation = compile_store(store, L("a", A(A(V("a"), false), true)))
    exclusive = compile_store(store, L("a", L("b", A(A(V("a"), A(negation, V("b"))), V("b")))))
    conjunction = compile_store(store, L("a", L("b", A(A(V("a"), V("b")), false))))
    disjunction = compile_store(store, L("a", L("b", A(A(V("a"), true), V("b")))))
    equality = compile_store(store, L("a", L("b", A(negation, A(A(exclusive, V("a")), V("b"))))))
    return {"TRUE": true, "FALSE": false, "NOT": negation, "XOR": exclusive,
            "AND": conjunction, "OR": disjunction, "XNOR": equality}


def minor_units(amount: str, decimal_places: int) -> int:
    if decimal_places == 0:
        return int(amount)
    whole, fraction = amount.split(".")
    return int(whole) * (10 ** decimal_places) + int(fraction)


def build(store: Store, g: dict[str, tuple], claim: dict) -> tuple:
    decimal_places = claim["decimal_places"]
    a = minor_units(claim["addends"][0], decimal_places)
    b = minor_units(claim["addends"][1], decimal_places)
    expected = minor_units(claim["expected"], decimal_places)

    bit = lambda value: g["TRUE"] if value else g["FALSE"]  # noqa: E731
    carry = g["FALSE"]
    sums = []
    for index in range(WIDTH):                       # listing step 3
        a_i, b_i = bit((a >> index) & 1), bit((b >> index) & 1)
        half = node(store, g["XOR"], a_i, b_i)
        sums.append(node(store, g["XOR"], half, carry))
        carry = node(store, g["OR"],
                     node(store, g["AND"], a_i, b_i),
                     node(store, g["AND"], carry, half))
    predicate = node(store, g["NOT"], carry)         # listing step 4
    for index in range(WIDTH):
        predicate = node(store, g["AND"], predicate,
                         node(store, g["XNOR"], sums[index], bit((expected >> index) & 1)))

    claim_bytes = json.dumps(claim, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True).encode("ascii")
    bound_atom = hashlib.sha256(PROFILE_ID.encode("ascii") + b"\x00" + claim_bytes).digest()
    root = node(store, ("lit", sha(b"K")), predicate, ("lit", bound_atom))  # listing step 5
    return root, claim_bytes, bound_atom


def main() -> int:
    vectors = json.loads(VECTORS.read_text())["vectors"]
    store = Store()
    g = gates(store)
    true_hash = term_hash(eval_hash(g["TRUE"][1], ATP_BUDGET, store)[0])
    false_hash = term_hash(eval_hash(g["FALSE"][1], ATP_BUDGET, store)[0])

    for vector in vectors:
        claim, expected = vector["claim"], vector["expected"]
        root, claim_bytes, bound_atom = build(store, g, claim)
        result, spent = eval_hash(root[1], expected["atp_budget"], store)
        result_hash = term_hash(result)
        verdict = ("C1-TRUE" if result_hash == true_hash
                   else "C1-FALSE" if result_hash == false_hash else "OTHER")

        for label, actual, wanted in (
            ("claim_sha256", hashlib.sha256(claim_bytes).hexdigest(), expected["claim_sha256"]),
            ("bound_claim_atom", bound_atom.hex(), expected["bound_claim_atom"]),
            ("term_hash", root[1].hex(), expected["term_hash"]),
            ("result_hash", result_hash.hex(), expected["result_hash"]),
            ("verdict", verdict, expected["verdict"]),
            ("atp_spent", spent, expected["atp_spent"]),
        ):
            if actual != wanted:
                print(f"FAIL {vector['id']}: {label} is {actual}, listing should give {wanted}",
                      file=sys.stderr)
                return 1
        print(f"OK   {vector['id']}: doc-derived rebuild reproduces {expected['term_hash'][:16]}…")

    print(f"PROFILE-DOC-REPLAY: ALL PASS ({len(vectors)} vectors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
