
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from sqlalchemy import create_engine, URL, text


# ==========================================
# STEP 1: PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Agricultural Decision Support",
    page_icon="🌾",
    layout="wide"
)


# ==========================================
# STEP 2: DATABASE CONFIGURATION
# ==========================================

st.title("🌾 Agricultural Decision Support System")

st.markdown(
    "Analyze crop yield, farm performance, weather conditions, "
    "input costs and market returns."
)

st.divider()

st.sidebar.header("Database Connection")

password = st.sidebar.text_input(
    "PostgreSQL Password",
    type="password"
)

if not password:
    st.info("Enter your PostgreSQL password in the sidebar to load the dashboard.")
    st.stop()


@st.cache_resource
def get_engine(db_password):

    db_url = URL.create(
        drivername="postgresql+psycopg2",
        username="postgres",
        password=db_password,
        host="localhost",
        port=5432,
        database="agricultural_db"
    )

    return create_engine(db_url)


# ==========================================
# STEP 3: LOAD DATA FROM POSTGRESQL
# ==========================================

@st.cache_data(ttl=60)
def load_data(db_password):

    engine = get_engine(db_password)

    with engine.connect() as connection:

        crop_data = pd.read_sql(
            text(
                "SELECT * FROM public.weather_integrated_crop_cycles"
            ),
            connection
        )

        weather_data = pd.read_sql(
            text(
                "SELECT * FROM public.weather_data"
            ),
            connection
        )

    return crop_data, weather_data


try:

    data, weather = load_data(password)

    st.sidebar.success("PostgreSQL connected successfully!")

except Exception as error:

    st.error("Unable to connect to PostgreSQL or load the data.")
    st.code(str(error))
    st.stop()


if data.empty:
    st.warning("No crop records found in PostgreSQL.")
    st.stop()


# ==========================================
# STEP 4: DATA PREPARATION
# ==========================================

required_columns = [
    "farm_id",
    "crop",
    "yield_per_hectare",
    "input_cost_per_hectare",
    "gross_return_per_hectare"
]

missing_columns = [
    column for column in required_columns
    if column not in data.columns
]

if missing_columns:

    st.error(
        "Required columns are missing from the integrated table: "
        + ", ".join(missing_columns)
    )

    st.stop()


numeric_columns = [
    "yield_per_hectare",
    "input_cost_per_hectare",
    "gross_return_per_hectare"
]

for column in numeric_columns:
    data[column] = pd.to_numeric(
        data[column], errors="coerce"
    )


if "location" not in data.columns:
    data["location"] = "Unknown"

if "farm_name" not in data.columns:
    data["farm_name"] = data["farm_id"]

if "season" not in data.columns:
    data["season"] = "Unknown"


# Prepare weather data

temperature_column = "temperature_mean"
rainfall_column = "rainfall_mm"
humidity_column = "humidity_percent"

if not weather.empty:

    for column in [
        temperature_column,
        rainfall_column,
        humidity_column
    ]:

        if column in weather.columns:
            weather[column] = pd.to_numeric(
                weather[column], errors="coerce"
            )


# ==========================================
# STEP 5: SIDEBAR FILTERS
# ==========================================

st.sidebar.divider()
st.sidebar.header("Dashboard Filters")

selected_crop = st.sidebar.selectbox(
    "Select Crop",
    ["All"] + sorted(
        data["crop"].dropna().astype(str).unique().tolist()
    )
)

selected_location = st.sidebar.selectbox(
    "Select Location",
    ["All"] + sorted(
        data["location"].dropna().astype(str).unique().tolist()
    )
)

selected_season = st.sidebar.selectbox(
    "Select Season",
    ["All"] + sorted(
        data["season"].dropna().astype(str).unique().tolist()
    )
)


# Apply filters

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
# STEP 6: PERFORMANCE INDICATORS
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
# STEP 7: CROP-WISE YIELD COMPARISON
# ==========================================

st.subheader("Crop-wise Yield Comparison")

yield_by_crop = filtered.groupby(
    "crop",
    as_index=False
)["yield_per_hectare"].mean()

