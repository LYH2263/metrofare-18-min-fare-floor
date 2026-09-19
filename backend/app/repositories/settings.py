import sqlite3

FLOOR_KEY = "floor_fare"


def get_map(conn: sqlite3.Connection) -> dict[str, str]:
    return {r["key"]: r["value"] for r in conn.execute("SELECT * FROM settings").fetchall()}


def set_value(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO settings(key,value) VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()


def get_floor_fare(conn: sqlite3.Connection) -> float | None:
    """正数底价；缺失或非法时视为未设置。底价比较只读本键，不读一日通等其他开关。"""
    row = conn.execute("SELECT value FROM settings WHERE key=?", (FLOOR_KEY,)).fetchone()
    if row is None:
        return None
    try:
        value = float(row["value"])
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None
