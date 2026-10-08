# exec-impact

Estimate market impact from Binance spot aggTrades and test whether
Almgren–Chriss optimal execution reduces implementation shortfall versus
TWAP and VWAP.

**Results are not in this README yet.** After `make data && make fit && make simulate && make report`,
this file will include the metrics table, figures, and an honest limitations
section. Every number will be generated from `config.yaml` with a fixed seed.

See `SPEC.md` and `PLAN.md` for the research design.

## Locked choices

- Main month: **2024-01** (includes US spot Bitcoin ETF-approval volatility; not a typical month).
- Robustness month: **2024-07**, run only after main results (`run_robustness: false` until then).
- Sigma: **1m close-to-close** log returns everywhere (empty minutes → zero return). Intra-bar RV is diagnostic only.
- AC linearization: **value-match** temporary impact at the **child-slice** participation rate implied by `ref_adv_frac`, horizon, and \(N\), using prior data only. Sensitivity across several `ref_adv_frac` values.

## Setup

Python 3.11. `uv` is preferred if installed; otherwise pip with the pins in `pyproject.toml`.

```bash
python -m venv .venv
.venv/Scripts/activate   # Windows
pip install -e ".[dev]"
make test
```

`make data` / `make fit` / `make simulate` / `make report` are stubs until later stages.
