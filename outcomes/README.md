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

Validate every recorded outcome with:

```sh
mise run outcomes:check
```
