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
verify independently. An earlier receipt keeps the shape it was filed under and
is validated against that version, never retrofitted to a later one.

A committed receipt keeps its bytes. Proving that a pathname survives proves
nothing about what now sits there, so every outcome is compared with the blob it
carried when it first entered the repository. A correction is a **new** receipt,
named `<REQUEST-ID>.<n>.json`, declaring `supersedes`; the earlier one stays
exactly as it was, and is still fully validated under the schema it declared.
Each chain ends at the receipt filed first, a correction must descend from what
it corrects, and exactly one receipt per request is current — a chain that closed
on itself would leave nothing live and nothing validated.

`DA-SIGMA-0001.json` is such a record: the `@v0` receipt as originally filed. It
was rewritten in place during the `@v1` migration, which is precisely the edit
these rules now forbid — so the original bytes were restored and the migrated
receipt lives beside it as `DA-SIGMA-0001.2.json`.

Validate every recorded outcome with:

```sh
mise run outcomes:check
```
