import json
import pandas as pd
from pyproj import Transformer
import config

def load_lookup():
    # Read the lookup csv, fix the missing values and give columns simple names

    lookup = pd.read_csv(config.RAW_ZONE_LOOKUP_FILE)
    lookup.columns = ["zone_id", "borough", "zone_name","service_zone"]

    #zones blank, filling them with Unknown
    lookup["borough"] = lookup["borough"].fillna("Unkown")
    lookup["zone_name"] = lookup["zone_name"].fillna("Unknown")
    lookup["service_zone"] = lookup["service_zone"].fillna("Unknown")

    return lookup

def convert_point(transformer, x, y):

    lon, lat = transformer.transform(x, y)
    return [round(lon, 6), round(lat, 6)]

def load_shapes():
    #read the geojson and return a dictionary
    with open(config.RAW_ZONE_SHAPES_FILE) as file:
        geo = json.load(file)

    transformer = Transformer.from_crs("EPSG:2263", "EPSG:4326", always_xy=True)

    shapes = {}
    for feature in geo["features"]:
        zone_id = feature["properties"]["LocationID"]
        geometry = feature["geometry"]

        if geometry["type"] == "Polygon":
            polygons = [geometry["coordinates"]]
        else:
            polygons = geometry["coordinates"]

        converted_polygons = []    
        for polygon in polygons:
            converted_rings = []
            for ring in polygon:
                converted_ring = []
                for point in ring:
                    converted_ring.append(convert_point(transformer,point[0],point[1]))
                converted_rings.append(converted_ring)
            converted_polygons.append(converted_rings)

        if zone_id not in shapes:
            shapes[zone_id] = []
        shapes[zone_id].extend(converted_polygons)

    return shapes

def find_center(polygons):

    outline = polygons[0][0]
    total_lon = 0
    total_lat = 0

    for lon, lat in outline:
        total_lon += lon
        total_lat += lat
    return round(total_lat / len(outline), 6), round(total_lon / len(outline), 6)

def main():
    lookup = load_lookup()
    shapes = load_shapes()

    centers_lat = []
    centers_lon = []
    has_boundary = []
    features = []

    for _, row in lookup.iterrows():
        zone_id = int(row["zone_id"])

        if zone_id in shapes:
            lat, lon = find_center(shapes[zone_id])
            centers_lat.append(lat)
            centers_lon.append(lon)
            has_boundary.append(True)

            features.append({
                "type": "Feature",
                "properties":{
                    "zone_id": zone_id,
                    "zone_name": row["zone_name"], 
                    "borough": row["borough"],
                },
                "geometry": {"type":"MultiPolygon", "coordinates": shapes[zone_id]},
            })
        else:
            centers_lat.append(None)
            centers_lon.append(None)
            has_boundary.append(False)

    lookup["center_lat"] = centers_lat
    lookup["center_lon"] = centers_lon
    lookup["has_boundary"] = has_boundary

    lookup.to_csv(config.CLEAN_ZONES_FILE, index=False)
    with open(config.CLEAN_ZONE_SHAPES_FILE, "w") as file:
        json.dump({"type": "FeatureCollection", "features": features}, file)

    print("Zones in look up table    :", len(lookup))
    print("Zones with a map boundary  :", len(features))
    print("Zones WITHOUT a boundary  :", list(lookup[~lookup["has_boundary"]]["zone_id"]))
    print("Saved:", config.CLEAN_ZONES_FILE, "and", config.CLEAN_ZONE_SHAPES_FILE)

if __name__ == "__main__":
    main()
