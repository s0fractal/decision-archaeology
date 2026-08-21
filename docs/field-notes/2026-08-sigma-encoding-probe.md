# Probe: what the barite exact-sum check costs as a Σ-GLYPH term

This note records a measurement and a routing decision. It does not claim that
Σ-GLYPH has accepted anything, and it does not change any case.

## What was tested

The first-case pressure report listed `decimal_exact_sum` as candidate demand on
Σ-GLYPH, with the explicit condition that the current vocabulary and the
projection bridge be tested before anything is promoted. That test was run
against `sigma-glyph@d78fe1698ca46f8be9a37232438a3740d1c8ff96`, using its own
reference evaluator `impl/sigma_glyph.py`.

The kernel is SKI — three combinators and application. There is no arithmetic
vocabulary, so the question was never "can it" but "at what price".

| Encoding of `178530840.00 + 157960871.70 == 336491711.70` | ATP |
| --- | --- |
| Church numerals over minor units | ~61 per unit of magnitude, i.e. ~2.05×10¹² |
| 36-bit LSB-first ripple-carry over C1-compiled booleans | 61,479 |

The positional term is `025e3c7632c63385…` and evaluates to TRUE; altering
either addend or the published sum by one minor unit makes it evaluate to
not-TRUE, so the check is falsifiable rather than decorative.

## What the measurement changed

The candidate placement moved from `protocol` to `profile`. Σ-GLYPH does not
need new arithmetic terms for this case: it already expresses the check ~3.3×10⁷
times more cheaply than the naive encoding, well inside a laptop budget. What it
does not have is a *named* encoding, so two parties who encode the same claim
independently get different term hashes — and a receipt over such a hash binds
our own toolchain rather than the assertion.

Book I §6 already speaks to this: frontend profiles other than C1 MAY exist
outside the standard as ordinary SKI citizens with no special status. That is a
deliberate position, and it may well be the answer here. Asking is therefore a
routing question, not a demand.

## Where it went

Filed as `DA-SIGMA-0001` under the `decision-archaeology.need@v0` packet
contract, carrying only the two public amounts and their published sum. The
dossier stays here; the target received the minimized reproducer, the exact
revisions, and the interpretation boundaries.

The reproducer is not mirrored into this repository as a runnable check, because
it needs a Σ-GLYPH checkout and cases must not depend on sibling checkouts. If
the request is fulfilled, the resolved dependency gets pinned in the case
manifest and the check is replayed under that pin.
