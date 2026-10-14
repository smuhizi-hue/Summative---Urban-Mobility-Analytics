# algorithms.py
# Our own hand-written algorithm: MERGE SORT, used to RANK taxi zones.
#
# Problem it solves:
#   The database gives us statistics for ~260 zones (pickups, average fare, ...) in no
#   particular order. The dashboard needs "the top 10 zones". We rank them ourselves,
#   WITHOUT sorted(), .sort(), sort_values(), heapq or Counter.
#
# Idea of merge sort ("divide and conquer"):
#   1. Cut the list in two halves.
#   2. Sort each half (by cutting it again... until a half has 0 or 1 item = already sorted).
#   3. MERGE the two sorted halves: repeatedly take the bigger front item of the two halves.


def merge(left, right, key):
    """Join two lists that are already sorted (biggest first) into one sorted list."""
    result = []
    i = 0          # position in the left list
    j = 0          # position in the right list

    while i < len(left) and j < len(right):
        if left[i][key] >= right[j][key]:      # ">=" keeps equal items in their old order
            result.append(left[i])
            i = i + 1
        else:
            result.append(right[j])
            j = j + 1

    # one list is finished; copy whatever is left in the other one
    while i < len(left):
        result.append(left[i])
        i = i + 1
    while j < len(right):
        result.append(right[j])
        j = j + 1

    return result


def merge_sort(items, key):
    """Sort a list of dictionaries by items[...][key], from BIGGEST to SMALLEST."""
    if len(items) <= 1:                  # 0 or 1 item: already sorted
        return items

    middle = len(items) // 2
    left = merge_sort(items[:middle], key)
    right = merge_sort(items[middle:], key)
    return merge(left, right, key)


def top_zones(zone_stats, metric, how_many, min_trips):
    """
    Return the best `how_many` zones for a metric (e.g. "pickups" or "avg_fare").

    zone_stats : list of dictionaries, one per zone, e.g.
                 {"zone_id": 237, "zone_name": "...", "pickups": 5000, "avg_fare": 9.5, ...}
    min_trips  : ignore zones with fewer pickups than this, because an average
                 calculated from only a handful of trips is not reliable.
    """
    # step 1: keep only the zones that have a real value for this metric
    usable = []
    for zone in zone_stats:
        if zone[metric] is not None and zone["pickups"] >= min_trips:
            usable.append(zone)

    # step 2: sort with our own merge sort
    ranked = merge_sort(usable, metric)

    # step 3: take the first `how_many` and give each one a rank number
    result = []
    position = 0
    while position < how_many and position < len(ranked):
        zone = dict(ranked[position])
        zone["rank"] = position + 1
        result.append(zone)
        position = position + 1
    return result
