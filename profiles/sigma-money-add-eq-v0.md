# Sigma money-add-equality profile v0

Identity: `decision-archaeology.sigma-money-add-eq@v0`

This is a Decision Archaeology application profile, routed from
`DA-SIGMA-0001`. It is not part of the Sigma-Glyph standard and does not claim
special status under Book I. Its sole purpose is to make one case-demanded
class of claims compile to the same term bytes for independent implementers.

## Upstream identity

- package: `sigma-glyph==0.6.7`;
- release revision: `16a1355142d0234ba0dcc519d674bb26b42a1d82`;
- consumed surface: Book I canonical node bytes, hash-thunk evaluation, and
  canonical lambda-to-SKI compiler Profile C1.

The package and its transitive artifact hashes are pinned in
`toolchain/uv.lock`.

## Closed claim

A claim is canonical ASCII JSON with exactly these fields:

```json
{
  "schema": "decision-archaeology.sigma-money-add-eq@v0",
  "unit": "UAH",
  "decimal_places": 2,
  "addends": ["178530840.00", "157960871.70"],
  "expected": "336491711.70"
}
```

Keys are sorted, separators are `,` and `:`, and no whitespace is emitted.
`unit` matches `[A-Z][A-Z0-9._-]{0,15}`. `decimal_places` is an integer from
0 through 9. Each amount is a non-negative canonical decimal string with
exactly that many fractional digits, no sign, and no leading zero. V0 accepts
exactly two ordered addends.

## Term construction

1. Convert each decimal string to exact minor units; binary floating point is
   forbidden.
2. Reject values or an addition that do not fit an unsigned 64-bit integer.
3. Encode bits least-significant first at a fixed width of 64.
4. Build a no-overflow ripple-carry addition and equality predicate from
   C1-compiled Church booleans.
5. Let `claim_bytes` be the canonical JSON and bind its metadata into the root:
   `K predicate LITERAL(SHA256(UTF8(profile_id) || 0x00 || claim_bytes))`.
   The root evaluates to the predicate while its hash commits to unit, scale,
   order, and every amount.
6. The only positive verdict is the normal-form hash of C1-compiled
   `lambda a. lambda b. a`; the only negative verdict is the normal-form hash
   of C1-compiled `lambda a. lambda b. b`. C1 is syntactically canonical rather
   than extensionally canonical, so the positive normal form MUST NOT be
   replaced by the extensionally equal bare K glyph. Dissonance, exhaustion,
   or any third normal form fails closed and produces no receipt.

The fixed evaluation budget is 1,000,000 ATP. Byte-level hashes, ATP spend, a
positive case, a one-minor-unit counterexample, and a 64-bit long-carry boundary
case are frozen in
`sigma_money_add_eq_v0.vectors.json`.

## Replay

```sh
mise run profile:sigma-money-add-eq
```

Passing vectors establish deterministic agreement with the pinned Python
reference package. They are not an independent implementation or an adoption
decision by Sigma-Glyph.
