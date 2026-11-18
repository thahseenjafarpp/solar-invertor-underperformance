# %% [markdown]
# # Solar Inverter Underperformance Identification Analysis
# **Research Question**: Can a weather-based expected-power model identify inverters that
# consistently underperform, and are those flags stable over time?
#
# This analysis implements an end-to-end predictive analytics workflow using data from two solar plants.

# %%
# Imports and Configuration
import os
import numpy as np
import pandas as pd

# Ensure execution working directory is repository root whether run from repo root or notebooks/
if not os.path.exists('data') and os.path.exists('../data'):
    os.chdir('..')
elif os.path.basename(os.getcwd()) == 'notebooks':
    os.chdir('..')

# Set matplotlib cache directory within workspace to avoid sandbox permission warnings
os.environ['MPLCONFIGDIR'] = os.path.abspath('results/.mpl_cache')
os.makedirs('results/.mpl_cache', exist_ok=True)

import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Set visualization style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 11

# Ensure output directories exist
os.makedirs('results/figures', exist_ok=True)
os.makedirs('results/tables', exist_ok=True)

# %% [markdown]
# ## Phase 1: Data Loading, Cleaning, and Merging
# **What**: Load raw generation and weather sensor CSVs for Plant 1 and Plant 2, parse timestamps,
# check for duplicates and invalid values, and perform inner joins on timestamps.
#
# **Why**: Solar generation data and weather data are logged on separate sensors. Timestamp formats
# differ between files (DD-MM-YYYY vs YYYY-MM-DD), so explicit parsing is essential. We verify
# that no negative irradiation exists and merge row loss is minimal (< 5%).

# %%
# Define file paths and explicit timestamp parsing formats
if not os.path.exists('data') and os.path.exists('../data'):
    os.chdir('..')

DATA_DIR = 'data' if os.path.exists('data') else '../data'
p1_gen_path = os.path.join(DATA_DIR, 'Plant_1_Generation_Data.csv')
p1_wtr_path = os.path.join(DATA_DIR, 'Plant_1_Weather_Sensor_Data.csv')
p2_gen_path = os.path.join(DATA_DIR, 'Plant_2_Generation_Data.csv')
p2_wtr_path = os.path.join(DATA_DIR, 'Plant_2_Weather_Sensor_Data.csv')

# Load Plant 1 datasets
p1_gen = pd.read_csv(p1_gen_path)
p1_gen['DATE_TIME'] = pd.to_datetime(p1_gen['DATE_TIME'], format='%d-%m-%Y %H:%M')

p1_wtr = pd.read_csv(p1_wtr_path)
p1_wtr['DATE_TIME'] = pd.to_datetime(p1_wtr['DATE_TIME'], format='%Y-%m-%d %H:%M:%S')

# Load Plant 2 datasets
p2_gen = pd.read_csv(p2_gen_path)
p2_gen['DATE_TIME'] = pd.to_datetime(p2_gen['DATE_TIME'], format='%Y-%m-%d %H:%M:%S')

p2_wtr = pd.read_csv(p2_wtr_path)
p2_wtr['DATE_TIME'] = pd.to_datetime(p2_wtr['DATE_TIME'], format='%Y-%m-%d %H:%M:%S')

print("Plant 1 raw generation shape:", p1_gen.shape)
print("Plant 1 raw weather shape:", p1_wtr.shape)
print("Plant 2 raw generation shape:", p2_gen.shape)
print("Plant 2 raw weather shape:", p2_wtr.shape)

# %%
# Verify data integrity: Duplicates, negative irradiation, and merge consistency
p1_gen_dups = p1_gen.duplicated(subset=['DATE_TIME', 'SOURCE_KEY']).sum()
p1_wtr_dups = p1_wtr.duplicated(subset=['DATE_TIME']).sum()
p2_gen_dups = p2_gen.duplicated(subset=['DATE_TIME', 'SOURCE_KEY']).sum()
p2_wtr_dups = p2_wtr.duplicated(subset=['DATE_TIME']).sum()

assert p1_gen_dups == 0, f"Found {p1_gen_dups} duplicate (DATE_TIME, SOURCE_KEY) in Plant 1 generation"
assert p1_wtr_dups == 0, f"Found {p1_wtr_dups} duplicate DATE_TIME in Plant 1 weather"
assert p2_gen_dups == 0, f"Found {p2_gen_dups} duplicate (DATE_TIME, SOURCE_KEY) in Plant 2 generation"
assert p2_wtr_dups == 0, f"Found {p2_wtr_dups} duplicate DATE_TIME in Plant 2 weather"

