# Probe: Warrant carried the case's check without being asked for anything

The pressure report listed Warrant as an owner of a blocked operation: bind a
frozen case identity, an exact input projection, and a check report to a
publisher's assertion, without confusing a valid signature with a true
allegation. `case-00` declared no Warrant dependency and held no signed receipt.

Before writing a packet, the same gate that saved `DA-SIGMA-0001` from asking for
the wrong thing was applied here: test the existing contract first.

## What was tested

Warrant's `ski@v1` reason runtime *is* Sigma-Glyph Book I v0.5, and SPEC §3.1
makes the warrant blob store the Sigma CAS. The case's profile term was written
into a store as ordinary blobs, published as a check document
`{ski, term, atp, expect}`, filed as the reason of an `accept` record, and
verified with the pinned `warrant-verify 0.9.0` release.

| step | result |
| --- | --- |
| `warrant check` re-executes the term | `pass`, result `bed95fbc…`, **203,530 ATP** |
| filing a `pass` the term does not support | refused before the record is written |
| one-minor-unit mutation of the claim | `fail` at 12,867 ATP, matching the frozen vector |
| `warrant verify` on the filed record | 0 errors, 1 warning (no keyring for the actor) |

The ATP figure is the same integer Sigma-Glyph 0.6.7 spends. Two independently
pinned releases, one bundled oracle each, identical cost to the unit.

## What that means for the loop

No packet was filed, because nothing was missing. This is the loop's first
`already-supported` result, and it was established by exercising the contract
rather than by reading its documentation and assuming.

`adapters/warrant_ski_reason_v0.py` records the round trip and is part of the
gate. Signing stays out of the repository: filing needs an actor key, which is an
identity decision rather than a build artifact, so the adapter files under an
ephemeral key to prove the path and commits only the deterministic part — the
check document a stranger re-runs.

## A related finding about DA-SIGMA-0001

Warrant's policy language, WPL, compiles rules to `ski@v1` terms — and refuses
arithmetic on purpose: "every operand must be a literal or a pinned fact, so the
verifier re-executes every step of the decision instead of trusting a number the
compiler worked out." A sum computed elsewhere and pinned as a fact is exactly
what the barite case could not accept, so the money profile complements WPL
rather than duplicating it. Had WPL contained arithmetic, `DA-SIGMA-0001` would
have been answered upstream and should have been closed as `wrong-owner`.
