"""2026-11-21 로컬 모델(Ollama) 학습 데이터셋 — 운영하면서 쌓기 · 확인 · 내보내기.

넘어가는 기준: 짧은 정리 작업만 담음(글 생성 작업·내부 작업은 안 담음), 개인정보 모양 문장은 담지 않음, 학습 칸에 세션 값 없음,
클릭이면 silver · 사람 확인이면 gold(이후 승격이 gold 를 덮지 않음), 내보내기는 문장 해시로 학습·시험 고정·gold 우선·출처 거르기,
임시 칸 90일·학습 칸 보관 기간 뒤 지움, 대화 경로에서 실제로 담기(LLMClient).
2026-11-22 검토 의견 반영: 기본 꺼짐 · 클릭은 그 차례에 보여 준 상품만 · 비슷한 문장 묶음으로 나눔 · 시험 칸은 gold 만 ·
고쳐도 출처 유지(edited) · 입구에서 가린 차례는 담지 않음 · 내보낸 파일 정리.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.services.ai import dataset as ds

SYSTEM = "상품어 하나를 JSON 으로"
T0 = datetime(2026, 11, 21, 3, 0, tzinfo=timezone.utc)


@pytest.fixture
def store(tmp_path):
    clock = {"t": T0}
    st = ds.DatasetStore(tmp_path / "d.sqlite3", clock=lambda: clock["t"])
    st._clock = clock
    return st


def test_capture_only_short_tasks_and_no_personal_info(store):
    assert store.capture("shop_keyword", "사과 5kg 추천해줘", {"keyword": "사과"}, "openai:gpt-5.4-mini", SYSTEM, "s1")
    assert not store.capture("food_knowledge", "딸기 제철", {"tips": []}, "openai:gpt-5.4", SYSTEM, "s1")   # 글 생성
    assert not store.capture("trend_cause", "제목들", {"cause": "x"}, "deepseek:x", SYSTEM, None)           # 내부 작업
    assert not store.capture("shop_keyword", "사과 010-1234-5678", {"keyword": "사과"}, "openai:m", SYSTEM, "s1")
    assert not store.capture("shop_keyword", "가" * 301, {"keyword": "가"}, "openai:m", SYSTEM, "s1")
    assert not store.capture("shop_keyword", "사과", "not a dict", "openai:m", SYSTEM, "s1")


def test_promote_signal_review_and_no_session_in_examples(store):
    store.capture("shop_keyword", "사과  5kg 추천해줘", {"keyword": "사과"}, "openai:gpt-5.4-mini", SYSTEM, "clicker", "t1")
    store.capture("shop_keyword", "사과 5kg 추천해줘", {"keyword": "사과"}, "openai:gpt-5.4-mini", SYSTEM, "other", "t2")
    store.capture("chat_intent", "고마워 근데 배도", {"intent": "shop"}, "openai:gpt-5.4-mini", SYSTEM, "x", "t3")
    store.note_query("t1", "사과 5kg", ["경북 사과 5kg"])
    store.note_query("t2", "사과 5kg", ["경북 사과 5kg"])
    store._clock["t"] = T0 + timedelta(hours=2)
    seen = []

    def clicks(sid, a, b, shown):
        seen.append((sid, shown))
        return sid in ("clicker", "x") and "경북 사과 5kg" in shown
    done = store.promote(clicks)
    assert ("x", ["경북 사과 5kg"]) not in seen          # 상품을 보여 주지 않은 차례(t3)는 클릭을 묻지도 않는다
    assert done == {"promoted": 3, "silver": 1}
    q = {(x["task"], x["input"]): x for x in store.queue()}
    kw = q[("shop_keyword", "사과 5kg 추천해줘")]
    assert (kw["label"], kw["seen"], kw["clicked"]) == ("silver", 2, 1)
    assert q[("chat_intent", "고마워 근데 배도")]["label"] == "candidate"
    import sqlite3

    cols = [r[1] for r in sqlite3.connect(store.path).execute("PRAGMA table_info(examples)")]
    assert "session_id" not in cols and "created_at" not in cols

    store.review(kw["id"], "ok")
    store.capture("shop_keyword", "사과 5kg 추천해줘", {"keyword": "사과"}, "openai:gpt-5.4-mini", SYSTEM, "again")
    store._clock["t"] += timedelta(hours=2)
    store.promote(None)
    assert all(x["input"] != "사과 5kg 추천해줘" for x in store.queue())       # gold 는 다시 확인 목록에 안 옴
    intent = q[("chat_intent", "고마워 근데 배도")]
    store.review(intent["id"], "fix", output={"intent": "shop", "item": "배"})
    with pytest.raises(ds.DatasetError):
        store.review(intent["id"], "fix", output=None)
    with pytest.raises(ds.DatasetError):
        store.review(intent["id"], "maybe")
    labels = {(r["task"], r["label"]): r["n"] for r in store.stats()["by_task"]}
    assert labels[("shop_keyword", "gold")] == 1 and labels[("chat_intent", "gold")] == 1
    assert labels[("chat_intent", "dropped")] == 1


FOODS = ["사과", "배", "감", "귤", "딸기", "포도", "수박", "참외", "복숭아", "자두", "망고", "키위", "레몬", "자몽", "체리",
         "블루베리", "바나나", "파인애플", "멜론", "석류", "한우", "돼지고기", "닭가슴살", "연어", "고등어", "갈치", "새우",
         "오징어", "전복", "굴", "김치", "두부", "계란", "우유", "치즈", "버터", "쌀", "현미", "보리", "감자"]


def _gold_all(store):
    for x in store.queue(limit=200):
        store.review(x["id"], "ok")


def test_export_split_is_stable_and_gold_first(store):
    for i, food in enumerate(FOODS):
        store.capture("shop_keyword", f"{food} 추천", {"keyword": food}, "openai:gpt-5.4-mini", SYSTEM, f"s{i}")
    store.capture("shop_keyword", "배 추천", {"keyword": "틀림"}, "deepseek:flash", SYSTEM, "z")
    store._clock["t"] = T0 + timedelta(hours=2)
    store.promote(None)
    assert store.export("shop_keyword") == {"train": [], "test": []}       # 기본은 gold 만 — 아직 확인 전
    _gold_all(store)
    first = store.export("shop_keyword")
    assert len(first["train"]) + len(first["test"]) == 40                 # 같은 문장은 하나만
    assert first["test"]                                                   # 시험 칸이 비지 않음 (40개 중 10% 안팎)
    assert first == store.export("shop_keyword")                          # 다시 내보내도 같음
    for split, rows in first.items():
        for r in rows:
            assert ds.split_of("shop_keyword", r["messages"][1]["content"]) == split
            assert r["messages"][0]["content"] == SYSTEM and json.loads(r["messages"][2]["content"])
    no_oa = store.export("shop_keyword", exclude_teachers=("openai",))
    assert [r["teacher"] for rows in no_oa.values() for r in rows] == ["deepseek:flash"]


def test_fix_keeps_original_teacher(store):
    store.capture("shop_keyword", "배 추천", {"keyword": "틀림"}, "deepseek:flash", SYSTEM, "z")
    store._clock["t"] = T0 + timedelta(hours=2)
    store.promote(None)
    wrong = store.queue()[0]
    store.review(wrong["id"], "fix", output={"keyword": "배"})
    rows = [r for rows in store.export("shop_keyword").values() for r in rows]
    assert len(rows) == 1
    r = rows[0]
    assert r["label"] == "gold" and json.loads(r["messages"][2]["content"]) == {"keyword": "배"}
    assert r["teacher"] == "deepseek:flash" and r["edited"] is True and r["reviewed_by"] == "operator"


def test_similar_sentences_share_a_split_and_test_is_gold_only(store):
    assert ds.group_of("사과 3kg 주세요") == ds.group_of("사과5kg  주세요!")
    assert ds.split_of("t", "사과 3kg 주세요") == ds.split_of("t", "사과5kg 주세요!")
    # 시험 묶음에 걸린 silver 는 시험에도 학습에도 넣지 않는다
    test_food = next(f for f in FOODS + [f"{a}{b}" for a in FOODS for b in FOODS]
                     if ds.split_of("shop_keyword", f"{f} 추천") == "test")
    store.capture("shop_keyword", f"{test_food} 추천", {"keyword": test_food}, "openai:m", SYSTEM, "s", "t1")
    store.note_query("t1", test_food, ["상품"])
    store._clock["t"] = T0 + timedelta(hours=2)
    store.promote(lambda *a: True)
    assert store.export("shop_keyword", labels=("gold", "silver")) == {"train": [], "test": []}


def test_pii_seen_turn_is_not_captured(tmp_path, monkeypatch):
    monkeypatch.setattr(ds, "enabled", lambda: True)     # 2026-11-22 학습 안 함 — 코드 경로 자체만 시험
    monkeypatch.setenv("DATASET_DB", str(tmp_path / "p.sqlite3"))
    token = ds.PII_SEEN.set(True)
    try:
        ds.capture("shop_keyword", "사과 [전화번호]", {"keyword": "사과"}, "openai:m", SYSTEM)
    finally:
        ds.PII_SEEN.reset(token)
    assert not (tmp_path / "p.sqlite3").exists()
    ds.capture("shop_keyword", "사과", {"keyword": "사과"}, "openai:m", SYSTEM)
    assert (tmp_path / "p.sqlite3").exists()


def test_off_by_default(monkeypatch):
    monkeypatch.delenv("DATASET_CAPTURE", raising=False)
    assert not ds.enabled()


def test_purge_exports(tmp_path, monkeypatch):
    import os

    d = tmp_path / "export"
    d.mkdir()
    old, new = d / "a_train.jsonl", d / "b_train.jsonl"
    old.write_text("{}\n")
    new.write_text("{}\n")
    now = datetime(2026, 11, 22, tzinfo=timezone.utc)
    os.utime(old, (now.timestamp() - 40 * 86400,) * 2)
    os.utime(new, (now.timestamp() - 1 * 86400,) * 2)
    assert ds.purge_exports(d, now) == 1 and not old.exists() and new.exists()


def test_purge(store, monkeypatch):
    store.capture("shop_keyword", "배 추천", {"keyword": "배"}, "openai:m", SYSTEM, "s")
    store._clock["t"] = T0 + timedelta(hours=2)
    store.promote(None)
    store._clock["t"] = T0 + timedelta(days=91)
    assert store.purge()["staging_deleted"] == 1
    monkeypatch.setenv("DATASET_KEEP_DAYS", "30")
    assert store.purge()["examples_deleted"] == 1


def test_llm_client_captures_on_customer_fast_tasks(tmp_path, monkeypatch):
    from app.services.nlu.llm_client import LLMClient

    monkeypatch.setattr(ds, "enabled", lambda: True)     # 2026-11-22 학습 안 함 — 코드 경로 자체만 시험
    monkeypatch.setenv("DATASET_DB", str(tmp_path / "live.sqlite3"))
    env = {"OPENAI_API_KEY": "o", "CUSTOMER_LLM_PROVIDER": "openai", "DEEPSEEK_API_KEY": "d", "DEEPSEEK_MODEL": "m"}

    def factory(**kw):
        def create(**req):
            msg = SimpleNamespace(content='{"keyword": "사과"}')
            return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=None, model=req["model"])
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    ds.CURRENT_SESSION.set("sess-1")
    LLMClient(SYSTEM, provider="deepseek", env=env, task="shop_keyword", openai_factory=factory).chat_json("사과 추천해줘")
    LLMClient(SYSTEM, provider="deepseek", env=env, task="food_knowledge", openai_factory=factory).chat_json("딸기 제철")
    import sqlite3

    rows = sqlite3.connect(tmp_path / "live.sqlite3").execute("SELECT session_id, task, input, teacher FROM staging").fetchall()
    assert rows == [("sess-1", "shop_keyword", "사과 추천해줘", "openai:gpt-5.4-mini")]


def test_capture_off_by_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DATASET_CAPTURE", "0")
    monkeypatch.setenv("DATASET_DB", str(tmp_path / "off.sqlite3"))
    ds.capture("shop_keyword", "사과", {"keyword": "사과"}, "openai:m", SYSTEM)
    assert not (tmp_path / "off.sqlite3").exists()


# ── 2026-11-22 22:10 사용자 결정: 학습 안 함 (3-D ①) ─────────────────────────────
def test_setting_on_still_captures_nothing(tmp_path, monkeypatch, caplog):
    """설정을 켜도 담지 않는다 (경고만)."""
    monkeypatch.setenv("DATASET_CAPTURE", "1")
    monkeypatch.setenv("DATASET_DB", str(tmp_path / "on.sqlite3"))
    monkeypatch.setattr(ds, "_WARNED", False)
    with caplog.at_level("WARNING"):
        assert ds.enabled() is False and ds.requested() is True
        ds.capture("shop_keyword", "사과 추천", {"keyword": "사과"}, "openai:m", SYSTEM)
        ds.note_query("사과", ["상품"])
    assert not (tmp_path / "on.sqlite3").exists()
    assert any("무시" in r.getMessage() for r in caplog.records)


def test_llm_client_captures_nothing_even_when_setting_on(tmp_path, monkeypatch):
    from app.services.nlu.llm_client import LLMClient

    monkeypatch.setenv("DATASET_CAPTURE", "1")
    monkeypatch.setenv("DATASET_DB", str(tmp_path / "live2.sqlite3"))
    env = {"OPENAI_API_KEY": "o", "CUSTOMER_LLM_PROVIDER": "openai", "DEEPSEEK_API_KEY": "d", "DEEPSEEK_MODEL": "m"}

    def factory(**kw):
        def create(**req):
            msg = SimpleNamespace(content='{"keyword": "사과"}')
            return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=None, model=req["model"])
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    LLMClient(SYSTEM, provider="deepseek", env=env, task="shop_keyword", openai_factory=factory).chat_json("사과 추천해줘")
    assert not (tmp_path / "live2.sqlite3").exists()


def test_export_script_refuses(tmp_path):
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "export_dataset_off", Path(__file__).resolve().parents[3] / "scripts" / "export_dataset.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.main(["--task", "shop_keyword", "--out", str(tmp_path / "x")]) == 2
    assert not (tmp_path / "x").exists()


def test_admin_shows_off(tmp_path, monkeypatch):
    monkeypatch.setenv("DATASET_DB", str(tmp_path / "admin.sqlite3"))
    from app.admin.routes import ai_dataset

    got = ai_dataset(None)
    assert got["status"] == "off" and got["off_since"] == ds.TRAINING_OFF_SINCE and got["queue"] == []
