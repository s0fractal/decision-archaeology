# Case-derived needs

Decision Archaeology turns a reproducible case blockage into bounded demand on
the repository that owns the affected contract. The target repository remains
the authority over its own protocol, implementation, profiles, and releases.

The exchange artifact is `decision-archaeology.need@v0`. A packet contains a
machine manifest, a short narrative, minimized fixtures, and a machine-readable
owner disposition. The complete investigation stays in Decision Archaeology.

## Routing loop

1. Record the blocked operation in the source case.
2. Freeze the source revision and artifact digests.
3. Copy an immutable need template into `needs/<request-id>-<slug>/` on a target
   repository branch.
4. Open a PR containing the packet and fixtures, but no bundled implementation.
5. Reproduce and classify it owner-side. Merging the classified packet records
   demand; it does not adopt a protocol change.
6. If an application adapter or profile is sufficient, implement it in its
   canonical owner. If a protocol change is needed, start the target's normal
   proposal and conformance process separately.
7. Pin the released or exact resolved dependency in the case and replay it.
8. Record an outcome receipt linking both repository revisions.

The closing artifact is `decision-archaeology.need-outcome@v0` under
`outcomes/`. It pins the target disposition, the exact resolution revision and
artifact digests, and one literal case replay. Outcome status records whether
the blocked operation was resolved; it does not upgrade routing into protocol
adoption or the case result into substantive truth.

GitHub issues may mirror the packet for notification and discussion, but they
are mutable control-plane records and are never the source of truth.

## Promotion gate

A field note becomes a packet only when it has all of the following:

- an exact source case revision and at least one source-artifact digest;
- an exact target revision and narrow owner surface;
- a literal minimal reproducer with a stated expected result;
- a tested local workaround and the remaining gap;
- a counterexample that can reroute or close the request;
- explicit data-minimization and non-claim boundaries.

The target disposition is deliberately non-normative. `protocol-candidate`
means only that normal proposal work may begin; it never means adopted.

## AI-first discovery

Target repositories should point agents to `needs/` from `AGENTS.md`, validate
packets in CI, and preserve closed packets with their disposition. Stable IDs,
closed status vocabularies, exact revisions, digests, and literal commands let
an agent reconstruct why a feature exists without loading the full case.
