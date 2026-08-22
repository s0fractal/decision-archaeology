# Proposal: an external pin for this repository's own records

**Status: proposal. Nothing here is adopted, implemented, or depended on.**

Every guard in this repository is enforced by reading git history. An absence
cannot be produced by deletion, a receipt cannot be rewritten, a requirement
cannot quietly ask for less — each of those holds because an earlier revision
can be read and compared.

All of it rests on one assumption: that the history is still there. A force-push
removes the fact and the evidence of its removal in the same act, and leaves
every check green. That is not a flaw in the guards; it is the boundary of what
any guard inside the artefact can do.

## What a signature does not fix

Signing the records does not close this. A Warrant receipt over a revision is
itself a file in the repository: rewrite the history and the signature goes with
it. Signing proves *who said* something to a reader who still has the bytes; it
does not keep the bytes.

The ecosystem's existing machinery has the same shape. Σ-GLYPH anchors its
specification set by content hash and governs changes with threshold warrants —
which answers "which bytes are the standard" precisely, and answers "does anyone
outside still hold them" not at all.

## The requirement

What is missing is an **independently retained observation**: some party that is
not us, and cannot be asked by us to forget, holding the statement *this
repository was at this revision at this time*.

- **R1 — retained elsewhere.** The observation survives anything done to this
  repository, including rewriting its history.
- **R2 — retrievable by a stranger.** A reader who trusts neither us nor the
  witness's goodwill can fetch the observation themselves.
- **R3 — verifiable offline.** The committed record is checkable against the
  retrieved observation without a live service in the loop at verification time.
- **R4 — degrades loudly.** A revision with no observation is recorded as
  unwitnessed, exactly as an unwitnessed source is. Silence must not read as a
  pin.
- **R5 — no new trusted party.** Nobody, ourselves included, gains the power to
  make a false observation verify.

R4 matters more than it looks. This repository already treats "not witnessed" as
a first-class state for its sources; applying the same vocabulary to its own
revisions keeps the failure visible instead of aspirational.

## Candidates, with what breaks each

| Candidate | Satisfies | Breaks |
| --- | --- | --- |
| Public web archive of the commit page | R1, R2 | No cryptographic binding, capture is best-effort, page shape can change; fails R3 in practice |
| OpenTimestamps (Bitcoin calendars) | R1, R3, R5 | Proof must be upgraded after confirmation; depends on calendar servers at creation time; adds a blockchain dependency to a repository that has none |
| Sigstore / Rekor transparency log | R1, R2, R3 | A log operator with a retention policy; strong append-only guarantees, but the guarantee is the operator's |
| Mirror in another repository we own | — | Same owner rewrites both; satisfies nothing |
| Anchoring the revision inside a sibling protocol repository | Partly R1 | Same operator across the ecosystem; buys separation of blast radius, not independence |
| GitHub branch protection and signed tags | Partly R1 | The party that can rewrite is the party being relied on |

Two of these are worth taking seriously — a timestamping proof for the
cryptographic binding, and an archived page for human-legible retrieval — and
they fail in different ways, which is an argument for recording both rather than
choosing between them.

## Sketch of the record

A pin would be a record like every other one here: settled fields, a closed
vocabulary, and a state for absence.

```json
{
  "schema": "decision-archaeology.revision-pin@v0",
  "revision": "<40 hex>",
  "custody": "independently-witnessed | self-attested | unwitnessed",
  "observations": [
    {"kind": "timestamp-proof", "provider": "…", "observed_at": "…",
     "proof": "pins/<revision>.ots", "verifies_with": "…"},
    {"kind": "public-web-archive", "provider": "…", "snapshot_url": "…",
     "snapshot_timestamp": "…", "raw_sha256": "…"}
  ],
  "authority": "revision-retention-only"
}
```

The verification task would refuse a pin whose observation cannot be re-checked,
and the repository would report how much of its own history is pinned — the way
it now reports how many of a case's sources are witnessed.

## What this proposal does not decide

Three questions are not technical and are not mine to answer:

1. **Whether to depend on a third party at all**, and which. Every candidate
   above adds an outside party with its own availability, jurisdiction, and
   retention policy.
2. **What is published.** A pin publishes this repository's revision hashes to
   an external service. The repository is public, so this leaks nothing new —
   but it is still an outward act, and creating an archive capture or a
   timestamp is not the same as reading one.
3. **Cadence and cost.** Every commit, every merge to `main`, or only revisions
   an outcome pins. Pinning everything is simplest to reason about and largest
   in dependency surface.

## Recommendation

Record both kinds of observation, pin at merges to `main` and at any revision
cited by an outcome receipt, and ship the `unwitnessed` state first — so the
repository can say honestly how much of its own past is retained by nobody but
itself, before it starts fixing that. Making the gap visible is the part that
needs no external dependency, and it is the part this repository already knows
how to do.
