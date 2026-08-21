# Kherson fortifications: source-sufficiency candidate

Status: **NOT ADMITTED AS A PUBLIC CASE**

## Bounded question

What can public and attributable sources substantiate, challenge, or leave
indeterminate about the reported markup in the supply chain used by TOV Global
Build Engineering for fortification work in Kherson region?

This wording is intentionally narrower than “prove a corruption scheme.” It
does not presume that a resale markup is an overpayment, that the intermediary
was unnecessary, that company connectedness is established, or that criminal
liability follows.

## What is currently attributable

- **ATTRIBUTED CLAIM — Bihus.Info:** Global Build Engineering received about
  `280 million UAH` for fortification work, bought materials through newly
  created Dnipro Promsnab Torh, and the journalists calculated a possible
  `35 million UAH` markup on anti-tank pyramids and concrete products.
- **ATTRIBUTED CLAIM — Bihus.Info:** the owner of the intermediary also received
  income from Global Build Engineering; Bihus.Info treats this as a signal of
  connectedness.
- **ATTRIBUTED COUNTERCLAIM — Anton Samoilenko via Suspilne:** he denied personal
  or business ties to Global Build Engineering, disputed the `35 million UAH`
  calculation, said the relevant acts require authorized access, and said the
  described “Lego blocks” were not used in Kherson fortifications.
- **ATTRIBUTED FOLLOW-UP — Bihus.Info:** prosecutors registered a proceeding
  under Part 5 of Article 191 after a submission by the outlet's legal project;
  the cited official response itself is not included in the public article.

None of those statements is converted into an unqualified repository fact.

## Why the proposed Prozorro-first dossier is blocked

The initial proposal assumed that all key contracts, estimates, acts, supplier
documents, and payments were available through Prozorro. The inventory does not
support that assumption:

- no exact Prozorro identifier for the asserted `280 million UAH` fortification
  scope has been bound to the named contractor;
- the alleged manufacturer → intermediary → contractor chain concerns private
  supply transactions and tax/accounting material, not necessarily separate
  public procurement contracts;
- the price calculation cannot be normalized without exact product
  specifications, quantity, delivery date, VAT treatment, transport, storage,
  financing, risk, and accepted-work scope;
- a reported income link is not the same predicate as common beneficial
  ownership;
- some performance material may be restricted because it concerns defensive
  fortifications.

The easily found public procurements involving the same contractor are not the
claimed Kherson fortification contracts. Treating them as evidence would be an
identity error.

## Admission gate

The gate is a record, not a checklist in prose: see
[`admission.json`](admission.json) and its rendering in
[`admission.md`](admission.md). A requirement counts as met only when it names
evidence that resolves, an unmet one must say what is missing, and every
material the inventory records as missing has to keep a requirement open.
`mise run candidates:check` decides the verdict and refuses to let this
directory appear under `examples/` while blocking requirements are unmet.

Current verdict: **NOT ADMITTED** — 1 of 9 requirements met.

See [`source-inventory.json`](source-inventory.json) and
[`search-log.md`](search-log.md).
