#indexes.sql : makes the dashboard queries fast.

USE nyc_taxi;


CREATE INDEX idx_trips_pickup_time  ON trips (pickup_time);
CREATE INDEX idx_trips_pickup_date  ON trips (pickup_date);
CREATE INDEX idx_trips_pickup_hour  ON trips (pickup_hour);
CREATE INDEX idx_trips_distance     ON trips (trip_distance);
CREATE INDEX idx_trips_fare         ON trips (fare_amount);
CREATE INDEX idx_trips_route        ON trips (pickup_zone_id, dropoff_zone_id);