
import pandas as pd
from pathlib import Path
from getpass import getpass
from sqlalchemy import create_engine, URL, text

# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# PostgreSQL configuration
DB_USER = "postgres"
DB_PASSWORD = getpass("Enter your PostgreSQL password: ")

DB_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host="localhost",
    port=5432,
    database="agricultural_db"
)

# Create database connection
engine = create_engine(DB_URL)

# CSV files and their PostgreSQL table names
datasets = {
    "farms": BASE_DIR / "data" / "farms.csv",
    "soil_tests": BASE_DIR / "data" / "soil_tests.csv",
    "crop_calendar": BASE_DIR / "data" / "crop_calendar.csv",
    "input_usage": BASE_DIR / "data" / "input_usage.csv",
    "harvest": BASE_DIR / "data" / "harvest.csv",
    "market_prices": BASE_DIR / "data" / "market_prices.csv",
    "weather_data": BASE_DIR / "data" / "weather_data.csv",
    "clean_crop_cycles": BASE_DIR / "reports" / "clean_crop_cycles.csv",
    "weather_integrated_crop_cycles": BASE_DIR / "reports" / "weather_integrated_crop_cycles.csv",
    "crop_performance": BASE_DIR / "reports" / "crop_performance.csv",
    "farm_performance": BASE_DIR / "reports" / "farm_performance.csv",
    "data_quality_report": BASE_DIR / "reports" / "data_quality_report.csv"
}

print("\n===================================")
print("AGRICULTURAL DATABASE LOADER")
print("===================================")

try:
    # Test database connection
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    print("\nPostgreSQL connection successful!")

    successful_tables = 0

    # Import each CSV file
    for table_name, file_path in datasets.items():

        print(f"\nLoading table: {table_name}")

        if not file_path.exists():
            print("File not found. Skipping:", file_path)
            continue

        # Read CSV
        df = pd.read_csv(file_path)

        # Convert date columns
        date_columns = [
            "date",
            "test_date",
            "sowing_date",
            "harvest_date",
            "expected_harvest_date",
            "price_date"
        ]

        for column in date_columns:
            if column in df.columns:
                df[column] = pd.to_datetime(
                    df[column], errors="coerce"
                )

        # Upload data to PostgreSQL
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists="replace",
            index=False
        )

        print("Successfully imported:", len(df), "records")
        successful_tables += 1

    # Verify imported tables
    print("\n===================================")
    print("DATABASE IMPORT SUMMARY")
    print("===================================")

    with engine.connect() as connection:

        for table_name in datasets:

            if table_name in [
                "farms", "soil_tests", "crop_calendar",
                "input_usage", "harvest", "market_prices",
                "weather_data", "clean_crop_cycles",
                "weather_integrated_crop_cycles",
                "crop_performance", "farm_performance",
                "data_quality_report"
            ]:

                result = connection.execute(
                    text(f'SELECT COUNT(*) FROM "{table_name}"')
                )

                count = result.scalar()

                print(f"{table_name}: {count} records")

    print("\nTables successfully imported:", successful_tables)
    print("\nDATABASE LOADING COMPLETED!")

except Exception as error:
    print("\nDATABASE CONNECTION OR IMPORT FAILED!")
    print("Error:", error)

finally:
    engine.dispose()
