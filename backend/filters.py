# This, here below, turns the filters chosen on the dashboard.

def build_where(args):

    conditions = []
    params = []

    # when
    if args.get("start_date"):
        conditions.append("trips.pickup_date >= %s")
        params.append(args["start_date"])

    if args.get("end_date"):
        conditions.append("trips.pickup_date <= %s")
        params.append(args["end_date"])

    if args.get("hour_from"):
        conditions.append("trips.pickup_hour >= %s")
        params.append(int(args["hour_from"]))

    if args.get("hour_to"):
        conditions.append("trips.pickup_hour <= %s")
        params.append(int(args["hour_to"]))

    if args.get("day_type") == "weekday":
        conditions.append("trips.is_weekend = 0")

    if args.get("day_type") == "weekend":
        conditions.append("trips.is_weekend = 1")

    # where
    if args.get("borough"):
        conditions.append(
            "trips.pickup_zone_id IN (SELECT z.zone_id FROM zones z" 
            "JOIN boroughs b ON z.borough_id = b.borough_id" 
            "WHERE b.borough_name = %s")
        params.append(args["borough"])

    if args.get("zone_id"):
        conditions.append("trips.pickup_zone = %s")
        params.append(int(args["zone_id"]))

    if args.get("airport_only") == "1":
        conditions.append("trips.is_airport_trip = 1")

    # Trip size and price
    if args.get("min_distance"):
        conditions.append("trips.trip_distance >= %s")
        params.append(float(args["min_distance"]))

    if args.get("max_distance"):
        conditions.append("trips.trip_distance <= %s")
        params.append(float(args["max_distance"]))

    if args.get("min_fare"):
        conditions.append("trips.fare_amount >= %s")
        params.append(float(args["min_fare"]))

    if args.get("max_fare"):
        conditions.append("trips.fare_amount <= %s")
        params.append(float(args["max_fare"]))

    if args.get("payment_type"):
        conditions.append("trips.payment_type_id = %s")
        params.append(int(args["payment_type"]))

    if args.get("hide_suspicious") == "1":
        conditions.append("trips.is_suspicious = 0")

    if len(conditions)  == 0:
        return "", []
    return " WHERE " + " AND ".join(conditions), params