# Progress

Status key: `not started` | `in progress` | `blocked` | `done`

| Stage | Status | Notes |
| ----- | ------ | ----- |
| 0. Planning docs (`SPEC.md`, `AGENTS.md`, `PROGRESS.md`, `PLAN.md`) | done | Plan approved 2026-10-08 with sigma / linearization / robustness overrides |
| 1. Repo skeleton (pyproject, config, Makefile, CI, gitignore) | done | pip pins (uv not installed); config locks 2024-01 + close-to-close sigma |
| 2. Data download, checksum verify, schema normalize, parquet cache | not started | `scripts/download_data.py`, `src/exec_impact/data.py` |
| 3. 1-minute bars | not started | close-to-close sigma; empty minutes → 0 return; intra-bar RV diagnostic only |
| 4. Impact model (fit, bootstrap CI, temp/perm, weekly stability, OOS R2) | not started | `src/exec_impact/impact.py` |
| 5. Execution schedules (TWAP, VWAP, oracle VWAP, AC, lambda sweep) | not started | value-match eta at child-slice participation; ref_adv_frac sensitivity |
| 6. Stretch: power-law numerical trajectory vs closed form | not started | after closed-form AC is green |
| 7. Tape-replay simulation | not started | `src/exec_impact/simulate.py` |
| 8. Synthetic Monte Carlo correctness check | not started | same module |
| 9. Metrics, figures, `results/` | not started | metrics.json: commit hash, config, seed, data month; commit key PNGs |
| 10. Tests (pytest) matching SPEC §5 | not started | `tests/` (skeleton tests exist) |
| 11. README + `make report` | not started | note 2024-01 ETF-approval vol; 2024-07 robustness after main |
| 12. CI green (`ruff` + `pytest`) | not started | workflow added; needs a remote run |

## Resume hint

Next: Stage 2 — implement `src/exec_impact/data.py` and `scripts/download_data.py`
(Binance aggTrades, CHECKSUM, header/ts detection, parquet under `data/`).
Do not download the robustness month until main 2024-01 results are done.
