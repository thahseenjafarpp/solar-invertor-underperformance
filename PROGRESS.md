# Project Progress Log

## Phase 0: Repository Scaffolding and Setup
- **Date/Time**: 2026-11-18
- **Decisions**:
  - Initialized repository structure following specified guidelines.
  - Configured `.gitignore` to prevent any CSV raw data in `data/` from being tracked or staged while permitting generated CSV tables in `results/tables/`.
  - Created placeholder directories: `notebooks/`, `results/figures/`, `results/tables/`.
  - Added MIT License, `requirements.txt`, `data/README.md`, `CHECKS.md`.
- **Files Created**:
  - `.gitignore`, `LICENSE`, `requirements.txt`, `README.md`, `PROGRESS.md`, `CHECKS.md`, `data/README.md`
  - `.gitkeep` files in `results/figures/`, `results/tables/`, `notebooks/`

## Phase 1: Data Loading, Cleaning, and Merging
- **Date/Time**: 2026-11-18
- **Files & Column Schemas**:
  - `data/Plant_1_Generation_Data.csv`: 68,778 rows, 7 columns (`DATE_TIME`, `PLANT_ID`, `SOURCE_KEY`, `DC_POWER`, `AC_POWER`, `DAILY_YIELD`, `TOTAL_YIELD`). Timestamp format: `%d-%m-%Y %H:%M`.
  - `data/Plant_1_Weather_Sensor_Data.csv`: 3,182 rows, 6 columns (`DATE_TIME`, `PLANT_ID`, `SOURCE_KEY`, `AMBIENT_TEMPERATURE`, `MODULE_TEMPERATURE`, `IRRADIATION`). Timestamp format: `%Y-%m-%d %H:%M:%S`.
  - `data/Plant_2_Generation_Data.csv`: 67,698 rows, same 7 columns. Timestamp format: `%Y-%m-%d %H:%M:%S`.
  - `data/Plant_2_Weather_Sensor_Data.csv`: 3,259 rows, same 6 columns. Timestamp format: `%Y-%m-%d %H:%M:%S`.
- **Integrity Findings**:
  - Duplicate `(DATE_TIME, SOURCE_KEY)` pairs in generation: 0 for Plant 1, 0 for Plant 2.
  - Duplicate `DATE_TIME` in weather: 0 for Plant 1, 0 for Plant 2.
  - Negative irradiation values: 0 (min irradiation is exactly 0.0 in both plants).
  - Missing/null values in merged datasets: 0.
- **Merge Results**:
  - Plant 1 inner merge: 68,774 rows (loss of 4 rows, 0.0058%, well under 5%).
  - Plant 2 inner merge: 67,698 rows (loss of 0 rows, 0.0000%).
- **Key Table Generated**: `results/tables/table1_data_summary.csv`.

## Phase 2: Exploratory Data Analysis (EDA)
- **Date/Time**: 2026-11-18
- **Daytime Threshold Justification**:
  - Chosen threshold: `IRRADIATION > 0.01` kW/m².
  - Justification: Readings with `IRRADIATION <= 0.01` represent night hours or pre-dawn sensor noise. Mean AC power under this threshold is 0.2175 kW (Plant 1) and 0.1817 kW (Plant 2), where >99% of readings are exactly 0.0 kW. Retaining nighttime rows would heavily skew regression baselines towards zero.
- **Key EDA Observations**:
  - AC power exhibits a strong linear-to-saturating relationship with solar irradiation.
  - Cell module temperatures rise up to ~65°C during peak midday hours (11:00 - 14:00), leading to thermal efficiency de-rating.
  - Noticeable performance variance exists between the 22 inverters under identical ambient conditions, establishing the basis for an expected-power residual model.
- **Figures Saved**:
  - `results/figures/fig1_power_vs_irradiation.png` (299,935 bytes)
  - `results/figures/fig2_power_vs_module_temp.png` (438,184 bytes)
  - `results/figures/fig3_daily_diurnal_profiles.png` (96,905 bytes)
  - `results/figures/fig4_inverter_mean_daily_yield.png` (109,159 bytes)

## Phase 3: Expected-Power Modeling
- **Date/Time**: 2026-11-18
- **Decisions**:
  - **Plant Selection**: Plant 1 was used exclusively for expected-power modeling, inverter ranking, and stability analysis. (Plant 2 was cleaned and compared during Phase 1 and 2 EDA, but features different unit conventions and scaling).
  - **Pooled Inverter Training**: The expected-power model was trained on all 22 inverters pooled together across Plant 1 to learn the plant-wide baseline.
  - Target variable: `AC_POWER` (inverter AC power output in kW).
  - Feature set: `['IRRADIATION', 'MODULE_TEMPERATURE', 'AMBIENT_TEMPERATURE', 'TIME_DECIMAL', 'IRRADIATION_SQ']`.
  - Leakage Guard: Verified features contain zero power, current, or yield columns.
  - Temporal Split: Early 24 days for training (2020-05-15 06:15:00 to 2020-06-07 18:15:00, 25,202 rows); last 10 days held out for testing (2020-06-08 06:15:00 to 2020-06-17 18:15:00, 10,736 rows).
  - Assertion passed: `max(train timestamp) < min(test timestamp)`.
