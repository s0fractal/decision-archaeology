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

A committed receipt keeps its bytes. Proving that a pathname survives proves
nothing about what now sits there, so every outcome is compared with the blob it
carried when it first entered the repository. A correction is a **new** receipt,
named `<REQUEST-ID>.<n>.json`, declaring `supersedes`; the earlier one stays
exactly as it was and is validated only for immutability and identity, under the
schema it declared at the time.

`DA-SIGMA-0001.json` is such a record: the `@v0` receipt as originally filed. It
was rewritten in place during the `@v1` migration, which is precisely the edit
these rules now forbid — so the original bytes were restored and the migrated
receipt lives beside it as `DA-SIGMA-0001.2.json`.

Validate every recorded outcome with:

```sh
mise run outcomes:check
```
