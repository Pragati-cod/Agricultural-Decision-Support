
import pandas as pd
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

WEATHER_FILE = BASE_DIR / "data" / "weather_data.csv"
CROP_FILE = BASE_DIR / "reports" / "clean_crop_cycles.csv"
OUTPUT_FILE = BASE_DIR / "reports" / "weather_integrated_crop_cycles.csv"

print("===================================")
print("WEATHER AND CROP DATA INTEGRATION")
print("===================================")

# 1. Load datasets
weather = pd.read_csv(WEATHER_FILE)
crops = pd.read_csv(CROP_FILE)

# 2. Standardize column names
weather.columns = weather.columns.str.strip().str.lower()
crops.columns = crops.columns.str.strip().str.lower()

print("Weather records:", len(weather))
print("Crop records:", len(crops))
print("\nWeather columns:", weather.columns.tolist())

# 3. Convert dates
weather["date"] = pd.to_datetime(weather["date"], errors="coerce")
crops["sowing_date"] = pd.to_datetime(
    crops["sowing_date"], errors="coerce"
)
crops["harvest_date"] = pd.to_datetime(
    crops["harvest_date"], errors="coerce"
)

# 4. Standardize farm IDs and crop names
weather["farm_id"] = weather["farm_id"].astype(str).str.strip().str.upper()
crops["farm_id"] = crops["farm_id"].astype(str).str.strip().str.upper()

weather["crop"] = weather["crop"].astype(str).str.strip().str.title()
crops["crop"] = crops["crop"].astype(str).str.strip().str.title()

# 5. Weather measurement columns
measurement_columns = {
    "temperature_mean": "avg_temperature",
    "temperature_max": "max_temperature",
    "temperature_min": "min_temperature",
    "rainfall_mm": "total_rainfall",
    "humidity_percent": "avg_humidity"
}

available_columns = {
    source: target
    for source, target in measurement_columns.items()
    if source in weather.columns
}

if not available_columns:
    raise ValueError("No weather measurement columns found.")

# Convert weather values to numeric
for column in available_columns:
    weather[column] = pd.to_numeric(
        weather[column], errors="coerce"
    )

# 6. Summarize weather for each crop cycle
weather_summary = []

for _, crop in crops.iterrows():

    farm_id = crop["farm_id"]
    crop_name = crop["crop"]
    sowing_date = crop["sowing_date"]
    harvest_date = crop["harvest_date"]

    if pd.isna(sowing_date) or pd.isna(harvest_date):
        print(f"Invalid crop dates for {farm_id}")
        continue

    farm_weather = weather[
        (weather["farm_id"] == farm_id) &
        (weather["date"] >= sowing_date) &
        (weather["date"] <= harvest_date)
    ].copy()

    summary = {
        "farm_id": farm_id,
        "crop": crop_name,
        "weather_days": len(farm_weather)
    }

    if farm_weather.empty:
        print(f"No weather records found for {farm_id}")

        for target_column in available_columns.values():
            summary[target_column] = None

    else:
        for source_column, target_column in available_columns.items():

            if source_column == "rainfall_mm":
                summary[target_column] = farm_weather[
                    source_column
                ].sum(min_count=1)
            else:
                summary[target_column] = farm_weather[
                    source_column
                ].mean()

    weather_summary.append(summary)

# 7. Create weather summary
weather_df = pd.DataFrame(weather_summary)

# 8. Merge with original crop dataset
result = crops.merge(
    weather_df,
    on=["farm_id", "crop"],
    how="left",
    validate="one_to_one"
)

# 9. Save integrated dataset
result.to_csv(OUTPUT_FILE, index=False)

# 10. Quality report
print("\n===================================")
print("WEATHER INTEGRATION QUALITY REPORT")
print("===================================")

print("Total crop records:", len(result))

print(
    "Records with weather data:",
    result["weather_days"].fillna(0).gt(0).sum()
)

print(
    "Records without weather data:",
    result["weather_days"].fillna(0).eq(0).sum()
)

print(
    "Average temperature:",
    round(result["avg_temperature"].mean(), 2),
    "°C"
)

print(
    "Total rainfall across crop cycles:",
    round(result["total_rainfall"].sum(), 2),
    "mm"
)

print("\nGenerated file:")
print(OUTPUT_FILE)

print("\nWEATHER INTEGRATION COMPLETED SUCCESSFULLY!")