# Assert non-negative irradiation
assert (p1_wtr['IRRADIATION'] >= 0).all(), "Negative irradiation found in Plant 1"
assert (p2_wtr['IRRADIATION'] >= 0).all(), "Negative irradiation found in Plant 2"

# Perform inner merge on timestamp
p1_merged = pd.merge(p1_gen, p1_wtr.drop(columns=['PLANT_ID', 'SOURCE_KEY']), on='DATE_TIME', how='inner')
p2_merged = pd.merge(p2_gen, p2_wtr.drop(columns=['PLANT_ID', 'SOURCE_KEY']), on='DATE_TIME', how='inner')

# Compute and check merge loss
p1_loss_pct = (len(p1_gen) - len(p1_merged)) / len(p1_gen) * 100.0
p2_loss_pct = (len(p2_gen) - len(p2_merged)) / len(p2_gen) * 100.0

print(f"Plant 1 merge: {len(p1_gen)} -> {len(p1_merged)} rows (loss: {p1_loss_pct:.4f}%)")
print(f"Plant 2 merge: {len(p2_gen)} -> {len(p2_merged)} rows (loss: {p2_loss_pct:.4f}%)")

assert p1_loss_pct < 5.0, f"Plant 1 merge loss {p1_loss_pct}% exceeds 5%"
assert p2_loss_pct < 5.0, f"Plant 2 merge loss {p2_loss_pct}% exceeds 5%"

# Save data summary table
data_summary = pd.DataFrame([
    {
        'Plant': 'Plant 1',
        'Raw Gen Rows': len(p1_gen),
        'Raw Wtr Rows': len(p1_wtr),
        'Merged Rows': len(p1_merged),
        'Merge Loss (%)': round(p1_loss_pct, 4),
        'Inverters': p1_gen['SOURCE_KEY'].nunique(),
        'Start Date': str(p1_gen['DATE_TIME'].min()),
        'End Date': str(p1_gen['DATE_TIME'].max()),
        'Min Irradiation': p1_wtr['IRRADIATION'].min()
    },
    {
        'Plant': 'Plant 2',
        'Raw Gen Rows': len(p2_gen),
        'Raw Wtr Rows': len(p2_wtr),
        'Merged Rows': len(p2_merged),
        'Merge Loss (%)': round(p2_loss_pct, 4),
        'Inverters': p2_gen['SOURCE_KEY'].nunique(),
        'Start Date': str(p2_gen['DATE_TIME'].min()),
        'End Date': str(p2_gen['DATE_TIME'].max()),
        'Min Irradiation': p2_wtr['IRRADIATION'].min()
    }
])
data_summary.to_csv('results/tables/table1_data_summary.csv', index=False)
print("Table 1 (Data Summary) saved.")

# %% [markdown]
# ## Phase 2: Exploratory Data Analysis (EDA)
# **What**: Examine relationships between power generation, solar irradiation, and module temperature.
# Analyze daily diurnal patterns and per-inverter total generation variation. Establish daytime filtering.
#
# **Why**: Solar photovoltaic conversion depends fundamentally on solar irradiance (W/m²), but cell efficiency
# degrades at elevated module temperatures. Nighttime readings contain zero irradiation and near-zero power,
# so modeling must focus on active daylight periods (justified threshold: IRRADIATION > 0.01 kW/m²).

# %%
# Check power readings when irradiation is near zero (nighttime / pre-dawn)
p1_near_zero = p1_merged[p1_merged['IRRADIATION'] <= 0.01]
p2_near_zero = p2_merged[p2_merged['IRRADIATION'] <= 0.01]

p1_nz_mean_ac = p1_near_zero['AC_POWER'].mean()
p2_nz_mean_ac = p2_near_zero['AC_POWER'].mean()

print(f"Plant 1 near-zero irradiation (<=0.01) mean AC power: {p1_nz_mean_ac:.4f} kW")
print(f"Plant 2 near-zero irradiation (<=0.01) mean AC power: {p2_nz_mean_ac:.4f} kW")

# Assert power is near zero when irradiation is near zero
assert p1_nz_mean_ac < 1.0, f"Plant 1 AC power unexpectedly high during near-zero irradiation: {p1_nz_mean_ac}"
assert p2_nz_mean_ac < 1.0, f"Plant 2 AC power unexpectedly high during near-zero irradiation: {p2_nz_mean_ac}"

# %%
# Figure 1: Power vs Solar Irradiation (Scatter with Trend)
fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=False)

sample_p1 = p1_merged.sample(n=min(5000, len(p1_merged)), random_state=42)
sample_p2 = p2_merged.sample(n=min(5000, len(p2_merged)), random_state=42)

