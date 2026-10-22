from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def suppress_small_cells(
    rows: list[Mapping[str, Any]],
    *,
    count_key: str,
    minimum: int = 10,
    total: int | None = None,
) -> list[dict[str, Any]]:
    """Mask small counts and apply conservative complementary suppression.

    When a published total is supplied and any small cell exists, every row is
    suppressed. This is intentionally conservative and prevents subtraction
    attacks without introducing a complex dependency.
    """
    copied = [dict(row) for row in rows]
    has_small_cell = any(int(row.get(count_key, 0)) < minimum for row in copied)
    suppress_all = total is not None and has_small_cell

    result: list[dict[str, Any]] = []
    for row in copied:
        should_suppress = suppress_all or int(row.get(count_key, 0)) < minimum
        if should_suppress:
            row[count_key] = None
        row["suppressed"] = should_suppress
        result.append(row)
    return result
