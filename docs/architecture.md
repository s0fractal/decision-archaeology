# Architecture boundaries

## Product responsibility

Decision Archaeology owns the investigation workflow: importing a bounded body
of material, navigating a decision graph, comparing interpretations, running
checks, publishing a dossier, and reproducing its outputs.

It may define local storage and presentation models. Those models must not be
presented as replacements for the protocols they project or consume.

## Integration rule

Every protocol integration should have four visible parts:

1. an exact upstream identity and version;
2. a narrow adapter or profile;
3. conformance vectors at the boundary;
4. a failure mode that preserves uncertainty instead of inventing absence or
   validity.

The first implementation should use only the integrations demanded by the
first case. Unused protocol placeholders are not implementation progress.

## Epistemic boundary

The system can establish that bytes, signatures, transformations, and declared
relationships satisfy explicit checks. It cannot establish that an allegation
is true merely because it is structured, signed, repeated, or present in a
graph.

The interface must keep at least these layers distinguishable:

- source: acquired material and provenance;
- observation: a bounded reading or extraction from a source;
- claim: an attributable assertion supported or challenged by observations;
- hypothesis: an interpretation that competes with alternatives;
- decision: an event reconstructed from declared evidence and uncertainty;
- check: a rerunnable predicate over explicit inputs;
- receipt: evidence of integrity, attribution, or execution.

## Evolution

The case structure is versioned independently from protocol specifications and
software package versions. Breaking changes require a new case schema identity
and a documented migration. A real case, not internal elegance, determines
whether a proposed field or integration is necessary.
