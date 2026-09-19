from app.engines.fare_rules import apply_floor, fare_for_hops
from app.engines.graph_bfs import shortest_hops


def quote_route(
    edges: list[tuple[str, str]],
    start: str,
    end: str,
    rules: list[dict],
    floor_fare: float | None = None,
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
    payable, lifted = apply_floor(fare, floor_fare)
    return {
        "start": start,
        "end": end,
        "hops": hops,
        "fare": fare,
        "payable": payable,
        "lifted": lifted,
        "reachable": True,
    }
