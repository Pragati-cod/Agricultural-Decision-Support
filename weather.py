
import pandas as pd
import requests
import os
import time

# ==========================================
# STEP 1: PROJECT PATHS
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATA_DIR = os.path.join(BASE_DIR, "data")

OUTPUT_FILE = os.path.join(
    DATA_DIR, "weather_data.csv"
)

# ==========================================
# STEP 2: LOAD AGRICULTURAL DATA
# ==========================================

farms = pd.read_csv(
    os.path.join(DATA_DIR, "farms.csv")
)

calendar = pd.read_csv(
    os.path.join(DATA_DIR, "crop_calendar.csv")
)

harvest = pd.read_csv(
    os.path.join(DATA_DIR, "harvest.csv")
)

# Combine farm and crop cycle information

cycles = calendar.merge(
    farms,
    on="farm_id",
    how="inner"
)

cycles = cycles.merge(
    harvest[["farm_id", "crop", "harvest_date"]],
    on=["farm_id", "crop"],
    how="left"
)

cycles["sowing_date"] = pd.to_datetime(
    cycles["sowing_date"]
)

cycles["harvest_date"] = pd.to_datetime(
    cycles["harvest_date"]
)

# ==========================================
# STEP 3: OPEN-METEO API CONFIGURATION
# ==========================================

API_URL = "https://archive-api.open-meteo.com/v1/archive"

weather_records = []

# ==========================================
# STEP 4: COLLECT WEATHER FOR EACH FARM
# ==========================================

for index, farm in cycles.iterrows():

    farm_id = farm["farm_id"]
    farm_name = farm["farm_name"]

    latitude = farm["latitude"]
    longitude = farm["longitude"]

    start_date = farm["sowing_date"].strftime(
        "%Y-%m-%d"
    )

    end_date = farm["harvest_date"].strftime(
        "%Y-%m-%d"
    )

    print(f"\nCollecting weather for {farm_name}...")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,

        "daily": (
            "temperature_2m_mean,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_sum,"
            "relative_humidity_2m_mean"
        ),

        "timezone": "auto",

        # ERA5 supports historical precipitation data
        "models": "era5"
    }

    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=120
        )

        response.raise_for_status()

        result = response.json()

        daily = result.get("daily", {})

        if not daily or not daily.get("time"):

            print("No weather data returned.")
            continue

        farm_weather = pd.DataFrame({

            "date": daily["time"],

            "temperature_mean":
                daily["temperature_2m_mean"],

            "temperature_max":
                daily["temperature_2m_max"],

            "temperature_min":
                daily["temperature_2m_min"],

            "rainfall_mm":
                daily["precipitation_sum"],

            "humidity_percent":
                daily["relative_humidity_2m_mean"]

        })

        # Add farm information

        farm_weather["farm_id"] = farm_id

        farm_weather["farm_name"] = farm_name

        farm_weather["location"] = farm["location"]

        farm_weather["crop"] = farm["crop"]

        farm_weather["season"] = farm["season"]

        farm_weather["latitude"] = latitude

        farm_weather["longitude"] = longitude

        weather_records.append(farm_weather)

        print(
            f"Successfully collected "
            f"{len(farm_weather)} daily records."
        )

    except requests.exceptions.RequestException as error:

        print(
            f"API request failed for {farm_name}: {error}"
        )

    except (KeyError, TypeError, ValueError) as error:

        print(
            f"Data processing failed for {farm_name}: {error}"
        )

    time.sleep(1)

# ==========================================
# STEP 5: COMBINE WEATHER RECORDS
# ==========================================

if weather_records:

    weather_data = pd.concat(
        weather_records,
        ignore_index=True
    )

    weather_data["date"] = pd.to_datetime(
        weather_data["date"]
    )

    weather_data = weather_data.drop_duplicates(
        subset=["farm_id", "crop", "date"]
    )

    # ======================================
    # STEP 6: DATA QUALITY CHECK
    # ======================================

    print("\nWEATHER DATA QUALITY CHECK")

    print(
        "Missing rainfall values:",
        weather_data["rainfall_mm"].isna().sum()
    )

    print(
        "Missing temperature values:",
        weather_data["temperature_mean"].isna().sum()
    )

    print(
        "Rainfall records above zero:",
        (weather_data["rainfall_mm"] > 0).sum()
    )

    # ======================================
    # STEP 7: SAVE WEATHER DATA
    # ======================================

    weather_data.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n===================================")

    print("WEATHER DATA COLLECTION COMPLETED")

    print("===================================")

    print(
        "Total weather records:",
        len(weather_data)
    )

    print(
        "Total farms:",
        weather_data["farm_id"].nunique()
    )

    print("\nAverage Temperature:")

    print(
        weather_data["temperature_mean"].mean()
    )

    print("\nTotal Rainfall:")

    print(
        weather_data["rainfall_mm"].sum(),
        "mm"
    )

    print("\nGenerated File:")

    print("data/weather_data.csv")

    print("\nAll operations completed!")

else:

    print(
        "\nNo weather records collected. "
        "Check internet connection and API response."
    )
