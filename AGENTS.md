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
