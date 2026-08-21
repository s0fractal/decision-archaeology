# Need outcomes

Each JSON file closes one case-derived need by linking the target owner's
non-normative disposition to an exact resolution revision and a rerun case
receipt. Outcomes preserve routing history; they do not confer review,
protocol-adoption, or substantive truth authority.

Artifact digests are verified against the blob at the outcome's own
`resolution.revision`, not against the working tree. An outcome records what
resolved a need at a point in history, so improving a resolved artifact later
must not break it — otherwise the cheapest way to make the gate green is to
rewrite the record until it matches the present, which is the one thing a
receipt must never do.

`decision-archaeology.need-outcome@v1` additionally requires a `rebuild` block:
the revision, path, and digest of a rebuild derived from one of the outcome's own
published artifacts, together with the implementations it was forbidden to read.
The validator rejects an outcome whose rebuild imports what it is supposed to
verify independently. The single `@v0` record was migrated in place rather than
kept as a second shape, and its rebuild is recorded at the revision where it ran.

Validate every recorded outcome with:

```sh
mise run outcomes:check
```
