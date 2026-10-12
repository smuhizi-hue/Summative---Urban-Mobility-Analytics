Create DATABASE IF NOT EXISTS nyc_taxi CHARACTER SET utf8mb4;
Use nyc_taxi;

DROP TABLE IF EXISTS trips;
DROP TABLE IF EXISTS zones;
DROP TABLE IF EXISTS boroughs;
DROP TABLE IF EXISTS vendors;
DROP TABLE IF EXISTS payment_types;
DROP TABLE IF EXISTS rate_codes;
DROP TABLE IF EXISTS cleaning_log;


CREATE Table boroughs (
    borough_id    TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    borough_name VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE zones (
    zone_id       SMALLINT UNSIGNED NOT NULL PRIMARY KEY,
    zone_name     Varchar(80) NOT NULL,
    borough_id    TINYINT UNSIGNED NOT NULL,
    service_zone  VARCHAR(30) NOT NULL,
    centre_lat    DECIMAL(9,6) NULL,
    center_lon    DECIMAL(9,6) NULL,
    has_boundary  BOOLEAN NOT NULL,
    FOREIGN KEY (borough_id) REFERENCES boroughs (borough_id)
);

CREATE TABLE vendors (
    vendor_id     TINYINT UNSIGNED NOT NULL PRIMARY KEY,
    vendor_name   VARCHAR(50) NOT NULL
);

CREATE TABLE payment_types (
    payment_type_id     TINYINT UNSIGNED NOT NULL PRIMARY KEY,
    payment_type_name   VARCHAR(30) NOT NULL
);
CREATE TABLE rate_codes (
    rate_code_id    TINYINT UNSIGNED NOT NULL PRIMARY KEY,
    rate_code_name  VARCHAR(30) NOT NULL 
);

CREATE TABLE trips (
    trip_id              INT UNSIGNED NOT NULL PRIMARY KEY,
    vendor_id            TINYINT UNSIGNED NOT NULL,
    pickup_time          DATETIME NOT NULL,
    dropoff_time         DATETIME NOT NULL,
    pickup_zone_id       SMALLINT UNSIGNED NOT NULL,
    dropoff_zone_id      SMALLINT UNSIGNED NOT NULL,
    rate_code_id         TINYINT UNSIGNED NOT NULL,
    payment_type_id      TINYINT UNSIGNED NOT NULL,
    passenger_type_id    TINYINT UNSIGNED NOT NULL,
    trip_distance        DECIMAL(6,2) NOT NULL,
    store_and_fwd_flag   CHAR(1) NOT NULL,

#money
    fare_amount          DECIMAL(7,2) NOT NULL,
    extra                DECIMAL(6,2) NOT NULL,
    mta_tax              DECIMAL(5,2) NOT NULL,
    tip_amount           DECIMAL(7,2) NOT NULL,
    tolls_amount         DECIMAL(6,2) NOT NULL,
    improvement_surcharge DECIMAL(4,2) NOT NULL,
    congestion_surcharge DECIMAL(4,2) NOT NULL,
    total_amount         DECIMAL(8,2) NOT NULL,


# derived features
trip_duration_min        DECIMAL(6,2) NOT NULL, 
avg_speed_mph            DECIMAL(5,2) NOT NULL,
fare_per_mile            DECIMAL(7,2) NOT NULL,
tip_percent              DECIMAL(8,2) NOT NULL,
pickup_date              DATE NOT NULL,
pickup_hour              TINYINT UNSIGNED NOT NULL,
pickup_day_of_week       TINYINT UNSIGNED NOT NULL,
is_weekend               BOOLEAN NOT NULL,
is_cross_borough         BOOLEAN NOT NULL,
is_airport_trip          BOOLEAN NOT NULL,
is_suspicious            BOOLEAN NOT NULL,

FOREIGN KEY (vendor_id)            REFERENCES vendors (vendor_id),
FOREIGN KEY (pickup_zone_id)       REFERENCES zones (zone_id),
FOREIGN KEY (dropoff_zone_id)      REFERENCES zones (zone_id),
FOREIGN KEY (rate_code_id)         REFERENCES rate_codes (rate_code_id),
FOREIGN KEY (payment_type_id)      REFERENCES payment_types (payment_type_id)
);

CREATE TABLE cleaning_log (
    reason        VARCHAR(50) NOT NULL PRIMARY KEY,
    rows_removed INT UNSIGNED NOT NULL
);