fig1 = px.bar(
    yield_by_crop,
    x="crop",
    y="yield_per_hectare",
    color="crop",
    title="Average Yield per Hectare by Crop",
    labels={
        "crop": "Crop",
        "yield_per_hectare": "Average Yield (kg/hectare)"
    },
    text_auto=".0f"
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

st.divider()


# ==========================================
# STEP 8: FARM-WISE PERFORMANCE
# ==========================================

st.subheader("Farm Performance")

fig2 = px.bar(
    filtered,
    x="farm_name",
    y="gross_return_per_hectare",
    color="crop",
    title="Gross Return per Hectare",
    hover_data=["location"],
    labels={
        "farm_name": "Farm Name",
        "gross_return_per_hectare": "Gross Return (₹/hectare)"
    }
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

st.divider()


# ==========================================
# STEP 9: INPUT COST VS GROSS RETURN
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
        "input_cost_per_hectare": "Input Cost (₹/hectare)",
        "gross_return_per_hectare": "Gross Return (₹/hectare)"
    }
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

st.divider()


# ==========================================
# STEP 10: WEATHER ANALYTICS
# ==========================================

st.subheader("🌦️ Weather Analytics")

if weather.empty:

    st.warning("No weather observations are available.")

elif temperature_column not in weather.columns:

    st.warning("Temperature data is not available in the weather table.")

else:

    weather_filtered = weather.copy()

    if "farm_id" in weather_filtered.columns:

        selected_farm_ids = filtered["farm_id"].unique()

        weather_filtered = weather_filtered[
            weather_filtered["farm_id"].isin(selected_farm_ids)
        ]

    if selected_crop != "All" and "crop" in weather_filtered.columns:

        weather_filtered = weather_filtered[
            weather_filtered["crop"] == selected_crop
        ]

    if selected_season != "All" and "season" in weather_filtered.columns:

        weather_filtered = weather_filtered[
            weather_filtered["season"] == selected_season
        ]

    if not weather_filtered.empty:

        weather_col1, weather_col2, weather_col3 = st.columns(3)

        weather_col1.metric(
            "Average Temperature",
            f"{weather_filtered[temperature_column].mean():.1f} °C"
        )

        if rainfall_column in weather_filtered.columns:

            weather_col2.metric(
                "Total Recorded Rainfall",
                f"{weather_filtered[rainfall_column].sum():,.1f} mm"
            )

        if humidity_column in weather_filtered.columns:

            weather_col3.metric(
                "Average Humidity",
                f"{weather_filtered[humidity_column].mean():.1f}%"
            )

        if "date" in weather_filtered.columns:

            weather_filtered["date"] = pd.to_datetime(
                weather_filtered["date"], errors="coerce"
            )

            temperature_trend = weather_filtered.dropna(
                subset=["date", temperature_column]
            )

            if not temperature_trend.empty:

                temperature_trend = temperature_trend.groupby(
                    "date", as_index=False
                )[temperature_column].mean()

                fig4 = px.line(
                    temperature_trend,
                    x="date",
                    y=temperature_column,
                    title="Daily Average Temperature Trend",
                    labels={
                        "date": "Date",
                        temperature_column: "Temperature (°C)"
                    }
                )

                st.plotly_chart(
                    fig4,
                    use_container_width=True
                )

        if rainfall_column in weather_filtered.columns:

            if "farm_name" in weather_filtered.columns:

                rainfall_by_farm = weather_filtered.groupby(
                    "farm_name",
                    as_index=False
                )[rainfall_column].sum()

                fig5 = px.bar(
                    rainfall_by_farm,
                    x="farm_name",
                    y=rainfall_column,
                    title="Total Recorded Rainfall by Farm",
                    labels={
                        "farm_name": "Farm",
                        rainfall_column: "Rainfall (mm)"
                    }
                )

                st.plotly_chart(
                    fig5,
                    use_container_width=True
                )

    else:

        st.info("No weather records match the selected filters.")

st.caption(
    "Weather values are historical gridded estimates from Open-Meteo, "
    "not direct measurements from individual farm weather stations."
)

st.divider()


# ==========================================
# STEP 11: SEASONAL COMPARISON
# ==========================================

st.subheader("Seasonal Crop Comparison")

season_data = filtered[
    filtered["season"].notna()
].copy()

if not season_data.empty:

    seasonal_yield = season_data.groupby(
        ["season", "crop"],
        as_index=False
    )["yield_per_hectare"].mean()

    fig6 = px.bar(
        seasonal_yield,
        x="season",
        y="yield_per_hectare",
        color="crop",
        barmode="group",
        title="Average Crop Yield Across Seasons",
        labels={
            "season": "Season",
            "yield_per_hectare": "Average Yield (kg/hectare)"
        },
        text_auto=".0f"
    )

    st.plotly_chart(
        fig6,
        use_container_width=True
    )

else:

    st.info("Seasonal data is not available.")


st.divider()


# ==========================================
# STEP 12: FARM-WISE AGRICULTURAL RECORDS
# ==========================================

st.subheader("Farm-wise Agricultural Records")

st.dataframe(
    filtered,
    use_container_width=True
)


# ==========================================
# STEP 13: DECISION SUPPORT INDICATORS
# ==========================================

st.divider()

st.subheader("🌱 Decision Support Indicators")

best_yield = filtered.loc[
    filtered["yield_per_hectare"].idxmax()
]

best_return = filtered.loc[
    filtered["gross_return_per_hectare"].idxmax()
]

decision_col1, decision_col2 = st.columns(2)

with decision_col1:

    st.markdown("**Highest Yield Record**")

    st.write(
        f"Farm: {best_yield['farm_name']}"
    )

    st.write(
        f"Crop: {best_yield['crop']}"
    )

    st.write(
        f"Yield: {best_yield['yield_per_hectare']:,.0f} kg/ha"
    )

with decision_col2:

    st.markdown("**Highest Gross Return Record**")

    st.write(
        f"Farm: {best_return['farm_name']}"
    )

    st.write(
        f"Crop: {best_return['crop']}"
    )

    st.write(
        f"Gross Return: ₹{best_return['gross_return_per_hectare']:,.0f}/ha"
    )

st.info(
    "These indicators identify the highest observed values in the "
    "selected records. They do not establish that a crop or farming "
    "practice caused better performance."
)


# ==========================================
# STEP 14: DATA QUALITY
# ==========================================

st.divider()

st.subheader("Data Quality")

if "incomplete_cycle" in filtered.columns:

    incomplete_count = int(
        filtered["incomplete_cycle"].fillna(False).astype(bool).sum()
    )

    st.write(
        "Incomplete crop cycles:",
        incomplete_count
    )

else:

    st.write("Incomplete crop cycle field is not available.")

st.write(
    "Total crop records:",
    len(filtered)
)

st.write(
    "Total weather records:",
    len(weather)
)


# ==========================================
# STEP 15: FOOTER
# ==========================================

st.divider()

st.markdown(
    "🌱 Agricultural Decision Support System | "
    "Python | PostgreSQL | Streamlit | Plotly | Open-Meteo"
)
