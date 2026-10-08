# PLAN: exec-impact

Status: **approved** (2026-10-08) with the overrides below. Stage 1 is the repo skeleton.

## Goal (one sentence)

Calibrate a no-lookahead impact model on one month of Binance BTCUSDT/ETHUSDT aggTrades, then compare Almgren–Chriss, TWAP, and VWAP on paired tape-replay shortfall, with a synthetic Monte Carlo as a model-correctness check.

## Proposed repo layout

```
.
├── AGENTS.md
├── SPEC.md
├── PLAN.md
├── PROGRESS.md
├── README.md                         # after results exist; numbers from make report
├── Makefile                          # data / fit / simulate / report / test
├── config.yaml                       # month, symbols, fees, grid, seeds, windows
├── pyproject.toml                    # python 3.11, ruff, pytest, pinned deps
├── .gitignore                        # data/, results caches, .venv, __pycache__, .pytest_cache
├── .github/workflows/ci.yml          # ruff + pytest (no data download in CI)
├── scripts/
│   ├── download_data.py              # fetch zips + CHECKSUM, verify, write parquet
│   ├── fit_impact.py                 # make fit
│   ├── run_simulate.py               # make simulate
│   └── make_report.py                # make report -> results/metrics.json + figures
├── src/exec_impact/
│   ├── __init__.py
│   ├── data.py                       # load/normalize aggTrades, checksum, parquet I/O
│   ├── bars.py                       # 1m (and resample 5m/15m) bars
│   ├── impact.py                     # Y, delta, temp/perm, bootstrap, OOS, weekly
│   ├── schedules.py                  # TWAP, VWAP, oracle VWAP, AC closed form (+ stretch)
│   ├── simulate.py                   # tape replay + synthetic GBM+linear impact
│   └── metrics.py                    # IS bps, CVaR, paired tests, tables, plots
├── tests/
│   ├── conftest.py
│   ├── test_data.py
│   ├── test_bars.py
│   ├── test_impact.py
│   ├── test_schedules.py
│   ├── test_simulate.py
│   ├── test_metrics.py
│   └── test_no_lookahead.py
├── data/                             # gitignored; parquet cache + raw zips
└── results/
    ├── metrics.json                  # generated; commit only if small and seed-locked
    └── figures/                      # generated pngs
```

CI will not download Binance data. Tests use synthetic fixtures and tiny hand-crafted trades.

## Config (`config.yaml`) — proposed keys

- `symbols`: `[BTCUSDT, ETHUSDT]`
- `market`: spot aggTrades
- `month`: `2024-01` (includes ETF-approval volatility; README must say so)
- `robustness_month`: `2024-07`, `run_robustness: false` until main results exist
- `data_dir`, `results_dir`
- `taker_fee_bps` (configurable constant line on plots)
- `bar_interval`: `1m`; impact intervals: `[1m, 5m, 15m]`
- `sigma.method`: `close_to_close_1m` only for impact and AC (empty minutes → 0 return). Intra-bar RV is a diagnostic column, never used for normalization or AC. Coarser intervals use realized variance from those 1m returns.
- `vwap_profile_lookback_days`: `7`
- `perm_lag_k`: integer intervals for permanent-impact lag
- `n_child_slices` or slice length derived from horizon / bar size
- `grid.adv_frac`: `[0.01, 0.05, 0.1, 0.5, 1.0]`
- `grid.horizons`: `[30m, 1h, 4h]`
- `grid.sides`: `[buy, sell]`
- `lambda_grid`: ≥ 6 values from near 0 to large
- `n_replay_starts`: ≥ 500
- `rng_seed`: fixed int
- `ac_linearization`: value-match linear vs power-law temporary impact at the **child-slice** participation rate implied by `ref_adv_frac`, horizon, and \(N\) (not parent size / ADV). Reference from prior data only. Sensitivity over several `ref_adv_frac` values.
- `stretch.power_law_optimize`: bool, default false until closed form is done

## Module list and responsibilities

### `src/exec_impact/data.py`

