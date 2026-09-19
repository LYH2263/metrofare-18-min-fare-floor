import json

from app.db import connect
from app.engines.route_quote import quote_route

EDGES = [("A1", "A2"), ("A2", "A3"), ("A2", "B1"), ("B1", "B2")]
RULES = [{"max_hops": 2, "price": 3.0}, {"max_hops": 4, "price": 4.0}, {"max_hops": None, "price": 6.0}]
DEFAULT_FLOOR_FARE = 2.0


def init_db():
    conn = connect()
    conn.executescript(
        """
    CREATE TABLE IF NOT EXISTS stations(id INTEGER PRIMARY KEY, code TEXT, name TEXT);
    CREATE TABLE IF NOT EXISTS edges(a TEXT, b TEXT);
    CREATE TABLE IF NOT EXISTS fare_rules(id INTEGER PRIMARY KEY, max_hops INTEGER, price REAL);
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE IF NOT EXISTS calc_runs(
        id INTEGER PRIMARY KEY, kind TEXT, input_json TEXT, result_json TEXT, created_at TEXT);
    """
    )
    # 已存在的旧库升级时补上正数底价默认值（不覆盖用户已改的值）
    conn.execute(
        "INSERT INTO settings(key,value) VALUES ('floor_fare',?) ON CONFLICT(key) DO NOTHING",
        (str(DEFAULT_FLOOR_FARE),),
    )
    conn.commit()
    if conn.execute("SELECT COUNT(*) c FROM stations").fetchone()["c"] == 0:
        for code, name in [
            ("A1", "城站"),
            ("A2", "市心"),
            ("A3", "东湾"),
            ("B1", "北苑"),
            ("B2", "机场(种子绕远)"),
        ]:
            conn.execute("INSERT INTO stations(code, name) VALUES (?,?)", (code, name))
        for a, b in EDGES:
            conn.execute("INSERT INTO edges(a,b) VALUES (?,?)", (a, b))
        conn.executemany(
            "INSERT INTO fare_rules(max_hops, price) VALUES (?,?)",
            [(2, 3.0), (4, 4.0), (None, 6.0)],
        )
        conn.execute("INSERT INTO settings(key,value) VALUES ('currency','CNY')")
        q1 = quote_route(EDGES, "A1", "A3", RULES, floor_fare=DEFAULT_FLOOR_FARE)
        conn.execute(
            "INSERT INTO calc_runs(kind,input_json,result_json,created_at) VALUES (?,?,?,datetime('now'))",
            ("quote", json.dumps({"start": "A1", "end": "A3"}), json.dumps(q1, ensure_ascii=False)),
        )
        conn.commit()
    conn.close()
