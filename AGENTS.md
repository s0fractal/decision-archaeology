# Repository guidance

Decision Archaeology is the application layer that exercises a stack of
independently governed protocols. Do not turn product needs into new normative
contracts here when OAIP, Warrant, Sigma-Glyph, BOS, or SEV already owns the
concept.

When a case exposes a missing capability:

1. record the concrete blocked operation and a minimal reproducer;
2. identify the canonical owner of the missing contract;
3. prefer a local adapter or narrow profile when it is sufficient;
4. request a protocol change only when the owner cannot express the required
   behavior without one;
5. pin the exact dependency version in the case manifest.

Promoted requests use the immutable template under `templates/need/` and the
workflow in `docs/case-derived-needs.md`. A target repository's merged need
packet records demand and routing only; it is not protocol adoption. Keep the
full dossier here and transfer only the minimized reproducer, exact revisions,
artifact digests, and interpretation boundaries.

A profile publishes bytes, not only semantics. Every profile document carries a
construction listing precise enough to rebuild its frozen vectors, and ships that
rebuild in `tests/<profile>_doc_replay_test.py`, derived from the listing alone
and forbidden to import the reference implementation. An outcome that resolves a
need names the rebuild it survived. Green vectors from the author's own module
prove nothing about agreement between strangers, which is what a profile is for.

A case records what it does not establish as data, not as prose. `exclusions.md`
is rendered from `exclusions.json`, an absence that nothing would resolve is a
claim rather than a limitation, and an exclusion leaves the record only by being
retired with a reason. The same rule governs a source's witness: absence must be
declared, never produced by deletion.

Keep facts, hypotheses, and speculation distinguishable. Generated artifacts
must retain links to their inputs and transformations. Do not describe a draft,
experiment, or proposed bridge as adopted or implemented.

Case data belongs under `examples/<case-id>/` and must record the exact template
identity from `templates/case/`. Never edit a published template version in
place; add a new version. Never commit private source material, secrets,
personal data without a lawful publication basis, or unverifiable allegations.

Do not rely on sibling repository checkouts. Published tools belong in the
locked toolchain; unreleased integrations must use an immutable source identity
and disclose that they are development inputs.
