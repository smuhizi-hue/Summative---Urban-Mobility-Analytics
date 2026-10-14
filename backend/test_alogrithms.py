# test_algorithms.py
# Checks our merge sort against Python's own sorted() on random data.
# Run with:  python test_algorithms.py

import random
from algorithms import merge_sort, top_zones


def test_merge_sort_random_lists():
    for _ in range(200):
        size = random.randint(0, 60)
        items = [{"value": random.randint(0, 20)} for _ in range(size)]
        ours = [item["value"] for item in merge_sort(items, "value")]
        expected = sorted([item["value"] for item in items], reverse=True)
        assert ours == expected, "merge_sort gave a wrong order"


def test_merge_sort_empty_and_single():
    assert merge_sort([], "value") == []
    assert merge_sort([{"value": 5}], "value") == [{"value": 5}]


def test_top_zones():
    zones = [
        {"zone_id": 1, "pickups": 500, "avg_fare": 10.0},
        {"zone_id": 2, "pickups": 900, "avg_fare": 30.0},
        {"zone_id": 3, "pickups": 5,   "avg_fare": 99.0},   # too few trips: must be ignored
        {"zone_id": 4, "pickups": 700, "avg_fare": None},   # no value: must be ignored
        {"zone_id": 5, "pickups": 300, "avg_fare": 20.0},
    ]
    best = top_zones(zones, "avg_fare", 2, 100)
    assert [z["zone_id"] for z in best] == [2, 5]
    assert best[0]["rank"] == 1 and best[1]["rank"] == 2


if __name__ == "__main__":
    test_merge_sort_random_lists()
    test_merge_sort_empty_and_single()
    test_top_zones()
    print("All algorithm tests passed.")
