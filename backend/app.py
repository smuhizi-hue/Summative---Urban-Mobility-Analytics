import json
import os 
import threading
from flask import Flask, jsonify, request, send_from_directory

import config
from  db import run_query
from filters import build_where
from algorithms import top_zones
from config import TIP_PERCENT_SQL

FRONTEND_FOLDER = os.path.join(config.BASE_DIR, "frontend")
app = Flask(__name__, static_folder=FRONTEND_FOLDER, static_url_path="")
cache ={}
zone_cache ={}

def cached(function):
    def wrapper(*args, **kwargs):
        key = (request.path, tuple(sorted(request.args.items())))
        if  key not in cache:
            if len(cache) > 300:
                cache.clear()
            cache[key] = function(*args, **kwargs)
        return cache[key]
    wrapper.__name__  = function.__name__
    return wrapper

    #Using total tips.
    TIP_PERCENT_SQL = "ROUND(100.0 * SUM(tip_amount) / NULLIF(SUM(fare_amount), 0), 1)"

#page
@app.route("/")
def home():
    return send_from_directory(FRONTEND_FOLDER, "index.html")

@app.route("/api/options")
@cached
def options():
    venders = run_query(
        "SELECT vendor_id, vendor_name FROM vendors ORDER BY vendor_name"
    )
    boroughs = run_query("SELECT borough_name FROM boroughs"
                        "WHERE borough_name <> 'Unknown' ORDER BY borough_name")
    payment  = run_query("SELECT payment_type_id, payment_type_name FROM payment_types "
                        "WHERE payment_type_id IN (1, 2, 3, 4)")
    dates = run_query("SELECT MIN(pickup_date) AS first_day, MAX(pickup_date) AS last_day FROM trips")
    return jsonify({ "boroughs":[b["borough_name"] for b in boroughs],
                    "payment_types": payment,
                    "first_day": dates[0]["first_day"],                     
                    "last_day": dates[0]["last_day"]})

@app.route("/api/kpis")
@cached
def kpis():
    where, params = build_where(request.args)
    sql  = f"""SELECT COUNT(*) AS trips,
                      ROUND(AVG(fare_amount), 2) AS avg_fare,
                      ROUND(AVG(trip_distance), 2) AS avg_distance,
                      ROUND(AVG(trip_duration_min), 1) AS avg_minutes,
                      ROUND(AVG(avg_speed_mph), 1) AS avg_speed,
                      {TIP_PERCENT_SQL} AS tip_percent
                FROM trips {where}"""
    return jsonify(run_query(sql, params)[0])


@app.route("/api/hourly")
@cached
def hourly():
    """Trips, speed, fare and tips for each hour of the day (weekday and weekend apart)."""
    where, params = build_where(request.args)
    sql = f"""SELECT pickup_hour AS hour, is_weekend,
                     COUNT(*) AS trips,
                     ROUND(AVG(avg_speed_mph), 2) AS avg_speed,
                     ROUND(AVG(fare_amount), 2) AS avg_fare
              FROM trips {where}
              GROUP BY pickup_hour, is_weekend 
              ORDER BY pickup_hour"""
    return jsonify(run_query(sql, params))  
    
@app.route("/api/daily")
@cached
def daily():
    where, params = build_where(request.args)
    sql = f"""SELECT pick_data AS day, COUNT(*) AS trips, ROUND(AVG(fare_amount), 2) AS avg_fare
              FROM trips {where}
              GROUP BY pickup_date ORDER BY pickup_date"""
    return jsonify(run_query(sql, params))

@app.route("/api/payments")
@cached
def payments():
    where, params = build_where(request.args)
    sql = f"""SELECT p.payment_name AS name, COUNT(*) AS  trips
              FROM trips JOIN payment_types p ON trips.payment_type_id = p.payment_type_id
              {where}
              GROUP BY p.payment_type_name ORDER BY trips DESC"""
    return jsonify(run_query(sql, params))

#zones and route
def get_zone_stats(args):
    """One row per pickup zone with its number (used by the map and by the ranking)."""
    where, params = build_where(args)
    key = (where, tuple(params))
    if key in zone_cache:
        return zone_cache[key]

    # Force a sequential scan for global aggreations to  avoid slow index lookups.
    #Keep the index active when filtering by a specific zone_id.
    hint = "" if args.get("zone_id") else "IGNORE INDEX (idx_trips_route)"
    sql = f"""SELECT trips.pickup_zone_id AS zone_id, z.zone_name, b.borough_name AS borough,
                      COUNT(*) AS pickups,
                      ROUND(AVG(fare_amount), 2) AS avg_fare,
                      ROUND(AVG(trip_distance), 2) AS  avg_distance,
                      ROUND(AVG(avg_speed_mph), 2) AS avg_speed,
                      {TIP_PERCENT_SQL} AS tip_percent

              FROM trips {hint}
              JOIN zones z ON trips.pickup_zone_id = z.zone_id
              JOIN boroughs b ON z.borough_id = b.borough_id
              {where}     
              GROUP BY trips.pickup_zone_id, z.zone_name, b.borough_name"""
    zone_cache[key] = run_query(sql, params)
    return zone_cache[key]

