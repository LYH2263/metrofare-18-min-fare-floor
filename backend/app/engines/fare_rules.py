def fare_for_hops(hops: int, rules: list[dict]) -> float:
    """rules sorted by max_hops ascending; last max_hops may be None (open)."""
    if hops < 0:
        raise ValueError("hops")
    for r in rules:
        mx = r.get("max_hops")
        if mx is None or hops <= int(mx):
            return round(float(r["price"]), 2)
    return round(float(rules[-1]["price"]), 2)


def apply_floor(fare: float, floor_fare: float | None) -> tuple[float, bool]:
    """分段价低于正数底价时应付抬到底价并标记抬升，否则应付等于分段价。"""
    if floor_fare is None:
        return round(float(fare), 2), False
    floor_fare = float(floor_fare)
    if floor_fare <= 0:
        raise ValueError("floor_fare must be positive")
    if float(fare) < floor_fare:
        return round(floor_fare, 2), True
    return round(float(fare), 2), False
