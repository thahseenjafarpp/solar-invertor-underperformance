# Solar Inverter Underperformance Analysis: Presentation & Explanation Guide

This guide provides plain-language explanations for each section of the project. It is structured so that a student can easily explain what was done, why it was done, and what the numbers mean during a project presentation or oral exam.

---

### Practical 1: Exploring Data
- **What was done**: We loaded the raw solar power generation readings and weather sensor logs for Plant 1, converted timestamps into proper datetime objects, and examined data types, shapes, and descriptive statistics.
- **Why it matters**: Before fitting any predictive model, we must understand the structure and physical scale of the measurements. Plant 1 contains 22 inverters logging DC and AC power every 15 minutes, while a single weather station records solar irradiance and temperatures. Checking date ranges confirmed that both files cover the exact same 34-day operational window.

---

### Practical 2: Data Preprocessing
- **What was done**: We merged the generation and weather data on timestamps, verified zero missing values and zero duplicate records, filtered out nighttime hours using an irradiation threshold of $0.01\text{ kW/m}^2$, split data chronologically (first 24 days for training, last 10 days for testing), and scaled features using Min-Max normalization.
- **Why it matters**: Solar panels produce zero power at night; keeping nighttime rows would artificially inflate model accuracy and bias regression baselines toward zero. We identified `SOURCE_KEY` (inverter ID) as a categorical identifier and strictly excluded it and power/yield columns from inputs to prevent data leakage. Fitting the `MinMaxScaler` only on training data ensures the model never sees future test data distributions.

---

### Practical 3: Correlation and Regression Analysis
- **What was done**: We computed a correlation matrix and heatmap, then trained three baseline regression models: Simple Linear Regression (using solar irradiation alone), Multiple Linear Regression (adding module temperature, ambient temperature, and hour of the day), and Polynomial Regression (degree 2). We also inspected a statsmodels OLS summary table.
- **Why it matters**: Solar power generation is fundamentally driven by sunlight (irradiation correlation $r \approx 0.97$), but solar cells lose efficiency as they get hotter (negative module temperature coefficient in OLS). Polynomial regression captures the slight non-linear saturation that occurs at peak midday irradiance, improving the test $R^2$ from $0.9542$ to $0.9626$.

---

### Practical 10: Model Performance and Ensemble
- **What was done**: We trained a Random Forest regressor with 100 decision trees on the same normalized inputs and evaluated all four models on the identical 10-day held-out test set using Root Mean Squared Error (RMSE), Mean Absolute Error (MAE), and $R^2$.
- **Why it matters**: Comparing linear, polynomial, and tree-based models on the exact same unseen test period allows us to pick the most balanced expected-power baseline. Random Forest achieves a strong $R^2 = 0.9594$ and $\text{MAE} = 35.88\text{ kW}$ without overfitting or suffering extreme polynomial tail behavior, making it an ideal benchmark of expected power.

---

### Section 5: Residual Analysis and Underperformance Ranking
- **What was done**: We defined residual as $\text{Residual} = \text{Actual AC Power} - \text{Expected AC Power}$. We calculated the mean residual and the percentage of readings with deficits exceeding $-20\text{ kW}$ for all 22 inverters on test days, ranking inverters from worst to best.
- **Why it matters**: Raw power output cannot reveal whether an inverter is struggling or simply shaded by clouds. By subtracting the weather-based expected power, we isolate pure inverter-specific health. Inverters with large negative residuals generate less power than their peers under identical ambient weather, signaling potential string faults, inverter clipping, or excessive soiling.

---

### Practical 6: Clustering (K-Means)
- **What was done**: We applied unsupervised K-Means clustering to the 22 inverters using two normalized features: mean residual and percentage of low readings. We plotted an elbow curve of inertia from $k=1$ to $k=5$ and clustered inverters with $k=3$.
- **Why it matters**: Clustering automatically segments the fleet into objective operational tiers without arbitrary manual cutoffs. The elbow curve shows a sharp drop from $k=1$ (inertia $2.635$) to $k=2$ ($0.246$) and $k=3$ ($0.091$). With $k=3$, the algorithm cleanly separates two chronic underperformers (`bvBO` and `1BY6`) into an isolated low-performance group, apart from average and top-performing units.

---

### Section 7: Temporal Stability Analysis
- **What was done**: We divided the 10-day test set into two chronological halves (5 days each: June 8–12 vs June 13–17). We computed per-inverter mean residuals in each half, calculated the Spearman rank correlation ($\rho$), and verified whether K-Means places the same inverters in the low-performance group across both periods.
- **Why it matters**: A maintenance flag is only actionable if it reflects a persistent hardware problem rather than fleeting cloud cover. The Spearman rank correlation is high ($\rho = 0.7832$, $p < 0.001$), and exactly the same two underperforming inverters (`bvBO` and `1BY6`) remain in the low group across both halves, proving that the flags are stable over time.

---

### Section 8: Summary & Limitations
- **What was done**: We verified all five automated project self-checks (chronological split, no leakage, no missing inputs, realistic $R^2 < 0.99$, and existing artifacts) and summarized operational constraints.
- **Why it matters**: In predictive analytics, knowing the boundaries of your model is as critical as the predictions. The 34-day window cannot capture seasonal degradation, results apply specifically to Plant 1, the absence of ground-truth maintenance logs means flags indicate "inspect for maintenance" rather than guaranteed broken parts, and pooled training establishes a peer-relative rather than absolute baseline.
