from carepath.aggregation import suppress_small_cells


def test_government_small_cells_are_suppressed() -> None:
    rows = [
        {"region": "A", "count": 9},
        {"region": "B", "count": 10},
    ]

    result = suppress_small_cells(rows, count_key="count", minimum=10)

    assert result[0] == {"region": "A", "count": None, "suppressed": True}
    assert result[1] == {"region": "B", "count": 10, "suppressed": False}


def test_secondary_suppression_prevents_differencing() -> None:
    rows = [
        {"region": "A", "count": 7},
        {"region": "B", "count": 40},
        {"region": "C", "count": 3},
    ]

    result = suppress_small_cells(
        rows,
        count_key="count",
        minimum=10,
        total=50,
    )

    suppressed = [row for row in result if row["suppressed"]]
    assert {row["region"] for row in suppressed} == {"A", "B", "C"}
