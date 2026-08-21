# Probe: the third and fourth owners, and why neither was the right one

The first pressure report routed two blocked operations to OAIP and SEV. Both
routings were written before either contract was exercised. Exercising them moved
both.

## OAIP does not acquire anything, and says so

The blocked operation: reproduce the exact bytes of a public record after the
publisher changes it. OAIP was named as the owner of acquisition and provenance.

Its SPEC settles the question directly. The threat table's row for a remote party
reads: **"OAIP opens no sockets and fetches nothing."** The protocol observes
what happened to a workspace — intent, execution, effects, claim, acceptance —
and its cardinal rule is that an account of work must be measured rather than
narrated. An acquisition modelled as an OAIP `Execution` would attest that some
command wrote some bytes into a workspace. That the bytes came from a given
authority at a given time would be exactly the narrated part, which is the thing
OAIP exists to refuse.

So the acquisition receipt is not an OAIP need. Filing one would have been
`wrong-owner`, and the packet contract has that disposition for a reason.

## SEV's loss manifest is about projection, not about the world

The blocked operation: state why a source cannot support a claim without turning
restricted or unlocated material into semantic absence.

SEV's `loss_manifest` is first-class honesty about a **projection** — L-SIG,
L-CANON, L-SETTLE, L-UNJUDGED and the rest qualify what the RDF view cannot
express or verify about a sealed snapshot. There is no code for material that was
never acquired, is access-restricted, or exists only as a report. SEV also states
its own status plainly: research, not adopted, nothing here is a live contract.

A repository whose absences are about the world therefore cannot borrow SEV's
vocabulary, and asking SEV to grow one would be asking a projection format to
model evidence acquisition.

## What testing found instead

Checking the barite case's five external sources produced a harder fact than
either routing anticipated:

| source | automated access | custody |
| --- | --- | --- |
| two Prozorro API records | HTTP 200 | publisher-verifiable |
| AMCU preliminary findings | **HTTP 403** | **unwitnessed** |
| AMCU final news | **HTTP 403** | independently witnessed (web.archive.org, 2026-07-16T14:52:51Z) |
| AMCU decision register entry | **HTTP 403** | **unwitnessed** |

The publisher of the case's decisive documents blocks automated clients
outright. Two of its three pages exist, today, in no copy this case can point to:
if either is edited or withdrawn, nothing establishes what it said. The third
survives only because a public archive captured it on the day it was published —
228,417 decoded bytes, digest recorded, retrieved and confirmed to carry the
headline the case cites.

The Prozorro records are in a quieter version of the same state: their digests
are recorded, but the bytes are not retained, so the digests can only be checked
while the publisher keeps serving identical bytes. Nobody independent holds them.

## Where it went

`tools/acquisition_state.py` and the committed
`sources/acquisition-state.json` record retrievability and custody with a closed
vocabulary — `retained-locally`, `publisher-verifiable`,
`independently-witnessed`, `unwitnessed` — validated offline in the gate and
re-checked over the network by `mise run case:barite:acquisition:live`.

A witness cannot be dropped quietly: the validator reads the last committed
version of the record and refuses one where a previously recorded snapshot has
disappeared without a stated reason. Absence has to be declared, which is the
same rule an outcome receipt already enforces about its own past.

It attests custody only. Whether a source supports a claim is a different
question, and a blocked automated fetch is a fact about this client rather than
evidence that anyone withheld anything.

No packet was filed at either owner. That is two of three routings from the
original pressure report corrected by testing rather than by argument, and the
one that survived — `DA-SIGMA-0001` — is also the one that was tested first.
