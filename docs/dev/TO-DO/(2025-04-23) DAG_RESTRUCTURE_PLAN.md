# DAG Renaming & Restructure Implementation Plan

This plan converts the current *provider‑/asset‑agnostic* DAG tree into the **function‑first, provider/asset‑aware** structure recommended in `RENAMING_RESEARCH.md`.
The tasks are written as **step‑by‑step instructions** for an automation agent.  Follow them **sequentially**.

---
## ➊ High‑Level Target Layout

```
dags/
├─ ingestion/            # raw data collection workflows
├─ execution/            # order routing & trading workflows
├─ transformation/       # clean / normalize / merge data
├─ analytics/            # reporting, back‑tests, dashboards
└─ … (future domains: monitoring/, compliance/, etc.)
```

Inside each domain all DAG *files* follow:
```
{provider}_{optional‑asset}_{domain}.py
```
* `provider`  – lowercase abbreviation listed in § 3.
* `asset`     – omit if provider has one asset domain; else choose from the controlled vocabulary in § 4.
* `domain`    – omit from filename if redundant with folder (e.g. keep `binance_spot_ingestion.py`, but inside `analytics/` simply use `portfolio_report.py`).

**Examples**
```
ingestion/binance_spot_ingestion.py
execution/ibkr_execution.py
transformation/crypto_ohlcv_aggregate.py
analytics/latency_comparison.py
```

---
## ➋ Migration Workflow

1. **Inventory current DAGs**  
   ```python
   from pathlib import Path
   DAG_ROOT = Path("dags")
   dag_files = list(DAG_ROOT.rglob("*.py"))
   ```
   Extract each DAG’s `dag_id`, provider, asset class, and workflow *domain* (**ingestion/execution/transformation/analytics**).
   *Hint*: parse filename & DAG docstring; fall back to manual mapping list `MIGRATION_MANUAL_OVERRIDES` (see end of file).

2. **Create target folders** if they don’t exist (`ingestion/`, `execution/`, …).

3. **Compute new paths & names**
   ```python
   new_path = DAG_ROOT / domain / f"{provider}_{asset}_{domain}.py"  # asset empty → skip underscore
   new_dag_id = f"{provider}_{asset}_{domain}".strip("_")          # same rule
   ```

4. **Move the file** (`git mv`) and **rewrite contents**:
   * update the `dag_id` argument in the `DAG()` constructor.
   * update any internal references to the old `dag_id`.
   * ensure module imports remain valid (absolute or relative paths may change).

5. **Refactor tests & utilities** referencing
   * old file paths
   * old `dag_id`s

6. **Run `airflow dags list`** to confirm every renamed DAG is discoverable.

7. **Commit in a single merge request** labelled `dag‑refactor`.

---
## ➌ Approved Provider Abbreviations
| Provider                        | Abbrev |
|---------------------------------|--------|
| Interactive Brokers            | `ibkr` |
| Binance                        | `binance` |
| Coinbase (Advanced/Exchange)   | `coinbase` |
| Alpaca                         | `alpaca` |
| Kraken                         | `kraken` |
| TradeStation                   | `tradestation` |
| TD Ameritrade                  | `tdameritrade` |
| Gemini                         | `gemini` |
| (extend as needed)             |         |

> New provider? Add row + use lowercase identifier.

---
## ➍ Controlled Asset Vocabulary
| Asset Domain          | Token        | Notes |
|-----------------------|--------------|-------|
| Equities / Stocks     | `equities`   | Use instead of `stocks` |
| Crypto – Spot         | `spot`       | Only for exchanges where both spot & derivatives exist |
| Crypto – Perp/Futures | `futures`    | Includes perpetual swaps |
| Options               | `options`    |   |
| Futures (non‑crypto)  | `futures`    | context clarifies |
| Forex                 | `forex`      |   |
| Bonds                 | `bonds`      |   |
| (extend …)            |              | keep lowercase |

If provider supports a **single asset** across all pipelines (e.g. Alpaca crypto ingestion only) you may **omit** the asset token.

---
## ➎ DAG ID & Schedule Conventions
* `dag_id` **must equal** the filename without extension.
* Prefix external‑trigger DAGs with `trigger_` (e.g. `trigger_ibkr_execution`).
* Retain existing `schedule_interval` unless a business rule change is explicitly documented.

---
## ➏ Documentation Updates
* Add a README to each domain folder explaining purpose & naming rules.
* Update top‑level `README.md` architecture diagram.
* List any new environment variables in `INSTRUCTIONS.md`.

---
## ➐ CI/CD Adjustments
* Update DAG path glob in lint/test workflows (`python -m pytest dags/**/*.py`).
* Adjust Docker image `AIRFLOW__CORE__DAGS_FOLDER` ENV if absolute path changed.

---
## ➑ Edge‑Cases & Manual Overrides
Define a Python dict in `migration/overrides.py` if automated inference fails:
```python
MIGRATION_MANUAL_OVERRIDES = {
    "old/path/legacy_crypto_ingest.py":
        {"provider": "kraken", "asset": "spot", "domain": "ingestion"},
}
```
Automation must check this mapping *before* heuristic parsing.

---
## ➒ Post‑Migration Validation Checklist
1. `airflow dags list` equals expected renamed IDs.
2. All `airflow dags test <dag_id> <date>` runs succeed for a smoke date.
3. `pytest` suite green.
4. No import errors when starting the scheduler & webserver.

---
## ➓ Timetable (Example)
| Day | Task |
|-----|------|
| 1   | Inventory & script authoring |
| 2   | Automated rename, commit, CI pass |
| 3   | Manual overrides & test fixes |
| 4   | Prod Airflow dry‑run sandbox |
| 5   | Merge & deploy |

---

### MIGRATION_MANUAL_OVERRIDES (seed)
Add known tricky files here:
```python
# File: migration/overrides.py
MIGRATION_MANUAL_OVERRIDES = {
    # "dags/hard_to_parse.py": {"provider": "ibkr", "asset": "options", "domain": "ingestion"},
}
```

### End of Plan
