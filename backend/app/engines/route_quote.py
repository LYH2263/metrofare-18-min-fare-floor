from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_hops


def apply_min_fare(fare: float | None, min_fare: float | None) -> dict:
    """分段价与正数底价比较：分段价低于底价则应付抬升为底价，否则应付等于分段价。

    只读取底价本身，不涉及一日通等任何其他开关。
    """
    if fare is None:
        return {"payable": None, "lifted": False}
    if min_fare is not None and fare < min_fare:
        return {"payable": round(float(min_fare), 2), "lifted": True}
    return {"payable": fare, "lifted": False}


def quote_route(
    edges: list[tuple[str, str]],
    start: str,
    end: str,
    rules: list[dict],
    min_fare: float | None = None,
) -> dict:
    hops = shortest_hops(edges, start, end)
    if hops is None:
        return {
            "start": start,
            "end": end,
            "hops": None,
            "fare": None,
            "payable": None,
            "lifted": False,
            "reachable": False,
        }
    fare = fare_for_hops(hops, rules)
    floor = apply_min_fare(fare, min_fare)
    return {
        "start": start,
        "end": end,
        "hops": hops,
        "fare": fare,
        **floor,
        "reachable": True,
    }
