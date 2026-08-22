# Revision pins

Every guard in this repository is enforced by reading git history: an absence
cannot be produced by deletion, a receipt cannot be rewritten, a requirement
cannot quietly ask for less. All of it holds only while the history holds.

These files record the other half of that sentence — who, apart from this
repository, is known to retain an observation of the revisions its own records
depend on.

Today that is nobody. `revisions.json` says so, and the gate prints it on every
run:

```
2 load-bearing revisions, 0 independently witnessed,
2 retained by nobody but this repository
```

That is not a failure state to be hidden until it is fixed. An unwitnessed
revision is not compromised; it is one whose survival depends entirely on us, and
the honest thing is to be able to count them. Closing the gap needs a party
outside this repository, which is a dependency decision — see
[`docs/proposals/external-pin.md`](../docs/proposals/external-pin.md), which is a
proposal and is not adopted.

```sh
mise run pins:check     # offline: the claims are consistent and the revisions readable
mise run pins:refresh   # asks a public archive what it already holds; creates nothing
```

The refresh is read-only by design. Asking an archive what it kept is an
observation; asking it to keep something is publication, and that is exactly the
decision the proposal leaves open.
