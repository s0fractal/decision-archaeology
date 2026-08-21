# Public cases

Each directory under `examples/` is a self-contained, publishable investigation
case. Copy `_template/` to begin a case; do not edit the template to contain a
specific investigation.

## Required layout

```text
<case-id>/
├── README.md
├── case.json
├── exclusions.md
├── sources/
├── observations/
├── claims/
├── decisions/
├── checks/
├── receipts/
└── artifacts/
```

The directories separate evidence from interpretation and authored records
from generated output:

- `sources/` contains source descriptors and, only when publication is lawful,
  source material;
- `observations/` contains bounded extracts or readings tied to sources;
- `claims/` contains attributable assertions and their support or challenge;
- `decisions/` contains reconstructed decision events and alternatives;
- `checks/` contains rerunnable predicates, fixtures, and commands;
- `receipts/` contains signed or hash-addressed execution and assertion records;
- `artifacts/` contains generated graphs, reports, and exports;
- `exclusions.md` discloses missing, withheld, unsafe, or out-of-scope material.

`artifacts/` is never the sole source of a substantive claim: generated output
must point back to the records and transformations that produced it.

The format is currently `decision-archaeology.case@v0` and is a draft.
