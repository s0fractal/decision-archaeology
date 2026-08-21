# Admission gate — kherson-fortifications

Rendered from `admission.json`; edit the record, not this file.

**Verdict: NOT ADMITTED**

A requirement counts as met only when it names evidence that resolves.

- [ ] **AG-001** — Exact contracting authority, contract identifiers, dates, scope, and payment records for the reported 280 million UAH.
  - open because: No Prozorro identifier has been bound to the named contractor for the asserted fortification scope; the easily found procurements involving the same contractor are different contracts, and treating them as evidence would be an identity error.
  - awaiting: `missing.kherson-contracts`
- [ ] **AG-002** — Attributable copies or lawful extracts of the invoices and delivery records behind the manufacturer to intermediary to contractor comparison.
  - open because: The price comparison exists only inside the investigative report; the underlying documents are not attached to it and are private supply material rather than published procurement records.
  - awaiting: `missing.supply-invoices`
- [ ] **AG-003** — Product equivalence normalized for specification, quantity, date, VAT, logistics, storage, financing, and risk.
  - open because: Without the acceptance acts and exact product specifications, a resale price difference cannot be normalized into a comparable unit price, so no markup figure can be reproduced.
  - awaiting: `missing.acceptance-acts`
- [ ] **AG-004** — Time-bound company-registry evidence for every claimed relationship.
  - open because: A reported income link is not the predicate of common beneficial ownership, and no registry snapshot bound to the relevant dates has been retained.
  - awaiting: `missing.company-snapshots`
- [ ] **AG-005** — An explicit distinction between observed resale markup, public loss, artificial overpayment, and criminal hypothesis.
  - open because: The distinction is stated in prose but cannot be applied to figures that do not yet exist in attributable form; it becomes checkable only once AG-002 and AG-003 close.
- [x] **AG-006** — A material counterposition retained as a first-class source.
  - evidence: `candidate.suspilne.counterposition`
- [ ] **AG-007** — A primary or attributable official record of the criminal proceeding and its current procedural status.
  - open because: The registration is described by the outlet that submitted the complaint; the official response itself is not published in the article, and a registered proceeding is not a finding of wrongdoing.
  - awaiting: `missing.proceeding-primary-record`
- [ ] **AG-008** — A publication review that excludes operationally sensitive fortification detail and unnecessary personal data.
  - open because: The material concerns defensive fortifications during wartime and names private individuals who have denied the allegations; the review cannot be completed before the material that would be published exists.
- [ ] **AG-009** — At least one deterministic check over retained, publishable inputs.
  - open because: Nothing publishable is retained to check. The stack can now compile an exact-arithmetic claim to a re-runnable term, which is what this requirement would use — but a check needs inputs, and the inputs are the thing that is missing.
