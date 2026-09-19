import json

import pytest

import app.db as db_mod
from app import seed
from app.engines.route_quote import quote_route
from app.services.metro_service import MetroService

# 种子线网：A1城站—A2市心—A3东湾，A2—B1北苑—B2机场
# 分段表：≤2 站 3.0，≤4 站 4.0，>4 站 6.0
EDGES = [("A1", "A2"), ("A2", "A3"), ("A2", "B1"), ("B1", "B2")]
RULES = [{"max_hops": 2, "price": 3.0}, {"max_hops": 4, "price": 4.0}, {"max_hops": None, "price": 6.0}]


@pytest.fixture
def svc(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "test.db")
    seed.init_db()
    with MetroService() as s:
        yield s


# ---------- 引擎层 ----------

def test_short_trip_lifted_when_floor_above_tier():
    # 城站→市心 1 站，分段价 3.0；底价 5.0 高于该档，必须抬升
    q = quote_route(EDGES, "A1", "A2", RULES, min_fare=5.0)
    assert q["hops"] == 1 and q["fare"] == 3.0
    assert q["payable"] == 5.0 and q["lifted"] is True


def test_long_trip_not_lifted_when_floor_below_tier():
    # 城站→机场 3 站，分段价 4.0；底价 2.0 低于该档，不得抬升
    q = quote_route(EDGES, "A1", "B2", RULES, min_fare=2.0)
    assert q["hops"] == 3 and q["fare"] == 4.0
    assert q["payable"] == 4.0 and q["lifted"] is False


def test_floor_equal_to_segment_does_not_lift():
    # 分段价“小于”底价才抬升；相等不算抬升
    q = quote_route(EDGES, "A1", "A2", RULES, min_fare=3.0)
    assert q["payable"] == 3.0 and q["lifted"] is False


def test_unreachable_has_no_payable_and_not_lifted():
    q = quote_route(EDGES, "A1", "ZZ", RULES, min_fare=9.0)
    assert q["reachable"] is False
    assert q["payable"] is None and q["lifted"] is False


# ---------- 服务层（真实 SQLite） ----------

def test_service_quote_applies_floor_from_settings(svc):
    svc.update_min_fare(5.0)
    q = svc.quote("A1", "A2", persist=False)
    assert q["fare"] == 3.0 and q["payable"] == 5.0 and q["lifted"] is True


def test_short_trip_payable_follows_floor_change(svc):
    # 底价先低于 1 站档：短程不抬
    svc.update_min_fare(2.0)
    before = svc.quote("A1", "A2", persist=False)
    assert before["payable"] == 3.0 and before["lifted"] is False
    # 改到高于 1 站档后：短程应付必须跟着抬
    svc.update_min_fare(4.5)
    after = svc.quote("A1", "A2", persist=False)
    assert after["fare"] == 3.0
    assert after["payable"] == 4.5 and after["lifted"] is True


def test_readonly_quote_persists_nothing(svc):
    before = len(svc.history())
    svc.update_min_fare(6.0)
    out = svc.quote("A1", "A2", persist=False)
    assert out["run_id"] is None and out["lifted"] is True
    assert len(svc.history()) == before


def test_history_run_keeps_write_time_lifted_and_payable(svc):
    svc.update_min_fare(5.0)
    written = svc.quote("A1", "A2", persist=True)
    assert written["lifted"] is True and written["payable"] == 5.0
    run_id = written["run_id"]

    svc.update_min_fare(1.0)  # 之后把底价调低，不得影响已写入的快照
    row = svc.history_run(run_id)
    assert row["result"]["lifted"] is True
    assert row["result"]["payable"] == 5.0
    assert row["result"]["fare"] == 3.0


def test_history_run_unknown_id_returns_none(svc):
    assert svc.history_run(999999) is None


def test_floor_comparison_ignores_day_pass_switch(svc):
    # 一日通开关存在与否，底价比较结果必须一致
    svc.update_min_fare(5.0)
    plain = svc.quote("A1", "A2", persist=False)
    svc._conn.execute("INSERT INTO settings(key,value) VALUES ('day_pass_enabled','1')")
    svc._conn.commit()
    toggled = svc.quote("A1", "A2", persist=False)
    assert toggled["payable"] == plain["payable"] == 5.0
    assert toggled["lifted"] == plain["lifted"] is True


def test_update_min_fare_rejects_non_positive(svc):
    svc.update_min_fare(2.0)
    for bad in (0, -1, -0.5, "abc", None, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            svc.update_min_fare(bad)
    # 非法写入不得改动原值
    assert svc.settings()["min_fare"] == "2.0"
