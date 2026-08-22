# Decision Archaeology

**Reproducible retrospective investigations as evidence-bound decision graphs.**

Decision Archaeology reconstructs how a consequential decision became possible:
which sources existed, what actors could know, which claims were made, which
alternatives were available, what checks were applied, and where uncertainty or
omission remains.

The product is an application and integration layer for independently governed
protocols. It is not a new umbrella protocol and it does not declare truth,
intent, guilt, or legal liability.

## What an investigation should produce

A public case should be an executable dossier rather than a persuasive essay:

- source material with explicit provenance and acquisition context;
- observations separated from claims and interpretations;
- a graph of decisions, actors, alternatives, and consequences;
- deterministic checks that another investigator can rerun;
- signed or hash-addressed receipts for important assertions and outputs;
- explicit exclusions, access limits, counter-evidence, and unresolved questions.

Humans and their AI agents should be able to inspect the same dossier, challenge
individual steps, and reproduce derived artifacts without trusting the original
author.

## Protocol roles

Decision Archaeology consumes protocols through narrow adapters and profiles.
Each protocol remains the canonical owner of its own contracts.

| Concern | Expected owner |
| --- | --- |
| Acquisition and provenance | OAIP |
| Signed assertions and commitments | Warrant |
| Deterministic bounded checks | Sigma-Glyph |
| Competing hypotheses | BOS |
| Recorded omission and loss | SEV |
| Investigation workflow and user experience | Decision Archaeology |

These integrations are a direction, not a claim that every bridge already
exists or is stable.

## Cases

Public investigations will live under [`examples/`](examples/README.md). Every
case starts from an immutable, versioned template and declares the exact
protocol and executable-tool versions it uses. The initial template is
deliberately small and still draft.

The first executable calibration dossier is
[`barite-bid-rigging-2025`](examples/barite-bid-rigging-2025/README.md). It
reconstructs the public boundary of an AMCU decision and deliberately retains
refutations and missing reasoning instead of presenting the authority's finding
as independently reproduced.

Source-poor investigations remain under [`candidates/`](candidates/README.md)
until they pass an explicit admission gate. The initial
[`kherson-fortifications`](candidates/kherson-fortifications/README.md) audit is
not a published allegation or completed dossier.

See [`templates/case/v0.1.0/`](templates/case/v0.1.0/README.md) and the draft
[`case.schema.json`](schemas/case.schema.json).

When a case exposes a missing capability, it can promote that pressure through
the versioned [case-derived needs](docs/case-derived-needs.md) loop. The target
repository receives a minimized reproducer and an owner-side disposition; the
full dossier and its interpretation boundaries remain here.

The first completed routing decision, `DA-SIGMA-0001`, resolved to the narrow
application-owned [`sigma-money-add-eq@v0`](profiles/sigma-money-add-eq-v0.md)
profile. This records a reproducible adapter boundary, not a Sigma-Glyph
protocol extension. Its exact cross-repository closure is preserved in the
[`DA-SIGMA-0001` outcome receipt](outcomes/DA-SIGMA-0001.json).

The guards over these records are enforced by reading git history, which is a
boundary worth naming: rewriting the history removes a fact and the evidence of
its removal together. An [external pin](docs/proposals/external-pin.md) is
proposed for that, and is not adopted. What is recorded already is the gap
itself: [`pins/revisions.json`](pins/revisions.json) counts the revisions this
repository's records depend on and how many of them anyone else is known to
retain — currently none.

## Reproducible toolchain

Cases must not depend on sibling checkouts of protocol repositories. The root
[`mise.toml`](mise.toml) pins the runtime and package manager; the committed
[`toolchain/uv.lock`](toolchain/uv.lock) pins the published verification tools
and their complete Python dependency graph.

```sh
mise install
mise run check
```

`mise` is a convenience and enforcement layer, not the only execution path.
The equivalent `uv` commands remain documented so the dossier can be reproduced
without adopting a particular shell version manager.

## Status

This repository now has one executable case gate and one source-sufficiency
candidate audit. There is still no stable API, sealed public-source escrow,
adopted cross-protocol case profile, or general investigation pipeline. Claims
about implemented capabilities must link to runnable code and a reproducible
check.

## License

[MIT](LICENSE)