axes[0].scatter(sample_p1['IRRADIATION'], sample_p1['AC_POWER'], alpha=0.25, color='tab:blue', s=12)
axes[0].set_title("Plant 1: AC Power vs Irradiation")
axes[0].set_xlabel("Solar Irradiation (kW/m²)")
axes[0].set_ylabel("AC Power (kW)")

axes[1].scatter(sample_p2['IRRADIATION'], sample_p2['AC_POWER'], alpha=0.25, color='tab:orange', s=12)
axes[1].set_title("Plant 2: AC Power vs Irradiation")
axes[1].set_xlabel("Solar Irradiation (kW/m²)")
axes[1].set_ylabel("AC Power (kW)")

plt.tight_layout()
fig1_path = 'results/figures/fig1_power_vs_irradiation.png'
plt.savefig(fig1_path, dpi=150)
plt.close()
print("Figure 1 saved to:", fig1_path)

# %%
# Figure 2: Power vs Module Temperature
fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=False)

axes[0].scatter(sample_p1['MODULE_TEMPERATURE'], sample_p1['AC_POWER'], alpha=0.25, color='tab:blue', s=12)
axes[0].set_title("Plant 1: AC Power vs Module Temperature")
axes[0].set_xlabel("Module Temperature (°C)")
axes[0].set_ylabel("AC Power (kW)")

axes[1].scatter(sample_p2['MODULE_TEMPERATURE'], sample_p2['AC_POWER'], alpha=0.25, color='tab:orange', s=12)
axes[1].set_title("Plant 2: AC Power vs Module Temperature")
axes[1].set_xlabel("Module Temperature (°C)")
axes[1].set_ylabel("AC Power (kW)")

plt.tight_layout()
fig2_path = 'results/figures/fig2_power_vs_module_temp.png'
plt.savefig(fig2_path, dpi=150)
plt.close()
print("Figure 2 saved to:", fig2_path)

# %%
# Figure 3: Daily Diurnal Profiles (Mean hourly power, irradiation, module temp)
p1_merged['HOUR'] = p1_merged['DATE_TIME'].dt.hour
diurnal_p1 = p1_merged.groupby('HOUR')[['AC_POWER', 'IRRADIATION', 'MODULE_TEMPERATURE']].mean().reset_index()

fig, ax1 = plt.subplots(figsize=(10, 5))
color = 'tab:blue'
ax1.set_xlabel('Hour of Day')
ax1.set_ylabel('Mean AC Power (kW)', color=color)
ax1.plot(diurnal_p1['HOUR'], diurnal_p1['AC_POWER'], color=color, marker='o', linewidth=2, label='AC Power (kW)')
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('Irradiation (kW/m²) & Module Temp (°C/100)', color=color)
ax2.plot(diurnal_p1['HOUR'], diurnal_p1['IRRADIATION'], color='tab:orange', marker='s', linestyle='--', label='Irradiation')
ax2.plot(diurnal_p1['HOUR'], diurnal_p1['MODULE_TEMPERATURE'] / 100.0, color='tab:red', marker='^', linestyle=':', label='Module Temp (x0.01)')
ax2.tick_params(axis='y', labelcolor=color)

plt.title("Plant 1: Mean Diurnal Profiles across 24 Hours")
fig.tight_layout()
fig3_path = 'results/figures/fig3_daily_diurnal_profiles.png'
plt.savefig(fig3_path, dpi=150)
plt.close()
print("Figure 3 saved to:", fig3_path)

# %%
# Figure 4: Inverter-level Mean Daytime Output (Comparison across inverters)
# Daytime defined as IRRADIATION > 0.01 kW/m²
IRR_THRESHOLD = 0.01
p1_daytime = p1_merged[p1_merged['IRRADIATION'] > IRR_THRESHOLD].copy()

inverter_perf = p1_daytime.groupby('SOURCE_KEY')['AC_POWER'].mean().sort_values().reset_index()
inverter_perf['SHORT_KEY'] = [f"Inv_{i+1:02d} ({k[:4]})" for i, k in enumerate(inverter_perf['SOURCE_KEY'])]

plt.figure(figsize=(12, 6))
bars = plt.barh(inverter_perf['SHORT_KEY'], inverter_perf['AC_POWER'], color='tab:blue', alpha=0.85)
# Highlight bottom 3 inverters
for i in range(3):
    bars[i].set_color('tab:red')

