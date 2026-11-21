
import pandas as pd
import os

# Project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_FILE = os.path.join(
    BASE_DIR, "reports", "clean_crop_cycles.csv"
)

OUTPUT_DIR = os.path.join(BASE_DIR, "reports")

# Load cleaned dataset
data = pd.read_csv(INPUT_FILE)

# Crop-wise performance analysis
crop_summary = data.groupby("crop").agg(
    average_yield=("yield_per_hectare", "mean"),
    average_input_cost=("input_cost_per_hectare", "mean"),
    average_gross_return=("gross_return_per_hectare", "mean")
).reset_index()

# Farm-wise performance analysis
farm_summary = data.groupby(
    ["farm_id", "farm_name", "location", "crop"]
).agg(
    yield_per_hectare=("yield_per_hectare", "mean"),
    input_cost_per_hectare=("input_cost_per_hectare", "mean"),
    gross_return_per_hectare=("gross_return_per_hectare", "mean")
).reset_index()

# Save analysis results
crop_summary.to_csv(
    os.path.join(OUTPUT_DIR, "crop_performance.csv"),
    index=False
)

farm_summary.to_csv(
    os.path.join(OUTPUT_DIR, "farm_performance.csv"),
    index=False
)

# Display results
print("\nCROP-WISE PERFORMANCE")
print(crop_summary.to_string(index=False))

print("\nFARM-WISE PERFORMANCE")
print(farm_summary.to_string(index=False))

print("\nAnalysis completed successfully!")
