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
