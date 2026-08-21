# First-case pressure report

The first calibration case and the Kherson candidate were used to find concrete
integration pressure. This note records blocked operations; it does not create
new protocol contracts or claim that any upstream change is adopted.

## OAIP: acquisition receipts for mutable public records

**Blocked operation:** reproduce the exact bytes of a public web page or a
large procurement record after the publisher changes it, without republishing
unnecessary personal data.

**Local adapter:** `source-index.json` records authority, URL, acquisition time,
retention mode, and SHA-256 for complete API responses, while the repository
commits a minimized projection. The live check detects source drift but cannot
recover old bytes if the authority replaces them.

**Owner:** OAIP for acquisition and provenance semantics. Before proposing a
protocol change, test whether an existing OAIP receipt plus a lawful external
content-addressed cache expresses the need.

## SEV: distinguish missing, restricted, and reported-only material

**Blocked operation:** state why a candidate cannot support a claim without
turning restricted or unlocated material into semantic absence.

**Local adapter:** the Kherson inventory uses `public-attributable`,
`reported-only`, `potentially-restricted`, `missing-primary-source`, and
`missing-exact-identity` as non-normative workflow labels.

**Owner:** SEV for recorded omission and loss. A useful upstream test is whether
its existing loss manifest can preserve access state, search boundary, and the
difference between “not located” and “does not exist.”

## Sigma-Glyph: small deterministic comparison vocabulary

**Blocked operation:** rerun decimal sums, participant identity binding,
unit-price deltas, and cross-bid document-hash intersections over a frozen case
without embedding case-specific Python forever.

**Local adapter:** eight standard-library checks in `case-00`, with exact decimal
strings and explicit company/tender identities.

**Owner:** Sigma-Glyph for bounded deterministic terms. Candidate terms exposed
by this case are `decimal_exact_sum`, `set_contains`, `unit_price_delta`, and
`hash_set_intersection`. They are feature demand, not a request to add them
until the current Sigma-Glyph vocabulary and projection bridge are tested.

## Warrant: publication and execution receipts

**Blocked operation:** bind a frozen case identity, exact input projection, check
report, and publisher assertion without confusing a valid signature with a
true allegation.

**Local adapter:** none yet. The root toolchain proves that
`warrant-verify==0.9.0` is available, but `case-00` declares no Warrant
dependency and contains no signed Warrant receipt.

**Owner:** Warrant for signed assertions. The next experiment should sign only
the publication/check execution statement, not the substantive AMCU finding.

## BOS: competing hypotheses only after source admission

The Kherson candidate already has a reported claim and material counterclaim,
but the primary price inputs are missing. A BOS graph now would make an
evidence-poor candidate look more complete than it is. The integration remains
deferred until the admission gate passes.

## Template decision

`decision-archaeology.case-template@v0.1.0` was sufficient for `case-00`.
Candidate admission state belongs outside published examples for now. No
`v0.2.0` template is justified yet; the pressure is recorded here instead of
mutating a published template or adding speculative fields.