@app.route("/api/zones/stats")
@cached
def zone_status():
    return jsonify(get_zone_stats(request.args))

@app.route("/api/zones/top")
@cached
def zones_top():
    """Top zones for a metric. the ranking is done by OUR merge sort (algorithms.py). """
    metric = request.args.get("metric", "pickups")
    allowed = ["pickups", "avg_fare", "avg_distance", "tip_percent"]
    if metric not in allowed:
        return jsonify({"error": "unknown metric"}), 400

    how_many = int(request.orgs.get("n", 10))
    stats = get_zone_stats(request.args)
    return jsonify(top_zones(stats, metric, how_many, 200))

@app.route("/api/zones/shapes")
def zones_shapes():
    with open(config.CLEAN_ZONE_SHAPES_FILE) as file:
         return jsonify(json.load(file))

@app.route("/api/routes/top")
@cached
def routes_top():
    """The most common pickup -> droff pairs."""
    where, params = build_where(request.args)
    how_many = min(int(request.args.get("n", 10)), 50)
#step 1 inner query
#step 2 outer query
    sql = f"""SELECT zp.zone_name AS pickup_zone, zd.zone_name AS dropoff_zone, t.trips
         FROM (SELECT pickup_zone_id, dropoff_zone_id, COUNT(*) AS trips
                FROM trips {where}
                GROUP  BY pickup_zone_id, dropoff_zone_id
                ORDER BY trips DESC LIMIT {how_many}) t
        JOIN zones zp ON t.pickup_zone_id = zp.zone_id
        JOIN zones zd  ON t.dropoff_zone_id = zd.zone_id
        ORDER BY t.trips DESC"""
    return  jsonify(run_query(sql, params))

#detail the table
@app.route("/api/trips")
@cached 
def trips_list():
    """ A page of individual trips, with sorting."""
   
        # We cannot use %s for a column name, so we only accept names from this safe list.
    sortable = ["pickup_time", "trip_distance", "fare_amount", "tip_amount",
                "total_amount", "trip_duration_min", "avg_speed_mph"]
    sort_by = request.args.get("sort_by", "pickup_time")
    if sort_by not in sortable:
        sort_by = "pickup_time"
    direction = "ASC" if request.args.get("order") == "asc" else "DESC"

    page = max(int(request.args.get("page", 1)), 1)
    per_page = 15
    offset = (page - 1) * per_page

    where = ""
    params = []

    total = run_query(f"SELECT COUNT(*) AS total FROM trips {where}", params)[0]["total"]
    # Step 1 (inner query): find just the 15 trips of this page (fast, can use an index).
    # Step 2 (outer query): add the zone names and payment names for those 15 trips only.
    sql = f"""SELECT t.trip_id, t.pickup_time, zp.zone_name AS pickup_zone, zd.zone_name AS dropoff_zone,
                     t.trip_distance, t.trip_duration_min, t.avg_speed_mph, t.fare_amount,
                     t.tip_amount, t.total_amount, p.payment_type_name AS payment
              FROM (SELECT trip_id, pickup_time, pickup_zone_id, dropoff_zone_id, payment_type_id,
                           trip_distance, trip_duration_min, avg_speed_mph, fare_amount,
                           tip_amount, total_amount
                    FROM trips {where}
                    ORDER BY {sort_by} {direction}
                    LIMIT {per_page} OFFSET {offset}) t
              JOIN zones zp ON t.pickup_zone_id = zp.zone_id
              JOIN zones zd ON t.dropoff_zone_id = zd.zone_id
              JOIN payment_types p ON t.payment_type_id = p.payment_type_id
              ORDER BY t.{sort_by} {direction}"""
    rows = run_query(sql, params)
    return jsonify({"total": total, "page": page, "per_page": per_page, "rows": rows})


#  data quality
@app.route("/api/cleaning-report")
@cached
def cleaning_report():
    reasons = run_query("SELECT reason, rows_removed FROM cleaning_log ORDER BY rows_removed DESC")
    kept = run_query("SELECT COUNT(*) AS kept FROM trips")[0]["kept"]
    suspicious = run_query("SELECT COUNT(*) AS n FROM trips WHERE is_suspicious = 1")[0]["n"]
    removed = sum(r["rows_removed"] for r in reasons)
    return jsonify({"rows_kept": kept, "rows_removed": removed, "suspicious_kept": suspicious,
                    "percent_kept": round(kept / (kept + removed) * 100, 2),
                    "reasons": reasons})


def warm_up_cache():

    client = app.test_client()
    for url in ["/api/options", "/api/kpis", "/api/hourly", "/api/daily", "/api/payments",
                "/api/zones/stats", "/api/zones/top?metric=pickups&n=10", "/api/routes/top?n=10",
                "/api/trips?page=1&sort_by=pickup_time&order=desc", "/api/cleaning-report"]:
        client.get(url)
    print("Cache is warm - the dashboard will open instantly.")


if __name__ == "__main__":
    threading.Thread(target=warm_up_cache, daemon=True).start()
    app.run(debug=False, threaded=True)

