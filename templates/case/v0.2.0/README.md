# Case title

Template identity: `decision-archaeology.case-template@v0.2.0`

Replace this file with a short, neutral entry point to the investigation, but
preserve the template identity in `case.json`.

## Question

State the bounded retrospective question the case attempts to answer.

## Scope

State the time range, institutions, decisions, and material included.

## Reproduce

List literal commands that rebuild checks and generated artifacts from the
committed inputs. Do not publish placeholder commands as runnable instructions.

## Findings

Summarize only findings traceable to case records. Label facts, hypotheses, and
speculation explicitly.

## Limitations

Link to [`exclusions.md`](exclusions.md) and summarize the limitations most
likely to change interpretation of the case.

## What v0.2.0 added

`exclusions.json` — the case's absences as data: kind, subject, boundary, and
what would resolve them. `exclusions.md` is rendered from it, so the prose
cannot drift from the record, and an absence cannot disappear without being
retired with a reason. v0.1.0 remains published and unchanged.
