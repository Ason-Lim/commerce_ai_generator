"""2026-11-21 로컬 모델(Ollama) 학습 데이터셋 — 운영하면서 쌓기 · 확인 · 내보내기.

넘어가는 기준: 짧은 정리 작업만 담음(글 생성 작업·내부 작업은 안 담음), 개인정보 모양 문장은 담지 않음, 학습 칸에 세션 값 없음,
클릭이면 silver · 사람 확인이면 gold(이후 승격이 gold 를 덮지 않음), 내보내기는 문장 해시로 학습·시험 고정·gold 우선·출처 거르기,
임시 칸 90일·학습 칸 보관 기간 뒤 지움, 대화 경로에서 실제로 담기(LLMClient).
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
    store.capture("shop_keyword", "사과  5kg 추천해줘", {"keyword": "사과"}, "openai:gpt-5.4-mini", SYSTEM, "clicker")
    store.capture("shop_keyword", "사과 5kg 추천해줘", {"keyword": "사과"}, "openai:gpt-5.4-mini", SYSTEM, "other")
    store.capture("chat_intent", "고마워 근데 배도", {"intent": "shop"}, "openai:gpt-5.4-mini", SYSTEM, "x")
    store._clock["t"] = T0 + timedelta(hours=2)
    done = store.promote(lambda sid, a, b: sid == "clicker")
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


def test_export_split_is_stable_and_gold_first(store):
    for i in range(40):
        store.capture("shop_keyword", f"상품 {i} 추천", {"keyword": f"상품{i}"}, "openai:gpt-5.4-mini", SYSTEM, f"s{i}")
    store.capture("shop_keyword", "상품 1 추천", {"keyword": "틀림"}, "deepseek:flash", SYSTEM, "z")
    store._clock["t"] = T0 + timedelta(hours=2)
    store.promote(lambda sid, a, b: True)
    first = store.export("shop_keyword")
    assert len(first["train"]) + len(first["test"]) == 40                 # 같은 문장은 하나만
    assert first == store.export("shop_keyword")                          # 다시 내보내도 같음
    for split, rows in first.items():
        for r in rows:
            assert ds.split_of("shop_keyword", r["messages"][1]["content"]) == split
            assert r["messages"][0]["content"] == SYSTEM and json.loads(r["messages"][2]["content"])
    no_ds = store.export("shop_keyword", exclude_teachers=("openai",))
    assert [r["teacher"] for rows in no_ds.values() for r in rows] == ["deepseek:flash"]
    wrong = next(x for x in store.queue(limit=100) if json.loads(json.dumps(x["output"])) == {"keyword": "틀림"})
    store.review(wrong["id"], "fix", output={"keyword": "상품1"})
    row = next(r for rows in store.export("shop_keyword").values() for r in rows if r["messages"][1]["content"] == "상품 1 추천")
    assert row["label"] == "gold" and json.loads(row["messages"][2]["content"]) == {"keyword": "상품1"}
    # 고친 정답이 새 값이면 출처는 사람
    other = next(x for x in store.queue(limit=100) if x["input"] == "상품 2 추천")
    store.review(other["id"], "fix", output={"keyword": "상품 둘"})
    row2 = next(r for rows in store.export("shop_keyword").values() for r in rows if r["messages"][1]["content"] == "상품 2 추천")
    assert row2["label"] == "gold" and row2["teacher"] == "human:operator"


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

    monkeypatch.setenv("DATASET_CAPTURE", "1")
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
