
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Agricultural Decision Support System",
    page_icon="🌾",
    layout="wide"
)

BASE_DIR = Path(__file__).parent

# ==========================================
# 2. LOAD CSV DATA
# ==========================================

@st.cache_data
def load_data():

    crop_file = BASE_DIR / "weather_integrated_crop_cycles.csv"
    weather_file = BASE_DIR / "weather_data.csv"

    if not crop_file.exists():
        raise FileNotFoundError(
            "weather_integrated_crop_cycles.csv is missing."
        )

    if not weather_file.exists():
        raise FileNotFoundError(
            "weather_data.csv is missing."
        )

    crop_data = pd.read_csv(crop_file)
    weather_data = pd.read_csv(weather_file)

    return crop_data, weather_data


st.title("🌾 Agricultural Decision Support System")

st.markdown(
    "Analyze crop yield, farm performance, weather conditions, "
    "input costs and market returns."
)

st.divider()

try:
    data, weather = load_data()
    st.sidebar.success("Datasets loaded successfully!")

except Exception as error:
    st.error("Unable to load project datasets.")
    st.exception(error)
    st.stop()


# ==========================================
# 3. DATA PREPARATION
# ==========================================

required_columns = [
    "farm_id",
    "crop",
    "yield_per_hectare",
    "input_cost_per_hectare",
    "gross_return_per_hectare"
]

missing_columns = [
    col for col in required_columns
    if col not in data.columns
]

if missing_columns:
    st.error(
        "Missing required columns: "
        + ", ".join(missing_columns)
    )
    st.stop()

numeric_columns = [
    "yield_per_hectare",
    "input_cost_per_hectare",
    "gross_return_per_hectare"
]

for col in numeric_columns:
    data[col] = pd.to_numeric(
        data[col], errors="coerce"
    )

for col in ["location", "season", "farm_name"]:
    if col not in data.columns:
        data[col] = "Unknown"

data["farm_name"] = data["farm_name"].fillna("Unknown")
data["location"] = data["location"].fillna("Unknown")
data["season"] = data["season"].fillna("Unknown")
data["crop"] = data["crop"].fillna("Unknown")

weather_numeric = [
    "temperature_mean",
    "temperature_max",
    "temperature_min",
    "rainfall_mm",
    "humidity_percent"
]

for col in weather_numeric:
    if col in weather.columns:
        weather[col] = pd.to_numeric(
            weather[col], errors="coerce"
        )

if "date" in weather.columns:
    weather["date"] = pd.to_datetime(
        weather["date"], errors="coerce"
    )


# ==========================================
# 4. SIDEBAR FILTERS
# ==========================================

st.sidebar.title("Dashboard Filters")

selected_crop = st.sidebar.selectbox(
    "Select Crop",
    ["All"] + sorted(
        data["crop"].astype(str).unique().tolist()
    )
)

selected_location = st.sidebar.selectbox(
    "Select Location",
    ["All"] + sorted(
        data["location"].astype(str).unique().tolist()
    )
)

selected_season = st.sidebar.selectbox(
    "Select Season",
    ["All"] + sorted(
        data["season"].astype(str).unique().tolist()
    )
)

filtered = data.copy()

if selected_crop != "All":
    filtered = filtered[
        filtered["crop"] == selected_crop
    ]

if selected_location != "All":
    filtered = filtered[
        filtered["location"] == selected_location
    ]

if selected_season != "All":
    filtered = filtered[
        filtered["season"] == selected_season
    ]

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()


# ==========================================
# 5. PERFORMANCE OVERVIEW
# ==========================================

st.subheader("Agricultural Performance Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Farms",
    filtered["farm_id"].nunique()
)

col2.metric(
    "Average Yield",
    f"{filtered['yield_per_hectare'].mean():,.0f} kg/ha"
)

col3.metric(
    "Average Input Cost",
    f"₹{filtered['input_cost_per_hectare'].mean():,.0f}/ha"
)

col4.metric(
    "Average Gross Return",
    f"₹{filtered['gross_return_per_hectare'].mean():,.0f}/ha"
)

st.divider()


# ==========================================
# 6. CROP-WISE YIELD COMPARISON
# ==========================================

st.subheader("Crop-wise Yield Comparison")

yield_by_crop = filtered.groupby(
    "crop", as_index=False
)["yield_per_hectare"].mean()

fig1 = px.bar(
    yield_by_crop,
    x="crop",
    y="yield_per_hectare",
    color="crop",
    title="Average Yield per Hectare by Crop",
    labels={
        "crop": "Crop",
        "yield_per_hectare": "Yield (kg/hectare)"
    },
    text_auto=".0f"
)

st.plotly_chart(fig1, use_container_width=True)

st.divider()


# ==========================================
# 7. FARM PERFORMANCE
# ==========================================

st.subheader("Farm Performance")

fig2 = px.bar(
    filtered,
    x="farm_name",
    y="gross_return_per_hectare",
    color="crop",
    hover_data=["location"],
    title="Gross Return per Hectare",
    labels={
        "farm_name": "Farm",
        "gross_return_per_hectare": "Gross Return (₹/ha)"
    }
)

st.plotly_chart(fig2, use_container_width=True)

st.divider()


# ==========================================
# 8. INPUT COST VS GROSS RETURN
# ==========================================

st.subheader("Input Cost vs Gross Return")

fig3 = px.scatter(
    filtered,
    x="input_cost_per_hectare",
    y="gross_return_per_hectare",
    color="crop",
    hover_name="farm_name",
    title="Farm Input Cost and Gross Return",
    labels={
        "input_cost_per_hectare": "Input Cost (₹/ha)",
        "gross_return_per_hectare": "Gross Return (₹/ha)"
    }
)

