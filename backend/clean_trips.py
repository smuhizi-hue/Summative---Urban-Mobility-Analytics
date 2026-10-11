import json
import pandas as pd
import config

def load_data():

    trips = pd.read_parquet(config.RAW_TRIPS_FILE)
    trips = trips.drop(columns=["airport_fee"])
    zones = pd.read_csv(config.CLEAN_ZONES_FILE)
    return trips, zones

def rename_columns(trips):

    trips = trips.rename(columns={

        "VendorID" : "vendor_id",
        "tpep_pickup_datetime" : "pickup_time",
        "tpep_dropoff_datetime" : "dropoff_time",
        "RatecodeID" : "rate_code_id",
        "PULocationID" : "pickup_zone_id",
        "DOLocation" : "dropoff_zone_id",
    })
    return trips

def add_duration_and_speed(trips):

    seconds = (trips["dropoff_time"] - trips["pickup_time"]).dt.total_seconds()
    trips["trip_duration_min"] = seconds / 60
    trips["avg_speed_mph"] = trips["trip_distance"] / (trips["trip_duration_min"] / 60)
    return trips



reason_names = []
reason_counts = {}

def mark(trips, reason, has_problem):

    reason_names.append(reason)
    rule_number = len(reason_names)

    not_marked_yet = trips["exclusion_code"] == 0
    newly_bad = has_problem & not_marked_yet

    reason_counts[reason] = int(newly_bad.sum())
    print(f" {reason:35s} {reason_counts[reason]:>9,} rows")

def apply_rules(trips, zones):
    trips["exclusion_code"] = 0
    start = pd.Timestamp(config.START_DATE)
    end = pd.Timestamp(config.END_DATE)

    # missing values
    mark(trips, "missing_required_values",
         trips[[
             "vendor_id", "pickup_time", "dropoff_time" , "trip_distance", "fare_amount", "extra", "mta_tax", "tip_amount", "tolls_amount", "improvement_surcharge", "total_amount"
         ]].isna().any(axis=1))

    # time problems
    mark(trips, "pickup_outside_january_2019",
         (trips["pickup_time"] < start ) | (trips["pickup_time"] >= end))
    mark(trips, "dropoff_not_after_pickup",
         trips["trip_duration_min"] <= 0)
    mark(trips, "trip_shorter_than_min",
         trips["trip_duration_min"] < config.MIN_TRIP_MINUTES)
    mark(trips, "trip_longer_than_max",
         trips["trip_duration_min"] > config.MAX_TRIP_MINUTES)
    
    # distance problems
    mark(trips, "distance_too_short",
         trips["trip_distance"] < config.MIN_DISTANCE_MILES)
    mark(trips, "distance_too_long",
         trips["trip_distance"] > config.MAX_DISTANCE_MILES)

    # money problems
    money_columns = ["fare_amount", "extra", "mta_tax", "tip_amount", "tolls_amount", "improvement_surcharge", "total_amount"]

    mark(trips, "negative_money_value",
         (trips[money_columns] < 0).any(axis=1))
    mark(trips, "fare_too_low",
         trips["fare_amount"] < config.MIN_FARE)
    mark(trips, "fare_too_high",
         trips["fare_amount"] > config.MAX_FARE)

    mark(trips, "fare_per_mile_too_high",
         trips["fare_amount"] / trips["trip_distance"] >
         config.MAX_FARE_PER_MILE)
    mark(trips, "tip_too_high",
         trips["tip_amount"] > config.MAX_TIP)
    mark(trips,
         trips["tolls_amount"] > config.MAX_TOLLS)

    # more invalid values
    mark(trips, "passenger_count_invalid",
         (trips["passenger_count"] < config.MIN_PASSENGERS) | (trips["passenger_count"] > config.MAX_PASSENGERS))
    mark(trips, "rate_code_invalid",
         ~trips["rate_code_id"].isin(list(config.RATE_CODES.keys())))
    mark(trips, "zone_id_not_in_lookup",
         ~trips["pickup_zone_id"].isin(zones["zone_id"]) | ~trips["dropoff_zone_id"].isin(zones["zone_id"]))
    mark(trips, "speed_impossible",
         trips["avg_speed_mph"] > config.MAX_SPEED_MPH)

    # duplicates
    same_trip_columns = ["vendor_id", "pickup_time", "dropoff_time", "pickup_zone_id", "dropoff_zone_id", "total_amount"]
    mark(trips, "duplicate_trip", trips.duplicated(subset=same_trip_columns, keep="first"))

    return trips


