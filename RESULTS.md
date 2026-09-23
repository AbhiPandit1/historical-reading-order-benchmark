# Results

Five segmentation systems on 40 historical pages across eight languages, each
scored on two separate questions: **did it find the lines** (detection F at
IoU ≥ 0.5) and **did it read them in the right order** (Kendall τ between the
predicted order and the ground-truth document order, on the matched lines).

## How to read these tables

- **F** — line-detection F-score at IoU ≥ 0.5, greedy matching to GT boxes.
- **τ** — Kendall rank correlation of predicted vs ground-truth reading order,
  computed **only on the lines that were correctly detected**. τ = 1.0 is a
  perfect order, τ ≈ 0.5 is close to random on a two-column page.
- A reading-order score is only meaningful if enough lines were matched to
  order. **τ is reported only for pages where a system matched ≥ 60 % of GT
  lines and ≥ 15 lines**; the count in `[n/5]` says on how many of the five
  pages that held. Where a system detected too few lines to score order, the
  cell reads **det-fail (x %)** with its mean matched fraction — that is itself
  a finding, not a gap to paper over.
- German is **excluded from scoring**: its ground truth is under-annotated
  (every system detects far more lines than the GT lists), so its F and τ are
  not comparable. See `data_note/SOURCES.md`.

## Per-language

Layout type drives everything, so the languages are grouped by it.

### Multi-column / complex layout — where reading order is contested

| Language | kraken F / τ | YOLO F / τ | Surya F / τ | Tesseract F / τ | docTR F / τ |
|----------|:---:|:---:|:---:|:---:|:---:|
| English (print, 2-col) | 1.00 / **0.97** | 0.98 / **0.50** | 0.97 / 0.50 | 0.97 / 0.99 | 0.97 / 0.52 |
| Swedish (court hand) | 0.95 / **1.00** | 0.94 / **0.47** | 0.81 / 0.49 | 0.22 / det-fail | 0.00 / det-fail |
| Middle-French (ms) | 0.94 / **1.00** | 0.94 / **0.52** | 0.90 / 0.56 | 0.32 / det-fail | 0.62 / 0.57 |

On these pages every system that detects lines well disagrees on order: the
layout-aware ones (kraken, and Tesseract *when it detects*) hold τ ≈ 0.97–1.00,
while the pure box-detectors (YOLO, Surya) collapse to τ ≈ 0.47–0.56, i.e. close
to random. Detection is not the problem — on English and Swedish YOLO detects as
well as kraken (F 0.98 / 0.94) yet orders half the lines wrong.

### Single-column / simple layout — the control

| Language | kraken F / τ | YOLO F / τ | Surya F / τ | Tesseract F / τ | docTR F / τ |
|----------|:---:|:---:|:---:|:---:|:---:|
| Spanish (print) | 0.97 / 1.00 | 0.93 / 1.00 | 0.94 / 1.00 | 0.93 / 0.95 | 0.91 / 1.00 |
| Italian (print) | 0.81 / 1.00 | 0.79 / 1.00 | 0.67 / 1.00 | 0.81 / 1.00 | 0.59 / 1.00 |
| French (ms) | 0.99 / 0.93 | 0.94 / 0.89 | 0.86 / 0.95 | 0.53 / 1.00* | 0.22 / 0.64* |
| Franco-provençal | 0.65 / 1.00* | 0.78 / 0.99* | 0.65 / 1.00* | 0.53 / 1.00* | 0.64 / 1.00* |
| Catalan | 0.98 / 0.98 | 0.96 / 0.99 | 0.41 / 1.00* | 0.42 / det-fail | 0.86 / 0.99 |

Where the page is a single column the ordering question disappears: a naive
top-to-bottom sort is already correct, so every system scores τ ≈ 1.0 regardless
of family. This is the control that isolates the effect above — the reading-order
tax is paid **only** when the layout has more than one column.
(*τ from fewer than 5 valid pages; see the harness output for per-page counts.)

## Overall (eight scored languages, German excluded)

| System | Detection F | Reading-order τ | Speed (s/page) | Native reading order |
|--------|:---:|:---:|:---:|:---:|
| **kraken** `blla` | 0.91 | **0.98** | 10.6 | yes |
| **YOLOv8m** detector | 0.91 | 0.77 | **1.2** | no (top-to-bottom) |
| Surya | 0.78 | 0.77 | 5.0 | no |
| docTR | 0.60 | 0.81 | 5.3 | native |
| Tesseract | 0.59 | 0.98 | 3.1 | layout-aware |

τ is averaged over valid pages only (kraken 36, YOLO 35, Surya 32, docTR 26,
Tesseract 18 of a possible 40).

## What the numbers say

1. **Detection is solved-enough and not the differentiator.** kraken and the
   YOLO box-detector tie at F 0.91. A fast, general detector finds historical
   lines as well as a purpose-built segmenter.
2. **Reading order is the differentiator, and only on multi-column pages.**
   Overall τ splits 0.98 (kraken) vs 0.77 (YOLO), and the entire gap lives in
   the three multi-column languages, where YOLO/Surya fall to ≈ 0.5. On
   single-column pages everyone scores ≈ 1.0.
3. **Print-oriented recognisers fail to *detect* historical handwriting.**
   Tesseract and docTR order well when they detect (Tesseract τ 0.98 overall),
   but on the Swedish court hand they matched 27 % / 0 % of lines — so their
   good order numbers come from the easy printed pages, not the hard manuscript
   ones. On manuscripts they are not usable as-is.
4. **Speed is not free.** YOLO is ~9× faster per page than kraken but needs an
   explicit ordering stage to be usable on multi-column material. The practical
   rule is two-tier: single column → fast detector is enough; multi-column →
   either pay for native ordering (kraken) or add a geometric ordering step on
   top of the fast detector.
5. **The effect is era-invariant.** The same pattern holds on a ~17th-century
   Swedish handwritten court record and a 20th-century printed English page —
   about three centuries apart. Reading order is a function of layout, not of
   date or script, which is why the finding generalises across the set.
