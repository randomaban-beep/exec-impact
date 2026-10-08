# Agent working rules (exec-impact)

## Stack

- Python 3.11.
- Dependency management: `uv` preferred, otherwise `pip` with pinned versions.
- Linting: `ruff`.
- Tests: `pytest`.
- Type hints on public functions and module-level APIs.

## Git

- Commit after each completed module with conventional messages (`feat:`, `test:`, `docs:`).
- Run tests before every commit.
- Never commit data files, caches, or secrets (`data/`, parquet, zips, `.env`, checksum caches).

## Research integrity

- Never use future information in any estimate (no lookahead). Every estimator
  (`sigma`, volume profile, impact params) uses data strictly before the decision time.
- Fix random seeds. Every number in the README must be reproducible with one command.
- Be honest: if a result is weak or an assumption is violated, say so in the README.

## Session continuity

- Update `PROGRESS.md` at the end of each stage so a fresh session can resume.