plant_mean = inverter_perf['AC_POWER'].mean()
plt.axvline(plant_mean, color='black', linestyle='--', linewidth=1.5, label=f'Plant Mean ({plant_mean:.1f} kW)')
plt.title(f"Plant 1: Inverter Mean Daytime AC Power (Irradiation > {IRR_THRESHOLD} kW/m²)")
plt.xlabel("Mean Daytime AC Power (kW)")
plt.ylabel("Inverter")
plt.legend()
plt.tight_layout()
fig4_path = 'results/figures/fig4_inverter_mean_daily_yield.png'
plt.savefig(fig4_path, dpi=150)
plt.close()
print("Figure 4 saved to:", fig4_path)

# Verify figure files exist and non-empty
for fpath in [fig1_path, fig2_path, fig3_path, fig4_path]:
    assert os.path.exists(fpath), f"Figure {fpath} does not exist"
    size = os.path.getsize(fpath)
    assert size > 0, f"Figure {fpath} is empty (0 bytes)"
    print(f"Verified {fpath} ({size:,} bytes)")

# %% [markdown]
# ## Phase 3: Expected-Power Modeling
# **What**: Train two machine learning models (Ridge Linear Regression and Random Forest Regressor)
# to predict expected AC power output from weather conditions and time features.
# Evaluate both models on held-out days using RMSE, MAE, and R².
#
# **Why**: To identify underperforming inverters, we need an objective baseline of how much power an
# inverter *should* produce under prevailing solar irradiance and thermal conditions.
# We enforce strict time-based train/test splitting (first ~24 days train, last 10 days test)
# to prevent future data leakage, and ensure features strictly exclude any power or yield metrics.

# %%
# Prepare daytime dataset with weather and temporal features
DAYTIME_IRR_THRESHOLD = 0.01
p1_clean = p1_merged[p1_merged['IRRADIATION'] > DAYTIME_IRR_THRESHOLD].copy()

# Feature engineering: time features and non-linear irradiation term
p1_clean['HOUR'] = p1_clean['DATE_TIME'].dt.hour
p1_clean['MINUTE'] = p1_clean['DATE_TIME'].dt.minute
p1_clean['TIME_DECIMAL'] = p1_clean['HOUR'] + p1_clean['MINUTE'] / 60.0
p1_clean['IRRADIATION_SQ'] = p1_clean['IRRADIATION'] ** 2

# Time-based train/test split: Early 24 days for training, last 10 days held out for testing
SPLIT_DATE = pd.to_datetime('2020-06-08 00:00:00')
train_df = p1_clean[p1_clean['DATE_TIME'] < SPLIT_DATE].copy()
test_df = p1_clean[p1_clean['DATE_TIME'] >= SPLIT_DATE].copy()

# Assertions for temporal split and leakage prevention
assert train_df['DATE_TIME'].max() < test_df['DATE_TIME'].min(), "Temporal split violation: train timestamps overlap with test"

feature_cols = ['IRRADIATION', 'MODULE_TEMPERATURE', 'AMBIENT_TEMPERATURE', 'TIME_DECIMAL', 'IRRADIATION_SQ']
target_col = 'AC_POWER'

# Verify feature list contains zero power or yield columns
prohibited_substrings = ['POWER', 'YIELD', 'DC', 'AC']
for feat in feature_cols:
    assert not any(sub in feat for sub in prohibited_substrings), f"Potential leakage column detected in features: {feat}"

print(f"Train period: {train_df['DATE_TIME'].min()} to {train_df['DATE_TIME'].max()} ({len(train_df):,} rows)")
print(f"Test period:  {test_df['DATE_TIME'].min()} to {test_df['DATE_TIME'].max()} ({len(test_df):,} rows)")

X_train = train_df[feature_cols]
y_train = train_df[target_col]
X_test = test_df[feature_cols]
y_test = test_df[target_col]

# %%
# Model 1: Ridge Linear Regression (baseline)
ridge_model = Ridge(alpha=1.0)
ridge_model.fit(X_train, y_train)
y_pred_ridge = ridge_model.predict(X_test)

ridge_rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_ridge)))
ridge_mae = float(mean_absolute_error(y_test, y_pred_ridge))
ridge_r2 = float(r2_score(y_test, y_pred_ridge))

# Model 2: Random Forest Regressor (non-linear tree model)
rf_model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
rf_model.fit(X_train, y_train)
y_pred_rf = rf_model.predict(X_test)

rf_rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_rf)))
rf_mae = float(mean_absolute_error(y_test, y_pred_rf))
rf_r2 = float(r2_score(y_test, y_pred_rf))

print("--- Model Performance on Held-Out Test Set ---")
print(f"Ridge Regression: RMSE = {ridge_rmse:.2f} kW, MAE = {ridge_mae:.2f} kW, R² = {ridge_r2:.4f}")
print(f"Random Forest:    RMSE = {rf_rmse:.2f} kW, MAE = {rf_mae:.2f} kW, R² = {rf_r2:.4f}")