st.plotly_chart(fig3, use_container_width=True)

st.divider()


# ==========================================
# 9. WEATHER ANALYTICS
# ==========================================

st.subheader("🌦️ Weather Analytics")

weather_filtered = weather.copy()

if "farm_id" in weather_filtered.columns:
    selected_farms = filtered["farm_id"].unique()

    weather_filtered = weather_filtered[
        weather_filtered["farm_id"].isin(selected_farms)
    ]

if "crop" in weather_filtered.columns and selected_crop != "All":
    weather_filtered = weather_filtered[
        weather_filtered["crop"] == selected_crop
    ]

if "season" in weather_filtered.columns and selected_season != "All":
    weather_filtered = weather_filtered[
        weather_filtered["season"] == selected_season
    ]

if weather_filtered.empty:
    st.info("No weather records match the selected filters.")

else:
    w1, w2, w3 = st.columns(3)

    if "temperature_mean" in weather_filtered.columns:
        w1.metric(
            "Average Temperature",
            f"{weather_filtered['temperature_mean'].mean():.1f} °C"
        )

    if "rainfall_mm" in weather_filtered.columns:
        w2.metric(
            "Total Recorded Rainfall",
            f"{weather_filtered['rainfall_mm'].sum():,.1f} mm"
        )

    if "humidity_percent" in weather_filtered.columns:
        w3.metric(
            "Average Humidity",
            f"{weather_filtered['humidity_percent'].mean():.1f}%"
        )

    if "date" in weather_filtered.columns:
        temperature_data = weather_filtered.dropna(
            subset=["date", "temperature_mean"]
        ).groupby(
            "date", as_index=False
        )["temperature_mean"].mean()

        if not temperature_data.empty:
            fig4 = px.line(
                temperature_data,
                x="date",
                y="temperature_mean",
                title="Daily Average Temperature Trend",
                labels={
                    "date": "Date",
                    "temperature_mean": "Temperature (°C)"
                }
            )

            st.plotly_chart(fig4, use_container_width=True)

    if "farm_name" in weather_filtered.columns and "rainfall_mm" in weather_filtered.columns:
        rainfall_data = weather_filtered.groupby(
            "farm_name", as_index=False
        )["rainfall_mm"].sum()

        fig5 = px.bar(
            rainfall_data,
            x="farm_name",
            y="rainfall_mm",
            title="Total Recorded Rainfall by Farm",
            labels={
                "farm_name": "Farm",
                "rainfall_mm": "Rainfall (mm)"
            }
        )

        st.plotly_chart(fig5, use_container_width=True)

st.caption(
    "Weather values are historical gridded estimates from Open-Meteo, "
    "not direct measurements from individual farm weather stations."
)

st.divider()


# ==========================================
# 10. SEASONAL COMPARISON
# ==========================================

st.subheader("Seasonal Crop Comparison")

seasonal_data = filtered.groupby(
    ["season", "crop"],
    as_index=False
)["yield_per_hectare"].mean()

if not seasonal_data.empty:

    fig6 = px.bar(
        seasonal_data,
        x="season",
        y="yield_per_hectare",
        color="crop",
        barmode="group",
        title="Average Crop Yield Across Seasons",
        labels={
            "season": "Season",
            "yield_per_hectare": "Yield (kg/hectare)"
        },
        text_auto=".0f"
    )

    st.plotly_chart(fig6, use_container_width=True)

else:
    st.info("Seasonal data is not available.")

st.divider()


# ==========================================
# 11. FARM-WISE AGRICULTURAL RECORDS
# ==========================================

st.subheader("Farm-wise Agricultural Records")

st.dataframe(
    filtered,
    use_container_width=True
)

st.divider()


# ==========================================
# 12. DECISION SUPPORT INDICATORS
# ==========================================

st.subheader("🌱 Decision Support Indicators")

decision_data = filtered.dropna(
    subset=[
        "yield_per_hectare",
        "gross_return_per_hectare"
    ]
)

if not decision_data.empty:

    best_yield = decision_data.loc[
        decision_data["yield_per_hectare"].idxmax()
    ]

    best_return = decision_data.loc[
        decision_data["gross_return_per_hectare"].idxmax()
    ]

    d1, d2 = st.columns(2)

    with d1:
        st.markdown("**Highest Yield Record**")
        st.write(f"Farm: {best_yield['farm_name']}")
        st.write(f"Crop: {best_yield['crop']}")
        st.write(
            f"Yield: {best_yield['yield_per_hectare']:,.0f} kg/ha"
        )

    with d2:
        st.markdown("**Highest Gross Return Record**")
        st.write(f"Farm: {best_return['farm_name']}")
        st.write(f"Crop: {best_return['crop']}")
        st.write(
            f"Gross Return: ₹{best_return['gross_return_per_hectare']:,.0f}/ha"
        )

st.info(
    "These indicators identify the highest observed values. "
    "They do not establish that a crop or farming practice caused "
    "better performance. Gross return is not net profit."
)

st.divider()


# ==========================================
# 13. DATA QUALITY
# ==========================================

st.subheader("Data Quality")

if "incomplete_cycle" in filtered.columns:
    incomplete = (
        filtered["incomplete_cycle"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "yes"])
        .sum()
    )

    st.write("Incomplete crop cycles:", int(incomplete))

else:
    st.write("Incomplete crop cycle field is not available.")

st.write("Total crop records:", len(filtered))
st.write("Total weather records:", len(weather_filtered))

st.divider()


# ==========================================
# 14. FOOTER
# ==========================================

st.markdown(
    "🌱 Agricultural Decision Support System | "
    "Python | Pandas | Streamlit | Plotly | Open-Meteo"
)
