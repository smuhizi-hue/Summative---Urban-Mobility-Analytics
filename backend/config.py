import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # this is the main project folder
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Defining paths
RAW_TRIPS_FILE = os.path.join(BASE_DIR, "data", "raw","yellow_tripdata_2019-01.parquet")
RAW_ZONE_LOOKUP_FILE = os.path.join(BASE_DIR, "data","raw", "taxi_zone_lookup.csv")
RAW_ZONE_SHAPES_FILE = os.path.join(BASE_DIR, "data", "raw", "taxi_zones.json" )

CLEAN_ZONES_FILE = os.path.join(BASE_DIR, "data","processed", "zones.csv")
CLEAN_ZONE_SHAPES_FILE = os.path.join(BASE_DIR, "data","processed", "zones.geojson")
CLEAN_TRIPS_FILE = os.path.join(BASE_DIR, "data", "processed", "trips_clean.parquet")

EXCLUDED_LOG_FILE = os.path.join(BASE_DIR, "logs", "excluded_records.csv")
SUMMARY_FILE = os.path.join(BASE_DIR, "logs", "cleaning_summary.json")

# cleaning deficits

START_DATE = "2019-01-01"
END_DATE = "2019-02-01"

MIN_TRIP_MINUTES = 1
MAX_TRIP_MINUTES = 180

MIN_DISTANCE_MILES = 0.1
MAX_DISTANCE_MILES = 100

MIN_FARE = 2.5
MAX_FARE = 500

MAX_FARE_PER_MILE = 100
MAX_TIP =200
MAX_TOLLS =100

MAX_SPEED_MPH = 80

MIN_PASSENGERS = 1
MAX_PASSENGERS = 6


PAYMENT_TYPES = {
    0: "Unkown", 1: "Credit card", 2: "Cash", 3: "No charge", 4: "Dispute", 5: "Unknown", 6: "Voided trip",
}

RATE_CODES = {
    1: "Standard rate", 2: "JFK", 3: "Newark", 4: "Nassau or Westchester", 5: "Negotiated fare", 6: "Group ride", 
}

VENDORS = {
    1: "Creative Mobile Technologies",
    2: "VeriFone Inc.",
    3: "Other vendor(id 3)",
    4: "Other vendor(id 4)",
}

# MYSQL Connection

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "mobility_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME", "nyc_taxi")
SCHEMA_FILE = os.path.join(BASE_DIR, "database", "schema.sql")
INDEXES_FILE = os.path.join(BASE_DIR, "database", "indexes.sql")