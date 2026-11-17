# Solar Inverter Underperformance Identification

## Project Overview
This predictive analytics project investigates whether a weather-based expected-power model can accurately identify solar inverters that consistently underperform, and whether those underperformance flags remain stable over time.

## Research Question
Can a weather-based expected-power model identify inverters that consistently underperform, and are those flags stable over time?

## Repository Structure
- `data/`: Documentation and raw CSV placement directory (raw data ignored from git).
- `notebooks/`: Single analysis notebook and paired script (`solar_analysis.py` / `solar_analysis.ipynb`).
- `results/figures/`: Saved visualizations (maximum 8 figures).
- `results/tables/`: Model evaluation and inverter ranking tables.
- `PROGRESS.md`: Project log tracking key decisions, file schemas, date formats, and thresholds.
- `CHECKS.md`: Verification log for self-checks across all project phases.
- `requirements.txt`: Python package requirements.
- `LICENSE`: MIT License.

## Setup & Execution
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. Download the Kaggle Solar Power Generation Data and place the 4 CSV files into `data/`.
4. Run the end-to-end analysis notebook in `notebooks/`.
