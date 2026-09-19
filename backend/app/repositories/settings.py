import sqlite3

MIN_FARE_KEY = "min_fare"


def get_map(conn: sqlite3.Connection) -> dict[str, str]:
    return {r["key"]: r["value"] for r in conn.execute("SELECT * FROM settings").fetchall()}


def get_min_fare(conn: sqlite3.Connection) -> float | None:
    """读取底价；未设置返回 None。只读这一个键，不看一日通开关。"""
    row = conn.execute("SELECT value FROM settings WHERE key=?", (MIN_FARE_KEY,)).fetchone()
    if row is None:
        return None
    return float(row["value"])


def set_min_fare(conn: sqlite3.Connection, value: float) -> None:
    conn.execute(
        "INSERT INTO settings(key,value) VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (MIN_FARE_KEY, repr(float(value))),
    )
    conn.commit()
