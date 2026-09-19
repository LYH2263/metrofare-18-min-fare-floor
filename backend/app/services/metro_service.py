import json
import math

from app.db import connect
from app.engines.route_quote import quote_route
from app.repositories import edges as edges_repo
from app.repositories import fare_rules as rules_repo
from app.repositories import runs as runs_repo
from app.repositories import settings as settings_repo
from app.repositories import stations as stations_repo


class MetroService:
    def __init__(self):
        self._conn = connect()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def stations(self):
        return stations_repo.list_all(self._conn)

    def station(self, code: str):
        return stations_repo.get_by_code(self._conn, code)

    def edges(self):
        return [{"a": a, "b": b} for a, b in edges_repo.list_pairs(self._conn)]

    def fare_rules(self):
        return rules_repo.list_ordered(self._conn)

    def settings(self):
        return settings_repo.get_map(self._conn)

    def update_min_fare(self, raw) -> dict:
        """把底价改为一个正数；非法值抛 ValueError，由路由转 400。"""
        try:
            value = float(raw)
        except (TypeError, ValueError):
            raise ValueError("底价必须是数字") from None
        if not math.isfinite(value) or value <= 0:
            raise ValueError("底价必须是正数")
        settings_repo.set_min_fare(self._conn, value)
        return self.settings()

    def quote(self, start: str, end: str, persist: bool):
        edges = edges_repo.list_pairs(self._conn)
        rules = rules_repo.as_calc_rules(self._conn)
        min_fare = settings_repo.get_min_fare(self._conn)
        result = quote_route(edges, start, end, rules, min_fare=min_fare)
        run_id = None
        if persist and result.get("reachable"):
            run_id = runs_repo.insert(self._conn, "quote", {"start": start, "end": end}, result)
        return {"run_id": run_id, **result}

    def history(self, limit=50):
        return runs_repo.list_recent(self._conn, limit)

    def history_run(self, run_id: int):
        """按编号取出一条试算记录；result 保持写入当时的 JSON 快照，不做重算。"""
        row = runs_repo.get_by_id(self._conn, run_id)
        if row is None:
            return None
        return {
            **row,
            "input": json.loads(row["input_json"]),
            "result": json.loads(row["result_json"]),
        }

    def dashboard(self):
        st = stations_repo.list_all(self._conn)
        clean = [s for s in st if "种子" not in s["name"]]
        dirty = [s for s in st if "种子" in s["name"]]
        return {
            "station_count": len(st),
            "edge_count": len(edges_repo.list_pairs(self._conn)),
            "clean_stations": len(clean),
            "dirty_stations": len(dirty),
        }