- Download daily `aggTrades` zips + `.CHECKSUM` from `data.binance.vision`.
- Verify checksum before unpack.
- Detect header vs no-header; map columns: `agg_trade_id`, `price`, `quantity`, `first_trade_id`, `last_trade_id`, `timestamp`, `is_buyer_maker`, `is_best_match` (best-match optional).
- Detect timestamp unit (ms vs µs) from magnitude; convert to UTC datetime.
- Aggressor: `is_buyer_maker == True` → **sell aggressor** (`signed_qty = -qty`); else **buy aggressor** (`signed_qty = +qty`).
- Cache normalized trades as parquet under `data/`.

### `src/exec_impact/bars.py`

- 1-minute bars: `last` (last trade price), `volume`, `signed_volume` (buy-minus-sell aggressor qty), `trade_count`, `realized_vol` (from intra-bar trade returns or 1m log returns as documented in README).
- Resample to 5m / 15m for impact regressions.
- Trailing `sigma` and trailing average volume `V`: rolling windows ending **strictly before** the interval used as the observation (shift by 1 bar).
- **Sigma (locked):** one series everywhere — 1m close-to-close log returns, with missing minutes forward-filled as **zero return**. Do not use intra-bar RV for impact \(r/\sigma\) or AC \(\sigma\) (bid-ask bounce). Optional diagnostic column only.

### `src/exec_impact/impact.py`

- Model: \( r/\sigma = Y \cdot \mathrm{sign}(Q) \cdot (|Q|/V)^\delta \).
- Fit free \(\delta\) via log-log Huber robust regression; also fit \(Y\) with \(\delta=0.5\) fixed.
- Bootstrap 95% CI for \(\delta\) (and \(Y\)).
- Temporary vs permanent: peak impact vs price change that persists `k` intervals after flow.
- Weekly and per-symbol refits; drift table.
- OOS: fit weeks 1–2, predictive \(R^2\) on weeks 3–4.
- Public API must take an `asof` / `end_ts` so callers cannot pass future bars.

### `src/exec_impact/schedules.py`

- Parent order \(X\), horizon \(T\), \(N\) slices.
- **TWAP**: \(X/N\) each slice; holdings monotone; sum exactly \(X\).
- **VWAP**: weights from **prior 7 calendar days** same-of-day minute (or slice) volume profile; weights sum to 1.
- **Oracle VWAP**: same using *realized* volume on the execution day; labelled unattainable.
- **Almgren–Chriss** remaining holdings:
  \( x_k = X \sinh(\kappa (T-t_k)) / \sinh(\kappa T) \)
  with \(\kappa\) from \(\lambda\), \(\sigma\), temporary \(\eta\), permanent \(\gamma\).
- **Linearization of sqrt-law (locked: value-match at child-slice rate):** let \(v_{\mathrm{ref}}\) be the participation rate of one child slice implied by `ref_adv_frac`, horizon \(T\), and \(N\) (not \(X/\mathrm{ADV}\)). Set linear \(\eta\) so \(\eta |v_{\mathrm{ref}}|\) equals the power-law temporary impact at \(v_{\mathrm{ref}}\). \(v_{\mathrm{ref}}\) uses **prior** volume only. Report AC sensitivity across `ref_adv_frac_sensitivity`.
- Sweep ≥ 6 \(\lambda\) values; \(\lambda \to 0\) → TWAP; larger \(\lambda\) more front-loaded.
- **Stretch (after closed form):** scipy/cvxpy trajectory under power-law temporary impact; compare to linearized AC.

### `src/exec_impact/simulate.py`

- **(A) Tape replay:** sample ≥ 500 start times once; reuse for every strategy (paired). Arrival = last trade price strictly before start. Slice fill = tape VWAP in the slice **plus** modeled temporary impact (params fit on data **before start**) **plus** accumulated permanent impact. The historical tape is not modified by our order (stated in README).
- **(B) Synthetic:** GBM + linear impact; confirm AC maximizes mean-variance utility under those assumptions. Correctness check, not a live-performance claim.
- Grid: ADV fractions × horizons × symbols × buy/sell. ADV is trailing, as-of start, prior-only.

### `src/exec_impact/metrics.py`

- Implementation shortfall in bps, sign-adjusted so **positive = cost** for both buy and sell.
- Mean, std, p95, CVaR95 per strategy × grid cell.
- Paired Δ vs TWAP: bootstrap 95% CI + Wilcoxon p-value.
- Cost-vs-size curves; risk/cost frontier across \(\lambda\); taker-fee constant line.
- Headline table including cells where AC does **not** help.
- Write `results/metrics.json` (must include **git commit hash, full config, seed, data month**) and `results/figures/*.png`. Commit `metrics.json` and a few small key PNGs used by the README.