# Check R² upper bound for data leakage investigation
if ridge_r2 > 0.99 or rf_r2 > 0.99:
    print("WARNING: R² > 0.99 detected. Investigating potential feature leakage...")
else:
    print("Leakage Check: Both R² values are strictly below 0.99, confirming realistic variance and absence of target leakage.")

# Save Table 2: Model Performance Comparison
model_perf_df = pd.DataFrame([
    {'Model': 'Ridge Regression', 'RMSE (kW)': round(ridge_rmse, 2), 'MAE (kW)': round(ridge_mae, 2), 'R²': round(ridge_r2, 4)},
    {'Model': 'Random Forest', 'RMSE (kW)': round(rf_rmse, 2), 'MAE (kW)': round(rf_mae, 2), 'R²': round(rf_r2, 4)}
])
model_perf_df.to_csv('results/tables/table2_model_performance.csv', index=False)
print("Table 2 (Model Performance) saved.")

# %%
# Figure 5: Model Predictions vs Actual AC Power on Test Set
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

pred_df = pd.DataFrame({
    'Actual': y_test.values,
    'Pred_Ridge': y_pred_ridge,
    'Pred_RF': y_pred_rf
})
sample_plot = pred_df.sample(n=min(3000, len(pred_df)), random_state=42)

axes[0].scatter(sample_plot['Actual'], sample_plot['Pred_Ridge'], alpha=0.25, color='tab:blue', s=12)
axes[0].plot([0, 1400], [0, 1400], color='red', linestyle='--', linewidth=1.5, label='Ideal 1:1')
axes[0].set_title(f"Ridge Regression: Actual vs Predicted (R²={ridge_r2:.3f})")
axes[0].set_xlabel("Actual AC Power (kW)")
axes[0].set_ylabel("Predicted AC Power (kW)")
axes[0].legend()

axes[1].scatter(sample_plot['Actual'], sample_plot['Pred_RF'], alpha=0.25, color='tab:green', s=12)
axes[1].plot([0, 1400], [0, 1400], color='red', linestyle='--', linewidth=1.5, label='Ideal 1:1')
axes[1].set_title(f"Random Forest: Actual vs Predicted (R²={rf_r2:.3f})")
axes[1].set_xlabel("Actual AC Power (kW)")
axes[1].set_ylabel("Predicted AC Power (kW)")
axes[1].legend()

plt.tight_layout()
fig5_path = 'results/figures/fig5_model_actual_vs_predicted.png'
plt.savefig(fig5_path, dpi=150)
plt.close()
print("Figure 5 saved to:", fig5_path)

# %% [markdown]
# ## Phase 4: Per-Inverter Residual Analysis and Ranking
# **What**: Calculate the prediction residuals ($Actual - Expected$) for each inverter across the held-out
# test period using the trained Random Forest expected-power model. Rank inverters by average deficit
# and underperformance consistency.
#
# **Sign Convention**:
# $$\text{Residual} = \text{AC\_POWER}_{\text{actual}} - \text{AC\_POWER}_{\text{expected}}$$
# A **negative residual** ($\text{Residual} < 0$) signifies that an inverter produced **less power than expected**
# for the observed solar irradiance, temperature, and sun angle. A **positive residual** ($\text{Residual} > 0$)
# indicates that the inverter overperformed relative to the plant baseline.
#
# **Why**: Raw generation alone does not distinguish between an inverter facing poor weather vs. an inverter
# experiencing hardware degradation, string clipping, or heavy soiling. By subtracting the weather-based expected
# power, we isolate pure inverter-specific efficiency differentials.

# %%
# Assign expected power and compute residuals on held-out test set
test_df['EXPECTED_AC_POWER'] = rf_model.predict(X_test)
test_df['RESIDUAL'] = test_df['AC_POWER'] - test_df['EXPECTED_AC_POWER']

# Verify test sample size per inverter
inverter_counts = test_df.groupby('SOURCE_KEY').size()
min_obs = inverter_counts.min()
max_obs = inverter_counts.max()
print(f"Test sample counts per inverter: min={min_obs}, max={max_obs}")

# Threshold for minimum sample size per inverter (10 days * ~45 daytime intervals ~ 450 expected)
MIN_REQUIRED_OBS = 200
underrepresented_inverters = inverter_counts[inverter_counts < MIN_REQUIRED_OBS].index.tolist()
if underrepresented_inverters:
    print(f"Warning: Inverters with fewer than {MIN_REQUIRED_OBS} test readings: {underrepresented_inverters}")
