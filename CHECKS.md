# Project Verification Checks

Earlier advanced version is saved in git tag v1-advanced.

| Practical / Section | Check Description | Status | Evidence / Notes |
|---|---|---|---|
| **Practical 2: Preprocessing** | Train dates strictly earlier than test dates | **PASS** | Train max (`2020-06-07 18:15:00`) < Test min (`2020-06-08 06:15:00`) |
| **Practical 2: Preprocessing** | Feature list contains no power, yield, or ID columns | **PASS** | Feature space: `['IRRADIATION', 'MODULE_TEMPERATURE', 'AMBIENT_TEMPERATURE', 'HOUR']` |
| **Practical 2: Preprocessing** | No missing values left in model inputs | **PASS** | Scaled feature matrix verified: 0 NaN values across all 25,202 train rows |
| **Practical 10: Model Eval** | Leakage check (all model R² < 0.99) | **PASS** | Simple LR: 0.9547, Multiple LR: 0.9542, Poly: 0.9626, RF: 0.9594 (all < 0.99) |
| **Section 8: Artifacts** | All 8 figure files and 5 table files exist and non-empty | **PASS** | Verified 8 PNGs in `results/figures/` (42 KB – 155 KB) and 5 CSVs in `results/tables/` |