### Scripts / Makefile

| Target | Action |
| ------ | ------ |
| `make data` | `scripts/download_data.py` |
| `make fit` | fit impact, write intermediate params under `results/` |
| `make simulate` | replay + synthetic |
| `make report` | metrics.json + figures + numbers consumed by README |
| `make test` | `ruff` + `pytest` |

One command for README numbers: `make report` (after `make data`) with seed from `config.yaml`.

## Proposed test list (`tests/`)

Must cover SPEC §5; extras that lock no-lookahead and schema handling:

| Test | What it asserts |
| ---- | ---------------- |
| `test_schedule_sums_to_x` | TWAP, VWAP, AC, oracle: sum of child sizes == \(X\) (float tolerance) |
| `test_schedule_nonnegative` | all child sizes ≥ 0 |
| `test_holdings_monotone` | remaining inventory monotone toward 0 |
| `test_ac_lambda_zero_is_twap` | \(\lambda \to 0\) matches TWAP |
| `test_ac_larger_lambda_frontloaded` | first-slice size increases in \(\lambda\) |
| `test_vwap_weights_sum_to_one` | profile weights sum to 1 |
| `test_vwap_no_lookahead` | mutating bars **after** decision time does not change VWAP schedule |
| `test_sigma_no_lookahead` | mutating future prices does not change \(\sigma\) at \(t\) |
| `test_impact_params_no_lookahead` | mutating future flow/returns does not change \((Y,\delta)\) as-of \(t\) |
| `test_volume_profile_prior_7d_only` | day-of volume does not enter non-oracle VWAP |
| `test_parameter_recovery_y_delta` | synthetic data with known \(Y,\delta\); estimator within tolerance |
| `test_buy_sell_shortfall_sign` | buy above arrival and sell below arrival both yield **positive** IS |
| `test_aggressor_side_mapping` | `is_buyer_maker=True` → negative signed volume |
| `test_timestamp_unit_detection` | ms vs µs samples normalize to the same UTC instants |
| `test_header_vs_no_header` | both CSV layouts parse to the same frame |
| `test_checksum_mismatch_raises` | bad checksum is rejected |
| `test_oracle_vwap_labelled_unattainable` | oracle path is a distinct strategy id, not mixed into “VWAP” |
| `test_paired_starts_identical` | all strategies receive the same start-time vector |
| `test_synthetic_ac_best_utility` | under GBM+linear impact, AC λ-sweep includes the best mean-variance utility (tolerance) |
| `test_seed_stability` | same seed → identical sampled starts |

## Implementation order (after approval)

1. Skeleton: `pyproject.toml`, `config.yaml`, Makefile, `.gitignore`, CI, package init.
2. `data.py` + download script + data tests.
3. `bars.py` + bar tests (incl. trailing windows).
4. `impact.py` + recovery / no-lookahead / weekly-OOS tests.
5. `schedules.py` + schedule tests.
6. `simulate.py` tape replay, then synthetic.
7. `metrics.py` + report script + figures.
8. Stretch optimizer if time.
9. README with honest limitations; freeze numbers from `make report`.

## Explicit limitations (will appear in README)

Public tape = market-wide response to **everyone’s** flow, not our hypothetical order. Simultaneous flow and price ⇒ endogeneity. No order book, no queue position, no hidden liquidity. Our simulated order **does not alter** historical prints; impact is an additive model on top of tape VWAP. One month, crypto spot, not equities. Oracle VWAP is not a tradable strategy.

## Approved choices (2026-10-08)

1. **Month:** `2024-01`. README must note ETF-approval volatility. Second calmer month `2024-07` as robustness **after** main results.
2. **Sigma:** one consistent close-to-close 1m series (empty minutes → 0 return); 5m-sampled RV is that same 1m variance aggregated. Intra-bar vol is diagnostic only.
3. **Artifacts:** commit seed-locked `metrics.json` (hash, config, seed, month) and a few small key PNGs for the README.
4. **Stretch optimizer:** after closed-form AC + tests are green.
5. **Linearization:** value-match at **child-slice** participation implied by `ref_adv_frac`, \(T\), and \(N\); prior data only; sensitivity across several `ref_adv_frac`.
