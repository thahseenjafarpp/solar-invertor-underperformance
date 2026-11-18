# Project Verification Checks

| Phase | Check Description | Status | Evidence / Notes |
|---|---|---|---|
| Phase 0 | All required files/folders exist | PASS | `.gitignore`, `LICENSE`, `requirements.txt`, `README.md`, `PROGRESS.md`, `CHECKS.md`, `data/README.md`, `notebooks/`, `results/figures/`, `results/tables/` verified |
| Phase 0 | Git status shows no data file staged | PASS | `git status` verifies raw data files in `data/` remain untracked and unstaged |
| Phase 0 | Initial git commit and first push | PASS | Initial commit b1f0f50 pushed successfully to origin/main; no data files tracked |
| Phase 1 | Timestamps parsed correctly in every file | PASS | Format `%d-%m-%Y %H:%M` for P1 Gen, `%Y-%m-%d %H:%M:%S` for P1 Wtr and P2 files parsed without error |
| Phase 1 | Merge row loss reported and under 5% | PASS | Plant 1 loss: 0.0058% (4 rows); Plant 2 loss: 0.0000% (0 rows) |
| Phase 1 | No duplicate (timestamp, inverter) pairs | PASS | 0 duplicate pairs found in Plant 1 and Plant 2 generation datasets |
| Phase 1 | Irradiation never negative | PASS | Verified min irradiation is 0.0 in both weather datasets |
| Phase 2 | Power near zero when irradiation near zero | PASS | Mean AC power <= 0.22 kW when irradiation <= 0.01 kW/m² (>99% zero) |
| Phase 2 | Every figure file saved and non-empty | PASS | `fig1` (300 KB), `fig2` (438 KB), `fig3` (97 KB), `fig4` (109 KB) saved and verified |
| Phase 3 | Assert max(train timestamp) < min(test timestamp) | PASS | Max train (2020-06-07 18:15:00) < Min test (2020-06-08 06:15:00) strictly asserted |
| Phase 3 | Assert feature list contains no power or yield columns | PASS | Features: `['IRRADIATION', 'MODULE_TEMPERATURE', 'AMBIENT_TEMPERATURE', 'TIME_DECIMAL', 'IRRADIATION_SQ']` |
| Phase 3 | Investigate if R² > 0.99 for data leakage | PASS | Ridge R² = 0.9619, RF R² = 0.9596 (both < 0.99, no target leakage detected) |
| Phase 3 | Both models compared on identical test set | PASS | Evaluated on 10,736 test rows (Ridge RMSE 67.27 kW vs RF RMSE 69.24 kW; Table 2 saved) |
| Phase 4 | Residual sign convention stated in markdown cell | PASS | Explicitly defined: $Residual = Actual - Expected$ ($<0$ indicates underperformance) |
| Phase 4 | Ranking table saved | PASS | `results/tables/table3_inverter_ranking.csv` generated with 22 inverters |
| Phase 4 | Each inverter has enough test rows (report count) | PASS | Exactly 488 daytime test readings for all 22 inverters (exceeds 200 requirement) |
| Phase 5 | Report overlap of flagged sets between halves & across thresholds | PASS | Documented in Table 4: at < -20 kW cutoff, 2 of 2 inverters persist across both halves (Jaccard = 1.0) |
| Phase 5 | Random seeds set | PASS | Set `random_state=42` across train/test splits, RF regressor, and bootstrap sampler |
| Phase 5 | State flag stability plainly without selective tuning | PASS | Severe underperformers (`bvBO`, `1BY6`) are highly stable (Spearman $\rho = 0.7832$, $p < 0.001$); marginal flags vary with weather |
| Phase 6 | Notebook executes without error from fresh kernel | PASS | `notebooks/solar_analysis.ipynb` executed top-to-bottom via `nbconvert` with 17 output objects |
| Phase 6 | Every number in README appears in notebook or tables | PASS | Metrics cross-checked directly against `table1`–`table4` |
| Phase 6 | Requirements installs cleanly from scratch | PASS | `requirements.txt` contains verified packages (`pandas`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn`, `jupytext`, `nbconvert`, `ipykernel`) |
| Phase 6 | Git push succeeded and repo contains no raw data | PASS | Verified `data/*.csv` ignored by `.gitignore` and remote push verified |