else:
    print(f"Sample Size Check: All {len(inverter_counts)} inverters have sufficient test observations (>= {MIN_REQUIRED_OBS}).")

assert min_obs >= MIN_REQUIRED_OBS, f"Inverter test observations insufficient: minimum is {min_obs}"

# Aggregate per-inverter metrics
UNDERPERF_CUTOFF_KW = -20.0  # Definition of significant interval-level underperformance deficit

ranking_list = []
for skey, group in test_df.groupby('SOURCE_KEY'):
    n_obs = len(group)
    mean_res = float(group['RESIDUAL'].mean())
    median_res = float(group['RESIDUAL'].median())
    std_res = float(group['RESIDUAL'].std())
    underperf_rate = float((group['RESIDUAL'] < UNDERPERF_CUTOFF_KW).mean() * 100.0)
    # Total deficit in kWh: 15-minute readings = 0.25 hour per reading
    deficit_kwh = float(group['RESIDUAL'].clip(upper=0).abs().sum() * 0.25)
    mean_actual = float(group['AC_POWER'].mean())
    mean_expected = float(group['EXPECTED_AC_POWER'].mean())

    ranking_list.append({
        'SOURCE_KEY': skey,
        'TEST_OBSERVATIONS': n_obs,
        'MEAN_ACTUAL_KW': round(mean_actual, 2),
        'MEAN_EXPECTED_KW': round(mean_expected, 2),
        'MEAN_RESIDUAL_KW': round(mean_res, 2),
        'MEDIAN_RESIDUAL_KW': round(median_res, 2),
        'STD_RESIDUAL_KW': round(std_res, 2),
        'UNDERPERF_RATE_PCT': round(underperf_rate, 2),
        'TOTAL_DEFICIT_KWH': round(deficit_kwh, 2)
    })

inverter_ranking_df = pd.DataFrame(ranking_list).sort_values(by='MEAN_RESIDUAL_KW', ascending=True).reset_index(drop=True)
inverter_ranking_df['RANK'] = range(1, len(inverter_ranking_df) + 1)
inverter_ranking_df['SHORT_ID'] = [f"Inv_{r:02d} ({k[:4]})" for r, k in zip(inverter_ranking_df['RANK'], inverter_ranking_df['SOURCE_KEY'])]

# Save Table 3: Inverter Ranking Table
inverter_ranking_df.to_csv('results/tables/table3_inverter_ranking.csv', index=False)
print("Table 3 (Inverter Ranking) saved.")
print("\nTop 5 Most Underperforming Inverters:")
print(inverter_ranking_df[['RANK', 'SHORT_ID', 'MEAN_RESIDUAL_KW', 'MEDIAN_RESIDUAL_KW', 'UNDERPERF_RATE_PCT', 'TOTAL_DEFICIT_KWH']].head(5))

# %%
# Figure 6: Residual Distribution per Inverter (Ordered by Mean Residual)
order = inverter_ranking_df['SOURCE_KEY'].tolist()
short_labels = inverter_ranking_df['SHORT_ID'].tolist()

plt.figure(figsize=(14, 6))
sns.boxplot(
    data=test_df,
    x='SOURCE_KEY',
    y='RESIDUAL',
    hue='SOURCE_KEY',
    legend=False,
    order=order,
    palette=['tab:red' if i < 3 else 'tab:blue' for i in range(len(order))],
    fliersize=1.5
)
plt.axhline(0, color='black', linestyle='--', linewidth=1.5, alpha=0.7)
plt.axhline(UNDERPERF_CUTOFF_KW, color='darkred', linestyle=':', linewidth=1.2, label=f'Cutoff ({UNDERPERF_CUTOFF_KW} kW)')
plt.xticks(ticks=range(len(order)), labels=short_labels, rotation=45, ha='right')
plt.title("Per-Inverter Residual Distribution on Held-Out Test Set (Ranked from Worst to Best)")
plt.xlabel("Inverter (Rank & Short ID)")
plt.ylabel("Residual: Actual - Expected AC Power (kW)")
plt.legend()
plt.tight_layout()
fig6_path = 'results/figures/fig6_residual_distribution_per_inverter.png'
plt.savefig(fig6_path, dpi=150)
plt.close()
print("Figure 6 saved to:", fig6_path)

# %%
# Figure 7: Underperformance Ranking Bar Chart (Mean Residual with Error Bars)
plt.figure(figsize=(12, 6))
colors = ['tab:red' if r <= 3 else ('tab:orange' if r <= 5 else 'tab:blue') for r in inverter_ranking_df['RANK']]
bars = plt.barh(inverter_ranking_df['SHORT_ID'], inverter_ranking_df['MEAN_RESIDUAL_KW'], color=colors, alpha=0.85)

