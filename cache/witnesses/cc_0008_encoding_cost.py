#!/usr/bin/env python3
"""CC-0008: re-measure the two encodings, here, with the pinned evaluator.

`counterexample` re-derives the marginal ATP of a Church-encoded addition and
reports the projected cost at the case's magnitude. `control` measures the
positional encoding of the same claim, so the number has something to be
compared with — a cost witness with only one number is a rumour.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from profiles.sigma_money_add_eq_v0 import evaluate  # noqa: E402
from sigma_glyph import Store, c1, eval_hash, sha, term_bytes  # noqa: E402

CLAIM = {"schema": "decision-archaeology.sigma-money-add-eq@v0", "unit": "UAH",
         "decimal_places": 2, "addends": ["178530840.00", "157960871.70"],
         "expected": "336491711.70"}
MAGNITUDE = 33_649_171_170

V = lambda name: ("var", name)                       # noqa: E731
L = lambda name, body: ("lam", name, body)           # noqa: E731
A = lambda fn, arg: ("lapp", fn, arg)                # noqa: E731
ADD = L("m", L("n", L("f", L("x", A(A(V("m"), V("f")),
                                    A(A(V("n"), V("f")), V("x")))))))


def put(store, term):
    if term[0] == "app":
        put(store, term[1]); put(store, term[2])
    return store.put(term_bytes(term))


def church(n):
    body = V("x")
    for _ in range(n):
        body = A(V("f"), body)
    return L("f", L("x", body))


def church_per_unit() -> float:
    store = Store()
    measured = []
    for value in (100, 200):
        term = c1(A(A(A(A(ADD, church(value)), church(value)),
                      ("lit", sha(b"I"))), ("lit", sha(b"I"))))
        _, spent = eval_hash(put(store, term), 10_000_000, store)
        measured.append((2 * value, spent))
    (n_1, s_1), (n_2, s_2) = measured
    return (s_2 - s_1) / (n_2 - n_1)


def main() -> int:
    half = sys.argv[1] if len(sys.argv) > 1 else "counterexample"
    if half == "counterexample":
        per_unit = church_per_unit()
        projected = per_unit * MAGNITUDE
        print(f"Church: ~{per_unit:.0f} ATP per unit of magnitude -> ~{projected:,.0f} ATP")
        return 0 if projected > 1e11 else 1
    spent = evaluate(CLAIM)["atp_spent"]
    print(f"positional, 64-bit: {spent:,} ATP for the same claim")
    return 0 if spent < 1_000_000 else 1


if __name__ == "__main__":
    raise SystemExit(main())
