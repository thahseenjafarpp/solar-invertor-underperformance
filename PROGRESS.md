# Project Progress Log

Earlier advanced version is saved in git tag v1-advanced.

## Practical 1: Exploring Data
- **Date/Time**: 2026-11-18
- **Scope**: Plant 1 exclusively (22 inverters).
- **Files Loaded**:
  - `data/Plant_1_Generation_Data.csv`: 68,778 rows, 7 columns (`DATE_TIME`, `PLANT_ID`, `SOURCE_KEY`, `DC_POWER`, `AC_POWER`, `DAILY_YIELD`, `TOTAL_YIELD`). Format: `%d-%m-%Y %H:%M`.
  - `data/Plant_1_Weather_Sensor_Data.csv`: 3,182 rows, 6 columns (`DATE_TIME`, `PLANT_ID`, `SOURCE_KEY`, `AMBIENT_TEMPERATURE`, `MODULE_TEMPERATURE`, `IRRADIATION`). Format: `%Y-%m-%d %H:%M:%S`.
- **Date Range**: 2020-05-15 00:00:00 to 2020-06-17 23:45:00 (34 consecutive days).

## Practical 2: Data Preprocessing
- **Date/Time**: 2026-11-18
- **Decisions**:
  - Inner join on timestamp: 68,774 rows retained (loss: 4 rows, 0.0058%).
  - Zero missing values, zero duplicate `(DATE_TIME, SOURCE_KEY)` pairs.
  - Variable types: `SOURCE_KEY` identified as categorical inverter ID and strictly excluded from regression features.
  - Daytime threshold: `IRRADIATION > 0.01` kW/m² retained 35,938 operational rows.
  - Chronological split: Early 24 days for training (25,202 rows), last 10 days held out for testing (10,736 rows).
  - Normalization: `MinMaxScaler` fitted exclusively on `train_df[feature_cols]` and applied to `test_df`.
- **Table Saved**: `results/tables/table1_data_summary.csv`.

## Practical 3: Correlation & Regression Analysis
- **Date/Time**: 2026-11-18
- **Correlations with AC_POWER**:
  - `IRRADIATION`: 0.97 (dominant positive driver)
  - `MODULE_TEMPERATURE`: 0.85
  - `AMBIENT_TEMPERATURE`: 0.70
  - `HOUR`: 0.17
- **Model Results on Test Set**:
  - Simple Linear Regression (Irradiation only): RMSE = 73.31 kW, MAE = 45.50 kW, R² = 0.9547
  - Multiple Linear Regression (Weather + Hour): RMSE = 73.72 kW, MAE = 45.99 kW, R² = 0.9542
  - Polynomial Regression (Degree 2): RMSE = 66.66 kW, MAE = 34.15 kW, R² = 0.9626
  - Statsmodels OLS Summary: R² = 0.954; irradiation coefficient positive and statistically significant (p < 0.001); module temperature coefficient negative reflecting thermal degradation.
- **Figures Saved**:
  - `results/figures/fig1_correlation_heatmap.png`
  - `results/figures/fig2_simple_linear_regression.png`
  - `results/figures/fig3_polynomial_regression.png`

## Practical 10: Model Performance and Ensemble
- **Date/Time**: 2026-11-18
- **Random Forest Regressor Results**:
  - RMSE = 69.46 kW, MAE = 35.88 kW, R² = 0.9594
- **Model Selection**: Random Forest selected as the expected-power model for residual analysis due to robust non-linear modeling without extreme edge-case polynomial extrapolation.
- **Leakage Guard**: All model R² values strictly below 0.99.
- **Figure & Table Saved**:
  - `results/figures/fig4_actual_vs_predicted.png`
  - `results/tables/table2_model_performance.csv`

## Section 5: Residual Analysis & Underperformance Ranking
- **Date/Time**: 2026-11-18
- **Sign Convention**: $\text{Residual} = \text{Actual} - \text{Expected}$. Negative residual indicates underperformance.
- **Ranking Highlights**:
  - Rank 1: `bvBOhCH3iADSZry` (`Inv_bvBO`) | Mean Residual: -60.19 kW | Low Readings (< -20 kW): 56.35%
  - Rank 2: `1BY6WEcLGh8j5v7` (`Inv_1BY6`) | Mean Residual: -54.06 kW | Low Readings (< -20 kW): 52.05%
  - Rank 3: `ih0vzX44oOqAx2f` (`Inv_ih0v`) | Mean Residual: -2.30 kW | Low Readings: 22.75%
  - Rank 22: `adLQvlD726eNBSB` (`Inv_adLQ`) | Mean Residual: +27.03 kW | Low Readings: 9.02%
- **Figures & Table Saved**:
  - `results/figures/fig5_inverter_mean_residual.png`
  - `results/figures/fig6_low_readings_percentage.png`
  - `results/tables/table3_inverter_ranking.csv`

## Practical 6: Clustering (K-Means)
- **Date/Time**: 2026-11-18
- **Inertia Elbow Values**:
  - k=1: 2.6351
  - k=2: 0.2457 (90.7% reduction)
  - k=3: 0.0915
  - k=4: 0.0483
  - k=5: 0.0324
- **Cluster Segmentation (k=3)**:
  - Low-Performance Cluster: Inverters `bvBO` and `1BY6` (Mean Residual = -57.12 kW, Low Readings = 54.20%)
  - Average Cluster: 11 inverters (Mean Residual = +6.09 kW, Low Readings = 17.08%)
  - High-Performance Cluster: 9 inverters (Mean Residual = +18.03 kW, Low Readings = 11.82%)
- **Figures & Table Saved**:
  - `results/figures/fig7_kmeans_elbow_plot.png`
  - `results/figures/fig8_kmeans_clusters.png`
  - `results/tables/table4_kmeans_clusters.csv`

## Section 7: Temporal Stability Analysis
- **Date/Time**: 2026-11-18
- **Split**: Half 1 (June 8–12) vs Half 2 (June 13–17).
- **Results**:
  - Spearman rank correlation: $\rho = 0.7832$ ($p = 1.63 \times 10^{-5}$)
  - K-Means low-group persistence: 2 of 2 inverters (`bvBO` and `1BY6`) flagged in both halves (100% persistent).
- **Table Saved**: `results/tables/table5_stability_metrics.csv`.

## Section 8: Final Verification & Integration
- **Date/Time**: 2026-11-18
- **Checks Summary**: All 5 self-checks passed without error.
- **Clean Execution**: Notebook `notebooks/solar_analysis.ipynb` executed top-to-bottom with clean kernel and preserved outputs.