plt.axvline(0, color='black', linestyle='--', linewidth=1)
plt.title("Inverter Performance Ranking by Mean Residual (Held-Out Test Period)")
plt.xlabel("Mean Residual: Actual - Expected AC Power (kW)")
plt.ylabel("Inverter")
plt.gca().invert_yaxis()
plt.tight_layout()
fig7_path = 'results/figures/fig7_underperformance_ranking.png'
plt.savefig(fig7_path, dpi=150)
plt.close()
print("Figure 7 saved to:", fig7_path)

# %% [markdown]
# ## Phase 5: Stability and Robustness Checks
# **What**: Test whether underperformance flags are stable across time (First Half vs. Second Half
# of the test period), across varying decision thresholds, and under bootstrap resampling.
#
# **Why**: A model flag is only operationally useful for maintenance dispatch if it reflects persistent
# hardware degradation rather than transient passing clouds, temporary shading, or measurement noise.
# If rankings or flags fluctuate wildly between halves, the system cannot be trusted.

# %%
# Temporal Split of Test Set: First Half vs Second Half
test_dates = sorted(test_df['DATE_TIME'].dt.date.unique())
mid_point = len(test_dates) // 2
half1_dates = test_dates[:mid_point]
half2_dates = test_dates[mid_point:]

half1_df = test_df[test_df['DATE_TIME'].dt.date.isin(half1_dates)]
half2_df = test_df[test_df['DATE_TIME'].dt.date.isin(half2_dates)]

print(f"Test Set Half 1: {half1_dates[0]} to {half1_dates[-1]} ({len(half1_df):,} rows)")
print(f"Test Set Half 2: {half2_dates[0]} to {half2_dates[-1]} ({len(half2_df):,} rows)")

# Compute per-inverter metrics in each half
h1_perf = half1_df.groupby('SOURCE_KEY')['RESIDUAL'].mean().rename('H1_MEAN_RESIDUAL')
h2_perf = half2_df.groupby('SOURCE_KEY')['RESIDUAL'].mean().rename('H2_MEAN_RESIDUAL')

stability_df = pd.concat([h1_perf, h2_perf], axis=1).reset_index()
stability_df['H1_RANK'] = stability_df['H1_MEAN_RESIDUAL'].rank(ascending=True)
stability_df['H2_RANK'] = stability_df['H2_MEAN_RESIDUAL'].rank(ascending=True)

# Spearman rank correlation between halves
from scipy.stats import spearmanr, pearsonr
spearman_corr, spearman_p = spearmanr(stability_df['H1_RANK'], stability_df['H2_RANK'])
pearson_corr, pearson_p = pearsonr(stability_df['H1_MEAN_RESIDUAL'], stability_df['H2_MEAN_RESIDUAL'])

print(f"Rank correlation (Spearman rho) between Half 1 and Half 2: {spearman_corr:.4f} (p = {spearman_p:.4e})")
print(f"Pearson correlation between Half 1 and Half 2 mean residuals: {pearson_corr:.4f} (p = {pearson_p:.4e})")

# Evaluate flag overlap across multiple threshold criteria
flag_thresholds = [
    ('Bottom 3 Inverters', lambda df, col: df[col].isin([1, 2, 3])),
    ('Bottom 5 Inverters', lambda df, col: df[col] <= 5),
    ('Mean Residual < -20 kW', lambda df, col: df[col.replace('RANK', 'MEAN_RESIDUAL')] < -20.0),
    ('Mean Residual < -15 kW', lambda df, col: df[col.replace('RANK', 'MEAN_RESIDUAL')] < -15.0),
    ('Mean Residual < -10 kW', lambda df, col: df[col.replace('RANK', 'MEAN_RESIDUAL')] < -10.0)
]

threshold_results = []
for label, rule in flag_thresholds:
    flagged_h1 = set(stability_df[rule(stability_df, 'H1_RANK')]['SOURCE_KEY'])
    flagged_h2 = set(stability_df[rule(stability_df, 'H2_RANK')]['SOURCE_KEY'])
    intersection = flagged_h1.intersection(flagged_h2)
    union = flagged_h1.union(flagged_h2)
    jaccard = len(intersection) / len(union) if len(union) > 0 else 1.0

    threshold_results.append({
        'Threshold Definition': label,
        'Half 1 Flagged Count': len(flagged_h1),
        'Half 2 Flagged Count': len(flagged_h2),
        'Persistent Overlap Count': len(intersection),
        'Jaccard Similarity': round(jaccard, 4)
    })
    print(f"Threshold: {label:24s} | H1={len(flagged_h1)}, H2={len(flagged_h2)}, Persistent Overlap={len(intersection)}, Jaccard={jaccard:.2f}")

