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
   C1-compiled Church booleans, exactly as fixed by the construction listing
   below.
5. Let `claim_bytes` be the canonical JSON and bind its metadata into the root:
   `APPLY(APPLY(<K>, predicate), LITERAL(SHA256(UTF8(profile_id) || 0x00 ||
   claim_bytes)))`, where `<K>` is the **genesis K glyph** `LITERAL(SHA256("K"))`
   and not the C1-compiled `lambda a. lambda b. a`. The root evaluates to the
   predicate while its hash commits to unit, scale, order, and every amount.
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

## Construction listing (byte-determining)

Extensional equality is not enough here: two correct adders that disagree on a
single gate shape produce different term bytes, so the identity a receipt pins
would depend on whose encoder ran. The steps below therefore fix the bytes, not
just the semantics.

1. **Compile-then-reference.** Every gate is compiled through C1 and stored
   before any later gate mentions it, so a later gate embeds the earlier one's
   node hash. Inlining a gate's lambda body instead changes the compiled bytes.
2. **Gates**, in this order, each closed and compiled as written:

   ```text
   TRUE  = lambda a. lambda b. a
   FALSE = lambda a. lambda b. b
   NOT   = lambda a. a FALSE TRUE
   XOR   = lambda a. lambda b. a (NOT b) b
   AND   = lambda a. lambda b. a b FALSE
   OR    = lambda a. lambda b. a TRUE b
   XNOR  = lambda a. lambda b. NOT (XOR a b)
   ```

3. **Adder**, for `index` ascending from 0 to 63, with `carry` starting at
   `FALSE`:

   ```text
   half_i  = XOR a_i b_i
   sum_i   = XOR half_i carry
   carry   = OR (AND a_i b_i) (AND carry half_i)
   ```

4. **Predicate**: start from `NOT carry` — the no-overflow condition — then fold
   the equality terms in ascending bit order, left-associated:

   ```text
   predicate = NOT carry
   predicate = AND predicate (XNOR sum_i expected_i)     for i = 0 .. 63
   ```

5. **Root**: `APPLY(APPLY(<K>, predicate), LITERAL(bound_claim_atom))` with the
   genesis `<K>` of step 5 above. The term identity is this root node's hash;
   every intermediate node is stored.

`tests/profile_doc_replay_test.py` rebuilds all frozen vectors from this listing
alone, without importing the reference module. It is a doc-derived rebuild in the
same repository, not an independent implementation or a review gate.

### Why the listing exists

The first version of this document stopped at "a no-overflow ripple-carry
addition and equality predicate from C1-compiled Church booleans", and wrote the
root head as an unqualified `K`. A rebuild that followed that text and read `K`
as the profile's own C1-TRUE produced term `e247e909...` for the barite claim
where the reference produced `293c4942...`; substituting the textbook-equivalent
`OR = lambda a. lambda b. a a b` produced `34cf0dc0...`. All three evaluate to
C1-TRUE and cost different ATP.

That is the failure `DA-SIGMA-0001` was filed about, reproduced one layer higher:
a profile that fixes semantics but not bytes leaves the term hash pinning the
encoder rather than the claim. The listing closes it for v0; the frozen vectors
and the doc-derived rebuild keep it closed.

## Replay

```sh
mise run profile:sigma-money-add-eq
mise run profile:doc-replay
```

Passing vectors establish deterministic agreement with the pinned Python
reference package. They are not an independent implementation or an adoption
decision by Sigma-Glyph.
