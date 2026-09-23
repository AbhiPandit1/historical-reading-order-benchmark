# Data sources

All pages come from openly licensed datasets: the [FONDUE](https://github.com/FoNDUE-HTR)
collection in the [HTR-United](https://htr-united.github.io/) catalogue, and the
public [Riksarkivet](https://huggingface.co/Riksarkivet) (Swedish National
Archives) HTR datasets on Hugging Face. Five pages per language. Only images and
ground truth already published under open licences are referenced here; see each
source repository for its exact licence. **No private or restricted archival
material is included.**

## Per-language provenance

| Lang | Label in benchmark | Source dataset | Layout | Era | Script |
|------|--------------------|----------------|--------|-----|--------|
| eng | English  | FONDUE-EN-PRINT-20 | two-column print | 20th c. | printed |
| spa | Spanish  | FONDUE-ES-PRINT-19 | single-column print | 19th c. | printed |
| ita | Italian  | FONDUE-IT-PRINT-20 | single-column print | 20th c. | printed |
| fra | French   | FONDUE-FR-MSS-18   | single-column ms | 18th c. | manuscript |
| frm | Middle-French | FONDUE (Gallica/BnF `btv1b…` manuscripts) | dense manuscript | late-medieval / early-modern | manuscript |
| frp | Franco-provençal | FONDUE regional manuscript set | single-column ms | early-modern | manuscript |
| cat | Catalan  | FONDUE Catalan set | single-column | 19th c. | mixed |
| swe | Swedish  | Riksarkivet — Göta hovrätt (court of appeal records) | multi-column court hand | early-modern (~17th c.) | handwritten |

Era is stated at the granularity the source dataset documents (usually a
century), taken from the dataset name or its catalogue entry — not inferred from
page content. Where a dataset does not pin a precise year, only the century is
claimed here. Nothing in this table is fabricated; unspecified fields are left at
century level on purpose.

## A note on eras (deliberate spread, not an accident)

The set spans roughly the 16th–20th centuries and mixes printed and handwritten
material on purpose. Reading order is a property of **layout**, not of date or
hand, so covering several centuries is a way to test whether the effect is an
artefact of one period. It is not: the same detection-vs-order split appears on a
~17th-century Swedish handwritten court record and a 20th-century printed English
page. See `RESULTS.md`, finding 5.

## Excluded from scoring

**German (FONDUE-MLT-ART).** Retained in the repository for completeness but
**excluded from all scored tables**: its ALTO ground truth is under-annotated
relative to the page (every system, including the layout-aware ones, detects
substantially more lines than the GT lists), so both F and τ are not comparable
to the other languages. This is a ground-truth coverage issue, not a system
result, and is flagged here rather than silently averaged in.
