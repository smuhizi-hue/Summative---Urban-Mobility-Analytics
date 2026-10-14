import json
import os 
import threading
from flask import Flask, jsonify, request, send _from_directory

import config
from bd import run_query
from filters import run_query
from filters import build_where
from alogorithms import top_zones
from config import TIP_PERCENT_SQL

FRONTEND_FOLDER = os.path.join(config.BASE_DIR, "frontend")
app = Flask(__name__, static__folder=FRONTEND_FOLDER, static_url_path="")
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
    TIP_PERCENT_SQL = ("ROUND(100) * SUM(CASE  WHEN trips.payment_type_id - 1 THEN tip_amount END) "
                      "/SUM(CASE WHEN trips.payment_type_id = 1 THEN fare_amount END), 1)")


@app.route("/")
def home():
    return send_form_directory(FRONTEND_FOLDER, "index.html")

@app.route("/api/options")
@cached
def options():
    boroughs = run_query("SELECT borough_name FROM boroughs"
                        "WHERE borough_name <> 'Unknown' ORDER BY borough_name")
    payment  = run_query("SELECT payment_type_id, payment_type_name FROM payment_types "
                        "WHERE payment_type_id IN (1, 2, 3, 4)")
    dates = run_query("SELECT MIN(pickup_date) AS first_day, MAX(pickup_date) AS last_day FROM trips")
    return jsonify({"broughs": [b["borough_name"] for b in boroughs],
                    "payment_types": payments,
                    "first_day": dates[0]["first_day"],                     
                    "last_day": dates[0]["last_day"]})

@app.route("/api/kpis")
@cached
def kpis():
    where, params = build_where(request.args)
    sql  = f"""SELECT COUNT(*) AS trips,
                      ROUND(AVG(fare_amount), 2) AS avg_fare,
                      ROUND(AVG(trip_distance), 2) AS avg_disatnce,
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
    where params = build_where(request.args)
    sql = f"""SELECT pick_data AS day, COUNT(*) AS trips, ROUND(AVG(fare_amount), 2) AS avg_fare
              FROM trips {Where}
              GROUP BY pickup_date ORDER BY pickup_date"""
    return jsonify(run_query(sql, params))

@app.route("/api/payments")
@cached
def payments():
    where, params = build_where(request.args)
    sql = f"""SELECT p.payment_name AS name, COUN(*) AS  trips
              FROM trips JOIN payment_types p ON trips.payment_type_id = p.payment_type_id
              {where}
              GROUP BY p.payment_type_name ORDER BY trips DESC"""
    return jsonify(run_query(sql, params))


#zones and route
def get_zone_stats(args):
    """One row per pickup zone with its number (used by the map and by the ranking)."""
    where, params = build_where(args)
    key = (where, tuple(parms))
    if key in zone_cache:
        return zone_cache[key]

    # Force a sequential scan for global aggreations to  avoid slow index lookups.
    #Keep the index active when filtering by a specific zone_id.
    hint = "" if args.get("zone_id") else "IGNORE INDEX (idx_trips_route)"
    sql = f"""SELECT trips.pickup_zone_id AS zone_id, z.zone_name, b.borough_name AS borough,
                      COUNT(*) AS pickups,
                      FOUND(AVG(fare_amount), 2) AS avg_fare,
                      FOUND(AVG(trip_disatance), 2) AS  avg_disatance,
                      FOUND(AVG(avg_speed_mph), 2) AS avg_speed,
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
    return jsonify(get_zone_status(request.args))

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
    return jsonify(top_zones(status, metric how_many, 200))

@app.route("/api/zones/shapes")
def zones_shapes():
    with open(config.CLEAN_ZONE_SHAPES_FILE) as file:
         return jsonify(json.load(file))

@app.route("/api/routes/top")
@cached
def routes_top():
    """The most common pickup
