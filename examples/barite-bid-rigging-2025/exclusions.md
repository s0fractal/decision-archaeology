# Exclusions and limits

Rendered from `exclusions.json`; edit the record, not this file.

## Searched for and not located

- **EX-001 — The complete text and evidentiary annexes of AMCU decision 535-р.** This case reconstructs the published administrative outcome, not the authority's full reasoning.
  - Searched: The official public sources inventoried on 2026-08-21: the AMCU news items, the decision register entry, and the two Prozorro API records.
  - Would resolve it: Publication of the decision text in the official register, or a lawful access request that returns it.

## Exists but access is restricted

- **EX-007 — Automated re-acquisition of the AMCU pages.** The publisher returns HTTP 403 to automated clients, so this case cannot re-read its own decisive sources mechanically; two of the three pages are held in no independent copy.
  - Restriction: Practical restriction by the publisher's bot protection, recorded per source in sources/acquisition-state.json. It is a fact about this client, not evidence that anything was withheld.
  - Would resolve it: An independent archival capture of the two unwitnessed pages, or a channel the publisher serves to automated readers.

## Held but deliberately not republished

- **EX-002 — The complete Prozorro API responses and bid documents.** The committed fixture is a data-minimized projection of the two official records.
  - Minimization: SHA-256 digests of the complete responses are recorded in sources/source-index.json; the responses and bid documents themselves are not republished here.
- **EX-005 — Personal and contact data in the source records.** Company names and identifiers are retained; unnecessary personal and contact data are not.
  - Minimization: The identifiers are necessary to bind the official decision to the public tender records; nothing beyond that necessity was carried into the committed projection.

## Checked by a method with a stated reach

- **EX-004 — The PDF metadata audit.** An exploratory null result is evidence about what the method examined, and about nothing else.
  - Method: Exploratory metadata scan over 59 public PDFs, returning no shared-authorship signal.
  - Not examined: archives and their revision history; digital signatures; deleted document revisions; network logs; banking data; evidence held by AMCU

## Present, and does not prove what it is often read to prove

- **EX-003 — Public participation, price, and document metadata.** None of it independently proves coordination, intent, guilt, or legal liability.

## Outside the frozen question

- **EX-006 — Appeals, judicial review, enforcement, payment of fines, and later record changes.** All of it falls outside the frozen acquisition snapshot this case reasons over.
