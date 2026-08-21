# Barite tenders and AMCU decision 535-r

Template identity: `decision-archaeology.case-template@v0.1.0`

This is calibration case `case-00`. It tests whether a compact public dossier
can preserve the difference between an authority's finding, facts observable in
public records, deterministic derivations, and attractive but unsupported
shortcuts.

## Question

Which parts of AMCU decision `535-р` can be reconstructed from the public
procurement record, and which proposed shortcuts are refuted by that record?

## Scope

The case covers two 2025 barite tenders by AT UkrGasVydobuvannya, the AMCU case
`145-26.13/35-26`, and public AMCU material through the 2026-08-21 acquisition.
It does not attempt to reproduce evidence that is not present in the inventoried
public sources.

## Reproduce

Offline, from committed minimized inputs:

```sh
mise install
mise run case:barite
```

Refresh the two official Prozorro records and fail if either the complete
response bytes or the minimized projection changed:

```sh
mise run case:barite:live
```

The live check is intentionally separate from the offline gate: remote
availability is not allowed to turn a frozen case green or red silently.

## Findings

- **FACT — attributed decision:** AMCU reports that decision `535-р` found TOV
  Nova Interpraiz and TOV Torhova Trubna Kompaniia responsible for bid-rigging in
  the two identified tenders. That is an attributed administrative finding, not
  a conclusion produced by this repository.
- **FACT — public record:** both named respondents submitted bids in both
  tenders. Other bidders participated as well: five bidders appear in the first
  record and four in the second.
- **FACT — exact arithmetic:** the API expected values sum to
  `336,491,711.70 UAH`. The AMCU news page states `336,491,711 UAH`; those values
  differ by `0.70 UAH` and must not be described as byte-for-byte or decimal
  equality.
- **REFUTATION:** the exactly `1 UAH/t` price difference in the second tender is
  between company IDs `35341905` and `37351098` (Torhova Trubna Kompaniia and
  Alfa Liuks), not between the two AMCU respondents. It is not a valid shortcut
  for reconstructing this decision's respondent pair.
- **FACT — null result:** the Prozorro API exposes no exact MD5 document-hash
  intersection between the two respondents in either tender. A separate audit
  found no exact full metadata-tuple match across 59 public PDFs belonging to
  those respondents.
- **HYPOTHESIS:** the public procurement material is sufficient to bind actors,
  tenders, bids, prices, and the published outcome, but insufficient to
  independently reconstruct why AMCU inferred coordination.

See [`claims/claims.jsonl`](claims/claims.jsonl), the reconstructed
[`decision event`](decisions/amcu-535-r.json), and the generated
[`check report`](artifacts/check-report.json).

## Limitations

The most important limitation is missing decisional reasoning: the public news
and registry establish the outcome, while the full evidence chain used by AMCU
was not located. See [`exclusions.md`](exclusions.md) for the complete boundary.