def standardise(trips):
    for column in ["vendor_id", "passenger_count", "rate_code_id"]:
        trips[column] = trips[column].astype(int)

    trips["congestion_surcharge"] = trips["congestion_surcharge"].fillna(0)

    money_columns = ["fare_amount", "extra", "mta_tax", "tip_amount", "tolls_amount", "improvement_surcharge", "total_amount", "congestion_surcharge"]

    for column in money_columns + ["trip_distance", "trip_duration_min", "avg_speed_mph"]:
        trips[column] = trips[column].round(2)

    return trips

def add_features(trips, zones):

    trips["fare_per_mile"] = (trips["tare_amount"] / trips["trip_distance"]).round(2)

    trips["tip_percent"] = (trips["tip_amount"] / trips["fare_amount"] * 100).round(2)
    not_credit_card = trips["payment_type"] != 1
    trips.loc[not_credit_card, "tip_percent"] = None

    # time features
    trips["pickup_hour"] = trips["pickup_time"].dt.hour
    trips["pickup_day_of_week"] = trips["pickup_time"].dt.dayofweek
    trips["is_weekend"] = trips["pickup_day_of_week"] >= 5

    # using the zone table to look up borough names and airports
    borough_of_zone = dict(zip(zones["zone_id"], zones["borough"]))
    pickup_borough = trips["pickup_zone_id"].map(borough_of_zone)
    dropoff_borough = trips["dropoff_zone_id"].map(borough_of_zone)

    #cross_borough
    trips["is_cross_borough"] = pickup_borough != dropoff_borough

    # is_airport_trip = True if it starts or stops at an airports
    airport_zones = zones[zones["zone_name"].str.contains("Airport")]
    airport_ids = list(airport_zones["zone_id"])
    trips["is_airport_trip"] = (trips["pickup_zone_id"].isin(airport_ids)) | trips["dropoff_zone_id"].isin(airport_ids)

    return trips

def flag_suspicious(trips):

    parts = (trips["fare_amount"] + trips["extra"] + trips["mta_tax"] + trips["tip_amount"] + trips["tolls_amount"] + trips["improvement_surcharge"] + trips["congestion_surcharge"])
    difference = (trips["total_amount"] - parts).abs()
    trips["is_suspicious"] = difference > 1.00

    return trips

def main():
    print("Loading data...")
    trips, zones = load_data()
    rows_raw = len(trips)
    print(f"{rows_raw:,} raw trips, {len(zones)} zones \n")

    trips = rename_columns(trips)
    trips = add_duration_and_speed(trips)

    print("Checking the rules (each row is counted for the first rule it breaks):")
    trips = apply_rules(trips, zones)

    # split into bad rows
    is_bad = trips["exclusion_code"] != 0
    excluded = trips[is_bad].copy()
    excluded["exclusion_reason"] = excluded["exclusion_code"].map(lambda code: reason_names[code - 1])
    excluded = excluded.drop(columns=["exclusion_code"])
    excluded.to_csv(config.EXCLUDED_LOG_FILE, index = False)
    print(f"\nSaved {len(excluded):,} excluded rows to {config.EXCLUDED_LOG_FILE}")

    clean = trips[~is_bad]
    del trips
    clean = clean.drop(columns=["exclusion_code"])

    clean = standardise(clean)
    clean = add_features(clean, zones)
    clean = flag_suspicious(clean)

    clean = clean.sort_values("pickup_time").reset_index(drop=True)
    clean.insert(0, "trip_id", clean.index + 1)
    clean.to_parquet(config.CLEAN_TRIPS_FILE, index=False)

    summary = {
        "rows_raw" : rows_raw,
        "rows_excluded" : len(excluded),
        "rows_clean" : len(clean),
        "percent_kept" : round(len(clean) / rows_raw * 100, 2),
        "excluded_by_reason" : reason_counts,
        "suspicious_rows_kept" : int(clean["is_suspicious"].sum()),
        "median_trip_minutes" : round(clean["trip_duration_min"].median(), 2),
        "median_trip_miles" : round(clean["trip_distance"].median(), 2),
        "median_fare_per_mile" : round(clean["fare_per_mile"].median(), 2),
        "median_tip_percent_credit_card": round(clean["tip_percent"].median(), 2),
    }

    with open(config.SUMMARY_FILE, "w") as file:
        json.dump(summary, file, indent=2)

    print(f"Saved {len(clean):,} clean rows to {config.CLEAN_TRIPS_FILE}")
    print(f"Kept {summary['percent_kept']}% of the data.Summary: {config.SUMMARY_FILE}")

if __name__ == "__main__":
    main()


