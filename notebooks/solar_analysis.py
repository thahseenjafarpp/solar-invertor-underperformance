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
DATA_DIR = 'data'
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
