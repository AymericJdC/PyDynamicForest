# Q-9E.1 - Audit diamétrique d'Écouves A5

## Scope

This lot reads individual circumferences and statuses, reconciles them with the selected aggregate series, flags anomalies, and writes four CSV files plus a Markdown report. It does not impute heights.

## Run

```bash
python scripts/article/audit_ecouves_a5.py
```

Optional explicit paths:

```bash
python scripts/article/audit_ecouves_a5.py --individual-data data/article/ecouves_a5/raw/Ecouves-A5.xlsx --reference-data "data/article/ecouves_a5/reference/Douglas2021(116obs).xlsx" --output-dir outputs/article_scenarios/ecouves_a5_reconstruction --plot-area-ha 0.1216
```

CSV files use UTF-8 encoding, comma separators and explicit unit suffixes. Selection minimizes `abs(ΔN)/N_ref + abs(ΔCg)/Cg_ref`. Ties rounded to 12 decimal places use the documented parsimony order: `all_measured`, `rest_only`, `rest_chab`, `rest_sec`, `all_statuses`. Audit years without reference aggregates remain descriptive and use `all_measured`; they are never marked as reconciled reference states.

## Test

```bash
pytest -q tests/article/test_ecouves_a5_inventory.py
```

Synthetic tests run without confidential data. The real-file test is skipped when local workbooks are absent.
