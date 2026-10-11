import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # this is the main project folder

# Defining paths
RAW_TRIPS_FILE = os.path.join(BASE_DIR, "data", "raw,","yellow_tripdata_2019-01")
RAW_ZONE_LOOKUP_FILE = os.path.join(BASE_DIR, "data","raw", "taxi_zone_lookup.csv")
RAW_ZONE_SHAPES_FILE = os.path.join(BASE_DIR, "data", "raw", "taxi_zones.json" )

CLEAN_ZONES_FILE = os.path.join(BASE_DIR, "data","processed", "zones.csv")
CLEAN_ZONE_SHAPES_FILE = os.path.join(BASE_DIR, "data","processed", "zones.geojson")
CLEAN_TRIPS_FILE = os.path.join(BASE_DIR, "data", "processed", "trips_clean.parquet")

EXCLUDED_LOG_FILE = os.path.join(BASE_DIR, "logs", "excluded_records.csv")
SUMMARY_FILE = os.path.join(BASE_DIR, "logs", "cleaning_summary.json")