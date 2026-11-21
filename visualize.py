
import pandas as pd
import plotly.express as px
import os

# Project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_DIR = os.path.join(BASE_DIR, "reports")

# Load analysis data
crop_data = pd.read_csv(
    os.path.join(REPORT_DIR, "crop_performance.csv")
)

farm_data = pd.read_csv(
    os.path.join(REPORT_DIR, "farm_performance.csv")
)

# Create output folder
CHART_DIR = os.path.join(REPORT_DIR, "charts")
os.makedirs(CHART_DIR, exist_ok=True)

# 1. Crop-wise yield comparison
fig1 = px.bar(
    crop_data,
    x="crop",
    y="average_yield",
    title="Average Crop Yield per Hectare",
    labels={
        "crop": "Crop",
        "average_yield": "Yield (kg/hectare)"
    },
    color="crop"
)

fig1.write_html(
    os.path.join(CHART_DIR, "crop_yield.html")
)

# 2. Farm-wise yield comparison
fig2 = px.bar(
    farm_data,
    x="farm_name",
    y="yield_per_hectare",
    color="crop",
    title="Farm-wise Agricultural Yield",
    labels={
        "farm_name": "Farm",
        "yield_per_hectare": "Yield (kg/hectare)"
    }
)

fig2.write_html(
    os.path.join(CHART_DIR, "farm_yield.html")
)

# 3. Input cost vs gross return
fig3 = px.scatter(
    farm_data,
    x="input_cost_per_hectare",
    y="gross_return_per_hectare",
    color="crop",
    hover_name="farm_name",
    title="Input Cost vs Gross Return",
    labels={
        "input_cost_per_hectare": "Input Cost (₹/hectare)",
        "gross_return_per_hectare": "Gross Return (₹/hectare)"
    }
)

fig3.write_html(
    os.path.join(CHART_DIR, "cost_vs_return.html")
)

print("All charts generated successfully!")
print("Charts saved in reports/charts/")