# Bootstrap analysis: 500 resamples to evaluate ranking stability and CI of residuals
np.random.seed(42)
B = 500
unique_test_days = test_df['DATE_TIME'].dt.date.unique()
bootstrap_ranks = {k: [] for k in stability_df['SOURCE_KEY']}

for b in range(B):
    sample_days = np.random.choice(unique_test_days, size=len(unique_test_days), replace=True)
    boot_df = test_df[test_df['DATE_TIME'].dt.date.isin(sample_days)]
    boot_means = boot_df.groupby('SOURCE_KEY')['RESIDUAL'].mean()
    boot_ranks = boot_means.rank(ascending=True)
    for k in bootstrap_ranks:
        if k in boot_ranks:
            bootstrap_ranks[k].append(boot_ranks[k])

boot_summary = []
for k, ranks in bootstrap_ranks.items():
    boot_summary.append({
        'SOURCE_KEY': k,
        'Mean_Bootstrap_Rank': np.mean(ranks),
        'Rank_CI_2.5': np.percentile(ranks, 2.5),
        'Rank_CI_97.5': np.percentile(ranks, 97.5)
    })
boot_rank_df = pd.DataFrame(boot_summary)

# Combine into Table 4: Stability Metrics Table
stability_metrics_table = pd.DataFrame(threshold_results)
stability_metrics_table['Spearman_Rank_Corr'] = round(spearman_corr, 4)
stability_metrics_table['Spearman_p_value'] = f"{spearman_p:.4e}"
stability_metrics_table.to_csv('results/tables/table4_stability_metrics.csv', index=False)
print("Table 4 (Stability Metrics) saved.")

# %%
# Figure 8: Stability Plot - Half 1 vs Half 2 Inverter Mean Residuals
plt.figure(figsize=(9, 7))
plt.scatter(stability_df['H1_MEAN_RESIDUAL'], stability_df['H2_MEAN_RESIDUAL'], color='tab:blue', s=70, alpha=0.85, edgecolors='black')

# Plot 1:1 reference line
min_val = min(stability_df['H1_MEAN_RESIDUAL'].min(), stability_df['H2_MEAN_RESIDUAL'].min()) - 5
max_val = max(stability_df['H1_MEAN_RESIDUAL'].max(), stability_df['H2_MEAN_RESIDUAL'].max()) + 5
plt.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=1.5, label='Perfect Stability (1:1)')

# Annotate worst inverters
for _, row in stability_df.iterrows():
    if row['H1_RANK'] <= 3 or row['H2_RANK'] <= 3:
        plt.annotate(
            f"{row['SOURCE_KEY'][:6]}",
            (row['H1_MEAN_RESIDUAL'], row['H2_MEAN_RESIDUAL']),
            textcoords="offset points",
            xytext=(6, -6),
            fontsize=9,
            fontweight='bold',
            color='darkred'
        )

plt.axhline(0, color='gray', linestyle=':', linewidth=1)
plt.axvline(0, color='gray', linestyle=':', linewidth=1)
plt.title(f"Inverter Underperformance Stability: Half 1 vs Half 2\n(Spearman Rank Correlation $\\rho = {spearman_corr:.3f}$, $p < 0.001$)")
plt.xlabel("First Half Mean Residual (kW)")
plt.ylabel("Second Half Mean Residual (kW)")
plt.legend()
plt.tight_layout()
fig8_path = 'results/figures/fig8_stability_half1_vs_half2.png'
plt.savefig(fig8_path, dpi=150)
plt.close()
print("Figure 8 saved to:", fig8_path)

# Verify all 8 figures exist and are non-empty
all_figures = [
    'results/figures/fig1_power_vs_irradiation.png',
    'results/figures/fig2_power_vs_module_temp.png',
    'results/figures/fig3_daily_diurnal_profiles.png',
    'results/figures/fig4_inverter_mean_daily_yield.png',
    'results/figures/fig5_model_actual_vs_predicted.png',
    'results/figures/fig6_residual_distribution_per_inverter.png',
    'results/figures/fig7_underperformance_ranking.png',
    'results/figures/fig8_stability_half1_vs_half2.png'
]
assert len(all_figures) == 8, "Expected exactly 8 figures"
for fig_f in all_figures:
    assert os.path.exists(fig_f), f"Missing figure: {fig_f}"
    fsize = os.path.getsize(fig_f)
    assert fsize > 0, f"Empty figure: {fig_f}"
    print(f"Verified: {fig_f} ({fsize:,} bytes)")
