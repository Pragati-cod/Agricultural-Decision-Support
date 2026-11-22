import pandas as pd
import os

# ==========================================
# STEP 1: SET PROJECT PATHS
# ==========================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================================
# STEP 2: EXTRACT DATASETS
# ==========================================

farms = pd.read_csv(os.path.join(DATA_DIR, "farms.csv"))
soil = pd.read_csv(os.path.join(DATA_DIR, "soil_tests.csv"))
calendar = pd.read_csv(os.path.join(DATA_DIR, "crop_calendar.csv"))
inputs = pd.read_csv(os.path.join(DATA_DIR, "input_usage.csv"))
harvest = pd.read_csv(os.path.join(DATA_DIR, "harvest.csv"))
market = pd.read_csv(os.path.join(DATA_DIR, "market_prices.csv"))

print("All datasets loaded successfully!")

# ==========================================
# STEP 3: STANDARDIZE TEXT DATA
# ==========================================

datasets = [farms, soil, calendar, inputs, harvest, market]

for df in datasets:
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

# Standardize farm IDs

for df in [farms, soil, calendar, inputs, harvest]:
    df["farm_id"] = df["farm_id"].str.upper()

# Standardize crop names

for df in [calendar, inputs, harvest, market]:
    df["crop"] = df["crop"].str.title()

farms["location"] = farms["location"].str.title()
market["market_location"] = market["market_location"].str.title()

# ==========================================
# STEP 4: CONVERT DATE COLUMNS
# ==========================================

soil["test_date"] = pd.to_datetime(
    soil["test_date"], errors="coerce"
)

calendar["sowing_date"] = pd.to_datetime(
    calendar["sowing_date"], errors="coerce"
)

calendar["expected_harvest_date"] = pd.to_datetime(
    calendar["expected_harvest_date"], errors="coerce"
)

harvest["harvest_date"] = pd.to_datetime(
    harvest["harvest_date"], errors="coerce"
)

market["price_date"] = pd.to_datetime(
    market["price_date"], errors="coerce"
)

# ==========================================
# STEP 5: REMOVE DUPLICATES
# ==========================================

farms = farms.drop_duplicates(subset=["farm_id"])

soil = soil.drop_duplicates(
    subset=["farm_id", "test_date"]
)

calendar = calendar.drop_duplicates(
    subset=["farm_id", "crop", "season"]
)

inputs = inputs.drop_duplicates(
    subset=["farm_id", "crop"]
)

harvest = harvest.drop_duplicates(
    subset=["farm_id", "crop", "harvest_date"]
)

market = market.drop_duplicates(
    subset=["crop", "market_location", "price_date"]
)

# ==========================================
# STEP 6: VALIDATE MEASUREMENTS
# ==========================================

farms["invalid_area"] = farms["area_hectares"] <= 0

harvest["invalid_quantity"] = harvest["quantity_kg"] <= 0

soil["invalid_ph"] = ~soil["ph"].between(0, 14)

# ==========================================
# STEP 7: PREPARE HARVEST DATA
# ==========================================

# Remove duplicate area column from harvest
# Use official farm area from farms.csv

harvest = harvest.drop(columns=["area_hectares"])

# ==========================================
# STEP 8: MERGE DATASETS
# ==========================================

data = harvest.merge(
    farms,
    on="farm_id",
    how="left"
)

data = data.merge(
    calendar,
    on=["farm_id", "crop"],
    how="left"
)

data = data.merge(
    inputs,
    on=["farm_id", "crop"],
    how="left"
)

# Merge soil test information

data = data.merge(
    soil,
    on="farm_id",
    how="left"
)

# ==========================================
# STEP 9: MATCH MARKET PRICES
# ==========================================

data = data.merge(
    market,
    left_on=["crop", "location", "harvest_date"],
    right_on=["crop", "market_location", "price_date"],
    how="left"
)

# ==========================================
# STEP 10: VALIDATE CROP CYCLES
# ==========================================

data["incomplete_cycle"] = (
    data["sowing_date"].isna() |
    data["harvest_date"].isna() |
    data["expected_harvest_date"].isna() |
    (data["harvest_date"] < data["sowing_date"]) |
    (data["harvest_date"] > data["expected_harvest_date"])
)

# ==========================================
# STEP 11: CALCULATE INPUT COST
# ==========================================

cost_columns = [
    "seed_cost",
    "fertilizer_cost",
    "pesticide_cost",
    "other_cost"
]

data["total_input_cost"] = data[cost_columns].sum(
    axis=1,
    min_count=len(cost_columns)
)

# ==========================================
# STEP 12: CALCULATE AGRICULTURAL INDICATORS
# ==========================================

data["yield_per_hectare"] = (
    data["quantity_kg"] / data["area_hectares"]
)

data["input_cost_per_hectare"] = (
    data["total_input_cost"] / data["area_hectares"]
)

data["gross_return_per_hectare"] = (
    data["yield_per_hectare"] *
    data["price_per_quintal"] / 100
)

# ==========================================
# STEP 13: SAVE CLEAN DATASET
# ==========================================

data.to_csv(
    os.path.join(OUTPUT_DIR, "clean_crop_cycles.csv"),
    index=False
)

# ==========================================
# STEP 14: GENERATE DATA QUALITY REPORT
# ==========================================

quality = pd.DataFrame({
    "Column": data.columns,
    "Missing Values": data.isnull().sum().values
})

quality.to_csv(
    os.path.join(OUTPUT_DIR, "data_quality_report.csv"),
    index=False
)

# ==========================================
# STEP 15: DISPLAY RESULTS
# ==========================================

print("\n================================")
print("ETL PIPELINE COMPLETED")
print("================================")

print("Total crop records:", len(data))

print(
    "Incomplete crop cycles:",
    data["incomplete_cycle"].sum()
)

print(
    "Invalid harvest quantities:",
    data["invalid_quantity"].sum()
)

print(
    "Invalid farm areas:",
    data["invalid_area"].sum()
)

print("\nAverage Yield per Hectare:")

print(data["yield_per_hectare"].mean())

print("\nGenerated Files:")
print("1. clean_crop_cycles.csv")
print("2. data_quality_report.csv")

print("\nAll operations completed successfully!")