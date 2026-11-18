# Solar Power Generation Data

## Source
- **Dataset**: [Kaggle: Solar Power Generation Data](https://www.kaggle.com/datasets/anikannal/solar-power-generation-data) by Ani Kannal.
- Collected from solar power plants in India over a 34-day period (15-minute intervals).

## Raw Files
Place the following raw CSV files in this `data/` directory (these files are git-ignored and not tracked in version control):
- `Plant_1_Generation_Data.csv`: **Used for modeling**. Inverter-level power generation readings for Plant 1 (`DATE_TIME`, `PLANT_ID`, `SOURCE_KEY`, `DC_POWER`, `AC_POWER`, `DAILY_YIELD`, `TOTAL_YIELD`).
- `Plant_1_Weather_Sensor_Data.csv`: **Used for modeling**. Weather sensor readings for Plant 1 (`DATE_TIME`, `PLANT_ID`, `SOURCE_KEY`, `AMBIENT_TEMPERATURE`, `MODULE_TEMPERATURE`, `IRRADIATION`).
- `Plant_2_Generation_Data.csv`: **Unused**. Plant 2 generation readings (kept for reference, not used in the simplified course project).
- `Plant_2_Weather_Sensor_Data.csv`: **Unused**. Plant 2 weather readings (kept for reference, not used in the simplified course project).
