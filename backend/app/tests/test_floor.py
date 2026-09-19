import json

import pytest

import app.db as db_mod
from app import seed
from app.engines.route_quote import quote_route
from app.engines.fare_rules import apply_floor
from app.repositories import settings as settings_repo
from app.services.metro_service import MetroService

# 种子网络：A1(城站)—A2(市心)—A3(东湾)，A2—B1(北苑)—B2(机场)
RULES = [{"max_hops": 2, "price": 3.0}, {"max_hops": 4, "price": 4.0}, {"max_hops": None, "price": 6.0}]
EDGES = [("A1", "A2"), ("A2", "A3"), ("A2", "B1"), ("B1", "B2")]


@pytest.fixture
def svc(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "test.db")
    seed.init_db()
    with MetroService() as s:
        yield s


# ---------- 引擎层 ----------

def test_apply_floor_lifts_only_when_strictly_below():
    assert apply_floor(3.0, 4.0) == (4.0, True)   # 分段价低于底价 → 抬升
    assert apply_floor(4.0, 3.0) == (4.0, False)  # 底价低于该档 → 不抬
    assert apply_floor(3.0, 3.0) == (3.0, False)  # 相等不算“低于”
    assert apply_floor(3.0, None) == (3.0, False)


def test_city_to_center_one_hop_lifts_above_tier():
    # 城站到市心站数为 1（分段价 3.0），底价高于该档须抬升
    q = quote_route(EDGES, "A1", "A2", RULES, floor_fare=4.0)
    assert q["hops"] == 1
    assert q["fare"] == 3.0 and q["payable"] == 4.0 and q["lifted"] is True


def test_city_to_airport_three_hops_not_lifted_below_tier():
    # 城站到机场站数为 3（分段价 4.0），底价低于该档不得抬升
    q = quote_route(EDGES, "A1", "B2", RULES, floor_fare=3.0)
    assert q["hops"] == 3
    assert q["fare"] == 4.0 and q["payable"] == 4.0 and q["lifted"] is False


def test_unreachable_has_no_payable():
    q = quote_route([("A1", "A2")], "A1", "ZZ", RULES, floor_fare=5.0)
    assert q["reachable"] is False and q["payable"] is None and q["lifted"] is False


# ---------- 服务层（真实 SQLite） ----------

def test_raising_floor_above_one_hop_tier_lifts_short_trip(svc):
    # 种子底价 2.0 低于 1 站档 3.0：短程不抬
    before = svc.quote("A1", "A2", persist=False)
    assert before["fare"] == 3.0 and before["payable"] == 3.0 and before["lifted"] is False

    # 底价改到高于 1 站档后，短程应付必须跟着抬
    svc.update_settings({"floor_fare": 4.0})
    after = svc.quote("A1", "A2", persist=False)
    assert after["fare"] == 3.0 and after["payable"] == 4.0 and after["lifted"] is True


def test_lower_floor_never_lifts_long_trip(svc):
    svc.update_settings({"floor_fare": 3.0})
    q = svc.quote("A1", "B2", persist=False)  # 3 站档 4.0
    assert q["fare"] == 4.0 and q["payable"] == 4.0 and q["lifted"] is False


def test_readonly_trial_writes_no_record_even_when_lifted(svc):
    svc.update_settings({"floor_fare": 4.0})
    n_before = len(svc.history())
    out = svc.quote("A1", "A2", persist=False)
    assert out["lifted"] is True and out["run_id"] is None
    assert len(svc.history()) == n_before


def test_history_snapshot_keeps_payable_and_lifted_at_write_time(svc):
    # 抬升期间落库
    svc.update_settings({"floor_fare": 4.0})
    run = svc.quote("A1", "A2", persist=True)
    run_id = run["run_id"]
    assert run["payable"] == 4.0 and run["lifted"] is True

    # 事后底价调低，按编号打开旧记录：应付与抬升标记保持写入当时的值
    svc.update_settings({"floor_fare": 2.0})
    row = svc.run_by_id(run_id)
    snapshot = json.loads(row["result_json"])
    assert snapshot["fare"] == 3.0
    assert snapshot["payable"] == 4.0 and snapshot["lifted"] is True


def test_floor_comparison_does_not_read_day_pass(svc):
    # 打开任何“一日通”开关都不得影响底价比较
    settings_repo.set_value(svc._conn, "day_pass_enabled", "on")
    settings_repo.set_value(svc._conn, "day_pass_price", "1.0")
    lifted = svc.quote("A1", "A2", persist=False)
    assert lifted["fare"] == 3.0 and lifted["payable"] == 3.0 and lifted["lifted"] is False

    svc.update_settings({"floor_fare": 4.0})
    still_lifted = svc.quote("A1", "A2", persist=False)
    assert still_lifted["payable"] == 4.0 and still_lifted["lifted"] is True


def test_floor_fare_must_be_positive(svc):
    for bad in (0, -1):
        with pytest.raises(ValueError):
            svc.update_settings({"floor_fare": bad})
    # 被拒绝后底价仍是种子值 2.0
    assert settings_repo.get_floor_fare(svc._conn) == 2.0