- **Model Comparison on Held-Out Test Set**:
  - Model 1 (Ridge Linear Regression, alpha=1.0): RMSE = 67.27 kW, MAE = 36.37 kW, R² = 0.9619.
  - Model 2 (Random Forest Regressor, n_estimators=100, max_depth=12, seed=42): RMSE = 69.24 kW, MAE = 35.25 kW, R² = 0.9596.
  - Both R² values strictly below 0.99; confirmed realistic physical variance and absence of target leakage.
- **Key Artifacts**:
  - Table: `results/tables/table2_model_performance.csv`
  - Figure: `results/figures/fig5_model_actual_vs_predicted.png` (306,279 bytes)

## Phase 4: Per-Inverter Residual Analysis and Ranking
- **Date/Time**: 2026-11-18
- **Residual Sign Convention & Deficit Calculation**:
  - $\text{Residual} = \text{AC\_POWER}_{\text{actual}} - \text{AC\_POWER}_{\text{expected}}$
  - $\text{Residual} < 0$ implies underperformance (inverter produced less AC power than expected for prevailing weather).
  - **Total Lost Energy Calculation**: $\sum_{i} \max(0, -\text{Residual}_i) \times 0.25\text{ hours}$ (kWh). Positive residuals are clipped to 0 so outperforming intervals do not offset deficits; 15-minute readings are multiplied by $0.25\text{ hr}$ to yield energy in kilowatt-hours (kWh).
- **Test Sample Size per Inverter**:
  - Exactly 488 daytime test observations for each of the 22 inverters (minimum required threshold was 200).
- **Underperformance Ranking Key Numbers**:
  - Rank 1 (Worst Underperformer): `bvBOhCH3iADSZry` (`Inv_01 (bvBO)`) | Mean Residual: -60.83 kW | Median Residual: -25.24 kW | Underperformance Rate (< -20 kW): 55.53% | Total Deficit: 7,911.72 kWh
  - Rank 2: `1BY6WEcLGh8j5v7` (`Inv_02 (1BY6)`) | Mean Residual: -54.70 kW | Median Residual: -19.10 kW | Underperformance Rate (< -20 kW): 48.98% | Total Deficit: 7,396.23 kWh
  - Rank 3: `ih0vzX44oOqAx2f` (`Inv_03 (ih0v)`) | Mean Residual: -2.94 kW | Median Residual: -1.71 kW | Underperformance Rate (< -20 kW): 21.93% | Total Deficit: 1,797.16 kWh
  - Top Performer (Rank 22): `adLQvlD726eNBSB` (`Inv_22 (adLQ)`) | Mean Residual: +26.39 kW
- **Key Artifacts**:
  - Table: `results/tables/table3_inverter_ranking.csv`
  - Figures:
    - `results/figures/fig6_residual_distribution_per_inverter.png` (137,877 bytes)
    - `results/figures/fig7_underperformance_ranking.png` (103,830 bytes)

## Phase 5: Stability and Robustness Checks
- **Date/Time**: 2026-11-18
- **Chronological Split**:
  - Half 1: 2020-06-08 to 2020-06-12 (5,390 rows)
  - Half 2: 2020-06-13 to 2020-06-17 (5,346 rows)
- **Statistical Stability Metrics**:
  - Spearman rank correlation ($\rho$): 0.7832 ($p = 1.63 \times 10^{-5}$)
  - Pearson residual correlation ($r$): 0.9399 ($p = 8.66 \times 10^{-11}$)
  - 500-iteration bootstrap analysis confirms severe underperformance ranks for `bvBO` and `1BY6` are rock solid across resampled days.
- **Flag Overlap Across Thresholds**:
  - Mean Residual < -20 kW: Half 1 = 2, Half 2 = 2, Persistent Overlap = 2, Jaccard = 1.0000 (100% persistent)
  - Mean Residual < -15 kW: Half 1 = 2, Half 2 = 2, Persistent Overlap = 2, Jaccard = 1.0000
  - Mean Residual < -10 kW: Half 1 = 3, Half 2 = 2, Persistent Overlap = 2, Jaccard = 0.6667
  - Bottom 3 Inverters: Half 1 = 3, Half 2 = 3, Persistent Overlap = 2, Jaccard = 0.5000
  - Bottom 5 Inverters: Half 1 = 5, Half 2 = 5, Persistent Overlap = 3, Jaccard = 0.4286
- **Stability Conclusion**:
  - Severe underperformance flags (inverters with >15 kW average deficit) are **highly stable** across time and operational conditions. Marginal/mild underperformance flags show moderate fluctuation due to variable cloud cover.
- **Key Artifacts**:
  - Table: `results/tables/table4_stability_metrics.csv`
  - Figure: `results/figures/fig8_stability_half1_vs_half2.png` (99,517 bytes)

## Phase 6: Final Integration and Execution Verification
- **Date/Time**: 2026-11-18
- **Execution**:
  - Notebook `notebooks/solar_analysis.ipynb` executed top-to-bottom without error via `nbconvert`.
  - All 16 code cells executed successfully; all markdown explanations and 17 output displays captured.
  - Total of 8 figures (all non-empty) saved in `results/figures/` and 4 tables in `results/tables/`.
  - README updated with comprehensive method, key metrics, figures, run instructions, and operational limitations.
