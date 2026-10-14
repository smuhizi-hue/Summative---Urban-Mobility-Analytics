import json 
import pandas as pd 
import pymysql
import pyarrow.parquet as pq
import config
BATCH_Size = 20000

TRIP_COLUMNS = [

    "trip_id", "vendor_id", "pickup_time", "dropoff_time", "pickup_zone_id", "dropoff_zone_id", "rate_code_id", "payment_type_id", "passenger_count",
    "trip_distance", "store_and_fwd_flag", "fare_amount", "extra", "mta_tax",
    "tip_amount", "tolls_amount", "improvement_surcharge", "congestion_surcharge",
    "total_amount", "trip_duration_min", "avg_speed_mph", "fare_per_mile",
    "tip_percent", "pickup_date", "pickup_hour", "pickup_day_of_week", "is_weekend", "is_cross_borough", "is_airport_trip", "is_suspicious",
]

def run_sql_file(connection, path):
    with open(path, encoding="utf-8") as file:
        sql = file.read()
   
   
    statement = sql.split(";")
    cursor = connection.cursor()
    
    
    for statement in statement:
        if statement.strip():
            cursor.execute(statement)
    connection.commit()
    cursor.close()

def fill_lookup_tables(connection):
    zones = pd.read_csv(config.CLEAN_ZONES_FILE)
    cursor = connection.cursor()

    boroughs_names = sorted(zones["borough"].unique())
    for name in boroughs_names:
        cursor.execute("INSERT INTO boroughs (borough_name) VALUES (%s)", (name,))
    cursor.execute("SELECT borough_id, borough_name FROM boroughs")
    boroughs_id_of = {}
    for borough_id, boroughs_name in cursor.fetchall():
        boroughs_id_of[boroughs_name] = borough_id

    for _, row in zones.iterrows():
        lat = None if  pd.isna(row["center_lat"]) else float(row["center_lat"])
        lon = None if pd.isna(row["center_lon"]) else float(row["center_lon"])
        cursor.execute(
            "INSERT INTO zones VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (int(row["zone_id"]), row["zone_name"], boroughs_id_of[row["borough"]], row["service_zone"], lat, lon, bool(row["has_boundary"]))
            )
    

    for vendor_id, name in config.VENDORS.items():
        cursor.execute("INSERT INTO vendors VALUES (%s, %s)", (vendor_id, name))
    for code, name in config.PAYMENT_TYPES.items():
        cursor.execute("INSERT INTO payment_types VALUES (%s, %s)", (code, name))
    for code, name in config.RATE_CODES.items():
        cursor.execute("INSERT INTO rate_codes VaLUES (%s, %s)", (code, name))
    connection.commit()
    print("Lookup tables filled.")

def insert_trips(connection):
    parquet_file =pq.ParquetFile(config.CLEAN_TRIPS_FILE)
    total = parquet_file.metadata.num_rows

    sql = (
        "INSERT INTO trips(" + ",".join(TRIP_COLUMNS) +") VALUES (" + ", ".join(["%s"] * len(TRIP_COLUMNS)) + ") ON DUPLICATE KEY UPDATE trip_id=trips.trip_id"
    )

    cursor = connection.cursor()
    done = 0

    try:
        for piece in parquet_file.iter_batches(batch_size=BATCH_Size):
            batch = piece.to_pandas()
            batch = batch.rename(columns={"payment_type": "payment_type_id"})

            batch["pickup_date"] = batch["pickup_time"].dt.strftime("%Y-%m-%d")
            batch = batch[TRIP_COLUMNS].copy()

            batch["pickup_time"] = batch["pickup_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
            batch["dropoff_time"] = batch["dropoff_time"].dt.strftime("%Y-%m-%d %H:%M:%S")

            for column in ["is_weekend", "is_cross_borough", "is_airport_trip","is_suspicious"]:
                batch[column] = batch[column].astype(int)

            batch = batch.astype(object).where(batch.notna(), None)
            cursor.executemany(sql, batch.values.tolist())
            connection.commit()

            done += len(batch)
            print(f"Processed {done:,} / {total:,} trips", flush=True)
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()



def save_cleaning_log(connection):
    with open(config.SUMMARY_FILE) as file:
        summary = json.load(file)
    cursor = connection.cursor()
    for reason, count in summary["excluded_by_reason"].items():
        cursor.execute ("INSERT INTO cleaning_log VALUES (%s, %s)", (reason, count))
    connection.commit()
    print("Cleaning log saved.")


def main():

    connection = pymysql.connect(
        host=config.DB_HOST, 
        port=config.DB_PORT, 
        user=config.DB_USER, 
        password=config.DB_PASSWORD, 
        database=config.DB_NAME
        )

    try:
        print("Loading the complete trip data set...")
        insert_trips(connection)
        print("Trip loading finished succefully")

    finally:
        connection.close()
    


if __name__ == "__main__":
    main()