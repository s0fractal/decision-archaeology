# Constraint and counterexample cache

**An experiment, deliberately kept inside this repository.** It is not a
protocol, not a product, and not a separate project. If the measurement below
fails, it is deleted rather than defended.

## What it is for

An agent that hits a wall pays for the discovery. Every other agent — including
the next instance of the same one — pays again, because nothing records that the
wall is there. This is a cache of walls, where consulting an entry means running
its witness rather than trusting its text.

## What it is careful not to become

A prohibition list. Most dead ends are local, and a system that files them all as
"refuted" converts one bad afternoon into a rule nobody may question. So the
**type of an entry decides what it may do**, and the evidence burden follows the
strength of the claim:

| type | may | needs |
| --- | --- | --- |
| `REFUTATION` | block a path without new evidence | runnable witness **and** a negative control |
| `BOUNDARY` | redirect; never block | witness (usually the design saying no in its own words) |
| `COST_WITNESS` | inform a choice | a measurement with its method |
| `FAILED_ATTEMPT` | record that one way failed | witness; says nothing about other ways |
| `INCONCLUSIVE` | be read, never cited as a reason to stop | nothing |
| `UNRUNNABLE` | admit the test could not run here | nothing |
| `SUPERSEDED` | point at what replaced it | a successor |

A refutation without a negative control is refused: a check that cannot fail is
not evidence that something is impossible. Every entry must say what would end
its reach (`applies_until`) and what re-checking costs — a cache is only worth
consulting when re-checking is cheaper than re-discovering.

```sh
mise run cache:check                                  # entries and blocking witnesses
python3 tools/constraints.py lookup "<what you are about to try>"
python3 tools/constraints.py witnesses --all          # every witness, not just blocking
```

## How this gets judged

Two failure modes matter, and only one of them is obvious.

**The obvious one: a graveyard.** An archive nobody consults at planning time is
decorated JSON. The measurement is paired blind runs — the same task, model and
budget, with the cache and without — and the honest quantity is not "tokens
saved" but:

```
benefit = avoided re-discovery
        − lookup cost
        − witness re-check cost
        − cost of wrongly abandoning a path that would have worked
```

**The selection bias that would make those runs meaningless.** If the same party
writes the entries and then picks the tasks, the benchmark measures nothing but
its own authorship. So: tasks must be drawn from work that was not chosen for
them — the arena's real defects and the protocol questions that arise anyway —
and the set must include tasks **no entry covers**, because that is the only way
the lookup tax and the false-stop rate become visible. A cache that helps on
every task in its own benchmark has been fitted, not measured.

**The non-obvious one: autoimmunity.** An entry that blocks a path also prevents
the evidence that would overturn it — nobody walks the wall, so nobody learns it
moved. Immune memory that is never re-exposed becomes an allergy. A fraction of
budget therefore goes to **re-litigation**: deliberately attacking the cache's
own blocking entries, starting with the most expensive ones, and recording the
outcome (`still-holds`, `narrowed`, `overturned`). An entry that has never been
re-litigated is not more trustworthy for being old.

## Kill criteria

| if | then |
| --- | --- |
| paired runs show no net benefit outside the entries' own authorship | delete it; the idea was wrong here |
| an entry blocks a path that later turns out to work, and re-litigation did not catch it first | the type system is too permissive — tighten before adding entries |
| entries accumulate faster than witnesses are re-run | it has become a collection, not a cache |
| it does show net benefit on independently drawn tasks | only then extract it from this repository |

## Where the first entries came from

Not from brainstorming. Every one is a wall this project actually walked into
over 2026-08-21 and 2026-08-22 — five of them found by an agent reviewing another
agent's work — and each witness is a test that already exists here because the
defect it describes is now permanently caught.
