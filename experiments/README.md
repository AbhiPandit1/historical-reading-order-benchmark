# Reading-order recovery experiments

Run from the repository root (needs the bundled `bench/` data and `harness/`):

```bash
python experiments/exp1_run.py    # ordering-control: naive vs column-clustering vs XY-cut vs kraken (tau)
python experiments/exp2_run.py    # downstream order-induced WER (perfect line recognition assumed)
python experiments/exp3_stats.py  # bootstrap 95% CIs for the key tau results
```

- `ordering.py` — geometric ordering rules (top-to-bottom, column clustering, XY-cut).
- These back Section 6 ("Recovering reading order with a cheap ordering stage") and
  Figure `figures/ordering_control.png` in `paper/paper.pdf`.
