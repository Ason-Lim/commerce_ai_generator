"""실수 신호 모으기 (2026-11-16) — 오늘 화면에서 찾은 실수가 신호로 잡히는지."""
import json
import os
from contextlib import contextmanager

from app.services.chat import miss_signals as M


@contextmanager
def env(**kv):
    old = {k: os.environ.get(k) for k in kv}
    os.environ.update(kv)
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _rows(tmp):
    return [json.loads(l) for p in tmp.glob("*.jsonl") for l in p.read_text(encoding="utf-8").splitlines()]


def _products(*names):
    return {"session_id": "s", "stage": "products",
            "blocks": [{"type": "product_list", "data": {"items": [{"product_name": n} for n in names]}}]}


def test_words_drop_request_words_and_unify_spelling():
    assert M.words("최강록 쉐프 라면 추천해 줘") == ["최강록", "셰프", "라면"]


def test_a_weak_match_and_a_requery_are_recorded(tmp_path):
    M._LAST.clear()
    with env(MISS_SIGNALS="on", MISS_SIGNALS_DIR=str(tmp_path)):
        _weak_then_requery(tmp_path)


def _weak_then_requery(tmp_path):
    # 2026-11-16 실제 화면: '최강록 쉐프 라면' → 청정원 쉐프의 치킨스톡·홍게라면이 섞였다
    M.observe("sess1", "최강록 쉐프 라면", _products("한일식품 본고장 홍게라면 나베 127g", "청정원 쉐프의 치킨스톡",
                                                    "고메 최강록 셰프 마제소바 2인분"))
    weak = [r for r in _rows(tmp_path) if r["kind"] == "weak_match"]
    assert len(weak) == 1 and weak[0]["items"] == ["한일식품 본고장 홍게라면 나베 127g", "청정원 쉐프의 치킨스톡"]
    M.observe("sess1", "다른 거 보여줘", _products("고메 최강록 셰프 마제소바 2인분"))
    req = [r for r in _rows(tmp_path) if r["kind"] == "requery"]
    assert req and req[0]["before"] == "최강록 쉐프 라면"


def test_good_results_record_nothing_and_off_switch_works(tmp_path):
    M._LAST.clear()
    with env(MISS_SIGNALS="on", MISS_SIGNALS_DIR=str(tmp_path)):
        _good(tmp_path)


def _good(tmp_path):
    M.observe("s2", "생크림 500mL", _products("서울우유 생크림 500mL", "매일 생크림 500ml"))
    assert _rows(tmp_path) == []
    with env(MISS_SIGNALS="off"):
        M.record("zero", text="x")
    assert _rows(tmp_path) == []


def test_zero_results_and_a_left_review_note(tmp_path):
    with env(MISS_SIGNALS="on", MISS_SIGNALS_DIR=str(tmp_path)):
        _zero_review()
    assert sorted(r["kind"] for r in _rows(tmp_path)) == ["review_left", "zero"]


def _zero_review():
    M.observe("s3", "최강록 라면 레시피", {"stage": "recipe_other", "blocks": [{"type": "text", "data": {"md": "글을 찾지 못했어요."}}]})
    M.observe("s3", "라면 만드는 법", {"stage": "recipe_ai", "blocks": [{"type": "text", "data": {"md": "**검토 AI 의견** 노른자"}}]})


def test_the_report_groups_repeated_sentences(tmp_path):
    import importlib.util

    with env(MISS_SIGNALS="on", MISS_SIGNALS_DIR=str(tmp_path)):
        for _ in range(2):
            M.record("zero", text="엉뚱한 상품", what="상품")
    spec = importlib.util.spec_from_file_location("mr", "scripts/miss_report.py")
    mr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mr)
    text = mr.report(mr.load(tmp_path, 7), 7)
    assert "**엉뚱한 상품** ×2" in text and "| 하나도 못 찾음 (zero) | 2 |" in text
